"""FraSoHome Live · comprueba que la carga inicial está completa.

    python verify.py            # SQL y Cosmos DB
    python verify.py --sin-cosmos

Para cada CSV de datos/ compara tres números:
  filas del CSV  −  filas rechazadas por la limpieza (quality.data_quality_issue)  =  filas en la base
y además que el recuento del CSV coincide con el que declara datos/catalogo-datos.csv.
Los ficheros que no se guardan porque se recalculan los lista aparte.
Sale con código 1 si alguna cifra no cuadra.
"""
from __future__ import annotations

import argparse
import csv
import sys

from comun import DATOS_DIR, connect_sql, read_csv, save_report, scalar

RETAIL = "retail_omnicanal/raw_csv/"
MKT = "marketing_precision/raw_csv/"
PEOPLE = "people_analytics/raw_csv/"
REL = "relaciones/"
RAG = "rag_copilot_studio/"

# fichero -> consulta que cuenta sus filas en SQL
SQL_COUNTS = {
    PEOPLE + "dim_departamentos_mapeo.csv": "SELECT COUNT(*) FROM ref.department_map",
    MKT + "guardrails_marca_genai.csv": "SELECT COUNT(*) FROM ref.brand_guardrail",
    PEOPLE + "dim_calendario.csv": "SELECT COUNT(*) FROM ref.calendar",
    REL + "store_aliases.csv": "SELECT COUNT(*) FROM xref.store_alias",
    REL + "product_aliases_rag_to_retail.csv": "SELECT COUNT(*) FROM xref.product_alias",
    REL + "employee_operational_aliases.csv": "SELECT COUNT(*) FROM xref.employee_alias",
    REL + "employee_store_assignment.csv": "SELECT COUNT(*) FROM xref.employee_store",
    RETAIL + "tiendas.csv": "SELECT COUNT(*) FROM store.store",
    RETAIL + "productos.csv": "SELECT COUNT(*) FROM catalog.product",
    RETAIL + "crm.csv": "SELECT COUNT(*) FROM crm.customer",
    RETAIL + "pedidos.csv": "SELECT COUNT(*) FROM sales.online_order",
    RETAIL + "lineas_pedido.csv": "SELECT COUNT(*) FROM sales.online_order_line",
    RETAIL + "ventas_pos.csv": "SELECT COUNT(*) FROM sales.pos_ticket_line",
    RETAIL + "pagos_tienda.csv": "SELECT COUNT(*) FROM sales.store_payment",
    RETAIL + "devoluciones_online.csv": "SELECT COUNT(*) FROM [returns].return_line l JOIN [returns].return_header h "
                                        "ON h.return_id = l.return_id WHERE h.return_channel = N'ONLINE'",
    RETAIL + "devoluciones_tienda.csv": "SELECT COUNT(*) FROM [returns].return_line l JOIN [returns].return_header h "
                                        "ON h.return_id = l.return_id WHERE h.return_channel = N'TIENDA'",
    RETAIL + "stock_diario.csv": "SELECT COUNT(*) FROM inventory.stock_snapshot",
    PEOPLE + "raw_hris_empleados.csv": "SELECT COUNT(*) FROM hr.employee",
    PEOPLE + "raw_movimientos_personal.csv": "SELECT COUNT(*) FROM hr.employee_movement",
    PEOPLE + "raw_absentismo.csv": "SELECT COUNT(*) FROM hr.absence",
    PEOPLE + "raw_horas_extra.csv": "SELECT COUNT(*) FROM hr.overtime",
    PEOPLE + "raw_formacion.csv": "SELECT COUNT(*) FROM hr.training",
    PEOPLE + "raw_evaluaciones_desempeno.csv": "SELECT COUNT(*) FROM hr.performance_review",
    PEOPLE + "raw_salarios_beneficios.csv": "SELECT COUNT(*) FROM hr.compensation",
    PEOPLE + "frasohome_people_analytics.csv": "SELECT COUNT(*) FROM hr.people_analytics_seed",
    PEOPLE + "frasohome_rotacion_mensual.csv": "SELECT COUNT(*) FROM hr.turnover_monthly_seed",
    PEOPLE + "frasohome_muestra_prompt_chatgpt.csv": "SELECT COUNT(*) FROM lab.prompt_sample",
    MKT + "campanas_marketing.csv": "SELECT COUNT(*) FROM mkt.campaign",
    MKT + "cupones_clientes.csv": "SELECT COUNT(*) FROM mkt.coupon",
    MKT + "contactos_campana.csv": "SELECT COUNT(*) FROM mkt.campaign_contact",
    MKT + "promociones_calendario.csv": "SELECT COUNT(*) FROM mkt.promotion",
    MKT + "afinidad_tienda_cliente.csv": "SELECT COUNT(*) FROM mkt.customer_store_affinity",
    MKT + "costes_operativos_transaccion.csv": "SELECT COUNT(*) FROM fin.transaction_cost",
    RAG + "structured_csv/FS_Clientes.csv": "SELECT COUNT(*) FROM rag.customer",
    RAG + "structured_csv/FS_Productos.csv": "SELECT COUNT(*) FROM rag.product",
    RAG + "structured_csv/FS_Tiendas.csv": "SELECT COUNT(*) FROM rag.store",
    RAG + "structured_csv/FS_StockDiario.csv": "SELECT COUNT(*) FROM rag.stock_daily",
    RAG + "structured_csv/FS_VentasResumenDiario.csv": "SELECT COUNT(*) FROM rag.sales_daily",
    RAG + "structured_csv/FS_DevolucionesFact.csv": "SELECT COUNT(*) FROM rag.return_fact",
    RAG + "structured_csv/FS_Alertas_Stockout.csv": "SELECT COUNT(*) FROM rag.stockout_alert",
    MKT + "identidades_cliente_ground_truth.csv": "SELECT COUNT(*) FROM lab.identity_ground_truth",
    RAG + "test_sets/FS_TestSet_Documental.csv": "SELECT COUNT(*) FROM lab.rag_test_case WHERE test_set = N'Documental'",
    RAG + "test_sets/FS_TestSet_Metrico_Mixto.csv": "SELECT COUNT(*) FROM lab.rag_test_case WHERE test_set = N'Metrico_Mixto'",
}
META_FILES = [MKT + "catalogo_datasets_marketing_precision.csv", MKT + "diccionario_columnas_marketing_precision.csv",
              MKT + "mapeo_casos_marketing_precision.csv", REL + "marketing_precision_operational_links.csv",
              PEOPLE + "diccionario_fuentes_brutas.csv", PEOPLE + "frasohome_diccionario_datos.csv",
              PEOPLE + "plantilla_backlog_indicadores.csv"]
