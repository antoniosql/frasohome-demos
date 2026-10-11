import os
import re
from pathlib import Path
from typing import Optional, Dict, List

import pandas as pd
import pyodbc

# =========================================================
# CONFIG
# =========================================================

SQL_SERVER = os.getenv("AZURE_SQL_SERVER")
SQL_DATABASE = os.getenv("AZURE_SQL_DATABASE")
SQL_USERNAME = os.getenv("AZURE_SQL_USERNAME")
SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD")

CSV_FOLDER = os.getenv("CSV_FOLDER")
SCHEMA = os.getenv("schema")
CHUNK_SIZE = 1000

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SQL_SERVER};"
    f"DATABASE={SQL_DATABASE};"
    f"UID={SQL_USERNAME};"
    f"PWD={SQL_PASSWORD};"
 
)

# =========================================================
# MAPEO CSV -> TABLA
# =========================================================

TABLE_CONFIG = {
    "crm.csv": "crm",
    "devoluciones_online.csv": "devoluciones_online",
    "devoluciones_tienda.csv": "devoluciones_tienda",
    "fact_transacciones.csv": "fact_transacciones",
    "lineas_pedido.csv": "lineas_pedido",
    "pagos_tienda.csv": "pagos_tienda",
    "pedidos.csv": "pedidos",
    "productos.csv": "productos",
    "stock_diario.csv": "stock_diario",
    "tiendas.csv": "tiendas",
    "ventas_pos.csv": "ventas_pos",
}

# =========================================================
# UTILIDADES DE LIMPIEZA
# =========================================================

SPANISH_MONTHS = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
    "septiembre": "09", "setiembre": "09", "octubre": "10",
    "noviembre": "11", "diciembre": "12"
}


def normalize_string(value):
    if pd.isna(value):
        return None
    s = str(value).strip()
    return s if s != "" else None


def normalize_id(value, to_upper=True):
    s = normalize_string(value)
    if s is None:
        return None
    s = re.sub(r"\s+", " ", s).strip()
    return s.upper() if to_upper else s


def normalize_decimal(value) -> Optional[float]:
    if pd.isna(value):
        return None

    s = str(value).strip()
    if s == "":
        return None

    s = s.replace("€", "").replace("EUR", "").replace(" ", "")

    # Caso 1.234,56 -> 1234.56
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    # Caso 127,74 -> 127.74
    elif "," in s:
        s = s.replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return None


def normalize_int(value) -> Optional[int]:
    dec = normalize_decimal(value)
    if dec is None:
        return None
    try:
        return int(round(dec))
    except Exception:
        return None


def normalize_bit(value) -> Optional[bool]:
    if pd.isna(value):
        return None

    s = str(value).strip().lower()
    if s in {"1", "true", "t", "yes", "y", "si", "sí"}:
        return True
    if s in {"0", "false", "f", "no", "n"}:
        return False
    return None


def replace_spanish_month_date(text: str) -> str:
    """
    Convierte cosas tipo:
    '14 de septiembre de 2025 08:25'
    a
    '14/09/2025 08:25'
    """
    s = text.lower().strip()
    pattern = r"(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})(?:\s+(\d{1,2}:\d{2}))?"
    m = re.match(pattern, s)
    if not m:
        return text

    day, month_name, year, hhmm = m.groups()
    month_name = month_name.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    month = SPANISH_MONTHS.get(month_name)
    if not month:
        return text

    if hhmm:
        return f"{day.zfill(2)}/{month}/{year} {hhmm}"
    return f"{day.zfill(2)}/{month}/{year}"


