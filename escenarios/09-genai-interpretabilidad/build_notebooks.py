from pathlib import Path

import nbformat as nbf


BASE = Path(__file__).resolve().parent


def md(text: str):
    return nbf.v4.new_markdown_cell(text.strip() + "\n")


def code(text: str):
    return nbf.v4.new_code_cell(text.strip() + "\n")


def write_nb(path: Path, cells: list):
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.x"},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, path)
    print(f"written {path}")


SETUP = r'''
from pathlib import Path
import sys
import json
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", 160)
pd.set_option("display.width", 160)
pd.set_option("display.max_colwidth", 180)

def find_project_root(start=None):
    current = Path(start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "datos").exists() and (candidate / "escenarios").exists():
            return candidate
    raise FileNotFoundError("No se ha encontrado la raíz del proyecto FraSoHome.")

PROJECT_ROOT = find_project_root()
DEMO_DIR = PROJECT_ROOT / "escenarios" / "09-genai-interpretabilidad"
ARTIFACT_DIR = DEMO_DIR / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(DEMO_DIR))

from common.genai_frasohome import (
    append_trace,
    build_agent_trace,
    build_rag_index,
    chunk_documents,
    evaluate_agent_trace,
    evaluate_rag_questions,
    grounded_answer,
    keyword_coverage,
    load_crm,
    load_knowledge_documents,
    load_sales_artifact,
    local_feature_contributions,
    recommendation_from_score,
    retrieve,
    simple_answer_rubric,
    summarize_customer_context,
)

print("PROJECT_ROOT:", PROJECT_ROOT)
print("DEMO_DIR:", DEMO_DIR)
'''


def demo_01_score_to_recommendation():
    cells = [
        md(
            """
            # Demo 01 · Del score ML a una recomendación GenAI explicable

            Esta demo conecta directamente con los notebooks de analítica de ventas e interpretabilidad ML. Partimos del modelo de inactividad ya entrenado, seleccionamos un cliente con score alto y construimos una recomendación comercial **trazable**.

            No usamos una API de LLM. Simulamos la capa generativa con una plantilla controlada para que el foco didáctico sea la explicabilidad: qué datos entran, qué señales del modelo se usan, qué documentos respaldan la recomendación y qué cautelas se comunican.
            """
        ),
        code(SETUP),
        md(
            """
            ## 1. Cargar el artefacto de ventas

            La demo depende del artefacto generado en la sesión anterior: datasets, pipeline, particiones y métricas. Esta dependencia es intencional: el asistente GenAI no inventa el análisis, lo consume.
            """
        ),
        code(
            r'''
artifact = load_sales_artifact(PROJECT_ROOT)
print("Artefacto cargado:", artifact["_path"])
print("Bloques disponibles:", [k for k in artifact.keys() if not k.startswith("_")])

churn = artifact["churn"]
display(pd.Series(churn["result"]["metrics"]).to_frame("métrica"))
'''
        ),
        md(
            """
            ## 2. Seleccionar un cliente prioritario y explicar el score

            En un sistema real podríamos usar SHAP, LIME o explicaciones precalculadas. Para esta demo usamos una aproximación local basada en señales transformadas e importancia del modelo, suficiente para enseñar el contrato de explicación.
            """
        ),
        code(
            r'''
score, row_raw, contributions = local_feature_contributions(churn["result"], top_n=12)
customer_context = summarize_customer_context(row_raw, contributions)

print(f"Score de inactividad seleccionado: {score:.3f}")
display(row_raw.T.head(30))
display(contributions)
display(pd.Series(customer_context).to_frame("valor"))
'''
        ),
        md(
            """
            ## 3. Recuperar evidencia documental

            La recomendación comercial no debería apoyarse solo en el score. Consultamos la base de conocimiento de FraSoHome para traer reglas de fidelización, permisos y cautelas operativas.
            """
        ),
        code(
            r'''
documents = load_knowledge_documents(PROJECT_ROOT)
chunks = chunk_documents(documents)
rag_index = build_rag_index(chunks, include_obsolete=False, include_security_test=False)

query = "reglas CRM fidelización consentimiento marketing campaña reactivación cliente Platino cupón"
evidence = retrieve(rag_index, query, top_k=5)
display(evidence[["rank", "score", "file_name", "chunk_id", "area"]])
'''
        ),
        md(
            """
            ## 4. Generar una recomendación explicable

            La salida separa cuatro elementos: recomendación, evidencia, cautelas y trazabilidad. Esta separación es más importante que el estilo textual.
            """
        ),
        code(
            r'''
recommendation = recommendation_from_score(score, customer_context, evidence)
print(recommendation["recommendation"])
print("\nFuentes usadas:")
for source in recommendation["evidence_files"]:
    print("-", source)
print("\nCautelas:")
for caveat in recommendation["caveats"]:
    print("-", caveat)
'''
        ),
        md(
            """
            ## 5. Trazabilidad de extremo a extremo

            Una recomendación GenAI debería poder reconstruirse después. La traza mínima registra datos, modelo, explicación, retrieval y respuesta final.
            """
        ),
        code(
            r'''
trace = [
    {"step": 1, "component": "modelo_ml", "detail": "score de inactividad", "value": round(score, 4)},
    {"step": 2, "component": "interpretabilidad_ml", "detail": "señales locales principales", "value": contributions["feature"].head(6).tolist()},
    {"step": 3, "component": "rag", "detail": "fuentes recuperadas", "value": evidence["file_name"].head(3).tolist()},
    {"step": 4, "component": "generación_controlada", "detail": "recomendación con cautelas", "value": recommendation["recommendation"]},
]
display(pd.DataFrame(trace))

trace_path = ARTIFACT_DIR / "demo_01_recommendation_trace.json"
trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
print("Traza guardada:", trace_path)
'''
        ),
        md(
            """
            ## 6. Lectura para el instructor

            El mensaje clave para clase: la IA generativa no sustituye a la interpretabilidad ML, la consume. Una buena recomendación separa lo que es dato, lo que es inferencia del modelo, lo que está respaldado por documentos y lo que es propuesta comercial.
            """
        ),
    ]
    write_nb(BASE / "notebooks_instructor" / "01_demo_score_a_recomendacion_genai_explicable.ipynb", cells)


