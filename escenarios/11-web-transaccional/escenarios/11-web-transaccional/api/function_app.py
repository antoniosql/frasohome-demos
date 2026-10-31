"""FraSoHome Live · API en Azure Static Web Apps (managed Functions, Python 3.11, modelo v2).

Una sola función HTTP recibe /api/* y la reparte con el enrutador de fsh.web; así toda la
lógica se prueba con pytest sin el host de Functions.
"""
from __future__ import annotations

import logging
from urllib.parse import urlsplit

import azure.functions as func

from fsh.app import handle
from fsh.web import Request

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
logging.getLogger("azure").setLevel(logging.WARNING)


@app.route(route="{*ruta}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def api(req: func.HttpRequest) -> func.HttpResponse:
    url = urlsplit(req.url)
    request = Request.build(req.method, url.path, dict(req.headers), req.get_body(), url.query)
    resp = handle(request)
    headers = dict(resp.headers)
    if resp.cookies:
        headers["Set-Cookie"] = resp.cookies[0]
    return func.HttpResponse(resp.encoded(), status_code=resp.status, headers=headers)
