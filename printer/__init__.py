

from sanic import Sanic

from printer.routes import printer

def create_app():
    app = Sanic(__name__)
    app.static('/static', "./printer/static")
    app.blueprint(printer)
    return app