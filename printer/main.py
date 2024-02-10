from __future__ import annotations
from os import environ
from sanic import Sanic, Config

from typing import Dict, Any, Optional

from printer.db import Database
from printer.printers import Printer
from printer.log import Logger, SimpleStreamLogger
from printer.routes import printer
from printer.parsers import get_config


Payload = Dict[str, Any]

banner = """\
 ______                     _  ______          _                             
(____  \                   | |(_____ \        (_)          _                 
 ____)  )  ____   ____   __| | _____) )  ____  _  ____   _| |_  _____   ____ 
|  __  (  / ___) / ___) / _  ||  ____/  / ___)| ||  _ \ (_   _)| ___ | / ___)
| |__)  )| |    ( (___ ( (_| || |      | |    | || | | |  | |_ | ____|| |    
|______/ |_|     \____) \____||_|      |_|    |_||_| |_|   \__)|_____)|_|    
"""

class Brcdprinter(object):
    """
    util wraper around Sanic webserver.
    handle brcd_configs and env configurations
    :parameterss:
        :app:
        :options:
        :barcodes:
        :printers:
        :db:
        :odoo:
    """
    def __init__(
        self,
        *,
        env: str,
        sanic: Payload,
        options: Payload,
        barcodes: Payload,
        printers: Payload,
        db: Optional[Payload] | None = None,
        odoo: Optional[Payload] | None = None,
        logger: Optional[Payload] | None = None
        ) -> None:
        self.env = env
        self.print_banner()
        
        if logger:
            logging = Logger(**logger)
        else:
            logging = SimpleStreamLogger()
                
        self.app = Sanic("app")
        self.app.static('/static', "./printer/static")
        self.app.blueprint(printer)
        
        if printers.get("printers", None) is None:
            raise KeyError("You must configure printers")
        self.register_printers(printers.get("printers"))
        self.set_default_printer(printers.get("default", None))

        if db:
            self.mount_db(db)        
        
    @classmethod
    def create_app(cls):
        cfg = get_config(environ.get("CONFIG_FILEPATH", "./printer_configs/config.yaml"))
        return cls(**cfg)
    
    def print_banner(self):
        print(banner)
        print(f"Booting {self.env} ENV")
    
    
    def register_printers(self, printers: Payload) -> None:
        self.app.ctx.printers = {k:Printer(**v) for k,v in printers.items()}
    
    def set_default_printer(self, pname: str | None) -> None:
        if pname is not None:
            self.app.ctx.default_printer = pname
        else:
            registered_printers = self.app.ctx.printers
            self.app.ctx.default_printer = registered_printers.keys()[0]
    
    def mount_db(self, db: Payload) -> None:
        kwargs = db.get("kwargs", None)
        db_type = db.get("type", "sqlite")
        if db_type != "sqlite":
            raise ValueError("Only sqlite db are currently handled by the app")
        if kwargs is None:
            raise KeyError("You must pass Kawargs into the db config")
        self.app.ctx.db = Database(**kwargs)
            