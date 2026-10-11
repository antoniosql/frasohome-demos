# App Streamlit · Marketing de precisión

Aplicación docente y ejecutiva para explorar FraSoHome desde el *customer analytics*, el marketing de precisión y la IA generativa. No llama a ninguna API externa.

## Ejecución

Desde la raíz del repositorio:

```bash
pip install -r escenarios/05-marketing-precision/streamlit_app/requirements.txt
streamlit run escenarios/05-marketing-precision/streamlit_app/app.py
```

En Linux o macOS también sirve `bash escenarios/05-marketing-precision/streamlit_app/run_app.sh`.

## De dónde lee

| Recurso | Ruta |
| --- | --- |
| Datos base | [`datos/retail_omnicanal/raw_csv`](../../../datos/retail_omnicanal/README.md) |
| Datos de marketing | [`datos/marketing_precision/raw_csv`](../../../datos/marketing_precision/README.md) |
| Salidas de modelos | `escenarios/05-marketing-precision/outputs/` si has ejecutado los notebooks; si no, [`sample_outputs/`](../sample_outputs/nb10_segment_summary.csv) |

## Páginas

1. **Resumen ejecutivo**: KPI globales, evolución por canal, segmentos de valor, campañas y *store marketing*.
2. **Explorador de datos**: cualquier dataset con filtros rápidos y exportación a CSV.
3. **Customer 360**: perfil unificado con valor, churn, categoría recomendada, tienda objetivo, transacciones, campañas y VOC.
4. **Audiencias**: listas de activación por consentimiento, segmento de valor, churn, CLV, categoría, activación local y omnicanalidad.
5. **Laboratorio de modelos**: segmentación con simulador, churn reentrenable, propensión por categoría, *cross-sell* con stock y margen, elasticidad promocional, riesgo de devolución y activación local.
6. **VOC + GenAI**: matriz VOC, *prompt packs* por tema y generador de copy con *guardrails*.
