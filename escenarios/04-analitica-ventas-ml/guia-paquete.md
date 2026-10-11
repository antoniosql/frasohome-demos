# FraSoHome · paquete de demos y ejercicios

Paquete docente para dos sesiones enlazadas:

- **Sesión 1 · Analítica de ventas**: preparación de datos, ingeniería de características, entrenamiento y priorización comercial.
- **Sesión 2 · Interpretabilidad de ML**: explicación global y local de los modelos creados en la sesión anterior.
- **Extensión · Interpretabilidad de LLM, RAG y agentes**: módulo teórico-práctico de 4 horas conectado con los modelos, explicaciones y decisiones comerciales anteriores. Ver [el temario de 4 h](../../docencia/temario-interpretabilidad-llm-rag-agentes-4h.md).

El paquete no genera nuevos CSV de origen. Todos los notebooks trabajan sobre los CSV operativos existentes en:

- `datos/retail_omnicanal/raw_csv`
- `datos/marketing_precision/raw_csv`

Los artefactos de trabajo se guardan en `artifacts` con `joblib` para conectar una sesión con la siguiente.

## Estructura

| Carpeta | Uso |
|---|---|
| `common` | Utilidades compartidas de carga, limpieza, feature engineering, preprocesado y entrenamiento. |
| `notebooks_instructor` | Demos completas para impartir en vivo. |
| `notebooks_alumnos` | Ejercicios con instrucciones y huecos TODO. |
| `notebooks_soluciones` | Soluciones ejecutables de referencia. |
| `artifacts` | Modelos y datasets serializados generados por los notebooks. |

## Orden recomendado para el instructor

1. Ejecutar `notebooks_instructor/01_demo_ventas_feature_engineering_modelos.ipynb`.
2. Confirmar que se crea `artifacts/sales_models_artifact.joblib`.
3. Ejecutar `notebooks_instructor/02_demo_interpretabilidad_modelos_ventas.ipynb`.

El segundo notebook carga el artefacto del primero. Esta dependencia es intencional: la interpretabilidad se aplica sobre los mismos modelos de analítica de ventas, no sobre ejemplos aislados.

La extensión de LLM/RAG/agentes parte de estos mismos resultados: los scores y explicaciones de ML pasan a ser señales que un asistente o agente comercial podría usar junto con políticas, documentos y reglas de negocio de FraSoHome.

Los notebooks de esa extensión están en:

- `../genai_interpretabilidad_frasohome/notebooks_instructor`

## Orden recomendado para alumnos

1. Resolver `notebooks_alumnos/01_ejercicio_ventas_feature_engineering_modelos.ipynb`.
2. Guardar `artifacts/alumnos_sales_models_artifact.joblib`.
3. Resolver `notebooks_alumnos/02_ejercicio_interpretabilidad_modelos_ventas.ipynb`.

Si un grupo se bloquea, se puede ejecutar la solución 01 para generar el artefacto y continuar con interpretabilidad.

## Casos analíticos incluidos

### Riesgo de inactividad

Unidad de análisis: cliente en un snapshot temporal.

- Histórico observado: 180 días anteriores.
- Horizonte de etiqueta: 90 días posteriores.
- Target: `label_inactive_90d`.
- Uso de negocio: priorizar acciones de retención/reactivación.

### Propensión de campaña

Unidad de análisis: contacto comercial.

- Histórico observado: 180 días anteriores al contacto.
- Horizonte de etiqueta: conversión a 30 días.
- Target: `conversion_30d_flag`.
- Uso de negocio: priorizar contactos, canales y ofertas.

## Técnicas cubiertas

- Lectura raw y diagnóstico de calidad.
- Normalización de IDs.
- Parseo de fechas e importes con formatos mixtos.
- Filtro de ventana operativa 2024-2025.
- Feature engineering temporal.
- Variables RFM, canal, categoría, margen, devolución, experiencia y actividad digital.
- Imputación, escalado y one-hot encoding con `Pipeline`.
- Entrenamiento de `RandomForestClassifier`.
- Métricas de clasificación y deciles de score.
- Importancia global del modelo.
- Permutation importance.
- PDP.
- SHAP.
- LIME.
- Traducción de explicaciones a decisiones comerciales.

## Dependencias

Las dependencias principales son:

- `pandas`
- `numpy`
- `scikit-learn`
- `matplotlib`
- `joblib`
- `shap`
- `lime`
- `nbformat`

En este entorno ya están disponibles. El fichero `requirements.txt` queda como referencia para reproducir el paquete en otro equipo.
