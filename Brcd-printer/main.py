from sanic import Sanic
from sanic.request import Request
from sanic.response import text
from sanic_ext import render

from PIL import Image
from io import BytesIO


from barcode.ean import EAN13
from barcode.writer import ImageWriter
from tempfile import NamedTemporaryFile

import brother_ql


app = Sanic(__name__)
app.static('/static', "./static")




@app.get("/")
async def index(request: Request):
    return await render("index.html")

@app.post("/job")
async def job(request: Request):
    form = request.get_form()
    
    ean = form["barcode"][0]
    brcd = EAN13(ean, writer=ImageWriter())
    with NamedTemporaryFile(suffix=".png") as fp:
        brcd.write(fp)
        
    return text('OK')




