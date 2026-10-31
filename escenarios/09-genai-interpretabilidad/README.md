# 09 · Interpretabilidad GenAI

| Capítulo | Audiencia | Duración | Tecnología |
| --- | --- | --- | --- |
| 7 · IA que se explica y agentes | IA aplicada, gobierno de IA, máster de Big Data | 4 h | Python · scikit-learn (TF-IDF) · python-docx · Jupyter · **sin APIs externas** |

## La historia en este punto

FraSoHome ya tiene modelos que puntúan clientes ([escenario 04](../04-analitica-ventas-ml/README.md)) y un asistente que responde con documentos ([escenario 07](../07-copilot-studio-rag/README.md)). Comercial quiere juntar ambos: que un asistente diga **a quién llamar, por qué y con qué oferta, sin saltarse la política**. Antes de ponerlo en manos de la red de tiendas, el comité de riesgos pregunta: ¿cómo sabemos por qué ha dicho lo que ha dicho? ¿Y cómo lo evaluamos?

## Qué se demuestra

- La diferencia entre *score*, explicación ML, evidencia documental y recomendación generada.
- Trazabilidad mínima de una solución GenAI: entradas, contexto, evidencia, reglas y salida.
- Un RAG local inspeccionable: *chunking*, recuperación, respuesta con citas y evaluación que separa recuperación y generación.
- Un agente comercial simulado que combina modelo, RAG y CRM, evaluado por capas: intención, plan, herramientas, evidencia, *guardrails* y respuesta final.
- Rúbricas sencillas para comparar respuestas.

La capa generativa está **simulada de forma controlada** para que la clase se centre en explicabilidad, trazabilidad y evaluación, no en la API de turno. En producción, el TF-IDF se sustituiría por *embeddings*, búsqueda híbrida y *reranking*; las preguntas de evaluación serían las mismas.

## Recursos necesarios

### Entorno

| Recurso | Para qué |
| --- | --- |
| Python 3.10+ y [`requirements.txt`](requirements.txt) | pandas, numpy, scikit-learn, matplotlib, joblib, python-docx, pyarrow, Jupyter |

### Datos y artefactos

| Recurso | Uso |
| --- | --- |
| [Documentos FS-KB-01 a FS-KB-10](../../datos/rag_copilot_studio/knowledge_base/Indice_Documentos_Conocimiento.md) | Corpus del RAG |
| [`FS_TestSet_Documental.csv`](../../datos/rag_copilot_studio/test_sets/FS_TestSet_Documental.csv) | Preguntas y respuestas esperadas |
| [`crm.csv`](../../datos/retail_omnicanal/raw_csv/crm.csv) | Contexto de cliente para el agente |
| [`sales_models_artifact.joblib`](../04-analitica-ventas-ml/artifacts/sales_models_artifact.joblib) | Modelos y explicaciones del escenario 04 |

### Material de la demo

| Fichero | Propósito |
| --- | --- |
| [01 · Del *score* a una recomendación GenAI explicable](notebooks_instructor/01_demo_score_a_recomendacion_genai_explicable.ipynb) | Convertir un *score* de inactividad y sus señales locales en una recomendación trazable |
| [02 · RAG explicable y evaluación](notebooks_instructor/02_demo_rag_explicable_evaluacion.ipynb) | Inspeccionar la recuperación, responder con citas y evaluar con el *test set* |
| [03 · Agente comercial: trazabilidad y evaluación](notebooks_instructor/03_demo_agente_comercial_trazabilidad_evaluacion.ipynb) | Simular un agente modelo + RAG + CRM y evaluar su traza por capas |
| [`common/genai_frasohome.py`](common/genai_frasohome.py) | Utilidades compartidas |
| [`artifacts/`](artifacts/demo_01_recommendation_trace.json) | Trazas y evaluaciones de ejemplo: [traza de recomendación](artifacts/demo_01_recommendation_trace.json), [evaluación RAG](artifacts/demo_02_rag_eval.parquet), [traza del agente](artifacts/demo_03_agent_trace.json) |
| [`build_notebooks.py`](build_notebooks.py) | Regenera los notebooks |
| [Guía del paquete](guia-paquete.md) | Orden y contenidos |
| [Temario · 4 h](../../docencia/temario-interpretabilidad-llm-rag-agentes-4h.md) · [Ebook](../../docencia/ebook-interpretabilidad-evaluacion-llm.md) | Programación y lectura de apoyo |

## Cómo ejecutarla

```bash
pip install -r escenarios/09-genai-interpretabilidad/requirements.txt
jupyter lab escenarios/09-genai-interpretabilidad/notebooks_instructor
```

Ejecuta los notebooks 01 → 02 → 03. Necesitan el artefacto del escenario 04, que ya viene en el repositorio; si lo regeneras allí, estos notebooks usan la versión nueva.

## Guion sugerido (4 h)

| Bloque | Contenido |
| --- | --- |
| 1 | De interpretabilidad ML a explicabilidad GenAI: interpretabilidad, explicabilidad, trazabilidad y evaluación |
| 2 | Qué se puede y qué no se puede explicar de un LLM: tokens, *embeddings*, contexto, atención |
| 3 | RAG explicable: anatomía, fallos típicos y métricas (notebook 02) |
| 4 | Agentes: traza, herramientas, evaluación por capas y riesgos (notebooks 01 y 03) |

## Mensajes clave

- En GenAI se explica el sistema, no solo el modelo.
- Una explicación generada por el propio LLM no es necesariamente la explicación real.
- El contexto es la primera unidad de explicabilidad: si no sabes qué entró, no sabes por qué salió.
- Un agente se evalúa por capas; la respuesta final es solo la última.

## Con datos vivos (opcional)

Esta demo usa los ficheros del escenario RAG y los de retail: una fotografía de 2024–2025 con errores intencionados. Si quieres trabajar con datos que cambien, el [escenario 11](../11-web-transaccional/README.md) es una web real donde se venden, devuelven y atienden pedidos sobre Azure SQL y Cosmos DB, y su exportación (`tools/export_csv.py` `--dominio rag,retail`) los devolverá al mismo formato que `datos/`, sin tocar el código de esta demo.

La exportación todavía no está construida (fase 5 del escenario 11). Hasta entonces, usa `datos/` como hasta ahora.
