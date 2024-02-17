from __future__ import annotations

from sanic import Blueprint
from sanic.request import Request
from sanic.response import text, HTTPResponse, json
from sanic_ext import render

from jinja2 import Environment, FileSystemLoader

# from printer.job import process_print_query
from printer.validator import validator, odoo_validator
from printer.utils import parse_subean
from printer.db import Database
from printer.odoo import Odoo
from printer.printers import Printer
import pprint

from time import perf_counter

printer = Blueprint("printer")

# ip = BROTHER_QL_PRINTER=tcp://192.168.1.174
# model = export BROTHER_QL_MODEL=QL-720NW 
# brother_ql print -l 62x29 ./barcode2.png

@printer.get("/")
async def index(request: Request):
    return await render("index.html")

@printer.post("/job")
@validator
@odoo_validator
async def job(request: Request):
    print('got job request', request.json)
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
async def hinting(request: Request):
    print("running hint search")
    tick = perf_counter()
    payload = parse_subean(request.load_json())

    opts = request.app.ctx.options
    enabled_hinting = opts.get("ean_hinting", False)
    odoo_hinting = opts.get("odoo_hinting", False)
    min_chars_for_odoo = opts.get("min_chars_for_odoo_hint", 4)
    input_len = payload["input"]
    
    if enabled_hinting is False:
        return json({"msg": "hinting is desabled"}, status=200)
    
    elif (odoo_hinting is False or len(input_len) < min_chars_for_odoo) or payload["_type"] == "name":
        # -- use db historical products
        db: Database = request.app.ctx.db
        res = db.fuzzy_search_product(**payload)
    
    elif odoo_hinting:
        odoo: Odoo = request.app.ctx.odoo
        res = None
        res = odoo.fuzzy_search_product(**payload)
        
    print(perf_counter() - tick)
    payload.update({"results":res})
    print(payload)
    return json(payload, status=200)


@printer.get("/historic")
async def get_historic(request:Request):
    db: Database = request.app.ctx.db
    res = db.get_historic()
    return json(res, status=200)


@printer.get("/products")
async def get_products(request:Request):
    db: Database = request.app.ctx.db
    res = db.get_products()
    return json(res, status=200)
    
@printer.get("/barcodes")
async def get_barcodes(request:Request):
    db: Database = request.app.ctx.db
    res = db.get_barcodes()
    return json(res, status=200)




