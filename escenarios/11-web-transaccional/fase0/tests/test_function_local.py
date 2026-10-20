"""Prueba local de la función de la fase 0 contra SQL Server y el emulador de Cosmos DB.

Requiere (por ejemplo con Docker Desktop):
  docker run -d --name fsh-sql -p 1433:1433 -e ACCEPT_EULA=Y -e "MSSQL_SA_PASSWORD=Fsh-Local-2026!" mcr.microsoft.com/mssql/server:2022-latest
  docker run -d --name fsh-cosmos -p 8081:8081 -p 1234:1234 mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview

y estas variables (los valores por defecto sirven para los contenedores de arriba):
  FSH_TEST_SQL      cadena de conexión sin "Driver="
  FSH_TEST_COSMOS   endpoint del emulador

Ejecutar desde la carpeta fase0:  python -m pytest -q tests
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

import pytest

azure_functions = pytest.importorskip("azure.functions")

API_DIR = Path(__file__).resolve().parents[1] / "api"
EMULATOR_KEY = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
SQL = os.environ.get("FSH_TEST_SQL", "Server=127.0.0.1,1433;Database=master;UID=sa;PWD=Fsh-Local-2026!;Encrypt=yes;TrustServerCertificate=yes")
COSMOS = os.environ.get("FSH_TEST_COSMOS", "http://localhost:8081")


@pytest.fixture(scope="module")
def fa():
    os.environ.update({"SQL_CONNECTION_STRING": SQL, "COSMOS_ENDPOINT": COSMOS, "COSMOS_KEY": EMULATOR_KEY,
                       "COSMOS_DATABASE": "frasohome"})
    from azure.cosmos import CosmosClient, PartitionKey

    try:
        db = CosmosClient(COSMOS, credential=EMULATOR_KEY).create_database_if_not_exists("frasohome")
        db.create_container_if_not_exists("fase0", partition_key=PartitionKey(path="/pk"))
    except Exception as exc:  # sin emulador no tiene sentido seguir
        pytest.skip(f"Emulador de Cosmos no disponible: {exc!r}")
    sys.path.insert(0, str(API_DIR))
    return importlib.import_module("function_app")


def _call(fa, name, method="GET", headers=None):
    func = getattr(fa, name)
    user_fn = func.build().get_user_function() if hasattr(func, "build") else func
    req = azure_functions.HttpRequest(method=method, url=f"/api/{name}", headers=headers or {}, body=b"")
    resp = user_fn(req)
    return resp, json.loads(resp.get_body())


def test_health_checks_both_sql_drivers_and_cosmos(fa):
    resp, body = _call(fa, "health")
    assert body["sql_mssql_python"]["ok"], body["sql_mssql_python"]
    assert body["sql_pyodbc"]["ok"], body["sql_pyodbc"]
    assert body["cosmos"]["ok"], body["cosmos"]
    assert resp.status_code == 200 and body["ok"]


def test_cookie_requires_csrf_header(fa):
    resp, body = _call(fa, "cookie_set", method="POST")
    assert resp.status_code == 400 and not body["ok"]


def test_cookie_is_httponly_secure_strict(fa):
    resp, body = _call(fa, "cookie_set", method="POST",
                       headers={"X-FSH-CSRF": "1", "X-Forwarded-Host": "frasohome.dataging.com"})
    cookie = resp.headers["Set-Cookie"]
    for flag in ("HttpOnly", "Secure", "SameSite=Strict", "Path=/", "Domain=frasohome.dataging.com"):
        assert flag in cookie
    value = body["sent"]
    _, back = _call(fa, "cookie_check", headers={"Cookie": f"otra=1; fsh_fase0={value}"})
    assert back == {"ok": True, "received": value}