def demo_02_rag_evaluation():
    cells = [
        md(
            """
            # Demo 02 · RAG explicable y evaluación con test set FraSoHome

            Esta demo construye un RAG local sobre los documentos de conocimiento de FraSoHome. Usa TF-IDF en lugar de embeddings externos para que sea reproducible sin APIs, pero mantiene la estructura conceptual de un RAG real: documentos, chunks, retrieval, respuesta con citas y evaluación.
            """
        ),
        code(SETUP),
        md(
            """
            ## 1. Cargar documentos y construir chunks

            La explicabilidad empieza antes del LLM. Si el documento está obsoleto, mal troceado o sin metadatos, el sistema puede fallar aunque el modelo generativo sea bueno.
            """
        ),
        code(
            r'''
documents = load_knowledge_documents(PROJECT_ROOT)
display(documents[["file_name", "area", "is_obsolete", "is_security_test"]])

chunks = chunk_documents(documents, max_chars=850)
print("Documentos:", len(documents))
print("Chunks:", len(chunks))
display(chunks[["chunk_id", "file_name", "area", "is_obsolete", "is_security_test"]].head(10))
'''
        ),
        md(
            """
            ## 2. Construir el índice RAG

            Por defecto excluimos documentos obsoletos y documentos de prueba de seguridad. Este filtro forma parte de la explicabilidad y del gobierno del sistema.
            """
        ),
        code(
            r'''
rag_index = build_rag_index(chunks, include_obsolete=False, include_security_test=False)
print("Chunks indexados:", len(rag_index.chunks))
display(rag_index.chunks["file_name"].value_counts().to_frame("chunks"))
'''
        ),
        md(
            """
            ## 3. Inspeccionar una consulta

            La demo muestra ranking, scores y textos. Esto permite discutir si el sistema recuperó evidencia suficiente o si el fallo está en retrieval, chunking o síntesis.
            """
        ),
        code(
            r'''
query = "¿Cuál es el plazo de devolución para compras online?"
retrieved = retrieve(rag_index, query, top_k=5)
display(retrieved[["rank", "score", "file_name", "chunk_id", "area"]])

answer_obj = grounded_answer(query, retrieved)
print("RESPUESTA SIMULADA:")
print(answer_obj["answer"])
print("\nCITAS:")
display(pd.DataFrame(answer_obj["citations"]))
'''
        ),
        md(
            """
            ## 4. Evaluar con el test set documental existente

            Usamos `FS_TestSet_Documental.csv`, que contiene preguntas y respuestas esperadas. La métrica de cobertura de keywords no reemplaza una revisión humana, pero ayuda a detectar regresiones y casos débiles.
            """
        ),
        code(
            r'''
test_path = PROJECT_ROOT / "datos" / "rag_copilot_studio" / "test_sets" / "FS_TestSet_Documental.csv"
test_set = pd.read_csv(test_path)
display(test_set)

rag_eval = evaluate_rag_questions(rag_index, test_set, top_k=5)
display(rag_eval[["question", "top_doc", "top_score", "retrieval_keyword_coverage", "answer_keyword_coverage", "citation_count"]])

summary = rag_eval[["retrieval_keyword_coverage", "answer_keyword_coverage", "citation_count"]].mean(numeric_only=True)
display(summary.to_frame("media"))
'''
        ),
        md(
            """
            ## 5. Diagnóstico de fallos

            Un caso puede recuperar bien pero responder mal. Eso separa fallo de retrieval y fallo de generación.
            """
        ),
        code(
            r'''
weak_cases = rag_eval.sort_values(["answer_keyword_coverage", "retrieval_keyword_coverage"]).head(5)
display(weak_cases[["question", "expected", "top_doc", "retrieval_keyword_coverage", "answer_keyword_coverage", "answer"]])
'''
        ),
        md(
            """
            ## 6. Comparar una respuesta mala y una respuesta explicable

            Esta comparación sirve para clase: una respuesta fluida sin fuentes no es equivalente a una respuesta trazable y con límites.
            """
        ),
        code(
            r'''
query = "¿Qué hago si el cliente no tiene ticket?"
retrieved = retrieve(rag_index, query, top_k=4)
good = grounded_answer(query, retrieved)
context = "\n".join(retrieved["text"].tolist())

bad_answer = "Puedes aceptar la devolución si el cliente insiste y parece de confianza."
good_answer = good["answer"] + " Si la evidencia no es suficiente, debe escalarse al Store Manager."

comparison = pd.DataFrame([
    {"tipo": "mala respuesta", "respuesta": bad_answer, **simple_answer_rubric(bad_answer, context, "buscar por fidelización; aprobación del Store Manager")},
    {"tipo": "respuesta explicable", "respuesta": good_answer, **simple_answer_rubric(good_answer, context, "buscar por fidelización; aprobación del Store Manager")},
])
display(comparison)
'''
        ),
        md(
            """
            ## 7. Guardar resultados de evaluación

            El resultado queda como evidencia de evaluación offline. En un proyecto real se compararía entre versiones de prompt, índice, modelo o chunking.
            """
        ),
        code(
            r'''
out_path = ARTIFACT_DIR / "demo_02_rag_eval.parquet"
rag_eval.to_parquet(out_path, index=False)
print("Evaluación guardada:", out_path)
'''
        ),
    ]
    write_nb(BASE / "notebooks_instructor" / "02_demo_rag_explicable_evaluacion.ipynb", cells)


