
from __future__ import annotations

import os
import time
from contextlib import ContextDecorator
from datetime import datetime
from functools import wraps
from functools import lru_cache
from http.client import CannotSendRequest
from odooly import Client, Record, RecordList, Model
from urllib.parse import urlsplit, urlunsplit, quote

from typing import Any, Callable

from printer.utils import ttl_hash

Conditions = list[tuple[str, str, Any]]

def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return type(value)(_jsonable(v) for v in value)
    return value

def normalize_conditions(conditions: Conditions) -> Conditions:
    return [_jsonable(clause) for clause in conditions]

def resilient(degree: int = 3):
    def decorator(f: Callable):
        @wraps(f)
        def wrapper(*args, **kwargs):
            self: OdooSession = args[0]
            success, tries = False, 0
            while success is False and tries <= degree:
                try:
                    res = f(*args, **kwargs)
                    success = True
                    return res
                except (CannotSendRequest, AssertionError):
                    tries += 1
                    self.renew_session()
            raise ConnectionError("Cannot establish connection with odoo.")
        return wrapper
    return decorator


class OdooConnector(object):
    def __init__(self, host: str, database: str, verbose: bool = False, **kwargs) -> None:
        self.host = host
        self.database = database
        self.verbose = verbose

    @property
    def url(self) -> str:
        user = os.environ.get("ERP_BASIC_USER", None)
        password = os.environ.get("ERP_BASIC_PASSWORD", None)
        if not all([user, password]):
            return self.host
        split = urlsplit(self.host)
        host = split.netloc.rsplit("@", 1)[-1]
        userinfo = f"{quote(str(user), safe='')}:{quote(str(password), safe='')}"
        return urlunsplit((split.scheme, f"{userinfo}@{host}", split.path, split.query, split.fragment))

    @staticmethod
    def credentials() -> tuple[str, str | None, str | None]:
        username = os.environ.get("ERP_USERNAME", None)
        password = os.environ.get("ERP_PASSWORD", None)
        api_key = os.environ.get("ERP_API_KEY", None)
        if username is None or not any([password, api_key]):
            raise ValueError(
                "ERP_USERNAME and one of ERP_PASSWORD / ERP_API_KEY must be set"
            )
        return (username, password, api_key)

    @classmethod
    def from_env(cls) -> OdooConnector:
        host = os.environ.get("ERP_URL", None)
        database = os.environ.get("ERP_DB", None)
        if host is None or database is None:
            raise ValueError("Missing ERP host or database")
        return cls(host, database)

    def make_session(self, max_retries: int = 5, retries_interval: int = 5) -> OdooSession:
        username, password, api_key = self.credentials()

        success, tries, last_error = False, 0, None
        while (success is False and tries <= max_retries):
            try:
                client = Client(
                    self.url + "/jsonrpc", 
                    self.database, 
                    username, 
                    password,
                    api_key=api_key, 
                    verbose=True,
                )
                success = True
                return OdooSession(client, self)
            
            except Exception as exc:
                last_error = exc
                time.sleep(retries_interval)
                tries += 1

        raise ConnectionError(
            f"Unable to generate an Odoo Session: {type(last_error).__name__}: {last_error}"
        ) from last_error


class OdooSession(ContextDecorator):
    client: Client
    connector: OdooConnector

    def __init__(self, client: Client, connector: OdooConnector) -> None:
        self.client = client
        self.connector = connector

    def __enter__(self) -> OdooSession:
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        del self

    def renew_session(self) -> None:
        username, password, api_key = self.connector.credentials()
        client = Client(
            self.connector.url + "/jsonrpc", 
            self.client.env.db_name, 
            username, 
            password,
            api_key=api_key, 
            verbose=False,
        )
        self.client = client

    def model(self, name: str) -> Model:
        return self.client.env[name]

    @resilient(degree=3)
    def get(self, model: str, conditions: Conditions) -> Record | None:
        return self.model(model).get(normalize_conditions(conditions))

    @resilient(degree=3)
    def browse(self, model: str, ids: list[int]) -> Record | RecordList:
        return self.model(model).browse(ids)

    @resilient(degree=3)
    def search(self, model: str, conditions: Conditions, limit: int | None = None) -> RecordList:
        return self.model(model).search(normalize_conditions(conditions), limit=limit)

    @resilient(degree=3)
    def create(self, model: str, values: dict[str, Any]):
        return self.model(model).create(values)

    def search_product_by_barcodes(self, barcode: str) -> Record | None:
        return self.get("product.product", [("active", "=", True),("barcode","=", barcode)])

    def get_name_translation(self, pt: Record) -> str:
        """
        get PT name or IR translation if any
        
        
        Since odoo 16/17, ir.translation has been removed.
        Translations now are contained inside the it's related tables as a `jsonb` type field.

        Apparently, `product.template.name` is supposed to be a `jsonb` field. Although, it's usage is not altered by this modification.
        """
        name = pt.name
        assert isinstance(name, str)
        # irt = self.search("ir.translation", [("res_id", "=", pt.id), ("name", "=", "product.template,name")])
        # if irt:
        #     name = irt[0].value
        return name.strip()

    def fuzzy_search_product(self, input:str, _type:str, limit: int | None = None) -> list[dict[str, Any]]:
        if _type == "barcode":
            res = self._fuzzy_search_product_barcode(input, limit, ttl_hash=ttl_hash())
        else:
            res = self._fuzzy_search_product_name(input, limit, ttl_hash=ttl_hash())
        return res
    
    @lru_cache(maxsize=32)
    def _fuzzy_search_product_barcode(self, barcode: str, limit: int | None = None, ttl_hash: int | None = None) -> list[dict[str, Any]]:
        res = self.search("product.product", [("active", "=", True),("barcode", "like", barcode)], limit=limit)
        return [{"barcode": r.barcode, "name": r.name} for r in res]
    
    @lru_cache(maxsize=32)
    def _fuzzy_search_product_name(self, name: str, limit: int | None = None, ttl_hash: int | None = None) -> list[dict[str, Any]]:
        res = self.search("product.product", [("active", "=", True), ("name", "ilike", name)], limit=limit)
        return [{"barcode": r.barcode, "name": r.name} for r in res]
