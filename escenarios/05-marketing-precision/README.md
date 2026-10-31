# 05 · Marketing de precisión

| Capítulo | Audiencia | Duración | Tecnología |
| --- | --- | --- | --- |
| 3 · Vender mejor, no solo vender más | Marketing, CRM, ecommerce, data science | 30 min de demo (app) · 1–2 días como curso (10 notebooks) | Python · pandas · scikit-learn · Streamlit |

## La historia en este punto

Marketing lanza 26 campañas al año por email, SMS y push, reparte cupones y mide aperturas. Pero no sabe si el cliente que abrió el email es el mismo que compró en tienda, si el descuento creó la venta o solo la adelantó, ni si está recomendando un sofá que no hay en el almacén de Sevilla. El equipo rediseña el caso FraSoHome para pasar **de la preparación de datos a decisiones de marketing**: a quién, qué, cuándo, por qué canal y con qué margen.

## Qué se demuestra

Diez casos de uso, cada uno con su notebook, su *score* o regla de decisión y su KPI de activación:

| # | Caso | Tipo | Notebook | Salidas |
| --- | --- | --- | --- | --- |
| 1 | Resolución de identidad y Customer 360 | Analítica avanzada | [09](notebooks/Notebook_09_Resolucion_Identidad_Customer360_FraSoHome.ipynb) | [identity_mapping](sample_outputs/nb09_identity_mapping.csv) · [customer360](sample_outputs/nb09_customer360.csv) |
| 2 | Segmentación de valor omnicanal y CLV | Analítica avanzada | [10](notebooks/Notebook_10_Segmentacion_Valor_CLV_FraSoHome.ipynb) | [segmentación](sample_outputs/nb10_customer_value_segmentation.csv) · [resumen](sample_outputs/nb10_segment_summary.csv) |
| 3 | Churn y *next best action* | IA predictiva | [11](notebooks/Notebook_11_Churn_Next_Best_Action_FraSoHome.ipynb) | [training](sample_outputs/nb11_churn_training_dataset.csv) · [scoring](sample_outputs/nb11_churn_scoring_latest.csv) |
| 4 | Propensión por categoría | IA predictiva | [12](notebooks/Notebook_12_Propension_Categoria_FraSoHome.ipynb) | [training](sample_outputs/nb12_propension_categoria_training.csv) · [scoring](sample_outputs/nb12_propension_categoria_scoring.csv) |
| 5 | *Cross-sell* con stock y margen | Recomendación | [13](notebooks/Notebook_13_Cross_Sell_Basket_Stock_Margen_FraSoHome.ipynb) | [reglas](sample_outputs/nb13_cross_sell_rules.csv) · [candidatos](sample_outputs/nb13_cross_sell_customer_candidates.csv) |
| 6 | Elasticidad promocional | Analítica avanzada | [14](notebooks/Notebook_14_Elasticidad_Promocional_FraSoHome.ipynb) | [scoreboard](sample_outputs/nb14_promo_scoreboard.csv) · [decisiones](sample_outputs/nb14_promo_decisions.csv) |
| 7 | Predicción de devolución | IA predictiva | [15](notebooks/Notebook_15_Prediccion_Devolucion_FraSoHome.ipynb) | [scoring](sample_outputs/nb15_return_risk_scoring.csv) · [por producto](sample_outputs/nb15_product_return_risk_summary.csv) |
| 8 | Activación local con stock | Activación | [16](notebooks/Notebook_16_Activacion_Local_Store_Marketing_FraSoHome.ipynb) | [plan](sample_outputs/nb16_local_activation_plan.csv) · [tienda × categoría](sample_outputs/nb16_store_category_summary.csv) |
| 9 | GenAI para voz del cliente | IA generativa | [17](notebooks/Notebook_17_GenAI_Voz_Cliente_FraSoHome.ipynb) | [matriz VOC](sample_outputs/nb17_voc_issue_matrix.csv) · [prompt pack](sample_outputs/nb17_voc_prompt_pack.csv) |
| 10 | GenAI para copy y creatividad | IA generativa | [18](notebooks/Notebook_18_GenAI_Copy_Creatividad_FraSoHome.ipynb) | [briefs](sample_outputs/nb18_genai_copy_briefs.csv) · [biblioteca de prompts](sample_outputs/nb18_genai_prompt_library.csv) |

Los casos 9 y 10 **no llaman a ningún LLM**: preparan contexto, *guardrails* de marca, *prompts* y borradores para que el uso posterior de IA generativa sea controlado y auditable.

## Recursos necesarios

### Entorno

