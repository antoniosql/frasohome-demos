# Datos

Todos los datos de FraSoHome en un solo sitio. Son **sintéticos** y están **sucios a propósito**: no los limpies aquí. Las demos leen estos ficheros tal cual y aplican la limpieza en su propio código.

| Dominio | Carpeta | Contenido | Ficheros |
| --- | --- | --- | ---: |
| Retail omnicanal | [retail_omnicanal](retail_omnicanal/README.md) | CRM, catálogo, tiendas, ecommerce, TPV, pagos, devoluciones, stock y *fact* integrada | 11 CSV |
| Marketing de precisión | [marketing_precision](marketing_precision/README.md) | Identidad, campañas, contactos, cupones, eventos web/app, voz del cliente, costes, afinidad, creatividades y *guardrails* | 17 CSV |
| People Analytics | [people_analytics](people_analytics/README.md) | Fuentes brutas de RR. HH. y datasets preparados para Power BI y ChatGPT | 19 CSV |
| Conocimiento para RAG | [rag_copilot_studio](rag_copilot_studio/README.md) | Documentos internos, CSV para Dataverse y juegos de evaluación | 10 DOCX · 9 CSV |
| Relaciones | [relaciones](relaciones/README.md) | Tablas puente entre dominios y checks de coherencia | 6 CSV |

## Catálogo completo

[`catalogo-datos.csv`](catalogo-datos.csv) (también en [Excel](catalogo-datos.xlsx)) lista cada fichero con su descripción, grano, número de filas y columnas, y los escenarios que lo usan.

## Convenciones

- **Codificación**: UTF-8 (algunos ficheros con BOM).
- **Separador**: coma. Los importes pueden traer coma decimal dentro de comillas.
- **Periodo principal**: 2024–2025 en retail y marketing; 2024–2026 en personas; 2026-01-01 a 2026-02-20 en los CSV de Dataverse.
- **Claves comunes**: `customer_id`, `product_id`, `store_id`, `order_id`, `ticket_id`, `campaign_id`, `employee_id`.

## Coherencia entre dominios

La [auditoría de coherencia](coherencia.md) explica qué enlaza al 100 % (por ejemplo, marketing con clientes retail) y qué huecos se conservan a propósito para las demos de calidad, atribución e identidad. El [universo de datos](../historia/universo-de-datos.md) lo muestra en un diagrama.

## Cargar los datos en una base de datos

El [escenario 03](../escenarios/03-sql-raw-core-analytics/README.md) contiene los scripts para cargarlo todo en Azure SQL o en Fabric SQL Database, con un esquema por dominio (`raw_retail`, `raw_marketing`, `raw_people`, `raw_rag`, `xref`).
