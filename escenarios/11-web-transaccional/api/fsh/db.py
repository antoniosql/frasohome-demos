"""FraSoHome Live · acceso a Azure SQL desde la API.

- Una conexión por hilo, reutilizada entre peticiones (el worker de Python de
  Functions atiende peticiones en un pool de hilos).
- Las escrituras son siempre procedimientos almacenados. `call` los envuelve en
  TRY/CATCH dentro del propio lote: el error vuelve como un último conjunto de
  resultados con su número, así se distinguen los errores de negocio
  (THROW 50000-50999, mensaje para el usuario) de los demás sin depender del
  driver (mssql-python no expone el número de error).
- La base gratuita puede estar en pausa: la primera conexión la despierta y se
  reintenta mientras responde 40613.
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from .web import HttpError

log = logging.getLogger("fsh.db")
_local = threading.local()
_PROC = re.compile(r"^\[?[a-z_]+\]?\.[a-z_0-9]+$")
_PARAM = re.compile(r"^[a-z_0-9]+$")


class BusinessError(HttpError):
    """Regla de negocio incumplida: el mensaje es para el usuario."""

    def __init__(self, number: int, message: str):
        super().__init__(422, message, f"regla_{number}")
        self.number = number


def _connection_string() -> str:
    cs = os.environ.get("SQL_CONNECTION_STRING", "").strip()
    if not cs:
        raise HttpError(503, "La API no tiene configurada la base de datos.", "sin_configuracion")
    return cs


def _connect():
    cs = _connection_string()
    last: Exception | None = None
    for attempt in range(4):
        try:
            try:
                import mssql_python  # type: ignore
                conn = mssql_python.connect(cs)
            except ImportError:
                import pyodbc  # type: ignore
                conn = pyodbc.connect(cs if "driver=" in cs.lower() else "Driver={ODBC Driver 18 for SQL Server};" + cs)
            conn.autocommit = True
            return conn
        except Exception as exc:  # noqa: BLE001
            last = exc
            text = str(exc)
            if "40613" in text or "not currently available" in text or "timeout" in text.lower():
                time.sleep(8)  # la base se está despertando
                continue
            break
    log.error("No se pudo conectar con SQL: %s", re.sub(r"(?i)(pwd|password)=[^;]*", r"\1=***", str(last)))
    raise HttpError(503, "La base de datos no está disponible. Inténtalo de nuevo en un minuto.", "sql_no_disponible")


def connection():
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = _local.conn = _connect()
    return conn


def reset_connection() -> None:
    conn = getattr(_local, "conn", None)
    _local.conn = None
    if conn is not None:
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass


def _param(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return value


def _result_sets(cur) -> list[list[dict[str, Any]]]:
    sets = []
    while True:
        if cur.description:
            cols = [d[0] for d in cur.description]
            sets.append([dict(zip(cols, row)) for row in cur.fetchall()])
        if not cur.nextset():
            break
    return sets


def _broken(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(s in text for s in ("communication link", "connection", "08s01", "40613", "10054", "closed"))


def query(sql: str, *params: Any) -> list[dict[str, Any]]:
    """Consulta de lectura: devuelve el primer conjunto de resultados."""
    for attempt in (1, 2):
        try:
            cur = connection().cursor()
            cur.execute(sql, tuple(_param(p) for p in params))
            sets = _result_sets(cur)
            return sets[0] if sets else []
        except HttpError:
            raise
        except Exception as exc:  # noqa: BLE001
            if attempt == 1 and _broken(exc):
                reset_connection()
                continue
            log.exception("Consulta fallida")
            raise HttpError(500, "Error interno al consultar la base de datos.", "sql_error") from exc
    return []


def one(sql: str, *params: Any) -> dict[str, Any] | None:
    rows = query(sql, *params)
    return rows[0] if rows else None


def scalar(sql: str, *params: Any) -> Any:
    row = one(sql, *params)
    return next(iter(row.values())) if row else None


def call(proc: str, **params: Any) -> list[list[dict[str, Any]]]:
    """Ejecuta un procedimiento y devuelve todos sus conjuntos de resultados."""
    if not _PROC.match(proc):
        raise ValueError(f"Nombre de procedimiento no válido: {proc}")
    names = list(params)
    for n in names:
        if not _PARAM.match(n):
            raise ValueError(f"Parámetro no válido: {n}")
    args = ", ".join(f"@{n} = ?" for n in names)
    batch = (f"SET NOCOUNT ON; BEGIN TRY EXEC {proc} {args}; END TRY "
             "BEGIN CATCH IF XACT_STATE() <> 0 ROLLBACK; "
             "SELECT ERROR_NUMBER() AS __fsh_error, ERROR_MESSAGE() AS __fsh_message; END CATCH")
    values = tuple(_param(params[n]) for n in names)
    try:
        cur = connection().cursor()
        cur.execute(batch, values)
        sets = _result_sets(cur)
    except HttpError:
        raise
    except Exception as exc:  # noqa: BLE001
        if _broken(exc):
            reset_connection()
        log.exception("Error al ejecutar %s", proc)
        raise HttpError(500, "Error interno al guardar en la base de datos.", "sql_error") from exc
    if sets and sets[-1] and "__fsh_error" in sets[-1][0]:
        err = sets[-1][0]
        number, message = int(err["__fsh_error"]), str(err["__fsh_message"])
        if 50000 <= number < 51000:
            raise BusinessError(number, message)
        if number in (2627, 2601):
            raise HttpError(409, "Ya existe un registro con esos datos.", "duplicado")
        if number == 547:
            raise HttpError(409, "La operación hace referencia a algo que no existe o está en uso.", "referencia")
        if number == 1205:
            raise HttpError(503, "La base de datos estaba ocupada. Vuelve a intentarlo.", "interbloqueo")
        log.error("Error SQL %s en %s: %s", number, proc, message)
        raise HttpError(500, "Error interno al guardar en la base de datos.", "sql_error")
    return sets


def call_one(proc: str, **params: Any) -> dict[str, Any]:
    """Primera fila del último conjunto de resultados (lo que devuelven los procedimientos)."""
    sets = call(proc, **params)
    for s in reversed(sets):
        if s:
            return s[0]
    return {}


def plain(row: dict[str, Any] | None) -> dict[str, Any] | None:
    """Convierte Decimal y fechas para JSON (la capa web ya lo hace; útil en pruebas)."""
    if row is None:
        return None
    out = {}
    for k, v in row.items():
        if isinstance(v, Decimal):
            out[k] = float(v)
        elif isinstance(v, (datetime, date)):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out
