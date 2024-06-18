import re
import logging
import subprocess
from tempfile import NamedTemporaryFile
from typing import Literal, get_args
from printer.barcodes import BarcodeGenerator
from printer.exception import BrotherQLError




Backends = Literal["network", "pyusb", "linux_kernel"]
Models = Literal[
    "QL-500", "QL-550", "QL-560", "QL-570", "QL-580N", "QL-650TD", 
    "QL-700", "QL-710W", "QL-720NW", "QL-800", "QL-810W", "QL-820NWB", 
    "QL-1050", "QL-1060N"
]
Dimensions = Literal[
    "12", "29", "38", "50", "54", "62", "102", "17x54",
    "17x87", "23x23", "29x42", "29x90", "39x90", "39x48", "52x29", "62x29",
    "62x100", "102x51", "102x152", "d12", "d24", "d58"
]
ADR_PATTERN = re.compile(r'^(tcp|udp)://(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
DIMENSIONS = {
    "12": (106, None),
    "29": (306, None),
    "38": (413, None),
    "50": (554, None),
    "54": (590, None),
    "62": (696, None),
    "102": (1164, None),
    "17x54":(165, 566),
    "17x87":(165, 956),
    "23x23":(202, 202),
    "29x42":(306, 425),
    "29x90":(306, 991),
    "39x90":(413, 991),
    "39x48":(425, 495),
    "52x29":(578, 271),
    "62x29":(696, 271),
    "62x100":(696, 1109),
    "102x51":(1164, 526),
    "102x152":(1164, 1660),
    "d12":(94, 94),
    "d24":(236, 236),
    "d58":(618, 618),
}


logger = logging.getLogger("brotherQl")
if logger.hasHandlers() is False:
    logger = None

class Printer(object):
    def __init__(
        self,
        *,
        address: str,
        model: Models,
        backend: Backends, 
        dimensions: Dimensions
        ) -> None:
        
        if bool(re.search(ADR_PATTERN, address)) is False:
            raise ValueError(f'Address argument "{address}" do not comply with recquired pattern {ADR_PATTERN.pattern}')
        if model not in get_args(Models):
            raise ValueError(f'Model argument "{model}" not in {get_args(Models)}')
        if backend not in get_args(Backends):
            raise ValueError(f'Backend argument "{backend}" not in {get_args(Backends)}')
        if dimensions not in DIMENSIONS.keys():
            raise ValueError(f'Printer dimension "{dimensions}" not in {list(DIMENSIONS.keys())}')
        
        self.address = address
        self.model = model
        self.backend = backend
        self.dimensions = dimensions
        self.img_dimensions = DIMENSIONS.get(dimensions)
       
    async def print_job(self, barcode: BarcodeGenerator, qty: int) -> None:
        with NamedTemporaryFile(suffix=".png") as fp:
            barcode.write(fp.name, self.img_dimensions)
            await self._print(fp.name, qty)
        
    async def _print(self, fp: str, qty: int) -> None:
        cmd = ["brother_ql", "-b", self.backend, "-m", self.model, "-p", self.address, "print", "-l", self.dimensions, fp]
        for _ in range(qty):
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            out = p.communicate(timeout=5)
            self.parse_job_communication(out)
            
    def parse_job_communication(self, res: tuple[str, str]) -> None:
        out, err = res
        out, err = out.decode("utf-8"), err.decode("utf-8")
        if "Traceback" in err and logger is not None:
            err = out + err
            logger.error(err.strip("\n"))
            raise BrotherQLError()
        elif "Traceback" in err and logger is None:
            raise BrotherQLError()
        elif "Traceback" not in err and logger is not None:
            out= out + err
            logger.info(out.strip("\n"))
            
