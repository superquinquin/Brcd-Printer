import subprocess
from barcode.ean import EAN13
from barcode.writer import ImageWriter

from tempfile import NamedTemporaryFile

def build_barcode(fp: str, ean: str) -> None:
    brcd = EAN13(ean, writer=ImageWriter())
    img = brcd.render()
    img = img.resize((696, 271))
    img.save(fp.name)
    

def print(fp:str, qty: int) -> None:
    """improvement: make -b, -m, -p, -l configurable"""
    for _ in range(qty):
        subprocess.run(
            [
                "brother_ql",
                "-b", 
                "network",
                "-m",
                "QL-720NW",
                "-p",
                "tcp://192.168.1.174",
                "print",
                "-l",
                "62x29",
                fp.name
            ]
        )
        
def process_print_query(ean: str, qty: int) -> None:
    with NamedTemporaryFile(suffix=".png") as fp:
        build_barcode(fp, ean)
        print(fp, qty)
        