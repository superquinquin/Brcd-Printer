import re


from typing import Dict, Any

Payload = Dict[str, Any]
_fname = str



def parse_subean(payload: Payload) -> Payload:
    def _field_inference(v:str) -> _fname:
        res = "name"
        if bool(re.search(r'^\d*$', v)):
            res = "barcode"
        return res
    
    payload.update({"_type": _field_inference(payload["input"])})
    return payload
