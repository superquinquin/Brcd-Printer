import re
import sys
from PIL.Image import Image
from barcode.ean import EAN13, EAN8, EAN14
from barcode.isxn import ISBN10, ISBN13, ISSN
from barcode.upc import UPCA
from barcode.writer import ImageWriter

from typing import Literal, TypeVar

_BarcodesTypes = TypeVar("_BarcodesTypes", EAN13, EAN8, EAN14, ISBN10, ISBN13, ISSN, UPCA)
BarcodeTypes = Literal["EAN13", "EAN8","EAN14", "ISBN-13", "ISBN-10"]
EAN8_PATTERN = re.compile(r'^[0-9]{8}$')
EAN13_PATTERN = re.compile(r'^[0-9]{13}$')
EAN14_PATTERN =re.compile(r'^[0-9]{14}$')
ISBN10_PATTERN = re.compile(r'^[0-9]-([0-9]{4}-){2}[0-9]$')
ISBN13_PATTERN = re.compile(r'^[0-9]{3}-[0-9]-([0-9]{4}-){2}[0-9]$')
ISSN_PATTERN = re.compile(r'^[0-9]{4}-[0-9]{3}[xX0-9]$')
UPCA_PATTERN = re.compile(r'^[0-9]{12}$')
# CODE_39_PATTERN = re.compile(r'^\*[A-Z0-9 -$%./+]*\*$')
# CODE_128_PATTERN = re.compile(r'{1,60}')


class BarcodeGenerator(object):
    __patterns = ["EAN13_PATTERN", "EAN8_PATTERN", "EAN14_PATTERN", "ISBN10_PATTERN", "ISBN13_PATTERN", "ISSN_PATTERN", "UPCA_PATTERN"]
    __writer = ImageWriter()
    def __init__(self, __ean: _BarcodesTypes) -> None:
        self._parser = self.__infer(__ean)
        if self._parser is None:
            raise ValueError(f"Input {__ean} does not fit any barcodes patterns")
        self.barcode = self._parser(__ean, self.__writer)

    def write(self, fp:str, dimensions: tuple[int, int | None]) -> None:
        img = self.barcode.render()
        img = self._resize(img, dimensions)
        img.save(fp)
        
    def _resize(self,img:Image, dimensions: tuple[int, int | None]) -> Image:
        if dimensions[1] is None:
            dimensions = (dimensions[0], img.size[1])
        return img.resize(dimensions)

    def __infer(self, __ean: _BarcodesTypes) -> None:
        module, parser = sys.modules[__name__], None
        for p in self.__patterns:
            _pattern = getattr(module, p)
            if bool(re.search(_pattern, __ean)):
                parser = getattr(module, p.removesuffix("_PATTERN"))
                break
        return parser


if __name__ == "__main__":
    ean13 = BarcodeGenerator("1234567890128")
    ean8 = BarcodeGenerator("65833254")
    ean14 = BarcodeGenerator("40700719670720")
    isbn10 = BarcodeGenerator("2-1234-5680-2")
    isbn13 = BarcodeGenerator("978-2-1234-5680-3")
    issn = BarcodeGenerator("1144-875X")
    upca = BarcodeGenerator("697929110035")
    assert type(ean13.barcode).__name__ == "EuropeanArticleNumber13"
    assert type(ean8.barcode).__name__ == "EuropeanArticleNumber8"
    assert type(ean14.barcode).__name__ == "EuropeanArticleNumber14"
    assert type(isbn10.barcode).__name__ == "InternationalStandardBookNumber10"
    assert type(isbn13.barcode).__name__ == "InternationalStandardBookNumber13"
    assert type(issn.barcode).__name__ ==  "InternationalStandardSerialNumber"
    assert type(upca.barcode).__name__ == "UniversalProductCodeA"