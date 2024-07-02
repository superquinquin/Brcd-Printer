from __future__ import annotations

import logging
import traceback
from time import perf_counter
from sanic import Blueprint
from sanic.request import Request
from sanic.response import HTTPResponse, json
from sanic_ext import render

from printer.validator import validator, odoo_validator
from printer.utils import parse_subean
from printer.db import Database
from printer.odoo import Odoo
from printer.printers import Printer
from printer.exception import (
    BrcdPrinterException,
    UnknownPrinter,
    HintingDesabled
)


logger = logging.getLogger("endpointAccess")
printer = Blueprint("printer")

async def error_handler(request: Request, exception: Exception):
    perf = round(perf_counter() - request.ctx.t, 5)
    status = getattr(exception, "status", 500)
    logger.error(
        f"{request.host} > {request.method} {request.url} : {str(exception)} [{request.load_json()}][{str(status)}][{str(len(str(exception)))}b][{perf}s]"
    )
    if not isinstance(exception.__class__.__base__, BrcdPrinterException):
        # log traceback of non handled errors
        logger.error(traceback.format_exc())
    return json({"type":"err", "msg": str(exception)}, status=status)

@printer.on_request(priority=100)
async def go_fast(request: Request) -> HTTPResponse:
    request.ctx.t = perf_counter()

@printer.on_response(priority=100)
async def log_exit(request: Request, response: HTTPResponse) -> HTTPResponse:
    perf = round(perf_counter() - request.ctx.t, 5)
    if response.status == 200:
        logger.info(
            f"{request.host} > {request.method} {request.url} [{request.load_json()}][{str(response.status)}][{str(len(response.body))}b][{perf}s]"
        )


@printer.get("/")
async def index(request: Request):
    return await render("index.html")

@printer.post("/job")
@validator
@odoo_validator
async def job(request: Request) -> HTTPResponse:
    pname = request.ctx.printer
    payload = request.ctx.payload

    if pname is None:
        pname = request.app.ctx.default_printer
    printer: Printer = request.app.ctx.printers.get(pname, None)

    if printer is None:
        raise UnknownPrinter()
    
    await printer.print_job(**payload)
    return json({"type":"ok", "msg": f"Code-barres: {payload['barcode'].value} imprimé"},status=200)


@printer.post("/getHint")
async def hinting(request: Request) -> HTTPResponse:
    payload = parse_subean(request.load_json())

    opts = request.app.ctx.options
    enabled_hinting = opts.get("ean_hinting", False)
    odoo_hinting = opts.get("odoo_hinting", False)
    min_chars_for_odoo = opts.get("min_chars_for_odoo_hint", 4)
    odoo_limits = opts.get("odoo_hint_limit", 5)
    db_limits = opts.get("db_hint_limit", 5)
    input_len = payload["input"]

    if enabled_hinting is False:
        raise HintingDesabled()

    elif (odoo_hinting is False or len(input_len) < min_chars_for_odoo):
        # -- use db historical products
        db: Database = request.app.ctx.db
        res = db.fuzzy_search_product(**payload, limit=db_limits)

    elif odoo_hinting:
        odoo: Odoo = request.app.ctx.odoo
        res = odoo.fuzzy_search_product(**payload, limit=odoo_limits)
    payload.update({"results":res})
    return json(payload, status=200)


@printer.get("/historic")
async def get_historic(request:Request) -> HTTPResponse:
    db: Database = request.app.ctx.db
    res = db.get_historic()
    return json(res, status=200)


@printer.get("/products")
async def get_products(request:Request) -> HTTPResponse:
    db: Database = request.app.ctx.db
    res = db.get_products()
    return json(res, status=200)

@printer.get("/barcodes")
async def get_barcodes(request:Request) -> HTTPResponse:
    db: Database = request.app.ctx.db
    res = db.get_barcodes()
    return json(res, status=200)




