from __future__ import annotations
import time
from erppeek import Client, Record
import os

class Odoo(object):
    connected = False
    
    @classmethod
    def connect(
        cls,
        url: str,
        username: str,
        password: str,
        db: str,
        verbose: bool,
        max_retries: int=5,
        **kwargs
        ) -> Odoo:
        
        odoo = cls()
        tries = 0
        while odoo.connected is False:
            if tries > max_retries:
                odoo.connected = False
                raise ConnectionError("enable to connect to Odoo.")
            try:
                odoo.client = Client(url, verbose=verbose)
                odoo.log = odoo.client.login(username, password=password, database=db)
                odoo.user = odoo.client.ResUsers.browse(odoo.log)
                odoo.tz = odoo.user.tz
                odoo.connected = True
                
            except Exception as e:
                print(e)
                tries += 1
                time.sleep(60)
        return odoo
    
    def search_product(self, barcode: str) -> Record | None:
        return self.client.model("product.product").get([("barcode","=", barcode)])
        
    
    def get_name_translation(self, pt: Record) -> str:
        """get PT name or IR translation if any"""
        name = pt.name
        irt = self.browse("ir.translation", [("res_id", "=", pt.id), ("name", "=", "product.template,name")])
        if irt:
            name = irt[0].value
        return name.strip()
