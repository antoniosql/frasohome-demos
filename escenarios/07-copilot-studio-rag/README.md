# 07 · Asistente RAG con Copilot Studio

| Capítulo | Audiencia | Duración | Tecnología |
| --- | --- | --- | --- |
| 5 · Preguntar a la empresa | Negocio, responsables de conocimiento, equipos low-code | 1 día (6 bloques) · 30 min como demo | Microsoft Copilot Studio · Dataverse · Power Fx |

## La historia en este punto

Cada semana llegan al equipo de datos y a operaciones las mismas preguntas: ¿cuál es el plazo de devolución online?, ¿cómo se reembolsa un pago mixto?, ¿qué son las ventas netas?, ¿cuánto vendió Madrid el día 10? Las respuestas están repartidas entre documentos Word, tablas y la memoria de algunas personas. Y hay trampas: conviven dos versiones de la política de devoluciones.

FraSoHome quiere **una única forma de preguntar y obtener respuestas fiables**: un asistente que cite el documento vigente, consulte las métricas en datos estructurados, se abstenga cuando no tenga evidencia y no se deje manipular.

## Qué se demuestra

- Diseño del asistente con un *RAG Canvas*: resultados, usuarios, casos de uso, fuentes, *guardrails* y evaluación.
- Base de conocimiento con citaciones y control de versiones (vigente frente a obsoleto).
- Instrucciones, formato de respuesta, abstención y mitigación de *prompt injection*.
- Datos estructurados en Dataverse y herramientas (*Tools*) para preguntas métricas.
- Arquitectura híbrida: enrutado documental, métrico o mixto.
- Evaluación con *test sets*, diagnóstico con Activity Map y checklist de gobierno.

## Recursos necesarios

### Entorno

| Recurso | Para qué |
| --- | --- |
| Licencia de Copilot Studio | Crear y probar el agente |
| Un entorno de Power Platform con Dataverse | Tablas y *Tools* (LAB 4 y 5) |
| Permisos para subir conocimiento y crear tablas | Todo el taller |

### Datos

**Base de conocimiento** ([índice y reglas de uso](../../datos/rag_copilot_studio/knowledge_base/Indice_Documentos_Conocimiento.md)):

| Documento | Estado | Lab |
| --- | --- | --- |
| [FS-KB-01 Política de devoluciones v1.3](../../datos/rag_copilot_studio/knowledge_base/Documentos_Knowledge_Clasificados/01_Politicas/FS-KB-01_Politica_Devoluciones_v1.3_Vigente.docx) | Vigente | LAB 2 |
| [FS-KB-02 Política de devoluciones v1.2](../../datos/rag_copilot_studio/knowledge_base/Documentos_Knowledge_Clasificados/01_Politicas/FS-KB-02_Politica_Devoluciones_v1.2_Obsoleta.docx) | **Obsoleta** (a propósito) | Final de LAB 2 · se retira en LAB 6 |
| [FS-KB-03 Diccionario de KPI](../../datos/rag_copilot_studio/knowledge_base/Documentos_Knowledge_Clasificados/02_KPI_y_Datos/FS-KB-03_Diccionario_KPI_Reglas_Calculo_v1.0.docx) | Vigente | LAB 2 y 5 |
| [FS-KB-04 Manual de caja y pagos mixtos](../../datos/rag_copilot_studio/knowledge_base/Documentos_Knowledge_Clasificados/03_Operaciones/FS-KB-04_Manual_Tienda_Caja_y_Pagos_Mixtos_v2.1.docx) | Vigente | LAB 2 |
| [FS-KB-05 Conciliación de pagos ecommerce](../../datos/rag_copilot_studio/knowledge_base/Documentos_Knowledge_Clasificados/03_Operaciones/FS-KB-05_Guia_Conciliacion_Pagos_Ecommerce_v1.4.docx) | Vigente | LAB 2 |
| [FS-KB-06 Taxonomía de catálogo y SKU](../../datos/rag_copilot_studio/knowledge_base/Documentos_Knowledge_Clasificados/04_Catalogo/FS-KB-06_Taxonomia_Catalogo_y_Reglas_SKU_v1.2.docx) | Vigente | LAB 2 |
| [FS-KB-07 Guía de fidelización CRM](../../datos/rag_copilot_studio/knowledge_base/Documentos_Knowledge_Clasificados/05_CRM/FS-KB-07_Guia_Fidelizacion_CRM_v1.1.docx) | Vigente | LAB 2 |
| [FS-KB-08 Política de datos y permisos del asistente](../../datos/rag_copilot_studio/knowledge_base/Documentos_Knowledge_Clasificados/06_Gobierno_y_Seguridad/FS-KB-08_Politica_Datos_y_Permisos_Asistente_v1.0.docx) | Vigente | LAB 2 (clave en LAB 3, 5 y 6) |
| [FS-KB-09 FAQ de operaciones y atención](../../datos/rag_copilot_studio/knowledge_base/Documentos_Knowledge_Clasificados/03_Operaciones/FS-KB-09_FAQ_Operaciones_y_Atencion_v1.0.docx) | Vigente | LAB 2 |
| [FS-KB-10 Prueba de *prompt injection*](../../datos/rag_copilot_studio/knowledge_base/Documentos_Knowledge_Clasificados/07_Test_Security/FS-KB-10_Documento_Prueba_Prompt_Injection_NO_PROD.docx) | **NO_PROD** | Solo durante LAB 3 · se retira al terminarlo |

