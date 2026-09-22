from __future__ import annotations

import os
from pathlib import Path
from sanic import Sanic, config
from sanic.log import LOGGING_CONFIG_DEFAULTS

from typing import Dict, Any, Optional

from printer.db import Database
from printer.odoo import OdooConnector
from printer.printers import Printer
from printer.routes import printer, error_handler, go_fast, log_exit
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

        self.app = Sanic("BRCDPrinter", log_config=self.configurate_logging(logging))

        self.app.static('/static', sanic["static"])
        self.app.config.update({k.upper():v for k,v in sanic.get("app", {}).items()})
        self.app.config.update({"ENV": env})
        
        self.app.blueprint(printer)

        self.app.on_request(go_fast, priority=100)
        self.app.on_response(log_exit, priority=100)
        self.app.error_handler.add(Exception, error_handler)

        default = printers.get("default", None)
        pprinters = printers.get("printers", None)
        if pprinters is None:
            raise KeyError("You must configure printers")
        self.register_printers(pprinters)
        self.set_default_printer(default)

        if db:
            self.mount_db(db)        

        connector = OdooConnector.from_env()
        self.app.ctx.odoo = connector
        self.app.ctx.options = options
        self.app.ctx.barcodes = barcodes

    @classmethod
    def create_app(cls, path: str | Path | None = None) -> Brcdprinter:
        env_path = os.environ.get("CONFIG_FILEPATH", None)
        if path is None and env_path is None:
            raise ValueError("Configs file path not found.")
        if path is None:
            path = env_path
        assert path is not None
        configs = get_config(str(path))
        return cls(**configs)

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

    def configurate_logging(self, configs: dict[str, Any] | None = None) -> dict[str, Any]:
        if configs is None:
            return LOGGING_CONFIG_DEFAULTS
        configs["loggers"].update(LOGGING_CONFIG_DEFAULTS["loggers"])
        configs["handlers"].update(LOGGING_CONFIG_DEFAULTS["handlers"])
        configs["formatters"].update(LOGGING_CONFIG_DEFAULTS["formatters"])
        return configs
        