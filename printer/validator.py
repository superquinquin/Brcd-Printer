from sanic.request import Request
from sanic.response import text
from functools import wraps

MAX_QTY = 32


def form_validator(f):
    def validate_ean(ean: str) -> bool:
        v = False
        if len(ean) == 13 and ean.isnumeric():
            v = True
        return v

    def validate_qty(qty: str) -> bool:
        v = False
        if qty.isnumeric() and  0 < int(qty) < MAX_QTY:
            v = True
        return v
    
    @wraps(f)
    def wrapper(*args, **kwargs):
        validated_ean, validated_qty = False, False
        request: Request = args[0]
        form = request.get_form()
        
        ean = form.get("barcode", None)
        qty = form.get("quantity", None)
        if ean is not None:
            validated_ean = validate_ean(ean)
        if qty is not None:
            validated_qty = validate_qty(qty)
        
        if validated_ean and validated_qty:
            return f(*args, **kwargs)
        elif validated_ean is False and validated_qty is False:
            return text("ean & qty pas OK")
        elif validated_ean is False:
            return text("ean pas OK")
        else:
            return text("qty pas OK")
    return wrapper


