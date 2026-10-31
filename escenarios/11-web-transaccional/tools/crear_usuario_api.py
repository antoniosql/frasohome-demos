"""FraSoHome Live · usuario de base de datos de la API.

Crea (o renueva la contraseña de) el usuario contenido `fsh_api` y el rol `fsh_api_rol`, con
permisos mínimos: SELECT y EXECUTE sobre los esquemas de FraSoHome Live, y nada más. La API
nunca escribe en las tablas directamente: toda escritura pasa por procedimientos almacenados,
que se ejecutan con los permisos de su propietario (encadenamiento de propiedad).

Los permisos se conceden sobre el esquema, así que sobreviven a los reinicios de datos
(sql/00_borrar.sql borra objetos, no esquemas).

Imprime en JSON la cadena de conexión para la app setting SQL_CONNECTION_STRING.

Uso (lo llama tools/configurar_api.ps1):
  python crear_usuario_api.py --server sql-xxx.database.windows.net --admin-login fsh_admin
      (contraseña del administrador en la variable FSH_SQL_ADMIN_PASSWORD)
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import string
import sys
import time

USER = "fsh_api"
ROLE = "fsh_api_rol"
SCHEMAS = ["crm", "catalog", "store", "sales", "returns", "inventory", "quality", "hr", "mkt", "fin", "ref", "xref",
           "rag", "meta", "lab", "app"]


def random_password(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits + "-_.!"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if any(c.islower() for c in pwd) and any(c.isupper() for c in pwd) and any(c.isdigit() for c in pwd):
            return pwd


def connect(conn_str: str):
    """Conecta reintentando mientras la base gratuita se despierta (error 40613)."""
    try:
        import mssql_python as driver  # type: ignore
        open_ = driver.connect
    except ImportError:
        import pyodbc  # type: ignore
        open_ = lambda cs: pyodbc.connect("Driver={ODBC Driver 18 for SQL Server};" + cs)  # noqa: E731
    last = None
    for _ in range(6):
        try:
            return open_(conn_str)
        except Exception as exc:  # noqa: BLE001
            last = exc
            if "40613" not in repr(exc) and "not currently available" not in repr(exc):
                raise
            time.sleep(15)
    raise last


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True, help="servidor, p. ej. sql-xxx.database.windows.net")
    ap.add_argument("--database", default="frasohome-oltp")
    ap.add_argument("--admin-login", required=True)
    ap.add_argument("--port", type=int, default=1433)
    ap.add_argument("--trust-server-certificate", action="store_true", help="solo para pruebas locales")
    args = ap.parse_args()

    admin_pwd = os.environ.get("FSH_SQL_ADMIN_PASSWORD")
    if not admin_pwd:
        print("Falta la variable FSH_SQL_ADMIN_PASSWORD", file=sys.stderr)
        return 2
    trust = "yes" if args.trust_server_certificate else "no"
    base = (f"Server=tcp:{args.server},{args.port};Database={args.database};Encrypt=yes;TrustServerCertificate={trust};"
            "ConnectRetryCount=3;ConnectRetryInterval=10")

    pwd = random_password()
    conn = connect(f"{base};UID={args.admin_login};PWD={admin_pwd}")
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sys.database_principals WHERE name = ?", (USER,))
        exists = cur.fetchone()[0] > 0
        # CREATE/ALTER USER no admiten parámetros: la contraseña se genera aquí y solo contiene
        # caracteres seguros dentro de un literal entre comillas simples.
        cur.execute(f"{'ALTER' if exists else 'CREATE'} USER [{USER}] WITH PASSWORD = '{pwd}'")
        cur.execute(f"IF DATABASE_PRINCIPAL_ID(N'{ROLE}') IS NULL CREATE ROLE [{ROLE}]")
        cur.execute(f"IF IS_ROLEMEMBER(N'{ROLE}', N'{USER}') = 0 ALTER ROLE [{ROLE}] ADD MEMBER [{USER}]")
        missing = []
        for schema in SCHEMAS:
            cur.execute("SELECT SCHEMA_ID(?)", (schema,))
            if cur.fetchone()[0] is None:
                missing.append(schema)
                continue
            cur.execute(f"GRANT SELECT, EXECUTE ON SCHEMA::[{schema}] TO [{ROLE}]")
        conn.commit()
    finally:
        conn.close()
    if missing:
        print(f"Faltan esquemas ({', '.join(missing)}): carga antes los datos (seed/cargar_datos.ps1).", file=sys.stderr)
        return 3

    user_conn = f"{base};UID={USER};PWD={pwd}"
    check = connect(user_conn)
    try:
        cur = check.cursor()
        cur.execute("SELECT COUNT(*) FROM crm.customer")
        customers = cur.fetchone()[0]
    finally:
        check.close()
    print(json.dumps({"user": USER, "created": not exists, "clientes_visibles": customers, "connection_string": user_conn}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
