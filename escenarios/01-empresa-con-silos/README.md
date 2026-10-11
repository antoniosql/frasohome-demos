# 01 · La empresa con silos

| Capítulo | Audiencia | Duración | Tecnología |
| --- | --- | --- | --- |
| 1 · Una empresa con datos pero sin visión única | MBA, comité de dirección, clase introductoria | 20–45 min | Ninguna: presentación y ficheros CSV |

## La historia en este punto

Lunes, comité de dirección. Marketing presenta la campaña de primavera como un éxito. Finanzas no ve el impacto en margen. Operaciones explica que las devoluciones de la web se recogen en tienda y "no salen en ningún sitio". RR. HH. avisa de que en logística se va la gente. Cada área trae su propia cifra y todas tienen razón con sus datos.

La directora general hace una pregunta sencilla: **¿cuánto vendimos el mes pasado, de verdad, descontando devoluciones y por canal?** Nadie puede contestar sin dos semanas de Excel.

## Qué se demuestra

- Por qué ventas, marketing, operaciones y RR. HH. no deciden bien si cada uno usa su fuente.
- Que los problemas de calidad son problemas de negocio: un cliente duplicado es un cliente mal segmentado; una devolución huérfana es margen que no se ve.
- Que la IA generativa no arregla nada de esto si se pone encima: primero hay que gobernar los datos y el conocimiento.

## Recursos necesarios

### Entorno

| Recurso | Para qué |
| --- | --- |
| Un visor de CSV o Excel | Abrir dos o tres ficheros en directo |
| Proyector | La presentación y los diagramas |

### Datos

| Fichero | Qué enseñar |
| --- | --- |
| [`tiendas.csv`](../../datos/retail_omnicanal/raw_csv/tiendas.csv) | `S003` duplicada, código postal vacío en Bilbao, Málaga con latitud 91 y apertura en 2027 |
| [`crm.csv`](../../datos/retail_omnicanal/raw_csv/crm.csv) | Clientes duplicados, niveles `Oro` y `Gold`, consentimientos `no`, `1`, `YES` |
| [`ventas_pos.csv`](../../datos/retail_omnicanal/raw_csv/ventas_pos.csv) | Tickets sin cliente, `store_id` mal escrito, fechas en varios formatos |
| [`pagos_tienda.csv`](../../datos/retail_omnicanal/raw_csv/pagos_tienda.csv) | `CC`, `Visa/Mastercard`, `Vale`: el mismo método con varios nombres |
| [`FS-KB-01` vigente](../../datos/rag_copilot_studio/knowledge_base/Documentos_Knowledge_Clasificados/01_Politicas/FS-KB-01_Politica_Devoluciones_v1.3_Vigente.docx) y [`FS-KB-02` obsoleta](../../datos/rag_copilot_studio/knowledge_base/Documentos_Knowledge_Clasificados/01_Politicas/FS-KB-02_Politica_Devoluciones_v1.2_Obsoleta.docx) | Dos políticas de devoluciones que dicen cosas distintas |

### Material

| Fichero | Uso |
| --- | --- |
| [La historia](../../historia/README.md) | Narrativa de los siete capítulos |
| [La empresa en cifras](../../historia/empresa.md) | Ficha de FraSoHome |
| [Los problemas de datos](../../historia/problemas-de-datos.md) | Silos y errores intencionados |
| [Universo de datos](../../historia/universo-de-datos.md) | Diagramas de dominios y arquitectura |
| [Presentación Fabric](../../presentaciones/fabric-intro-deck.md) · [Presentación caso People Analytics](../../presentaciones/caso-people-analytics.md) | Guiones de diapositivas reutilizables |

## Cómo ejecutarla

1. Presenta FraSoHome con la [ficha de empresa](../../historia/empresa.md): cinco tiendas, ecommerce, unos 100 productos, programa de fidelización, unas 670 personas.
2. Plantea la pregunta del comité: *¿cuánto vendimos de verdad el mes pasado?*
3. Abre `tiendas.csv` y `crm.csv`. Pide a la audiencia que encuentre errores. Siempre los encuentran en menos de un minuto.
4. Enseña la tabla de silos de [problemas de datos](../../historia/problemas-de-datos.md): qué sabe y qué no sabe cada sistema.
5. Abre las dos políticas de devoluciones. Pregunta: *si un asistente de IA lee las dos, ¿cuál cita?*
6. Cierra con el [diagrama de arquitectura](../../historia/universo-de-datos.md#del-origen-al-consumo) y presenta los capítulos siguientes.

## Guion sugerido (30 min)

| Minuto | Bloque | Mensaje |
| --- | --- | --- |
| 0–5 | La empresa | Una cadena normal que ha crecido deprisa |
| 5–12 | El comité | Cuatro áreas, cuatro cifras, ninguna mentira |
| 12–20 | Los datos | Los errores están a la vista de cualquiera |
| 20–25 | El conocimiento | También los documentos tienen versiones y silos |
| 25–30 | El camino | Ordenar, modelar, explicar y solo entonces automatizar |

## Mensajes clave

- La calidad del dato es una decisión de negocio, no una tarea técnica.
- Una vista única del negocio exige acordar definiciones antes que tecnología.
- La IA generativa amplifica lo que ya hay: datos sucios y documentos obsoletos producen respuestas seguras e incorrectas.

## Siguiente paso

Según la audiencia: [02 · Fabric](../02-fabric-preparacion-datos/README.md) para equipos técnicos, [06 · People Analytics](../06-power-bi-people-analytics/README.md) para RR. HH., o [07 · Copilot Studio](../07-copilot-studio-rag/README.md) para negocio.
