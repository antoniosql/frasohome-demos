# 04 · Analítica de ventas y ML

| Capítulo | Audiencia | Duración | Tecnología |
| --- | --- | --- | --- |
| 3 · Vender mejor, no solo vender más | Analistas, data science, máster de Big Data | Dos sesiones de 8 h (analítica de ventas + interpretabilidad ML) | Python · pandas · scikit-learn · SHAP · LIME · Jupyter |

## La historia en este punto

Con la *fact table* en orden, el director comercial deja de preguntar "cuánto vendimos" y empieza a preguntar **a quién hay que llamar**: qué clientes se están enfriando, a quién merece la pena enviar una campaña y qué productos acaban devueltos. El equipo construye modelos sencillos y, en una segunda sesión, aprende a explicarlos para que comercial confíe en ellos.

## Qué se demuestra

- Lectura raw, diagnóstico de calidad y normalización de IDs, fechas e importes.
- Ventana operativa 2024–2025 para no contaminar el análisis con fechas imposibles.
- *Feature engineering* temporal: RFM, canal, categoría, margen, devoluciones, experiencia y actividad digital.
- Dos casos con etiqueta temporal honesta:
    - **Riesgo de inactividad**: cliente en un *snapshot*, 180 días de histórico, etiqueta `label_inactive_90d`.
    - **Propensión de campaña**: contacto comercial, 180 días de histórico, etiqueta `conversion_30d_flag`.
- `Pipeline` de scikit-learn con imputación, escalado y *one-hot*; `RandomForestClassifier`; métricas y deciles.
- Interpretabilidad global y local: importancia, *permutation importance*, PDP, SHAP y LIME, y su traducción a decisiones comerciales.

## Recursos necesarios

### Entorno

| Recurso | Para qué |
| --- | --- |
| Python 3.10+ y [`requirements.txt`](requirements.txt) | pandas, numpy, scikit-learn, matplotlib, joblib, shap, lime, nbformat, Jupyter |

### Datos

| Fichero | Uso |
| --- | --- |
| [`fact_transacciones.csv`](../../datos/retail_omnicanal/raw_csv/fact_transacciones.csv) | Movimientos comerciales |
| [`crm.csv`](../../datos/retail_omnicanal/raw_csv/crm.csv) | Atributos de cliente |
| [`productos.csv`](../../datos/retail_omnicanal/raw_csv/productos.csv) · [`stock_diario.csv`](../../datos/retail_omnicanal/raw_csv/stock_diario.csv) | Categoría, coste, margen y disponibilidad |
| [`contactos_campana.csv`](../../datos/marketing_precision/raw_csv/contactos_campana.csv) | Unidad de análisis de propensión |
| [`eventos_web_app.csv`](../../datos/marketing_precision/raw_csv/eventos_web_app.csv), [`feedback_clientes.csv`](../../datos/marketing_precision/raw_csv/feedback_clientes.csv), [`tickets_atencion_cliente.csv`](../../datos/marketing_precision/raw_csv/tickets_atencion_cliente.csv), [`costes_operativos_transaccion.csv`](../../datos/marketing_precision/raw_csv/costes_operativos_transaccion.csv) | Actividad digital, experiencia y costes |

El paquete no genera CSV nuevos: la fuente de verdad son los ficheros raw.

### Material de la demo

| Carpeta o fichero | Contenido |
| --- | --- |
| [`common/frasohome_ml.py`](common/frasohome_ml.py) | Carga, limpieza, *features*, preprocesado y entrenamiento compartidos |
| [`notebooks_instructor/`](notebooks_instructor/01_demo_ventas_feature_engineering_modelos.ipynb) | [01 · Ventas, *features* y modelos](notebooks_instructor/01_demo_ventas_feature_engineering_modelos.ipynb) · [02 · Interpretabilidad](notebooks_instructor/02_demo_interpretabilidad_modelos_ventas.ipynb) |
| [`notebooks_alumnos/`](notebooks_alumnos/01_ejercicio_ventas_feature_engineering_modelos.ipynb) | Ejercicios con huecos `TODO`: [01](notebooks_alumnos/01_ejercicio_ventas_feature_engineering_modelos.ipynb) · [02](notebooks_alumnos/02_ejercicio_interpretabilidad_modelos_ventas.ipynb) |
| [`notebooks_soluciones/`](notebooks_soluciones/01_solucion_ventas_feature_engineering_modelos.ipynb) | Soluciones ejecutables: [01](notebooks_soluciones/01_solucion_ventas_feature_engineering_modelos.ipynb) · [02](notebooks_soluciones/02_solucion_interpretabilidad_modelos_ventas.ipynb) |
| [`artifacts/sales_models_artifact.joblib`](artifacts/sales_models_artifact.joblib) | Modelos y datasets ya entrenados (los usa también el [escenario 09](../09-genai-interpretabilidad/README.md)) |
| [`build_notebooks.py`](build_notebooks.py) | Regenera los notebooks desde código |
| [Guía del paquete](guia-paquete.md) | Casos, técnicas y orden recomendado |
| [Temario analítica de ventas · 8 h](../../docencia/temario-analitica-ventas-8h.md) · [Temario interpretabilidad ML · 8 h](../../docencia/temario-interpretabilidad-ml-8h.md) | Programación de las sesiones |
| [Ebook de analítica de ventas](../../docencia/ebook-analitica-ventas.md) · [versión extendida](../../docencia/ebook-analitica-ventas-narrativa-extendida.md) | Lectura de apoyo |

## Cómo ejecutarla

```bash
pip install -r escenarios/04-analitica-ventas-ml/requirements.txt
jupyter lab escenarios/04-analitica-ventas-ml
```

**Instructor**

1. Ejecuta `notebooks_instructor/01_demo_ventas_feature_engineering_modelos.ipynb`.
2. Comprueba que se actualiza `artifacts/sales_models_artifact.joblib`.
3. Ejecuta `notebooks_instructor/02_demo_interpretabilidad_modelos_ventas.ipynb`, que carga ese artefacto.

**Alumnos**

1. Resuelven `notebooks_alumnos/01_...` y guardan `artifacts/alumnos_sales_models_artifact.joblib`.
2. Resuelven `notebooks_alumnos/02_...`.
3. Si un grupo se bloquea, la solución 01 genera el artefacto y permite seguir.

Los notebooks localizan la raíz del repositorio buscando las carpetas `datos/` y `escenarios/`, así que funcionan desde cualquier subcarpeta.

## Guion sugerido

| Sesión | Bloques |
| --- | --- |
| Analítica de ventas (8 h) | Del reporting al sistema de decisión · *fact table* comercial · KPI de ventas, margen y cliente · Customer 360 y RFM · del caso de uso al dataset · modelos baseline · activación · roadmap |
| Interpretabilidad ML (8 h) | Por qué interpretar · tipos de explicación · modelos interpretables · importancia global · PDP e ICE · LIME · SHAP · comunicación ejecutiva |

## Mensajes clave

- La etiqueta se define en el tiempo: histórico antes del *snapshot*, resultado después. Lo demás es fuga de información.
- Un score no es una decisión: hay que traducirlo a quién, cuándo y con qué acción.
- La explicación se hace sobre el mismo modelo que se va a usar, no sobre un ejemplo de juguete.

## Siguiente paso

[05 · Marketing de precisión](../05-marketing-precision/README.md) amplía los casos de uso, y [09 · Interpretabilidad GenAI](../09-genai-interpretabilidad/README.md) convierte estos scores en recomendaciones trazables.
