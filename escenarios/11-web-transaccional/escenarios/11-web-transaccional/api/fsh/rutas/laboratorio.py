"""Escenario 16 · laboratorio docente (rol profesor): corrección de la consola de identidad
contra la verdad conocida, juegos de evaluación RAG, muestras para prompts y backlog de indicadores."""
from __future__ import annotations

import json

from .. import cosmos, db
from ..util import field, number, one_of
from ..web import Request, not_found, route

ROLES = {"profesor"}
TEST_SETS = ["Documental", "Metrico_Mixto"]
RAG_TABLES = {"clientes": "rag.customer", "productos": "rag.product", "tiendas": "rag.store", "stock": "rag.stock_daily",
              "ventas": "rag.sales_daily", "devoluciones": "rag.return_fact", "alertas": "rag.stockout_alert"}


@route("GET", "/lab/identidad/evaluacion", ROLES)
def evaluacion(req: Request):
    """Compara el cliente asignado a cada señal con la verdad conocida."""
    truth = {r["identity_signal_id"]: r["customer_id_canonico"]
             for r in db.query("SELECT identity_signal_id, customer_id_canonico FROM lab.identity_ground_truth")}
    signals = cosmos.query("senales_identidad", "SELECT c.id, c.customer_id_candidato, c.customer_id_raw, c.fuente_sistema, "
                           "c.asignado_por FROM c", max_items=100_000)
    graded = [s for s in signals if s["id"] in truth]
    correct = [s for s in graded if s.get("customer_id_candidato") == truth[s["id"]]]
    unassigned = [s for s in graded if not s.get("customer_id_candidato")]
    wrong = [s for s in graded if s.get("customer_id_candidato") and s["customer_id_candidato"] != truth[s["id"]]]
    manual = [s for s in graded if s.get("asignado_por")]
    return {"senales_evaluadas": len(graded), "correctas": len(correct), "sin_asignar": len(unassigned),
            "erroneas": len(wrong), "exactitud": round(len(correct) / len(graded), 4) if graded else None,
            "asignadas_a_mano": len(manual),
            "aciertos_a_mano": sum(1 for s in manual if s.get("customer_id_candidato") == truth[s["id"]]),
            "errores": [{"senal": s["id"], "asignado": s.get("customer_id_candidato"), "correcto": truth[s["id"]],
                         "id_en_bruto": s.get("customer_id_raw"), "fuente": s.get("fuente_sistema")}
                        for s in sorted(wrong, key=lambda x: x["id"])][:200],
            "pendientes": [{"senal": s["id"], "correcto": truth[s["id"]], "id_en_bruto": s.get("customer_id_raw")}
                           for s in sorted(unassigned, key=lambda x: x["id"])][:200]}


@route("GET", "/lab/rag/casos", ROLES)
def casos(req: Request):
    test_set = req.query.get("juego") or None
    return db.query("""SELECT test_set, row_num, question, expected_response, updated_by, updated_at FROM lab.rag_test_case
                       WHERE (? IS NULL OR test_set = ?) ORDER BY test_set, row_num""", test_set, test_set)


@route("POST", "/lab/rag/casos", ROLES)
def nuevo_caso(req: Request):
    d = req.json()
    return db.call_one("lab.usp_rag_test_case_upsert", test_set=one_of(d.get("juego"), TEST_SETS, "juego"), row_num=None,
                       question=field(d, "pregunta", max_len=1000), expected_response=field(d, "respuesta", max_len=2000),
                       user_login=req.user.login)


@route("PUT", "/lab/rag/casos/{juego}/{fila}", ROLES)
def editar_caso(req: Request):
    d = req.json()
    return db.call_one("lab.usp_rag_test_case_upsert", test_set=one_of(req.params["juego"], TEST_SETS, "juego"),
                       row_num=number(req.params["fila"], "fila", lo=1, hi=10_000, integer=True),
                       question=field(d, "pregunta", max_len=1000), expected_response=field(d, "respuesta", max_len=2000),
                       user_login=req.user.login)


@route("DELETE", "/lab/rag/casos/{juego}/{fila}", ROLES)
def borrar_caso(req: Request):
    db.call("lab.usp_rag_test_case_delete", test_set=one_of(req.params["juego"], TEST_SETS, "juego"),
            row_num=number(req.params["fila"], "fila", lo=1, hi=10_000, integer=True))
    return {"ok": True}


@route("GET", "/lab/prompts", ROLES)
def prompts(req: Request):
    return db.query("SELECT * FROM lab.prompt_sample ORDER BY employee_id")


@route("GET", "/lab/backlog", ROLES)
def backlog(req: Request):
    rows = db.query("SELECT row_num, row_json FROM meta.reference_row WHERE file_path LIKE N'%plantilla_backlog_indicadores.csv' "
                    "ORDER BY row_num")
    return [{"fila": r["row_num"], **json.loads(r["row_json"])} for r in rows]


@route("GET", "/lab/rag/tablas/{tabla}", ROLES)
def rag_tabla(req: Request):
    table = RAG_TABLES.get(req.params["tabla"])
    if table is None:
        raise not_found(f"Tablas disponibles: {', '.join(RAG_TABLES)}.")
    limit = req.int_arg("tamano", 500, 1, 5000)
    return db.query(f"SELECT TOP (?) * FROM {table}", limit)
