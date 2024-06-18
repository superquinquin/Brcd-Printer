from __future__ import annotations
from os import environ
from sanic import Sanic
from sanic.log import LOGGING_CONFIG_DEFAULTS

from typing import Dict, Any, Optional

from printer.db import Database
from printer.odoo import Odoo
from printer.printers import Printer
from printer.routes import printer, error_handler
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
    util wrapper for configuring and building app context for brcdPrinter.
    :parameters:
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
        logging: Optional[Payload] | None = None
        ) -> None:
        self.env = env
        self.print_banner()

                
        logging["loggers"].update(LOGGING_CONFIG_DEFAULTS["loggers"])
        logging["handlers"].update(LOGGING_CONFIG_DEFAULTS["handlers"])
        logging["formatters"].update(LOGGING_CONFIG_DEFAULTS["formatters"])
        
        self.app = Sanic("BRCDPrinter", log_config=logging)
        self.app.static('/static', sanic.get("static"))
        self.app.config.update({"ENV": env})
        self.app.config.update({k.upper():v for k,v in sanic.get("app", {}).items()})
        self.app.blueprint(printer)
        self.app.error_handler.add(Exception, error_handler)

        default = printers.get("default", None)
        pprinters = printers.get("printers", None)
        if pprinters is None:
            raise KeyError("You must configure printers")
        self.register_printers(pprinters)
        self.set_default_printer(default)

        if db:
            self.mount_db(db)        
        
        if odoo:
            erp = odoo.get("erp", None)
            if erp is None:
                raise KeyError("you must set odoo credentials")
            self.app.ctx.odoo = Odoo(**erp)

        self.app.ctx.options = options
        self.app.ctx.barcodes = barcodes
            
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