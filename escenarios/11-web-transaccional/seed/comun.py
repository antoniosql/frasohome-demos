"""FraSoHome Live · utilidades comunes de la carga inicial.

Conexión a Azure SQL (mssql-python o pyodbc), lectura de los CSV de datos/,
inserción por lotes con OPENJSON y registro de incidencias de calidad.
Solo usa la biblioteca estándar más el driver de SQL.
"""
from __future__ import annotations

import csv
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

SCENARIO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SCENARIO_DIR.parents[1]
DATOS_DIR = REPO_ROOT / "datos"
SQL_DIR = SCENARIO_DIR / "sql"
LOCAL_DIR = REPO_ROOT / ".local" / "frasohome-live"

# Orden de los scripts de esquema. 03 (procedimientos) y 06 (vistas de exportación)
# llegan en las fases 3 y 5.
DDL_FILES = ["01_core.sql", "02_hr_mkt_fin_ref_xref.sql", "04_app.sql", "05_rag_meta_lab.sql"]
DROP_FILE = "00_borrar.sql"


# ---------------------------------------------------------------- CSV

@dataclass
class CsvFile:
    """Un CSV de datos/ leído como texto, sin perder nada."""
    path: Path
    header: list[str]
    rows: list[dict[str, str]]
    has_bom: bool

    @property
    def rel(self) -> str:
        return self.path.relative_to(DATOS_DIR).as_posix()


def read_csv(rel_path: str) -> CsvFile:
    path = DATOS_DIR / rel_path
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    reader = csv.reader(text.splitlines(keepends=True))
    header = next(reader)
    rows = []
    for values in reader:
        if not values:
            continue
        values = values + [""] * (len(header) - len(values))
        rows.append(dict(zip(header, values)))
    return CsvFile(path=path, header=header, rows=rows, has_bom=has_bom)


# ---------------------------------------------------------------- incidencias

@dataclass
class Issue:
    schema: str
    table: str
    source_file: str
    source_key: str | None
    issue_type: str
    severity: str            # rechazo | corregido | aviso
    description: str
    source_row: dict[str, str] | None = None

    def as_row(self) -> dict[str, Any]:
        return {
            "source_schema": self.schema,
            "source_table": self.table,
            "source_file": self.source_file,
            "source_key": (self.source_key or "")[:255] or None,
            "issue_type": self.issue_type,
            "issue_severity": self.severity,
            "issue_description": self.description[:1000],
            "source_row": json.dumps(self.source_row, ensure_ascii=False) if self.source_row is not None else None,
        }


@dataclass
class IssueLog:
    """Acumula incidencias de un fichero de origen hacia una tabla de destino."""
    schema: str
    table: str
    source_file: str
    issues: list[Issue] = field(default_factory=list)

    def add(self, severity: str, issue_type: str, description: str, key: str | None = None,
            row: dict[str, str] | None = None) -> None:
        self.issues.append(Issue(self.schema, self.table, self.source_file, key, issue_type,
                                 severity, description, row))

    def rejected(self, issue_type: str, description: str, key: str | None, row: dict[str, str]) -> None:
        self.add("rechazo", issue_type, description, key, row)

    def fixed(self, issue_type: str, description: str, key: str | None, row: dict[str, str] | None = None) -> None:
        self.add("corregido", issue_type, description, key, row)

    def warn(self, issue_type: str, description: str, key: str | None, row: dict[str, str] | None = None) -> None:
        self.add("aviso", issue_type, description, key, row)

    def count(self, severity: str) -> int:
        return sum(1 for i in self.issues if i.severity == severity)


# ---------------------------------------------------------------- conexión SQL

def connection_string() -> str:
    cs = os.environ.get("FSH_SQL_CONNECTION_STRING", "").strip()
    if not cs:
        raise SystemExit("Falta FSH_SQL_CONNECTION_STRING (la pone seed/cargar_datos.ps1).")
    return cs


def _redact(text: str) -> str:
    return re.sub(r"(?i)((password|pwd)\s*=)[^;]*", r"\1***", text)


def connect_sql(cs: str | None = None, retries: int = 6):
    """Conecta con mssql-python (o pyodbc si no está). Reintenta mientras la base
    gratuita se despierta de la autopausa (error 40613)."""
    cs = cs or connection_string()
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            try:
                import mssql_python  # type: ignore
                conn = mssql_python.connect(cs)
            except ImportError:
                import pyodbc  # type: ignore
                odbc_cs = cs if "driver=" in cs.lower() else "Driver={ODBC Driver 18 for SQL Server};" + cs
                conn = pyodbc.connect(odbc_cs)
            conn.autocommit = False
            return conn
        except Exception as exc:  # noqa: BLE001 - se informa abajo
            last = exc
            text = str(exc)
            waking = "40613" in text or "not currently available" in text or "timeout" in text.lower()
            if attempt < retries and waking:
                print(f"    La base se está despertando (intento {attempt}/{retries}); espero 20 s...")
                time.sleep(20)
                continue
            break
    raise SystemExit(f"No se pudo conectar con SQL: {_redact(str(last))}")


