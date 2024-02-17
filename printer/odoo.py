from __future__ import annotations
import time
from erppeek import Client, Record

from typing import Dict, Any



class Odoo(object):
    
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        db: str,
        verbose: bool,
        ) -> None:
        self.connect(url, username, password, db, verbose)
    
    def connect(
        self,
        url: str,
        username: str,
        password: str,
        db: str,
        verbose: bool,
        max_retries: int=5
        ) -> None:
        _conn, _tries = False, 0
        while (_conn is False and _tries <= max_retries):
            try:
                self.client = Client(url, verbose=verbose)
                self.log = self.client.login(username, password=password, database=db)
                self.user = self.client.ResUsers.browse(self.log)
                self.tz = self.user.tz
                _conn = True
            except Exception as e:
                time.sleep(5)
                _tries += 1
        
        if _conn is False:
            raise ConnectionError("enable to connect to Odoo.")
    
    def search_product_by_barcodes(self, barcode: str) -> Record | None:
        return self.client.model("product.product").get([("active", "=", True),("barcode","=", barcode)])
        
    def get_name_translation(self, pt: Record) -> str:
        """get PT name or IR translation if any"""
        name = pt.name
        irt = self.client.model("ir.translation").browse([("res_id", "=", pt.id), ("name", "=", "product.template,name")])
        if irt:
            name = irt[0].value
        return name.strip()



    def fuzzy_search_product(self, input:str, _type:str) -> list[Dict[str, Any]]:
        if _type == "barcode":
            res = self._fuzzy_search_product_barcode(input)
        else:
            res = self._fuzzy_search_product_name(input)
        return res
    
    def _fuzzy_search_product_barcode(self, barcode: str) -> list[Dict[str, Any]]:
        res = self.client.model("product.product").browse([("active", "=", True),("barcode", "like", barcode)])
        return [{"barcode": r.barcode, "name": r.name} for r in res]
    
    def _fuzzy_search_product_name(self, name: str) -> list[Dict[str, Any]]:
        res = self.client.model("product.product").browse([("active", "=", True), ("name", "ilike", name)])
        return [{"barcode": r.barcode, "name": r.name} for r in res]