# Marketing de precisión

Datos operacionales de marketing para pasar de la preparación de datos a decisiones de *customer analytics*, activación y GenAI. Enlazan con retail por `customer_id`, `order_id`, `ticket_id`, `product_id` y `store_id`. Se conservan algunos IDs defectuosos a propósito para las demos de atribución y resolución de identidad.

**Escenarios que lo usan**: [03](../../escenarios/03-sql-raw-core-analytics/README.md) · [04](../../escenarios/04-analitica-ventas-ml/README.md) · [05](../../escenarios/05-marketing-precision/README.md) · [08](../../escenarios/08-fabric-iq-ontologia/README.md)

## Ficheros

| Fichero | Descripción | Grano | Filas | Columnas |
| --- | --- | --- | ---: | ---: |
| [`afinidad_tienda_cliente.csv`](raw_csv/afinidad_tienda_cliente.csv) | Afinidad y cercanía a tienda por cliente | Cliente | 100 | 13 |
| [`campanas_marketing.csv`](raw_csv/campanas_marketing.csv) | Maestro de campañas con planificación y resultados agregados | Campaña | 26 | 40 |
| [`catalogo_datasets_marketing_precision.csv`](raw_csv/catalogo_datasets_marketing_precision.csv) | Catálogo de datasets de marketing | Dataset | 14 | 6 |
| [`contactos_campana.csv`](raw_csv/contactos_campana.csv) | Contactos CRM por cliente-campaña con outcome 30 días | Contacto | 480 | 23 |
| [`costes_operativos_transaccion.csv`](raw_csv/costes_operativos_transaccion.csv) | Costes operativos y margen neto por transacción | Transacción | 1829 | 21 |
| [`creatividades_segmento.csv`](raw_csv/creatividades_segmento.csv) | Variantes creativas y performance estimada | Variante creativa | 78 | 19 |
| [`cupones_clientes.csv`](raw_csv/cupones_clientes.csv) | Cupones emitidos y canjeados a nivel cliente | Cupón individual | 367 | 21 |
| [`diccionario_columnas_marketing_precision.csv`](raw_csv/diccionario_columnas_marketing_precision.csv) | Diccionario de columnas de marketing | Columna | 258 | 4 |
| [`eventos_campana.csv`](raw_csv/eventos_campana.csv) | Eventos post-contacto y atribución | Evento | 935 | 13 |
| [`eventos_web_app.csv`](raw_csv/eventos_web_app.csv) | Navegación web/app y comportamiento pre-compra | Evento digital | 9030 | 22 |
| [`feedback_clientes.csv`](raw_csv/feedback_clientes.csv) | Reviews, NPS y encuestas post-soporte/post-devolución | Feedback | 850 | 15 |
| [`guardrails_marca_genai.csv`](raw_csv/guardrails_marca_genai.csv) | Reglas de marca y seguridad para GenAI | Regla | 12 | 5 |
| [`identidades_cliente.csv`](raw_csv/identidades_cliente.csv) | Señales de identidad cross-canal para entity resolution | Señal individual | 411 | 17 |
| [`identidades_cliente_ground_truth.csv`](raw_csv/identidades_cliente_ground_truth.csv) | Ground truth docente para evaluar matching | Señal individual | 411 | 2 |
| [`mapeo_casos_marketing_precision.csv`](raw_csv/mapeo_casos_marketing_precision.csv) | Mapeo de los diez casos de uso con sus datasets | Caso | 10 | 5 |
| [`promociones_calendario.csv`](raw_csv/promociones_calendario.csv) | Calendario promocional por categoría, tienda y campaña | Promoción | 98 | 16 |
| [`tickets_atencion_cliente.csv`](raw_csv/tickets_atencion_cliente.csv) | Interacciones de soporte con texto libre | Ticket soporte | 560 | 20 |
| [`validacion_datasets_marketing_precision.csv`](raw_csv/validacion_datasets_marketing_precision.csv) | Validaciones de integridad de los datasets | Check | 16 | 5 |

## Joins recomendados

- `contactos_campana.customer_id` → `crm.customer_id`
- `eventos_campana.contact_id` → `contactos_campana.contact_id`
- `eventos_web_app.customer_id` → `crm.customer_id`
- `cupones_clientes.campaign_id` → `campanas_marketing.campaign_id`
- `costes_operativos_transaccion.order_id` → `pedidos.order_id`
- `costes_operativos_transaccion.ticket_id` → `ventas_pos.ticket_id` (agregando a ticket)
- `feedback_clientes.customer_id`, `tickets_atencion_cliente.customer_id`, `afinidad_tienda_cliente.customer_id` → `crm.customer_id`

Más detalle en la [nota original del paquete](raw_csv/README.md) y en [`marketing_precision_operational_links.csv`](../relaciones/marketing_precision_operational_links.csv).