COSMOS_FILES = {MKT + "eventos_web_app.csv": "eventos_web", MKT + "eventos_campana.csv": "eventos_campana",
                MKT + "identidades_cliente.csv": "senales_identidad", MKT + "feedback_clientes.csv": "feedback",
                MKT + "tickets_atencion_cliente.csv": "atencion_cliente", MKT + "creatividades_segmento.csv": "creatividades",
                PEOPLE + "raw_encuesta_clima_respuestas.csv": "encuesta_clima",
                PEOPLE + "raw_exit_interviews.csv": "entrevistas_salida"}
# Se recalculan en la exportación (fase 5): no se guardan para no contradecir lo operado.
DERIVED = {RETAIL + "fact_transacciones.csv": "vista exp.fact_transacciones (pedidos, tickets y devoluciones)",
           PEOPLE + "frasohome_comentarios_clima.csv": "encuesta de clima (Cosmos) + hr.employee",
           PEOPLE + "frasohome_comentarios_salida.csv": "entrevistas de salida (Cosmos) + hr.employee",
           MKT + "validacion_datasets_marketing_precision.csv": "recuentos reales de la exportación",
           REL + "coherence_check_summary.csv": "comprobaciones de coherencia de la exportación",
           "catalogo-datos.csv": "catálogo regenerado por la exportación"}