def split_batches(sql_text: str) -> list[str]:
    """Separa un script T-SQL por líneas GO."""
    batches, current = [], []
    for line in sql_text.splitlines():
        if re.fullmatch(r"\s*GO\s*;?\s*", line, flags=re.IGNORECASE):
            if "".join(current).strip():
                batches.append("\n".join(current))
            current = []
        else:
            current.append(line)
    if "".join(current).strip():
        batches.append("\n".join(current))
    return batches


def run_script(conn, file_name: str) -> int:
    text = (SQL_DIR / file_name).read_text(encoding="utf-8-sig")
    cur = conn.cursor()
    n = 0
    for batch in split_batches(text):
        try:
            cur.execute(batch)
        except Exception as exc:
            conn.rollback()
            first = batch.strip().splitlines()[0][:120]
            raise SystemExit(f"Error en {file_name}, lote que empieza por «{first}»:\n{exc}") from exc
        n += 1
    conn.commit()
    return n


def table_columns(conn, full_name: str) -> list[tuple[str, str, bool]]:
    """(columna, tipo SQL para OPENJSON, es_identity) en orden."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT c.name,
               CASE
                 WHEN ty.name IN ('nvarchar','nchar','varchar','char','varbinary','binary')
                   THEN ty.name + '(' + CASE WHEN c.max_length = -1 THEN 'max'
                                             WHEN ty.name IN ('nvarchar','nchar') THEN CAST(c.max_length / 2 AS varchar(10))
                                             ELSE CAST(c.max_length AS varchar(10)) END + ')'
                 WHEN ty.name IN ('decimal','numeric')
                   THEN ty.name + '(' + CAST(c.precision AS varchar(5)) + ',' + CAST(c.scale AS varchar(5)) + ')'
                 WHEN ty.name IN ('datetime2','time','datetimeoffset')
                   THEN ty.name + '(' + CAST(c.scale AS varchar(5)) + ')'
                 ELSE ty.name
               END,
               c.is_identity
        FROM sys.columns AS c
        JOIN sys.types AS ty ON ty.user_type_id = c.user_type_id
        WHERE c.object_id = OBJECT_ID(?)
        ORDER BY c.column_id
        """,
        (full_name,),
    )
    cols = [(r[0], r[1], bool(r[2])) for r in cur.fetchall()]
    if not cols:
        raise SystemExit(f"No existe la tabla {full_name}: ejecuta antes el DDL (--recrear).")
    return cols


def _json_default(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    from decimal import Decimal
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Tipo no serializable: {type(value)}")


def insert_rows(conn, full_name: str, rows: Sequence[dict[str, Any]], chunk: int = 1500) -> int:
    """Inserta filas (diccionarios) con un INSERT ... SELECT FROM OPENJSON por lote:
    una sola ida y vuelta por cada `chunk` filas, con la conversión de tipos en SQL."""
    if not rows:
        return 0
    meta = table_columns(conn, full_name)
    present = set().union(*(r.keys() for r in rows))
    cols = [(n, t) for (n, t, ident) in meta if n in present and not ident]
    unknown = present - {n for n, _, _ in meta}
    if unknown:
        raise SystemExit(f"{full_name}: columnas desconocidas {sorted(unknown)}")
    col_list = ", ".join(f"[{n}]" for n, _ in cols)
    with_list = ", ".join(f"[{n}] {t} '$.\"{n}\"'" for n, t in cols)
    sql = f"INSERT INTO {full_name} ({col_list}) SELECT {col_list} FROM OPENJSON(?) WITH ({with_list})"
    cur = conn.cursor()
    total = 0
    for i in range(0, len(rows), chunk):
        part = rows[i:i + chunk]
        payload = json.dumps(part, ensure_ascii=False, default=_json_default)
        cur.execute(sql, (payload,))
        total += len(part)
    return total


def scalar(conn, sql: str, params: Iterable[Any] = ()) -> Any:
    cur = conn.cursor()
    cur.execute(sql, tuple(params))
    row = cur.fetchone()
    return row[0] if row else None


def save_report(name: str, data: Any) -> Path:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    path = LOCAL_DIR / name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    return path