def demo_03_agent_trace():
    cells = [
        md(
            """
            # Demo 03 · Agente comercial con trazabilidad y evaluación

            Esta demo simula un agente comercial de FraSoHome que combina cuatro herramientas: modelo de inactividad, explicación local, RAG documental y CRM. El objetivo es enseñar cómo se audita un agente por pasos, no solo por la respuesta final.
            """
        ),
        code(SETUP),
        md("## 1. Preparar herramientas del agente"),
        code(
            r'''
artifact = load_sales_artifact(PROJECT_ROOT)
churn = artifact["churn"]
crm = load_crm(PROJECT_ROOT)

documents = load_knowledge_documents(PROJECT_ROOT)
chunks = chunk_documents(documents)
rag_index = build_rag_index(chunks, include_obsolete=False, include_security_test=False)

print("Artefacto ventas:", artifact["_path"])
print("Clientes CRM:", crm["customer_id_std"].nunique())
print("Chunks RAG:", len(rag_index.chunks))
'''
        ),
        md(
            """
            ## 2. Definir la solicitud de negocio

            El agente recibe una tarea ambigua pero realista. Debe entenderla, planificar, consultar herramientas, respetar guardrails y responder con evidencia.
            """
        ),
        code(
            r'''
user_request = "Selecciona clientes Platino con alto riesgo de inactividad y prepara una propuesta de campaña respetando consentimiento, margen y presión comercial."
trace = build_agent_trace(user_request)
append_trace(trace, "intent", "reactivación comercial de clientes de alto valor con restricciones de gobierno")
append_trace(trace, "plan", "1) obtener cliente con score alto; 2) explicar drivers; 3) consultar reglas CRM; 4) comprobar consentimiento; 5) generar recomendación con cautelas")
display(pd.DataFrame(trace))
'''
        ),
        md("## 3. Tool 1: modelo de inactividad + explicación local"),
        code(
            r'''
append_trace(trace, "tool_call", "churn_model.predict_proba + explicación local", {"target": "label_inactive_90d"})
score, row_raw, contributions = local_feature_contributions(churn["result"], top_n=10)
customer_context = summarize_customer_context(row_raw, contributions)
append_trace(trace, "tool_result", "cliente prioritario y señales principales", {"score": round(score, 4), "signals": contributions["feature"].head(5).tolist()})

print(f"Score seleccionado: {score:.3f}")
display(row_raw.T.head(25))
display(contributions)
'''
        ),
        md("## 4. Tool 2: RAG sobre reglas CRM, consentimiento y campañas"),
        code(
            r'''
rag_query = "fidelización CRM consentimiento marketing presión comercial campaña reactivación cupón cliente Platino"
append_trace(trace, "tool_call", "rag.retrieve", {"query": rag_query, "top_k": 5})
evidence = retrieve(rag_index, rag_query, top_k=5)
append_trace(trace, "evidence", "documentos recuperados", evidence[["file_name", "chunk_id", "score"]].head(3).to_dict(orient="records"))
display(evidence[["rank", "score", "file_name", "chunk_id", "area"]])
'''
        ),
        md("## 5. Tool 3: CRM y guardrails"),
        code(
            r'''
customer_id = row_raw.iloc[0].get("customer_id_std")
crm_row = crm[crm["customer_id_std"] == customer_id].head(1)
append_trace(trace, "tool_call", "crm.lookup", {"customer_id": customer_id})

if len(crm_row):
    consent = str(crm_row.iloc[0].get("consentimiento_marketing", "")).lower()
    status = crm_row.iloc[0].get("estado_cliente", "")
    tier = crm_row.iloc[0].get("tier_fidelizacion", "")
else:
    consent, status, tier = "", "", ""

allowed_consent = consent in ["1", "sí", "si", "yes", "true", "s"]
not_blocked = "bloqueado" not in str(status).lower()
guardrail_ok = allowed_consent and not_blocked

append_trace(trace, "tool_result", "crm y consentimiento", {"customer_id": customer_id, "tier": tier, "estado": status, "consentimiento": consent})
append_trace(trace, "guardrail", "verificación de consentimiento y estado de cliente", {"approved_for_activation": guardrail_ok})

display(crm_row.T if len(crm_row) else pd.DataFrame({"warning": ["cliente no encontrado en CRM"]}))
print("Guardrail activación aprobado:", guardrail_ok)
'''
        ),
        md("## 6. Respuesta final del agente"),
        code(
            r'''
recommendation = recommendation_from_score(score, customer_context, evidence)
if not guardrail_ok:
    final_answer = (
        "No se recomienda activar automáticamente la campaña para este cliente. "
        "Aunque el score de inactividad es alto, la comprobación de consentimiento/estado no permite una acción directa. "
        "Se puede registrar el caso para revisión o buscar otro cliente elegible."
    )
else:
    final_answer = recommendation["recommendation"]

append_trace(trace, "final_answer", "respuesta al usuario", {"answer": final_answer})
print(final_answer)
'''
        ),
        md(
            """
            ## 7. Evaluar la traza del agente

            Evaluamos si la interacción contiene las capas mínimas: intención, plan, tool calls, evidencia, guardrails y respuesta final. Esta evaluación no mide si el texto suena bien; mide si el agente es auditable.
            """
        ),
        code(
            r'''
trace_df = pd.DataFrame(trace)
display(trace_df)
display(evaluate_agent_trace(trace))

trace_path = ARTIFACT_DIR / "demo_03_agent_trace.json"
trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
print("Traza guardada:", trace_path)
'''
        ),
        md(
            """
            ## 8. Lectura para el instructor

            El punto clave es separar tres niveles: el agente puede seleccionar bien las herramientas, pero aun así tener prohibida la activación por consentimiento; puede tener una respuesta razonable, pero sin evidencia; o puede tener buena evidencia, pero un plan incorrecto. Evaluar agentes implica revisar la cadena completa.
            """
        ),
    ]
    write_nb(BASE / "notebooks_instructor" / "03_demo_agente_comercial_trazabilidad_evaluacion.ipynb", cells)


if __name__ == "__main__":
    demo_01_score_to_recommendation()
    demo_02_rag_evaluation()
    demo_03_agent_trace()
