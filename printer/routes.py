from __future__ import annotations

from sanic import Blueprint
from sanic.request import Request
from sanic.response import text
from sanic_ext import render

from jinja2 import Environment, FileSystemLoader

from printer.job import process_print_query
from printer.validator import form_validator


templates = Environment(loader=FileSystemLoader('./printer/templates/'),enable_async=True)
printer = Blueprint("printer")

# ip = BROTHER_QL_PRINTER=tcp://192.168.1.174
# model = export BROTHER_QL_MODEL=QL-720NW 
# brother_ql print -l 62x29 ./barcode2.png

@printer.get("/")
async def index(request: Request):
    template = templates.get_template("index.html")
    return await render(template)

@printer.post("/job")
@form_validator
async def job(request: Request):
    form = request.get_form()
    ean, qty = form.get("barcode"), int(form.get("quantity"))
    process_print_query(ean, qty)
    return await render(templates.get_template("index.html"))








