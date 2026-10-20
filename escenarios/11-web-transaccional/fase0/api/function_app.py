"""FraSoHome Live · Fase 0 · función de prueba.

Comprueba en el entorno real de Azure Static Web Apps (managed Functions, Python 3.11):
  GET  /api/health  -> conecta a Azure SQL con mssql-python y con pyodbc, escribe y lee en Cosmos DB
  POST /api/cookie  -> fija una cookie HttpOnly; Secure; SameSite=Strict
  GET  /api/cookie  -> dice si la cookie vuelve en la siguiente petición

No guarda nada de valor: es una prueba desechable. La API real llega en la fase 3.
"""
from __future__ import annotations

import json
import os
import platform
import secrets
import sys
import time
from datetime import datetime, timezone

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

COOKIE_NAME = "fsh_fase0"
SQL_QUERY = "SELECT @@VERSION AS version, DB_NAME() AS db, SYSUTCDATETIME() AS now_utc"


def _json(body: dict, status: int = 200, headers: dict | None = None) -> func.HttpResponse:
    h = {"Cache-Control": "no-store"}
    h.update(headers or {})
    return func.HttpResponse(json.dumps(body, ensure_ascii=False, default=str, indent=2),
                             status_code=status, mimetype="application/json", headers=h)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def check_sql(driver: str) -> dict:
    """Conecta con el driver indicado y lanza una consulta trivial.

    La base gratuita puede estar en pausa: el primer intento la despierta y suele
    fallar con el error 40613; se reintenta una vez tras 20 segundos.
    """
    conn_str = os.environ.get("SQL_CONNECTION_STRING")
    if not conn_str:
        return {"ok": False, "error": "Falta la app setting SQL_CONNECTION_STRING"}
    started = time.perf_counter()
    try:
        if driver == "mssql_python":
            import mssql_python as mod
            connect = lambda: mod.connect(conn_str)  # noqa: E731
            extra = {"driver_version": getattr(mod, "__version__", "?")}
        else:
            import pyodbc as mod
            drivers = mod.drivers()
            odbc = next((d for d in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server") if d in drivers), None)
            extra = {"driver_version": mod.version, "odbc_drivers": drivers}
            if odbc is None:
                return {"ok": False, "error": "No hay driver ODBC de SQL Server en la imagen", **extra}
            connect = lambda: mod.connect(f"Driver={{{odbc}}};{conn_str}")  # noqa: E731
    except Exception as exc:  # import fallido: es justo lo que la fase 0 quiere saber
        return {"ok": False, "error": f"No se pudo importar {driver}: {exc!r}"}

    attempts = []
    for attempt in (1, 2):
        try:
            conn = connect()
            try:
                cur = conn.cursor()
                cur.execute(SQL_QUERY)
                row = cur.fetchone()
            finally:
                conn.close()
            return {"ok": True, "attempts": attempt, "seconds": round(time.perf_counter() - started, 2),
                    "server_version": str(row[0]).splitlines()[0], "database": row[1], "server_utc": str(row[2]),
                    "previous_errors": attempts, **extra}
        except Exception as exc:
            attempts.append(repr(exc)[:400])
            if attempt == 1 and ("40613" in repr(exc) or "not currently available" in repr(exc)):
                time.sleep(20)
                continue
            break
    return {"ok": False, "seconds": round(time.perf_counter() - started, 2), "errors": attempts, **extra}


def check_cosmos() -> dict:
    """Escribe y relee un documento en el contenedor fase0 y mide las RU."""
    endpoint, key = os.environ.get("COSMOS_ENDPOINT"), os.environ.get("COSMOS_KEY")
    database = os.environ.get("COSMOS_DATABASE", "frasohome")
    if not endpoint or not key:
        return {"ok": False, "error": "Faltan las app settings COSMOS_ENDPOINT / COSMOS_KEY"}
    started = time.perf_counter()
    try:
        from azure.cosmos import CosmosClient

        client = CosmosClient(endpoint, credential=key)
        container = client.get_database_client(database).get_container_client("fase0")
        doc = {"id": "ultima-comprobacion", "pk": "fase0", "comprobado_utc": _now(), "nonce": secrets.token_hex(4)}
        container.upsert_item(doc)
        write_ru = float(container.client_connection.last_response_headers.get("x-ms-request-charge", 0))
        back = container.read_item("ultima-comprobacion", partition_key="fase0")
        read_ru = float(container.client_connection.last_response_headers.get("x-ms-request-charge", 0))
        return {"ok": back.get("nonce") == doc["nonce"], "seconds": round(time.perf_counter() - started, 2),
                "write_ru": write_ru, "read_ru": read_ru}
    except Exception as exc:
        return {"ok": False, "seconds": round(time.perf_counter() - started, 2), "error": repr(exc)[:400]}


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    result = {
        "checked_utc": _now(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "sql_mssql_python": check_sql("mssql_python"),
        "sql_pyodbc": check_sql("pyodbc"),
        "cosmos": check_cosmos(),
    }
    result["ok"] = (result["sql_mssql_python"]["ok"] or result["sql_pyodbc"]["ok"]) and result["cosmos"]["ok"]
    return _json(result, 200 if result["ok"] else 503)


def _public_host(req: func.HttpRequest) -> str:
    """Host que ve el navegador (SWA lo pasa en X-Forwarded-Host), sin puerto."""
    host = req.headers.get("X-Forwarded-Host") or req.headers.get("Host") or ""
    return host.split(",")[0].strip().split(":")[0]


# El worker de Python convierte Set-Cookie en un objeto cookie y, si no lleva Domain, lo
# reemite con "domain=" vacío. Static Web Apps descarta esa cookie. Variantes para comprobarlo:
#   dominio (por defecto): Domain = host público -> la que usará la API real
#   sin-dominio: sin Domain (sale "domain=" vacío)
#   expires: sin Domain y con Expires en vez de Max-Age
COOKIE_VARIANTS = ("dominio", "sin-dominio", "expires")


@app.route(route="cookie", methods=["POST"])
def cookie_set(req: func.HttpRequest) -> func.HttpResponse:
    if req.headers.get("X-FSH-CSRF") != "1":
        return _json({"ok": False, "error": "Falta la cabecera X-FSH-CSRF"}, 400)
    variant = req.params.get("variante", "dominio")
    if variant not in COOKIE_VARIANTS:
        return _json({"ok": False, "error": f"Variante desconocida; usa {', '.join(COOKIE_VARIANTS)}"}, 400)
    value = secrets.token_urlsafe(16)
    cookie = f"{COOKIE_NAME}={value}; Path=/; HttpOnly; Secure; SameSite=Strict"
    if variant == "expires":
        cookie += "; Expires=Wed, 21 Oct 2037 07:28:00 GMT"
    else:
        cookie += "; Max-Age=600"
    host = _public_host(req)
    if variant == "dominio" and host:
        cookie += f"; Domain={host}"
    return _json({"ok": True, "sent": value, "variant": variant, "attempted_set_cookie": cookie},
                 headers={"Set-Cookie": cookie})


@app.route(route="cookie", methods=["GET"])
def cookie_check(req: func.HttpRequest) -> func.HttpResponse:
    raw = req.headers.get("Cookie", "")
    pairs = dict(p.strip().split("=", 1) for p in raw.split(";") if "=" in p)
    value = pairs.get(COOKIE_NAME)
    return _json({"ok": value is not None, "received": value})
