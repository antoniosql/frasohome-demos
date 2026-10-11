import pyodbc
import os
import argparse
from pathlib import Path

# =========================================================
# CONFIGURACIÓN
# =========================================================

SQL_SERVER = os.getenv("AZURE_SQL_SERVER")
SQL_DATABASE = os.getenv("AZURE_SQL_DATABASE")
SQL_USERNAME = os.getenv("AZURE_SQL_USERNAME")
SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD")

SCHEMA = os.getenv("schema")


CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SQL_SERVER};"
    f"DATABASE={SQL_DATABASE};"
    f"UID={SQL_USERNAME};"
    f"PWD={SQL_PASSWORD};"
 
)


# =========================================================
# CONEXIÓN
# =========================================================

def get_connection():
    conn = pyodbc.connect(CONNECTION_STRING)
    conn.autocommit = False
    return conn


# =========================================================
# LECTURA DEL SQL
# =========================================================

def read_sql_file(file_path: Path):
    """
    Lee un archivo SQL y lo divide en comandos utilizando GO
    """
    with open(file_path, "r", encoding="utf-8") as f:
        sql = f.read()

    statements = []

    batch = []

    for line in sql.splitlines():

        if line.strip().upper() == "GO":
            if batch:
                statements.append("\n".join(batch))
                batch = []
        else:
            batch.append(line)

    if batch:
        statements.append("\n".join(batch))

    return statements


# =========================================================
# EJECUCIÓN
# =========================================================

def execute_sql_file(conn, sql_file):

    sql_file = Path(sql_file)

    if not sql_file.exists():
        raise FileNotFoundError(f"No existe el archivo SQL: {sql_file}")

    print(f"\nEjecutando script: {sql_file}")

    statements = read_sql_file(sql_file)

    cursor = conn.cursor()

    for i, statement in enumerate(statements, start=1):

        sql = statement.strip()

        if not sql:
            continue

        print(f"Ejecutando bloque {i}...")

        try:
            cursor.execute(sql)
            conn.commit()

        except Exception as e:
            print("\nERROR ejecutando bloque SQL:")
            print(sql[:500])
            raise e

    cursor.close()

    print("\nScript ejecutado correctamente.")


# =========================================================
# MAIN
# =========================================================

def main():

    parser = argparse.ArgumentParser(description="Ejecutar script SQL en Azure SQL")
    parser.add_argument("--file", required=True, help="Ruta al archivo .sql")

    args = parser.parse_args()

    conn = get_connection()

    try:
        execute_sql_file(conn, "ddl.sql")
    finally:
        conn.close()


if __name__ == "__main__":
    main()