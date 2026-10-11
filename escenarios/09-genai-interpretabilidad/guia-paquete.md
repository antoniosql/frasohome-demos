# FraSoHome · demos de interpretabilidad GenAI

Notebooks de demostración para el módulo de 4 horas **Interpretabilidad de LLM, RAG y Agentes**.

Estas demos están conectadas con el paquete anterior de analítica de ventas e interpretabilidad ML:

- usan el artefacto `sales_models_artifact.joblib` generado en `escenarios/04-analitica-ventas-ml`;
- reutilizan los documentos de conocimiento de `datos/rag_copilot_studio`;
- no dependen de APIs externas de LLM;
- simulan la capa generativa de forma controlada para centrar la clase en explicabilidad, trazabilidad y evaluación.

## Orden recomendado

1. `notebooks_instructor/01_demo_score_a_recomendacion_genai_explicable.ipynb`
2. `notebooks_instructor/02_demo_rag_explicable_evaluacion.ipynb`
3. `notebooks_instructor/03_demo_agente_comercial_trazabilidad_evaluacion.ipynb`

## Demos

| Notebook | Propósito |
|---|---|
| `01_demo_score_a_recomendacion_genai_explicable.ipynb` | Convertir un score de inactividad y sus señales locales en una recomendación comercial trazable. |
| `02_demo_rag_explicable_evaluacion.ipynb` | Construir un RAG local, inspeccionar retrieval, generar respuestas con citas y evaluar con el test set documental. |
| `03_demo_agente_comercial_trazabilidad_evaluacion.ipynb` | Simular un agente que combina modelo, RAG y CRM, y evaluar su traza por capas. |

## Datos y artefactos usados

- `datos/rag_copilot_studio/knowledge_base/Documentos_Knowledge_Clasificados`
- `datos/rag_copilot_studio/test_sets/FS_TestSet_Documental.csv`
- `datos/retail_omnicanal/raw_csv/crm.csv`
- `escenarios/04-analitica-ventas-ml/artifacts/sales_models_artifact.joblib`

## Qué se enseña

- Diferencia entre score, explicación ML, evidencia documental y recomendación generada.
- Trazabilidad mínima de una solución GenAI.
- Evaluación de RAG separando recuperación y generación.
- Uso de rúbricas sencillas para comparar respuestas.
- Evaluación de agentes por capas: intención, plan, herramientas, evidencia, guardrails y respuesta final.

## Nota docente

El RAG usa `TfidfVectorizer` para evitar dependencias externas. En una implantación real se sustituiría por embeddings, búsqueda híbrida y reranking, pero las preguntas de evaluación serían las mismas.
