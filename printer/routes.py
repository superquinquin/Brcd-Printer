from __future__ import annotations

from sanic import Blueprint
from sanic.request import Request
from sanic.response import json
from sanic_ext import render

from typing import Coroutine

from printer.validator import validator, odoo_validator, logging_hook
from printer.utils import parse_subean
from printer.db import Database
from printer.odoo import Odoo
from printer.printers import Printer

printer = Blueprint("printer")

@printer.get("/")
@logging_hook
async def index(request: Request):
    return await render("index.html")

@printer.post("/job")
@logging_hook
@validator
@odoo_validator
async def job(request: Request) -> Coroutine:
    pname = request.ctx.printer
    payload = request.ctx.payload
    
    if pname is None:
        pname = request.app.ctx.default_printer
    printer: Printer = request.app.ctx.printers.get(pname, None)
    
    if printer is None:
        return json({"type":"err","msg": "L'imprimante sélectionnée n'existe pas."},status=500)    
    printer.print_job(**payload)
    return json({"type":"ok", "msg": f"Code-barres: {payload['barcode'].value} imprimé"},status=200)


@printer.post("/getHint")
@logging_hook
async def hinting(request: Request) -> Coroutine:
    payload = parse_subean(request.load_json())

    opts = request.app.ctx.options
    enabled_hinting = opts.get("ean_hinting", False)
    odoo_hinting = opts.get("odoo_hinting", False)
    min_chars_for_odoo = opts.get("min_chars_for_odoo_hint", 4)
    odoo_limits = opts.get("odoo_hint_limit", 5)
    db_limits = opts.get("db_hint_limit", 5)
    input_len = payload["input"]
    
    if enabled_hinting is False:
        return json({"type": "err","msg": "hinting is desabled"}, status=200)
    
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
@logging_hook
async def get_historic(request:Request) -> Coroutine:
    db: Database = request.app.ctx.db
    res = db.get_historic()
    return json(res, status=200)


@printer.get("/products")
@logging_hook
async def get_products(request:Request) -> Coroutine:
    db: Database = request.app.ctx.db
    res = db.get_products()
    return json(res, status=200)
    
@printer.get("/barcodes")
@logging_hook
async def get_barcodes(request:Request) -> Coroutine:
    db: Database = request.app.ctx.db
    res = db.get_barcodes()
    return json(res, status=200)