# Incidencias que no son rechazo pero tampoco añaden fila (la variante se fusiona con otra).
NOT_LOADED = ("duplicado_mayusculas",)


def catalog_counts() -> dict[str, int]:
    out = {}
    with open(DATOS_DIR / "catalogo-datos.csv", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            path = r["ruta"].removeprefix("datos/")
            try:
                out[path] = int(r["filas"])
            except ValueError:
                pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sin-cosmos", action="store_true", help="solo comprueba SQL")
    args = ap.parse_args()

    conn = connect_sql()
    cur = conn.cursor()
    cur.execute(f"""SELECT source_file, SUM(CASE WHEN issue_severity = N'rechazo'
                           OR issue_type IN ({",".join("?" * len(NOT_LOADED))}) THEN 1 ELSE 0 END)
                    FROM quality.data_quality_issue GROUP BY source_file""", NOT_LOADED)
    rejected = {r[0]: int(r[1]) for r in cur.fetchall()}
    catalog = catalog_counts()

    rows = []

    def check(rel: str, where: str, in_db: int | None) -> None:
        n_csv = len(read_csv(rel).rows)
        rej = rejected.get(rel, 0)
        expected = n_csv - rej
        cat = catalog.get(rel)
        ok = in_db == expected
        rows.append({"fichero": rel, "destino": where, "filas_csv": n_csv, "catalogo": cat, "rechazadas": rej,
                     "esperadas": expected, "en_base": in_db, "ok": ok,
                     "catalogo_ok": cat is None or cat == n_csv})

    for rel, sql in SQL_COUNTS.items():
        check(rel, "SQL", scalar(conn, sql))
    for rel in META_FILES:
        check(rel, "SQL meta", scalar(conn, "SELECT COUNT(*) FROM meta.reference_row WHERE file_path = ?", (rel,)))
    if not args.sin_cosmos:
        from load_cosmos import cosmos_database, count_docs
        db = cosmos_database()
        for rel, name in COSMOS_FILES.items():
            check(rel, f"Cosmos {name}", count_docs(db.get_container_client(name)))

    bad = [r for r in rows if not r["ok"]]
    cat_bad = [r for r in rows if not r["catalogo_ok"]]
    issues = scalar(conn, "SELECT COUNT(*) FROM quality.data_quality_issue")
    print(f"{'fichero':<58} {'CSV':>6} {'rechaz.':>7} {'esper.':>7} {'base':>7}")
    for r in rows:
        mark = "" if r["ok"] else "  ← NO CUADRA"
        print(f"{r['fichero']:<58} {r['filas_csv']:>6} {r['rechazadas']:>7} {r['esperadas']:>7} {str(r['en_base']):>7}{mark}")
    print("\nSe recalculan en la exportación (no se guardan):")
    for rel, how in DERIVED.items():
        print(f"    {rel:<58} {how}")
    if cat_bad:
        print("\nEl catálogo datos/catalogo-datos.csv declara otro número de filas:")
        for r in cat_bad:
            print(f"    {r['fichero']}: catálogo {r['catalogo']}, CSV {r['filas_csv']}")
    covered = len(rows) + len(DERIVED)
    print(f"\n{len(rows)} ficheros guardados + {len(DERIVED)} recalculados = {covered} ficheros de datos/.")
    print(f"{issues} incidencias de calidad en quality.data_quality_issue.")
    save_report("verificacion.json", {"ficheros": rows, "recalculados": DERIVED, "incidencias": issues})
    if bad:
        print(f"\n{len(bad)} ficheros no cuadran.")
        return 1
    print("\nTodo cuadra.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