**Datos estructurados para Dataverse** (rango 2026-01-01 a 2026-02-20):

| Fichero | Tabla |
| --- | --- |
| [`FS_Tiendas.csv`](../../datos/rag_copilot_studio/structured_csv/FS_Tiendas.csv) | Tiendas (`MAD01`, `BCN01`, `VLC01`) |
| [`FS_Productos.csv`](../../datos/rag_copilot_studio/structured_csv/FS_Productos.csv) | Productos (`FSH-*`) |
| [`FS_Clientes.csv`](../../datos/rag_copilot_studio/structured_csv/FS_Clientes.csv) | Clientes |
| [`FS_VentasResumenDiario.csv`](../../datos/rag_copilot_studio/structured_csv/FS_VentasResumenDiario.csv) | Ventas netas por día, tienda y canal |
| [`FS_DevolucionesFact.csv`](../../datos/rag_copilot_studio/structured_csv/FS_DevolucionesFact.csv) | Devoluciones con motivo y aprobación |
| [`FS_StockDiario.csv`](../../datos/rag_copilot_studio/structured_csv/FS_StockDiario.csv) | Stock diario |
| [`FS_Alertas_Stockout.csv`](../../datos/rag_copilot_studio/structured_csv/FS_Alertas_Stockout.csv) | Alertas de rotura de stock |

**Evaluación**: [`FS_TestSet_Documental.csv`](../../datos/rag_copilot_studio/test_sets/FS_TestSet_Documental.csv) y [`FS_TestSet_Metrico_Mixto.csv`](../../datos/rag_copilot_studio/test_sets/FS_TestSet_Metrico_Mixto.csv).

Los códigos de tienda y producto de este dominio se traducen a los de retail con [`store_aliases.csv`](../../datos/relaciones/store_aliases.csv) y [`product_aliases_rag_to_retail.csv`](../../datos/relaciones/product_aliases_rag_to_retail.csv).

### Material de la demo

