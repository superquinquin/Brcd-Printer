from __future__ import annotations
import time
from functools import lru_cache
from erppeek import Client, Record

from typing import Dict, Any, Optional

from printer.utils import ttl_hash



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
            except Exception:
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



    def fuzzy_search_product(self, input:str, _type:str, limit: Optional[int] | None = None) -> list[Dict[str, Any]]:
        if _type == "barcode":
            res = self._fuzzy_search_product_barcode(input, limit, ttl_hash=ttl_hash())
        else:
            res = self._fuzzy_search_product_name(input, limit, ttl_hash=ttl_hash())
        return res
    
    @lru_cache(maxsize=32)
    def _fuzzy_search_product_barcode(
        self, 
        barcode: str, 
        limit: Optional[int] | None = None, 
        ttl_hash: Optional[int] | None = None
        ) -> list[Dict[str, Any]]:
        print('in')
        res = self.client.model("product.product").browse([("active", "=", True),("barcode", "like", barcode)], limit=limit)
        return [{"barcode": r.barcode, "name": r.name} for r in res]
    
    @lru_cache(maxsize=32)
    def _fuzzy_search_product_name(
        self, 
        name: str, 
        limit: Optional[int] | None = None,
        ttl_hash: Optional[int] | None = None
        ) -> list[Dict[str, Any]]:
        res = self.client.model("product.product").browse([("active", "=", True), ("name", "ilike", name)], limit=limit)
        return [{"barcode": r.barcode, "name": r.name} for r in res]