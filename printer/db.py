from __future__ import annotations
from sqlite3 import Cursor, Row, connect

from typing import Dict, Any, TypeVar, Literal

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
    def record_factory(cursor: Cursor, row: Row) -> Dict[str, _SqliteTypes]:
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}
    
    def write(self, tn:TableName, cn: list[_ColNames], values: list[_SqliteTypes]) -> None:
        _cn_str, _v_anchors = ' ,'.join(cn), ' ,'.join(["?" for _ in range(len(values))])
        self.cursor.execute(f"INSERT INTO {tn}({_cn_str}) VALUES({_v_anchors});", tuple(values))
        self.con.commit()
        
    def search_product(self, barcode: str) -> Record:
        return self.con.execute(
            f"""
            SELECT product.pid, product.name, barcodes.barcodes
            FROM barcodes
            JOIN product ON barcodes.product_id = product.id
            WHERE barcode = "{barcode}";
            """
        ).fetchone()
        
    def fuzzy_search_product(self, barcode:str) -> list[Record]:
        res = self.con.execute(
            f"""
            SELECT product.pid, product.name, barcodes.barcodes
            FROM barcodes
            JOIN product ON barcodes.product_id = product.id
            WHERE barcode LIKE %"{barcode}"%;
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
    
    
    def _build_historic_table(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS historic
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                ean TEXT NOT NULL,
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
                pid INTEGER NOT NULL,
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
