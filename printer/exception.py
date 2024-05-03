

class BrcdPrinterException(Exception):
    pass

class QtyIncorrect(BrcdPrinterException):
    message = """Qantité incorrect. la quantité doit être entre 1 et {mx_qty}"""
    def __init__(self, mx_qty: int) -> None:
        super().__init__(self.message.format(mx_qty=str(mx_qty)))
        
class UnknownBarcodeFormat(BrcdPrinterException):
    message = """Le code-barres ne correspond à aucun format connu"""
    def __init__(self) -> None:
        super().__init__(self.message)
        
class NotAcceptedBarcodeFormat(BrcdPrinterException):
    message = """Les codes-barres de type "{btype}" ne sont pas acceptés."""
    def __init__(self, btype: str) -> None:
        super().__init__(self.message.format(btype=btype))
        
class ProductNotFound(BrcdPrinterException):
    message = """Le produit (code-barres: {brcd}) n'existe pas dans Odoo"""
    def __init__(self, brcd: str) -> None:
        super().__init__(self.message.format(brcd=brcd))