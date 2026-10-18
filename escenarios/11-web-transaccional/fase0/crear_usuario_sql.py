"""FraSoHome Live · fase 0 · usuario de base de datos para la función de prueba.

Crea (o renueva la contraseña de) un usuario contenido `fsh_fase0` en la base
frasohome-oltp. No recibe ningún permiso: a la prueba le basta con conectar y
leer @@VERSION. Imprime en JSON la cadena de conexión para la app setting
SQL_CONNECTION_STRING; nada más sale por pantalla.

Uso (lo llama desplegar.ps1):
  python crear_usuario_sql.py --server sql-xxx.database.windows.net --database frasohome-oltp \
      --admin-login fsh_admin   (la contraseña del administrador va en la variable FSH_SQL_ADMIN_PASSWORD)
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import string
import sys
import time

import mssql_python

USER = "fsh_fase0"


def random_password(length: int = 24) -> str:
    alphabet = string.ascii_letters + string.digits + "-_.!"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        # Azure SQL exige tres de las cuatro clases de caracteres.
        if any(c.islower() for c in pwd) and any(c.isupper() for c in pwd) and any(c.isdigit() for c in pwd):
            return pwd


def connect(conn_str: str):
    """Conecta reintentando: la base gratuita en pausa tarda en despertar (error 40613)."""
    last = None
    for attempt in range(6):
        try:
            return mssql_python.connect(conn_str)
        except Exception as exc:  # noqa: BLE001
            last = exc
            if "40613" not in repr(exc) and "not currently available" not in repr(exc):
                raise
            time.sleep(15)
    raise last


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True)
    ap.add_argument("--database", default="frasohome-oltp")
    ap.add_argument("--admin-login", required=True)
    ap.add_argument("--trust-server-certificate", action="store_true", help="solo para pruebas locales")
    args = ap.parse_args()

    admin_pwd = os.environ.get("FSH_SQL_ADMIN_PASSWORD")
    if not admin_pwd:
        print("Falta la variable FSH_SQL_ADMIN_PASSWORD", file=sys.stderr)
        return 2
    trust = "yes" if args.trust_server_certificate else "no"
    base = f"Server=tcp:{args.server},1433;Database={args.database};Encrypt=yes;TrustServerCertificate={trust};ConnectRetryCount=3;ConnectRetryInterval=10"

    pwd = random_password()
    conn = connect(f"{base};UID={args.admin_login};PWD={admin_pwd}")
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sys.database_principals WHERE name = ?", (USER,))
        exists = cur.fetchone()[0] > 0
        # CREATE/ALTER USER no admiten parámetros: la contraseña se genera aquí y solo
        # contiene caracteres seguros dentro de un literal entre comillas simples.
        verb = "ALTER" if exists else "CREATE"
        cur.execute(f"{verb} USER [{USER}] WITH PASSWORD = '{pwd}'")
        conn.commit()
    finally:
        conn.close()

    # Comprobación: el usuario nuevo conecta.
    user_conn = f"{base};UID={USER};PWD={pwd}"
    check = connect(user_conn)
    check.close()
    print(json.dumps({"user": USER, "created": not exists, "connection_string": user_conn}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
