from __future__ import annotations

from sanic import Blueprint
from sanic.request import Request
from sanic.response import text
from sanic_ext import render

from jinja2 import Environment, FileSystemLoader

from barcode.ean import EAN13
from barcode.writer import ImageWriter
from tempfile import NamedTemporaryFile

import brother_ql

from brcdprinter.validator import form_validator


templates = Environment(loader=FileSystemLoader('./brcdprinter/templates/'),enable_async=True)
printer = Blueprint("printer")

@printer.get("/")
async def index(request: Request):
    template = templates.get_template("index.html")
    return await render(template)

@printer.post("/job")
@form_validator
async def job(request: Request):
    form = request.get_form()
    ean, qty = form.get("barcode"), form.get("quantity")    
    brcd = EAN13(ean, writer=ImageWriter())
    with NamedTemporaryFile(suffix=".png") as fp:
        brcd.write(fp)
        
    return text('OK')




