#!/bin/sh
sanic asgi:app --host=0.0.0.0 --port=8000 --workers=1