| Fichero | Contenido |
| --- | --- |
| [Caso completo](caso.md) | Problema de negocio, tipos de pregunta e implicaciones RAG |
| [Índice de laboratorios](laboratorios/indice.md) | Qué se construye y en qué orden |
| [LAB 2 · Base de conocimiento](laboratorios/LAB2_Base_de_conocimiento_RAG_en_Copilot_Studio.md) | Documentos vigentes, citaciones y conflicto de versiones |
| [LAB 3 · Prompting y seguridad](laboratorios/LAB3_Prompting_Citaciones_y_Control_de_Fallback.md) | Instrucciones, formato, abstención y *prompt injection* |
| [LAB 4 · Dataverse](laboratorios/LAB4_Dataverse_y_Datos_Estructurados.md) | Tablas desde CSV |
| [LAB 5 · Arquitectura híbrida](laboratorios/LAB5_Arquitectura_Hibrida_Tools_y_RAG.md) | *Tools* de Dataverse + RAG |
| [LAB 6 · Evaluación y gobierno](laboratorios/LAB6_Evaluacion_Seguridad_y_Gobierno.md) | *Test sets*, diagnóstico y checklist |
| [Plantilla RAG Canvas en blanco](plantillas/RAG_Canvas_FraSoHome_Plantilla_Blanco.md) · [v2](plantillas/RAG_Canvas_FraSoHome_v2.md) · [versión objetivo](plantillas/RAG_Canvas_FraSoHome_Version_Target.md) | LAB 1 (diseño) |
| [Canvas solución del instructor](canvas-solucion-instructor.md) | Solución de referencia del LAB 1 |
| [Guía del instructor](guia-instructor.md) | Preparación, temporización, respuestas esperadas y errores frecuentes |
| [Answer key de los test sets](evaluacion/FraSoHome_AnswerKey_TestSets.xlsx) · [Rúbrica de calificación](evaluacion/FraSoHome_Rubrica_Calificacion.xlsx) | Corrección |
| [README del pack original](pack-original.md) | Referencia histórica del paquete para alumnos |

## Cómo ejecutarla

1. **Preparación del instructor**: confirma licencias y entorno con Dataverse; revisa la [guía del instructor](guia-instructor.md).
2. **LAB 1 (opcional)**: completa el [RAG Canvas](plantillas/RAG_Canvas_FraSoHome_Plantilla_Blanco.md).
3. **LAB 2**: crea el agente, sube FS-KB-01 y 03 a 09, prueba citaciones. Al final añade FS-KB-02 y observa el conflicto.
4. **LAB 3**: ajusta instrucciones y formato; sube temporalmente FS-KB-10 y prueba la inyección; retíralo.
5. **LAB 4**: crea las siete tablas en Dataverse desde los CSV.
6. **LAB 5**: añade las *Tools* de Dataverse y el *topic* de consultas métricas.
7. **LAB 6**: importa los dos *test sets*, revisa resultados y cierra la lista de acciones.

## Guion sugerido (1 día)

| Bloque | Contenido | Duración |
| --- | --- | --- |
| 1 | Introducción + LAB 1 (Canvas) | 45 min |
| 2 | LAB 2 (base RAG + versionado) | 60 min |
| 3 | LAB 3 (prompting + seguridad) | 60 min |
| 4 | LAB 4 (Dataverse) | 60 min |
| 5 | LAB 5 (híbrido) | 75 min |
| 6 | LAB 6 (evaluación) + cierre | 60 min |

**Versión demo (30 min)**: pregunta documental con cita → pregunta con la política obsoleta cargada → intento de *prompt injection* → pregunta métrica con *Tool* → resultados de evaluación.

## Mensajes clave

- Un RAG es tan bueno como el gobierno de su conocimiento: versiones, vigencia y permisos.
- Las preguntas métricas no se responden leyendo documentos: necesitan datos y un cálculo trazable.
- Citar no es decoración: es el requisito operativo que permite auditar una respuesta.
- Se evalúa la recuperación y la respuesta por separado, con un *test set* antes de publicar.

## Con datos vivos (opcional)

Esta demo usa los ficheros del escenario RAG: una fotografía de 2024–2025 con errores intencionados. Si quieres trabajar con datos que cambien, el [escenario 11](../11-web-transaccional/README.md) es una web real donde se venden, devuelven y atienden pedidos sobre Azure SQL y Cosmos DB, y su exportación (`tools/export_csv.py` `--dominio rag`) los devolverá al mismo formato que `datos/`, sin tocar el código de esta demo.

La exportación todavía no está construida (fase 5 del escenario 11). Hasta entonces, usa `datos/` como hasta ahora.
