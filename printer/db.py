from __future__ import annotations
from functools import partial
from sqlite3 import Cursor, Row, connect

from typing import Dict, Any, TypeVar, Literal, Optional

Record = Dict[str, Any]
_SqliteTypes = TypeVar("_SqliteTypes", str, int, bool, bytes)
_ColNames = str
TableName = Literal["historic", "product", "barcodes"]

class Database(object):
    def __init__(self, *, fp: str) -> None:
        self.con = connect(fp)
        self.cursor = self.con.cursor()
        self.con.row_factory = self.record_factory
        self._build_products_table()
        self._build_historic_table()
        self._build_barcodes_table()

    @staticmethod
    def record_factory(cursor: Cursor, row: Row) -> dict[_ColNames, _SqliteTypes]:
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}
    
    def add_product(self, values: list[_SqliteTypes]) -> int:
        _writer = partial(self._write, tn="product", cn=["pid", "name"])
        return _writer(values=values)
    
    def add_barcode(self, values: list[_SqliteTypes]) -> int:
        _writer = partial(self._write, tn="barcodes", cn=["barcode", "product_id"])
        return _writer(values=values)

    def add_historic(self, values:list[_SqliteTypes]) -> int:
        _writer = partial(self._write, tn="historic", cn=["timestamp", "barcode", "quantity", "success", "product_id", "error_name"])
        return _writer(values=values)
    
    def get_historic(self) -> dict[str, _SqliteTypes]:
        return self.con.execute(
            f"""
            SELECT *
            FROM historic;
            """
        ).fetchall()
    
    def get_products(self) -> dict[_ColNames, _SqliteTypes]:
        res = self.con.execute(
                f"""
                SELECT product.id, product.name, product.pid, barcode
                FROM product
                JOIN barcodes ON product.id = barcodes.product_id;
                """
        ).fetchall()
        
        products = {}
        for p in res:
            record = products.get(p['id'], None)
            if record:
                record["barcodes"].append(p["barcode"])
            else:
                barcode = p.pop("barcode")
                p.update({"barcodes": [barcode]})
                products[p["id"]] = p    
        return products
    
    def get_barcodes(self) -> dict[_ColNames, _SqliteTypes]:
        return self.con.execute(
            f"""
            SELECT product.id, product.name, product.pid, barcode
            FROM barcodes
            JOIN product ON product_id = product.id;
            """
        ).fetchall()
    
    def search_product_by_pid(self, pid: int) -> dict[_ColNames, _SqliteTypes] | None:
        return self.con.execute(
            f"""
            SELECT id, pid, name
            FROM product
            WHERE pid = {pid};
            """
        ).fetchone()
        
    def search_product(self, barcode: str) -> Record:
        return self.con.execute(
            f"""
            SELECT product.pid, product.name, barcodes.barcodes
            FROM barcodes
            JOIN product ON barcodes.product_id = product.id
            WHERE barcode = "{barcode}";
            """
        ).fetchone()
        
    def fuzzy_search_product(self, input: str, _type: str, limit: int) -> list[Record]:
        if _type == "barcode":
            res = self._fuzzy_search_product_barcode(input, limit)
        else:
            res = self._fuzzy_search_product_name(input, limit)
        return res
        
    def _fuzzy_search_product_barcode(self, barcode:str, limit: Optional[int] | None = None) -> list[Record]:
        res = self.con.execute(
            f"""
            SELECT product.name, product.pid, barcode
            FROM barcodes
            JOIN product ON barcodes.product_id = product.id
            WHERE barcode LIKE "%{barcode}%"{self._parse_limit(limit)};
            """
        ).fetchall()
        
        # -- multiple barcodes can lead to the same product. 
        # -- we must return unique selection of products.
        products, seen = [], set()
        for r in res:
            pid = r["pid"]
            if pid not in seen:
                seen.add(pid)
                products.append(r)
        return products
    
    def _fuzzy_search_product_name(self, name: str, limit: Optional[int] | None = None) -> list[Record]:
        res = self.con.execute(
            f"""
            SELECT product.name, product.pid, barcode
            FROM barcodes
            JOIN product ON barcodes.product_id = product.id
            WHERE product.name LIKE "%{name}%"{self._parse_limit(limit)};
            """
        )
        products, seen = [], set()
        for r in res:
            pid = r["pid"]
            if pid not in seen:
                seen.add(pid)
                products.append(r)
        return products

    @staticmethod
    def _parse_limit(limit: int | None) -> str:
        lmt = ""
        if limit is not None:
            lmt = f" LIMIT {str(limit)}"
        return lmt

    def _write(self, tn:TableName, cn: list[_ColNames], values: list[_SqliteTypes]) -> int:
        _cn_str, _v_anchors = ' ,'.join(cn), ' ,'.join(["?" for _ in range(len(values))])
        self.cursor.execute(f"INSERT OR IGNORE INTO {tn}({_cn_str}) VALUES({_v_anchors});", tuple(values))
        self.con.commit()
        return self.cursor.lastrowid 
        

    def _build_historic_table(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS historic
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                barcode TEXT NOT NULL,
                quantity INT NOT NULL,
                success BOOL NOT NULL,
                product_id INTEGER,
                error_name TEXT,
                FOREIGN KEY(product_id) REFERENCES product(id)
            );
            """
        )
        self.con.commit()
    
    def _build_products_table(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS product
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pid INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL
            );
            """
        )
        self.con.commit()
        
    def _build_barcodes_table(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS barcodes
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE NOT NULL,
                product_id INTEGER,
                FOREIGN KEY(product_id) REFERENCES product(id)
            );
            """
        )
        self.con.commit()
