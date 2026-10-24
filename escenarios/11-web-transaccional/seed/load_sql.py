"""FraSoHome Live · carga inicial de Azure SQL desde los CSV de datos/.

    python load_sql.py              # carga sobre tablas vacías (falla si ya hay datos)
    python load_sql.py --recrear    # borra y crea el esquema y vuelve a cargar

La cadena de conexión llega en FSH_SQL_CONNECTION_STRING (la pone
seed/cargar_datos.ps1). Todo se hace en una transacción: si algo falla, la base
queda como estaba. El resumen se guarda en .local/frasohome-live/carga_sql.json.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone

from comun import (DDL_FILES, DROP_FILE, connect_sql, insert_rows, run_script, save_report, scalar,
                   table_columns)
from fuentes_sql import CargaSQL

# Contadores de identificadores legibles: de qué columna sale el último número usado.
ID_SOURCES = {
    "order": ("sales.online_order", "order_id"), "order_line": ("sales.online_order_line", "order_line_id"),
    "ticket": ("sales.pos_ticket", "ticket_id"), "ticket_line": ("sales.pos_ticket_line", "ticket_line_id"),
    "payment": ("sales.store_payment", "payment_id"),
    "return_online": ("returns.return_header", "return_id"), "return_store": ("returns.return_header", "return_id"),
    "customer": ("crm.customer", "customer_id"), "product": ("catalog.product", "product_id"),
    "campaign": ("mkt.campaign", "campaign_id"), "contact": ("mkt.campaign_contact", "contact_id"),
    "coupon": ("mkt.coupon", "coupon_instance_id"), "coupon_code": ("mkt.coupon", "coupon_code"),
    "promo": ("mkt.promotion", "promo_id"), "cost": ("fin.transaction_cost", "transaction_cost_id"),
    "employee": ("hr.employee", "employee_id"), "movement": ("hr.employee_movement", "movement_id"),
    "absence": ("hr.absence", "absence_id"), "overtime": ("hr.overtime", "overtime_id"),
    "training": ("hr.training", "training_id"), "review": ("hr.performance_review", "review_id"),
    "payroll": ("hr.compensation", "payroll_id"),
}


def seed_counters(conn, kinds: dict[str, list[str]]) -> dict[str, int]:
    """Deja cada contador justo después del mayor identificador cargado de su tipo.
    `kinds` = {tipo: [identificadores existentes]}. Los tipos por año empiezan en 1
    cada año, así que solo cuentan los identificadores del año en curso."""
    cur = conn.cursor()
    cur.execute("SELECT kind, prefix_template, number_width, per_year FROM app.id_kind")
    templates = {r[0]: (r[1], r[2], bool(r[3])) for r in cur.fetchall()}
    year = datetime.now(timezone.utc).year
    result = {}
    for kind, ids in kinds.items():
        if kind not in templates:
            continue
        template, width, per_year = templates[kind]
        prefix = template.replace("{Y}", str(year))
        rx = re.compile("^" + re.escape(prefix) + r"(\d+)$")
        nums = [int(m.group(1)) for i in ids if i and (m := rx.match(i))]
        nxt = (max(nums) + 1) if nums else 1
        period = year if per_year else 0
        cur.execute(
            """MERGE app.id_counter AS t
               USING (SELECT ? AS kind, ? AS period_key) AS s ON t.kind = s.kind AND t.period_key = s.period_key
               WHEN MATCHED THEN UPDATE SET next_value = CASE WHEN t.next_value > ? THEN t.next_value ELSE ? END
               WHEN NOT MATCHED THEN INSERT (kind, period_key, prefix_template, number_width, next_value)
                                     VALUES (?, ?, ?, ?, ?);""",
            (kind, period, nxt, nxt, kind, period, template, width, nxt))
        result[kind] = nxt
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--recrear", action="store_true", help="borra y crea el esquema antes de cargar")
    args = ap.parse_args()

    t0 = time.time()
    conn = connect_sql()
    print("Conectado a SQL.")

    if args.recrear:
        print("Borrando y creando el esquema...")
        run_script(conn, DROP_FILE)
        for f in DDL_FILES:
            n = run_script(conn, f)
            print(f"    {f}: {n} lotes")
    elif scalar(conn, "SELECT OBJECT_ID('crm.customer')") is None:
        print("No existe el esquema: lo creo.")
        for f in DDL_FILES:
            run_script(conn, f)
    elif scalar(conn, "SELECT COUNT(*) FROM crm.customer") > 0:
        print("La base ya tiene datos. Usa --recrear para borrarla y cargarla de nuevo (o seed/reset.py).")
        return 2

    print("Leyendo y limpiando los CSV...")
    carga = CargaSQL(columnas=lambda t: table_columns(conn, t))
    carga.ejecutar()

    print("Insertando...")
    counts: dict[str, int] = {}
    try:
        for table, rows in carga.tables.items():
            if table == "hr.employee#manager":
                continue
            counts[table] = insert_rows(conn, table, rows)
            print(f"    {table:<34} {counts[table]:>6}")
        managers = carga.tables.get("hr.employee#manager", [])
        if managers:
            import json
            conn.cursor().execute(
                """UPDATE e SET manager_id = j.manager_id
                   FROM hr.employee AS e
                   JOIN OPENJSON(?) WITH (employee_id nvarchar(20), manager_id nvarchar(20)) AS j
                     ON j.employee_id = e.employee_id""", (json.dumps(managers),))
            print(f"    {'hr.employee (responsables)':<34} {len(managers):>6}")
        issues = carga.issues()
        counts["quality.data_quality_issue"] = insert_rows(conn, "quality.data_quality_issue", issues)
        print(f"    {'quality.data_quality_issue':<34} {counts['quality.data_quality_issue']:>6}")

        kinds = {kind: [r.get(col) for r in carga.tables.get(table, [])] for kind, (table, col) in ID_SOURCES.items()}
        counters = seed_counters(conn, kinds)
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    sev = Counter(i["issue_severity"] for i in issues)
    types = Counter((i["issue_severity"], i["issue_type"]) for i in issues)
    report = {
        "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "segundos": round(time.time() - t0, 1),
        "tablas": counts,
        "ficheros": carga.sources,
        "incidencias": dict(sev),
        "incidencias_por_tipo": {f"{s}/{t}": n for (s, t), n in types.most_common()},
        "contadores": counters,
    }
    path = save_report("carga_sql.json", report)
    print(f"\nCarga SQL terminada en {report['segundos']} s: {sum(v for k, v in counts.items() if not k.startswith('quality'))} filas.")
    print(f"Incidencias: {sev.get('rechazo', 0)} rechazos, {sev.get('corregido', 0)} correcciones, {sev.get('aviso', 0)} avisos.")
    print(f"Detalle: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
