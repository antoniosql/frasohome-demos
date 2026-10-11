# Conocimiento para RAG

Fuentes del asistente de FraSoHome: documentos internos para la base de conocimiento, CSV resumidos para Dataverse y juegos de evaluación. Este dominio usa sus propios códigos (`MAD01`, `FSH-*`); se traducen a los de retail con [`store_aliases.csv`](../relaciones/store_aliases.csv) y [`product_aliases_rag_to_retail.csv`](../relaciones/product_aliases_rag_to_retail.csv).

**Escenarios que lo usan**: [01](../../escenarios/01-empresa-con-silos/README.md) · [03](../../escenarios/03-sql-raw-core-analytics/README.md) · [07](../../escenarios/07-copilot-studio-rag/README.md) · [09](../../escenarios/09-genai-interpretabilidad/README.md)

## Base de conocimiento

El [índice de documentos](knowledge_base/Indice_Documentos_Conocimiento.md) explica el estado de cada documento y qué subir en cada laboratorio.

| Fichero | Descripción | Grano | Filas | Columnas |
| --- | --- | --- | ---: | ---: |
| [`FS-KB-01_Politica_Devoluciones_v1.3_Vigente.docx`](knowledge_base/Documentos_Knowledge_Clasificados/01_Politicas/FS-KB-01_Politica_Devoluciones_v1.3_Vigente.docx) | Politica Devoluciones v1.3 (vigente) | Documento |  |  |
| [`FS-KB-02_Politica_Devoluciones_v1.2_Obsoleta.docx`](knowledge_base/Documentos_Knowledge_Clasificados/01_Politicas/FS-KB-02_Politica_Devoluciones_v1.2_Obsoleta.docx) | Politica Devoluciones v1.2 (obsoleto, solo formación) | Documento |  |  |
| [`FS-KB-03_Diccionario_KPI_Reglas_Calculo_v1.0.docx`](knowledge_base/Documentos_Knowledge_Clasificados/02_KPI_y_Datos/FS-KB-03_Diccionario_KPI_Reglas_Calculo_v1.0.docx) | Diccionario KPI Reglas Calculo v1.0 (vigente) | Documento |  |  |
| [`FS-KB-04_Manual_Tienda_Caja_y_Pagos_Mixtos_v2.1.docx`](knowledge_base/Documentos_Knowledge_Clasificados/03_Operaciones/FS-KB-04_Manual_Tienda_Caja_y_Pagos_Mixtos_v2.1.docx) | Manual Tienda Caja y Pagos Mixtos v2.1 (vigente) | Documento |  |  |
| [`FS-KB-05_Guia_Conciliacion_Pagos_Ecommerce_v1.4.docx`](knowledge_base/Documentos_Knowledge_Clasificados/03_Operaciones/FS-KB-05_Guia_Conciliacion_Pagos_Ecommerce_v1.4.docx) | Guia Conciliacion Pagos Ecommerce v1.4 (vigente) | Documento |  |  |
| [`FS-KB-09_FAQ_Operaciones_y_Atencion_v1.0.docx`](knowledge_base/Documentos_Knowledge_Clasificados/03_Operaciones/FS-KB-09_FAQ_Operaciones_y_Atencion_v1.0.docx) | FAQ Operaciones y Atencion v1.0 (vigente) | Documento |  |  |
| [`FS-KB-06_Taxonomia_Catalogo_y_Reglas_SKU_v1.2.docx`](knowledge_base/Documentos_Knowledge_Clasificados/04_Catalogo/FS-KB-06_Taxonomia_Catalogo_y_Reglas_SKU_v1.2.docx) | Taxonomia Catalogo y Reglas SKU v1.2 (vigente) | Documento |  |  |
| [`FS-KB-07_Guia_Fidelizacion_CRM_v1.1.docx`](knowledge_base/Documentos_Knowledge_Clasificados/05_CRM/FS-KB-07_Guia_Fidelizacion_CRM_v1.1.docx) | Guia Fidelizacion CRM v1.1 (vigente) | Documento |  |  |
| [`FS-KB-08_Politica_Datos_y_Permisos_Asistente_v1.0.docx`](knowledge_base/Documentos_Knowledge_Clasificados/06_Gobierno_y_Seguridad/FS-KB-08_Politica_Datos_y_Permisos_Asistente_v1.0.docx) | Politica Datos y Permisos Asistente v1.0 (vigente) | Documento |  |  |
| [`FS-KB-10_Documento_Prueba_Prompt_Injection_NO_PROD.docx`](knowledge_base/Documentos_Knowledge_Clasificados/07_Test_Security/FS-KB-10_Documento_Prueba_Prompt_Injection_NO_PROD.docx) | Documento Prueba Prompt Injection (NO_PROD, pruebas de seguridad) | Documento |  |  |

`FS-KB-02` está **obsoleto** a propósito (control de versiones) y `FS-KB-10` contiene *prompt injection* simulado (**NO_PROD**). Ninguno de los dos debe llegar a producción.

## Datos estructurados (Dataverse)

| Fichero | Descripción | Grano | Filas | Columnas |
| --- | --- | --- | ---: | ---: |
| [`FS_Alertas_Stockout.csv`](structured_csv/FS_Alertas_Stockout.csv) | Alertas de rotura de stock | Alerta | 15 | 6 |
| [`FS_Clientes.csv`](structured_csv/FS_Clientes.csv) | Clientes resumidos | Cliente | 60 | 5 |
| [`FS_DevolucionesFact.csv`](structured_csv/FS_DevolucionesFact.csv) | Devoluciones con motivo y aprobación | Devolución | 248 | 12 |
| [`FS_Productos.csv`](structured_csv/FS_Productos.csv) | Productos del dominio RAG (FSH-*) | Producto | 32 | 11 |
| [`FS_StockDiario.csv`](structured_csv/FS_StockDiario.csv) | Stock diario | Día × tienda × producto | 2295 | 7 |
| [`FS_Tiendas.csv`](structured_csv/FS_Tiendas.csv) | Tiendas del dominio RAG (MAD01, BCN01, VLC01) | Tienda | 3 | 4 |
| [`FS_VentasResumenDiario.csv`](structured_csv/FS_VentasResumenDiario.csv) | Ventas netas diarias por tienda y canal (2026-01-01 a 2026-02-20) | Día × tienda × canal | 204 | 9 |

## Evaluación

| Fichero | Descripción | Grano | Filas | Columnas |
| --- | --- | --- | ---: | ---: |
| [`FS_TestSet_Documental.csv`](test_sets/FS_TestSet_Documental.csv) | Test set de preguntas documentales | Pregunta | 10 | 2 |
| [`FS_TestSet_Metrico_Mixto.csv`](test_sets/FS_TestSet_Metrico_Mixto.csv) | Test set de preguntas métricas y mixtas | Pregunta | 6 | 2 |
