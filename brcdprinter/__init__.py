

from sanic import Sanic

from brcdprinter.routes import printer

def create_app():
    app = Sanic(__name__)
    app.static('/static', "./brcdprinter/static")
    app.blueprint(printer)
    return app