from sanic.request import Request
from datetime import datetime
from functools import wraps

from printer.barcodes import BarcodeGenerator
from printer.odoo import Odoo
from printer.db import Database
from printer.exception import QtyIncorrect, UnknownBarcodeFormat, NotAcceptedBarcodeFormat, ProductNotFound

from typing import Coroutine

def validator(f) -> Coroutine:
    @wraps(f)
    def wrapper(*args, **kwargs) -> Coroutine:
        request: Request = args[0]
        payload = request.load_json()
        db: Database = request.app.ctx.db
        brcd_opts = request.app.ctx.barcodes
        max_qty = brcd_opts.get("max_qty", 32)
        enabled_brcd = brcd_opts.get("accepted_types", ["ean13"])
        
        qty = payload["qty"] 
        if qty.isnumeric() is False or int(qty) > max_qty:
            raise QtyIncorrect(max_qty)
        try:
            barcode = BarcodeGenerator(payload["barcode"])
        except ValueError:
            db.add_historic([datetime.now().isoformat(), payload["barcode"], payload["qty"], False, None, "barcode doesn't fit any formats"])
            raise UnknownBarcodeFormat()
        
        if barcode.btype not in enabled_brcd:
            db.add_historic([datetime.now().isoformat(), payload["barcode"], payload["qty"], False, None, "barcode type not accepted"])
            raise NotAcceptedBarcodeFormat(barcode.btype)
            
        request.ctx.printer = payload.get("printer", None)
        request.ctx.payload = {"barcode": barcode, "qty": int(qty)}
        return f(*args, **kwargs)
    return wrapper

def odoo_validator(f) -> Coroutine:
    @wraps(f)
    def wrapper(*args, **kwargs) -> Coroutine:
        request: Request = args[0]
        payload = request.ctx.payload
        db: Database = request.app.ctx.db
        odoo: Odoo = request.app.ctx.odoo
        opts = request.app.ctx.options
        
        barcode = payload["barcode"].value
        odoo_product = odoo.search_product_by_barcodes(barcode)        
        if opts.get("odoo_verification", True) is False:
            db.add_historic([datetime.now().isoformat(), barcode, payload["qty"], True, None, None])
            return f(*args, **kwargs)
        
        if bool(odoo_product) is False:
            db.add_historic([datetime.now().isoformat(), barcode, payload["qty"], False, None, "Product not found in Odoo"])
            raise ProductNotFound(str(barcode))
        
        product = db.search_product_by_pid(odoo_product.id)
        if product:
            rowid = product["id"]
        else:
            rowid = db.add_product([odoo_product.id, odoo.get_name_translation(odoo_product.product_tmpl_id)])    
        db.add_barcode([barcode, rowid])
        db.add_historic([datetime.now().isoformat(), barcode, payload["qty"], True, rowid, None])
        return f(*args, **kwargs)
    return wrapper