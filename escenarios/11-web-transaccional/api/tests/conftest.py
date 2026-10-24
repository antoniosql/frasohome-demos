"""Pruebas de la API contra SQL Server y el emulador de Cosmos DB en local (no gastan cuota de Azure).

Antes de lanzarlas:
  1. SQL Server y el emulador de Cosmos en Docker (ver README de la fase 3);
  2. datos recién cargados: seed/reset.py --si;
  3. variables SQL_CONNECTION_STRING, COSMOS_ENDPOINT y COSMOS_KEY (las de local).
Las pruebas crean sus propios usuarios (login «t.*») y los borran al terminar.
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fsh import db, usuarios  # noqa: E402
from fsh.app import handle  # noqa: E402
from fsh.web import Request  # noqa: E402

PASSWORD = "Prueba-Segura-2026"

if not os.environ.get("SQL_CONNECTION_STRING"):
    pytest.skip("Faltan SQL_CONNECTION_STRING y COSMOS_* de local: ver tests/conftest.py", allow_module_level=True)


class Client:
    """Cliente HTTP en memoria: guarda la cookie de sesión, pone la cabecera CSRF y una Idempotency-Key nueva."""

    def __init__(self, host: str = "frasohome.dataging.com"):
        self.cookie: str | None = None
        self.host = host

    def request(self, method: str, path: str, body: dict | None = None, *, csrf: bool = True,
                idem: str | None = None, headers: dict | None = None):
        h = {"host": self.host, "x-forwarded-host": self.host, "user-agent": "pytest"}
        if self.cookie:
            h["cookie"] = f"fsh_session={self.cookie}"
        if method != "GET" and csrf:
            h["x-fsh-csrf"] = "1"
        if method == "POST":
            h["idempotency-key"] = idem or uuid.uuid4().hex
        h.update(headers or {})
        path, _, query = path.partition("?")
        raw = json.dumps(body).encode() if body is not None else b""
        resp = handle(Request.build(method, "/api" + path, h, raw, query))
        for c in resp.cookies:
            value = c.split(";")[0].split("=", 1)[1]
            self.cookie = value or None
        resp.json = json.loads(resp.encoded() or b"null")
        return resp

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, body=None, **kw):
        return self.request("POST", path, body or {}, **kw)

    def put(self, path, body=None, **kw):
        return self.request("PUT", path, body or {}, **kw)

    def delete(self, path, **kw):
        return self.request("DELETE", path, **kw)

    def login(self, login: str, password: str = PASSWORD):
        r = self.post("/auth/login", {"login": login, "password": password})
        assert r.status == 200, r.json
        return r


def pick(sql: str, *params):
    return db.scalar(sql, *params)


def admin_sql(sql: str, *params) -> None:
    """Preparación y limpieza que la API no puede hacer (no tiene permisos de escritura directa).
    Con SQL_ADMIN_CONNECTION_STRING las pruebas corren con el usuario de la API (fsh_api) y esto
    usa el administrador; sin ella, todo usa la misma conexión."""
    cs = os.environ.get("SQL_ADMIN_CONNECTION_STRING")
    if not cs:
        db.query(sql + "; SELECT 1 AS ok", *params)
        return
    try:
        import mssql_python
        conn = mssql_python.connect(cs)
    except ImportError:
        import pyodbc
        conn = pyodbc.connect("Driver={ODBC Driver 18 for SQL Server};" + cs)
    try:
        conn.cursor().execute(sql, params)
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(scope="session")
def people():
    """Usuarios de prueba, uno por rol, atados a datos reales."""
    emp_store = db.one("""SELECT TOP 1 a.canonical_employee_id AS e FROM xref.employee_alias a
                          JOIN xref.employee_store s ON s.employee_id = a.canonical_employee_id AND s.canonical_store_id = N'S001'
                          JOIN hr.employee x ON x.employee_id = a.canonical_employee_id AND x.employee_status = N'Activo'
                          WHERE a.source_system = N'POS' ORDER BY a.canonical_employee_id""")["e"]
    manager = db.one("""SELECT TOP 1 m.employee_id AS e FROM hr.employee m JOIN hr.employee e ON e.manager_id = m.employee_id
                        WHERE m.employee_status = N'Activo' AND e.employee_status = N'Activo'
                        GROUP BY m.employee_id ORDER BY COUNT(*) DESC, m.employee_id""")["e"]
    report = pick("SELECT TOP 1 employee_id FROM hr.employee WHERE manager_id = ? AND employee_status = N'Activo' ORDER BY employee_id",
                  manager)
    outsider = pick("""SELECT TOP 1 employee_id FROM hr.employee WHERE employee_status = N'Activo' AND ISNULL(manager_id, N'') <> ?
                       AND employee_id <> ? ORDER BY employee_id DESC""", manager, manager)
    customers = [r["customer_id"] for r in db.query(
        """SELECT TOP 2 customer_id FROM crm.customer WHERE customer_status = N'Activo' AND email_is_valid = 1
           AND marketing_consent = 1 ORDER BY customer_id""")]
    plan = {
        "cliente": (["cliente"], {"customer": [customers[0]]}),
        "cliente2": (["cliente"], {"customer": [customers[1]]}),
        "cajero": (["cajero", "empleado"], {"store": ["S001"], "employee": [emp_store]}),
        "tienda": (["tienda"], {"store": ["S001"]}),
        "almacen": (["tienda"], {"store": ["ONLINE"]}),
        "atencion": (["atencion"], {}), "marketing": (["marketing"], {}), "rrhh": (["rrhh"], {}),
        "manager": (["manager", "empleado"], {"employee": [manager]}), "empleado": (["empleado"], {"employee": [report]}),
        "direccion": (["direccion"], {}), "profesor": (["profesor"], {}), "admin": (["admin"], {}),
    }
    created = []
    for name, (roles, scopes) in plan.items():
        login = f"t.{name}"
        _drop_user(login)
        usuarios.create(login, f"Prueba {name}", roles, scopes, password=PASSWORD, must_change=False, actor="pytest")
        created.append(login)
    info = {"customer": customers[0], "customer2": customers[1], "cashier": emp_store, "manager": manager,
            "report": report, "outsider": outsider}
    yield info
    for login in created:
        _drop_user(login)


def _drop_user(login: str) -> None:
    uid = db.scalar("SELECT user_id FROM app.app_user WHERE login = ?", login)
    if uid is None:
        return
    for table in ("app.user_session", "app.user_role", "app.user_scope", "app.idempotency_key"):
        admin_sql(f"DELETE FROM {table} WHERE user_id = ?", uid)
    admin_sql("DELETE FROM app.app_user WHERE user_id = ?", uid)


@pytest.fixture
def as_role(people):
    def make(role: str) -> Client:
        c = Client()
        c.login(f"t.{role}")
        return c
    return make


@pytest.fixture
def anon():
    return Client()