def normalize_datetime(value) -> Optional[pd.Timestamp]:
    if pd.isna(value):
        return None

    s = str(value).strip()
    if s == "":
        return None

    s = replace_spanish_month_date(s)

    # Intento flexible: dayfirst=True para soportar 20/11/25 20:43
    dt = pd.to_datetime(s, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return None
    return dt.to_pydatetime()


def normalize_date(value):
    dt = normalize_datetime(value)
    if dt is None:
        return None
    return dt.date()


# =========================================================
# TRANSFORMACIONES POR TABLA
# =========================================================

def transform_crm(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["customer_id"] = df["customer_id"].apply(normalize_id)
    df["email"] = df["email"].apply(normalize_string)
    df["telefono"] = df["telefono"].apply(normalize_string)
    df["fecha_alta_programa"] = df["fecha_alta_programa"].apply(normalize_datetime)
    df["puntos_acumulados"] = df["puntos_acumulados"].apply(normalize_decimal)
    df["fecha_nacimiento"] = df["fecha_nacimiento"].apply(normalize_date)
    df["codigo_postal"] = df["codigo_postal"].apply(normalize_string)
    df["consentimiento_marketing"] = df["consentimiento_marketing"].apply(normalize_bit)
    df["fecha_baja"] = df["fecha_baja"].apply(normalize_date)
    df["ultima_actualizacion"] = df["ultima_actualizacion"].apply(normalize_datetime)
    return df


def transform_devoluciones_online(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in ["return_id", "order_id", "order_line_id", "product_id"]:
        df[c] = df[c].apply(normalize_id)
    df["fecha_devolucion"] = df["fecha_devolucion"].apply(normalize_datetime)
    df["cantidad_devuelta"] = df["cantidad_devuelta"].apply(normalize_int)
    df["importe_reembolsado"] = df["importe_reembolsado"].apply(normalize_decimal)
    return df


def transform_devoluciones_tienda(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    id_cols = [
        "return_id", "store_id", "ticket_id_original", "ticket_line_id_original",
        "order_id_original", "customer_id", "product_id"
    ]
    for c in id_cols:
        df[c] = df[c].apply(normalize_id)
    df["fecha_devolucion"] = df["fecha_devolucion"].apply(normalize_datetime)
    df["cantidad_devuelta"] = df["cantidad_devuelta"].apply(normalize_int)
    df["importe_reembolsado"] = df["importe_reembolsado"].apply(normalize_decimal)
    return df


def transform_fact_transacciones(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    id_cols = [
        "fact_id", "store_id_raw", "store_id_std", "doc_id_raw", "doc_id_std",
        "line_id_raw", "line_id_std", "return_id", "customer_id_raw",
        "customer_id_std", "product_id_raw", "product_id_std",
        "ticket_id_original", "ticket_line_id_original", "order_id_original",
        "order_line_id_original", "caja_id", "cajero_id"
    ]
    for c in id_cols:
        if c in df.columns:
            df[c] = df[c].apply(normalize_id)

    bit_cols = [
        "es_devolucion", "flag_customer_in_crm", "flag_product_in_master",
        "flag_fecha_parseada", "flag_importe_parseado"
    ]
    for c in bit_cols:
        df[c] = df[c].apply(normalize_bit)

    if "fecha_movimiento" in df.columns:
        df["fecha_movimiento"] = df["fecha_movimiento"].apply(normalize_datetime)

    int_cols = ["cantidad_raw"]
    for c in int_cols:
        df[c] = df[c].apply(normalize_int)

    dec_cols = [
        "cantidad_signed", "cantidad_abs", "precio_unitario_num",
        "descuento_pct_raw", "descuento_pct_num", "descuento_importe_raw",
        "descuento_importe_num", "importe_signed_num", "importe_abs_num",
        "iva_pct", "coste_unitario_num", "coste_total_num", "margen_bruto_num",
        "precio_venta_num"
    ]
    for c in dec_cols:
        if c in df.columns:
            df[c] = df[c].apply(normalize_decimal)

    return df


def transform_lineas_pedido(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in ["order_line_id", "order_id", "product_id"]:
        df[c] = df[c].apply(normalize_id)
    df["cantidad"] = df["cantidad"].apply(normalize_int)
    for c in ["precio_unitario", "descuento_pct", "descuento_importe", "importe_linea", "iva_pct"]:
        df[c] = df[c].apply(normalize_decimal)
    return df


def transform_pagos_tienda(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in ["payment_id", "ticket_id", "store_id", "caja_id", "cajero_id"]:
        df[c] = df[c].apply(normalize_id)
    df["fecha_pago"] = df["fecha_pago"].apply(normalize_datetime)
    df["importe_pagado"] = df["importe_pagado"].apply(normalize_decimal)
    return df


def transform_pedidos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in ["order_id", "customer_id", "usuario_online_id"]:
        df[c] = df[c].apply(normalize_id)
    df["fecha_pedido"] = df["fecha_pedido"].apply(normalize_datetime)
    df["importe_total"] = df["importe_total"].apply(normalize_decimal)
    df["gastos_envio"] = df["gastos_envio"].apply(normalize_decimal)
    df["codigo_postal_envio"] = df["codigo_postal_envio"].apply(normalize_string)
    df["ultima_actualizacion"] = df["ultima_actualizacion"].apply(normalize_datetime)
    return df


def transform_productos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["product_id"] = df["product_id"].apply(normalize_id)
    num_cols = [
        "precio_venta", "coste_unitario", "iva_pct", "peso_kg",
        "largo_cm", "ancho_cm", "alto_cm"
    ]
    for c in num_cols:
        df[c] = df[c].apply(normalize_decimal)
    df["fecha_alta_catalogo"] = df["fecha_alta_catalogo"].apply(normalize_date)
    df["ean"] = df["ean"].apply(normalize_string)
    return df


def transform_stock_diario(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["fecha"] = df["fecha"].apply(normalize_datetime)
    df["store_id"] = df["store_id"].apply(normalize_id)
    df["product_id"] = df["product_id"].apply(normalize_id)
    for c in ["stock_cierre", "stock_reservado", "stock_en_transito"]:
        df[c] = df[c].apply(normalize_decimal)
    df["stock_minimo"] = df["stock_minimo"].apply(normalize_int)
    return df


def transform_tiendas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["store_id"] = df["store_id"].apply(normalize_id)
    df["codigo_postal"] = df["codigo_postal"].apply(normalize_string)
    df["fecha_apertura"] = df["fecha_apertura"].apply(normalize_date)
    df["metros_cuadrados"] = df["metros_cuadrados"].apply(normalize_int)
    df["lat"] = df["lat"].apply(normalize_decimal)
    df["lon"] = df["lon"].apply(normalize_decimal)
    return df


def transform_ventas_pos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    id_cols = ["ticket_line_id", "ticket_id", "store_id", "caja_id", "cajero_id", "customer_id", "product_id"]
    for c in id_cols:
        df[c] = df[c].apply(normalize_id)
    df["fecha_hora"] = df["fecha_hora"].apply(normalize_datetime)
    df["cantidad"] = df["cantidad"].apply(normalize_int)
    for c in ["precio_unitario", "descuento_pct", "descuento_importe", "importe_linea"]:
        df[c] = df[c].apply(normalize_decimal)
    return df


TRANSFORMERS = {
    "crm": transform_crm,
    "devoluciones_online": transform_devoluciones_online,
    "devoluciones_tienda": transform_devoluciones_tienda,
    "fact_transacciones": transform_fact_transacciones,
    "lineas_pedido": transform_lineas_pedido,
    "pagos_tienda": transform_pagos_tienda,
    "pedidos": transform_pedidos,
    "productos": transform_productos,
    "stock_diario": transform_stock_diario,
    "tiendas": transform_tiendas,
    "ventas_pos": transform_ventas_pos,
}

# =========================================================
# SQL HELPERS
# =========================================================

def get_connection():
    conn = pyodbc.connect(CONNECTION_STRING)
    conn.autocommit = False
    return conn


def truncate_table(conn, schema: str, table: str):
    sql = f"DELETE FROM {schema}.{table};"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def insert_dataframe(conn, schema: str, table: str, df: pd.DataFrame):
    cols = list(df.columns)
    col_list = ", ".join(f"[{c}]" for c in cols)
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT INTO {schema}.{table} ({col_list}) VALUES ({placeholders})"

    rows = [tuple(None if pd.isna(v) else v for v in row) for row in df.itertuples(index=False, name=None)]

    with conn.cursor() as cur:
        cur.fast_executemany = True
        cur.executemany(sql, rows)
    conn.commit()


def load_csv_file(conn, csv_path: Path, schema: str, table: str):
    print(f"[INFO] Cargando {csv_path.name} -> {schema}.{table}")

    transformer = TRANSFORMERS[table]

    first_chunk = True
    for chunk in pd.read_csv(csv_path, chunksize=CHUNK_SIZE, dtype=str):
        # Reconversión mínima de columnas numéricas que vienen como str:
        # las transformaciones específicas ya se encargan.
        chunk = transformer(chunk)

        if first_chunk:
            truncate_table(conn, schema, table)
            first_chunk = False

        insert_dataframe(conn, schema, table, chunk)

    print(f"[OK] {csv_path.name} cargado correctamente")


def main():
    csv_folder = Path(CSV_FOLDER)
    if not csv_folder.exists():
        raise FileNotFoundError(f"No existe la carpeta de CSV: {csv_folder.resolve()}")

    conn = get_connection()
    try:
        for file_name, table_name in TABLE_CONFIG.items():
            file_path = csv_folder / file_name
            if not file_path.exists():
                print(f"[WARN] No encontrado {file_name}, se omite")
                continue

            load_csv_file(conn, file_path, SCHEMA, table_name)

        print("[FIN] Carga completada")
    finally:
        conn.close()


if __name__ == "__main__":
    main()