| Recurso | Para qué |
| --- | --- |
| Python 3.10+ y [`requirements.txt`](requirements.txt) | Notebooks (pandas, numpy, scikit-learn, Jupyter) |
| [`streamlit_app/requirements.txt`](streamlit_app/requirements.txt) | App (Streamlit, Altair, scikit-learn) |

No hace falta conexión a ninguna API.

### Datos

| Carpeta | Ficheros |
| --- | --- |
| [`datos/retail_omnicanal/raw_csv`](../../datos/retail_omnicanal/README.md) | `crm`, `fact_transacciones`, `productos`, `stock_diario`, `pedidos`, `lineas_pedido`, `ventas_pos`, devoluciones, `tiendas` |
| [`datos/marketing_precision/raw_csv`](../../datos/marketing_precision/README.md) | Los 17 CSV del dominio: identidad, campañas, contactos, eventos, promociones, cupones, tickets, feedback, costes, afinidad, creatividades y *guardrails* |
| [`datos/relaciones`](../../datos/relaciones/README.md) | [`marketing_precision_operational_links.csv`](../../datos/relaciones/marketing_precision_operational_links.csv) documenta qué columnas enlazan con retail |

### Material de la demo

| Carpeta o fichero | Contenido |
| --- | --- |
| [`notebooks/`](notebooks/catalogo_notebooks.csv) | Notebooks 09 a 18 y su [catálogo](notebooks/catalogo_notebooks.csv) |
| [`helpers/marketing_precision_utils.py`](helpers/marketing_precision_utils.py) | Carga, limpieza y exportación comunes |
| [`sample_outputs/`](sample_outputs/nb10_segment_summary.csv) | Salidas de referencia de cada notebook |
| [`streamlit_app/`](streamlit_app/README.md) | App ejecutiva: resumen, explorador, Customer 360, audiencias, laboratorio de modelos y VOC + GenAI |
| [Análisis del rediseño del caso](caso.md) | Diagnóstico y los diez casos explicados |
| [Guía docente](guia-docente.md) | Secuencia recomendada para clase |

## Cómo ejecutarla

### La app (demo de 30 minutos)

```bash
pip install -r escenarios/05-marketing-precision/streamlit_app/requirements.txt
streamlit run escenarios/05-marketing-precision/streamlit_app/app.py
```

La app lee los datos de `datos/` y las salidas de `sample_outputs/`. Si regeneras los notebooks, usa automáticamente las salidas nuevas de `outputs/`.

### Los notebooks (curso)

```bash
pip install -r escenarios/05-marketing-precision/requirements.txt
cd escenarios/05-marketing-precision/notebooks
jupyter lab
```

Cada notebook escribe sus CSV en `escenarios/05-marketing-precision/outputs/` (ignorada por git).

## Guion sugerido

**Demo con la app (30 min)**

| Minuto | Página | Mensaje |
| --- | --- | --- |
| 0–5 | Resumen ejecutivo | Ventas por canal, segmentos de valor y campañas |
| 5–12 | Customer 360 | Un cliente con identidad resuelta: valor, churn, categoría recomendada, tienda, VOC |
| 12–18 | Audiencias | Una audiencia con consentimiento, valor, churn y stock local, lista para exportar |
| 18–25 | Laboratorio de modelos | Elasticidad promocional y riesgo de devolución |
| 25–30 | VOC + GenAI | *Prompt pack* y copy con *guardrails*, sin llamar a ningún modelo |

**Curso**: 09 + 10 (base de cliente y rentabilidad) → 11 + 12 + 13 (predicción y recomendación) → 14 + 15 + 16 (promociones, devoluciones y activación local) → 17 + 18 (IA generativa con *guardrails*).

## Mensajes clave

- Sin resolución de identidad no hay Customer 360, y sin Customer 360 la personalización es una suposición.
- Recomendar lo que no hay en stock o lo que se devuelve destruye margen.
- La IA generativa en marketing se prepara con datos y reglas de marca antes de escribir el primer *prompt*.

## Con datos vivos (opcional)

Esta demo usa los CSV de marketing y de retail: una fotografía de 2024–2025 con errores intencionados. Si quieres trabajar con datos que cambien, el [escenario 11](../11-web-transaccional/README.md) es una web real donde se venden, devuelven y atienden pedidos sobre Azure SQL y Cosmos DB, y su exportación (`tools/export_csv.py` `--dominio marketing,retail`) los devolverá al mismo formato que `datos/`, sin tocar el código de esta demo.

La exportación todavía no está construida (fase 5 del escenario 11). Hasta entonces, usa `datos/` como hasta ahora.
