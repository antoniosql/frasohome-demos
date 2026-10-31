# 02 · Fabric: del CSV a la fact table

| Capítulo | Audiencia | Duración | Tecnología |
| --- | --- | --- | --- |
| 2 · Poner orden en los datos | Equipos de datos, preventa técnica, formación Microsoft Fabric | 40 min de demo · 8–10 h como curso | Microsoft Fabric (Lakehouse + notebooks) o Python local · Streamlit |

## La historia en este punto

La dirección ha pedido una vista única del negocio. El equipo de datos recibe once CSV exportados del CRM, el ecommerce, el TPV y el ERP, tal cual salen de cada sistema. Antes de hablar de dashboards o de IA tiene que responder a algo más básico: **¿se puede confiar en estos datos?** Y si no, ¿qué hay que hacer para que sí?

## Qué se demuestra

- Ingesta "en bruto" (`dtype=str`) para no perder los errores que hay que estudiar.
- Perfilado y un *Data Quality Report* con nulos, duplicados, formatos e integridad referencial.
- Limpieza y estandarización de IDs, fechas, importes y textos, dejando constancia de cada regla.
- Integración de ventas y devoluciones online y en tienda en una *fact table* con un grano explícito.
- *Features* de cliente (RFM, devoluciones, canal) y de producto, cesta y propensión.
- Preparación para ML/BI, modelos baseline y *scoring* exportable a Power BI.
- Una app Streamlit para enseñar KPI, calidad, RFM, producto, stock y cesta.

## Recursos necesarios

### Entorno

| Opción | Requisitos |
| --- | --- |
| **Microsoft Fabric** | Workspace con capacidad (o prueba), un Lakehouse y permisos para crear notebooks |
| **Local** | Python 3.10+ y las dependencias de [`requirements.txt`](requirements.txt) (pandas, numpy, scikit-learn, matplotlib, joblib, Jupyter) |
| App Streamlit | Las dependencias de [`streamlit_app/requirements_streamlit.txt`](streamlit_app/requirements_streamlit.txt) |

### Datos

Los once CSV de [`datos/retail_omnicanal/raw_csv`](../../datos/retail_omnicanal/README.md):

| Fichero | Sistema | Grano |
| --- | --- | --- |
| [`crm.csv`](../../datos/retail_omnicanal/raw_csv/crm.csv) | CRM | Cliente |
| [`productos.csv`](../../datos/retail_omnicanal/raw_csv/productos.csv) | ERP | Producto |
| [`tiendas.csv`](../../datos/retail_omnicanal/raw_csv/tiendas.csv) | Maestro | Tienda o ubicación |
| [`pedidos.csv`](../../datos/retail_omnicanal/raw_csv/pedidos.csv) | Ecommerce | Cabecera de pedido |
| [`lineas_pedido.csv`](../../datos/retail_omnicanal/raw_csv/lineas_pedido.csv) | Ecommerce | Línea de pedido |
| [`devoluciones_online.csv`](../../datos/retail_omnicanal/raw_csv/devoluciones_online.csv) | Ecommerce | Devolución |
| [`ventas_pos.csv`](../../datos/retail_omnicanal/raw_csv/ventas_pos.csv) | TPV | Línea de ticket |
| [`pagos_tienda.csv`](../../datos/retail_omnicanal/raw_csv/pagos_tienda.csv) | TPV | Pago (admite pagos mixtos) |
| [`devoluciones_tienda.csv`](../../datos/retail_omnicanal/raw_csv/devoluciones_tienda.csv) | TPV | Devolución |
| [`stock_diario.csv`](../../datos/retail_omnicanal/raw_csv/stock_diario.csv) | ERP | Tienda × producto × día |
| [`fact_transacciones.csv`](../../datos/retail_omnicanal/raw_csv/fact_transacciones.csv) | Integrada | Línea de venta o devolución (referencia) |

### Material de la demo

| Fichero | Contenido |
| --- | --- |
| [Notebook 1 · Ingesta y tipado](notebooks/Notebook_1_Ingesta_y_Tipado_FraSoHome.ipynb) | Carga robusta, fechas heterogéneas, importes con `€` y coma |
| [Notebook 2 · Perfilado y calidad](notebooks/Notebook_2_Perfilado_y_Reporte_Calidad_FraSoHome.ipynb) | Nulos, duplicados, PK/FK, conciliaciones y *Data Quality Report* |
| [Notebook 3 · Limpieza](notebooks/Notebook_3_Limpieza_y_Estandarizacion_FraSoHome.ipynb) | Reglas por dataset y métricas antes/después |
| [Notebook 4 · Integración](notebooks/Notebook_4_Integracion_y_Fact_Table_FraSoHome.ipynb) | *Fact table* omnicanal con devoluciones en negativo |
| [Notebook 5 · Features](notebooks/Notebook_5_Features_RFM_Churn_Basket_Propension_FraSoHome.ipynb) | RFM, churn, cesta, propensión por *snapshots* |
| [Notebook 6 · Preprocesamiento](notebooks/Notebook_6_Preprocesamiento_Final_ML_BI_FraSoHome.ipynb) | Imputación, escalado y *one-hot* |
| [Notebook 7 · Modelos baseline](notebooks/Notebook_7_Baseline_Modeling_FraSoHome.ipynb) | Dummy, regresión logística, random forest, gradient boosting |
| [Notebook 8 · Scoring y export BI](notebooks/Notebook_8_Scoring_y_Export_BI_FraSoHome.ipynb) | Score, deciles, *drivers* y diccionario de acciones |
| [App Streamlit](streamlit_app/README.md) | [`app_frasohome_streamlit.py`](streamlit_app/app_frasohome_streamlit.py) y el notebook que la explica |
| [Perfil de datos](perfil-datos.md) | Filas, grano, claves y problemas por fichero |
| [Ejemplo de *Data Quality Report*](salidas-ejemplo/data_quality_report_provisional.csv) | Salida del notebook 2 |
| [Guion de presentación Fabric](../../presentaciones/fabric-intro-deck.md) | Diapositivas de introducción |

## Cómo ejecutarla

### En local

```bash
pip install -r escenarios/02-fabric-preparacion-datos/requirements.txt
cd escenarios/02-fabric-preparacion-datos/notebooks
jupyter lab
```

Ejecuta los notebooks del 1 al 8 en orden. Leen los CSV desde `datos/retail_omnicanal/raw_csv` y cada uno deja sus salidas en una carpeta junto a los notebooks (`output_clean`, `output_integrated`, `output_features`, `output_ml`, `output_models`, `output_scoring`). Esas carpetas están en `.gitignore`.

### En Microsoft Fabric

1. Crea un Lakehouse y sube los once CSV a `Files/raw_csv`.
2. Importa los notebooks en el workspace y asócialos al Lakehouse.
3. En cada notebook, cambia `DATA_DIR` por la ruta que indica su comentario (`/lakehouse/default/Files/raw_csv`).
4. Ejecuta del 1 al 8. Para persistir las salidas en OneLake, apunta también las carpetas `output_*` a `/lakehouse/default/Files/`.

### La app

```bash
pip install -r escenarios/02-fabric-preparacion-datos/streamlit_app/requirements_streamlit.txt
streamlit run escenarios/02-fabric-preparacion-datos/streamlit_app/app_frasohome_streamlit.py
```

La app lee directamente `datos/retail_omnicanal/raw_csv`. Si existe `output_scoring/churn_scoring.csv` en la carpeta desde la que la lanzas, también muestra el *scoring*.

## Guion sugerido (40 min)

| Minuto | Bloque | Qué enseñar |
| --- | --- | --- |
| 0–5 | Contexto | La pregunta del comité y los once ficheros |
| 5–15 | Notebook 2 | El *Data Quality Report*: duplicados, claves huérfanas, fechas imposibles |
| 15–22 | Notebook 3 | Una regla de limpieza explicada (IDs o fechas) y el antes/después |
| 22–30 | Notebook 4 | El grano de la *fact table* y por qué las devoluciones van en negativo |
| 30–36 | Notebook 5 | RFM y la ventana operativa: qué pasa si no filtras las fechas de 2031 |
| 36–40 | App | KPI, calidad y cesta en la app Streamlit |

## Mensajes clave

- Primero se aterriza en bruto; limpiar en la ingesta destruye la evidencia.
- Cada regla de limpieza es una decisión de negocio que hay que documentar.
- Una *fact table* se define por su grano: una fila por línea de venta o devolución.
- Las fechas anómalas no son anécdotas: si no se filtran, el "hoy" del análisis sería 2031.

## Notas de ejecución

- Los notebooks funcionan con pandas 2.x y 3.x.
- El notebook 5 trabaja con el esquema de la *fact* de referencia (`fact_transacciones.csv`). La *fact* que construye el notebook 4 usa nombres de columna propios y sirve para discutir la integración.
- El notebook 5 filtra la ventana operativa 2024–2025 antes de calcular RFM y *snapshots*.

## Material complementario

- Infraestructura SQL para las capas Raw, Core y Analytics: [escenario 03](../03-sql-raw-core-analytics/README.md).
- Versión agéntica del mismo pipeline: [escenario 10](../10-agentes-foundry/README.md).
- Caso original completo: [preparación de datos en retail omnicanal](../../historia/caso-preparacion-datos.md).

## Con datos vivos (opcional)

Esta demo usa los CSV de `datos/retail_omnicanal/raw_csv`: una fotografía de 2024–2025 con errores intencionados. Si quieres trabajar con datos que cambien, el [escenario 11](../11-web-transaccional/README.md) es una web real donde se venden, devuelven y atienden pedidos sobre Azure SQL y Cosmos DB, y su exportación (`tools/export_csv.py` `--dominio retail`) los devolverá al mismo formato que `datos/`, sin tocar el código de esta demo.

La exportación todavía no está construida (fase 5 del escenario 11). Hasta entonces, usa `datos/` como hasta ahora.
