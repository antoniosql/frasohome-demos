# FraSoHome · datasets adicionales para marketing de precisión

Estos ficheros son **sintéticos pero coherentes** con el caso FraSoHome existente.  
Se han construido para ampliar el caso desde una lógica de preparación de datos hacia una lógica de **customer analytics, marketing de precisión, activación y GenAI**.

## Qué incluyen

Se añaden datasets para cubrir 10 casos:
1. Resolución de identidad y customer 360
2. Segmentación de valor omnicanal y CLV
3. Churn y next best action
4. Propensión de compra por categoría
5. Cross-sell con margen y stock
6. Elasticidad promocional y dependencia del descuento
7. Predicción de devolución
8. Activación local y store marketing
9. GenAI para voz del cliente
10. GenAI para personalización de copy

## Principios de diseño

- Claves alineadas con el caso original: `customer_id`, `order_id`, `ticket_id`, `product_id`, `store_id`, `campaign_id`.
- Ventana temporal principal: 2024-2025.
- Datos en español y listos para trabajar con pandas / notebooks.
- Mezcla de datos estructurados y texto libre para casos de analítica avanzada e IA generativa.
- Se incluye un fichero `identidades_cliente_ground_truth.csv` para evaluación docente del caso de entity resolution.

## Ficheros generados

| Dataset | Filas | Uso principal |
|---|---:|---|
| identidades_cliente.csv | 411 | Entity resolution y customer 360 |
| identidades_cliente_ground_truth.csv | 411 | Evaluación docente del matching |
| campanas_marketing.csv | 26 | Maestro de campañas y resultados agregados |
| contactos_campana.csv | 480 | Contactos CRM con control y outcomes a 30 días |
| eventos_campana.csv | 935 | Aperturas, clics, visitas, compras atribuidas |
| eventos_web_app.csv | 9030 | Navegación digital y señales de intención |
| promociones_calendario.csv | 98 | Calendario promocional |
| cupones_clientes.csv | 367 | Emisión y canje de cupones |
| tickets_atencion_cliente.csv | 560 | Soporte y VOC con texto libre |
| feedback_clientes.csv | 850 | Reviews, NPS y encuestas |
| costes_operativos_transaccion.csv | 1829 | CLV neto, margen y ROI |
| afinidad_tienda_cliente.csv | 100 | Activación local por tienda |
| creatividades_segmento.csv | 78 | GenAI de copy / creatividad |
| guardrails_marca_genai.csv | 12 | Reglas de marca y guardrails |
| mapeo_casos_marketing_precision.csv | 10 | Qué dataset usar en cada caso |
| catalogo_datasets_marketing_precision.csv | 14 | Resumen de granularidad y claves |
| diccionario_columnas_marketing_precision.csv | 258 | Diccionario de columnas |

## Joins recomendados

- `contactos_campana.customer_id` -> `crm.customer_id`
- `eventos_campana.contact_id` -> `contactos_campana.contact_id`
- `eventos_web_app.customer_id` -> `crm.customer_id`
- `cupones_clientes.campaign_id` -> `campanas_marketing.campaign_id`
- `costes_operativos_transaccion.order_id` -> `pedidos.order_id`
- `costes_operativos_transaccion.ticket_id` -> `ventas_pos.ticket_id` (vía agregación a ticket)
- `feedback_clientes.customer_id` -> `crm.customer_id`
- `tickets_atencion_cliente.customer_id` -> `crm.customer_id`
- `afinidad_tienda_cliente.customer_id` -> `crm.customer_id`

## Notas docentes

- `contactos_campana.csv` ya incluye variables de outcome a 30 días (`conversion_30d_flag`, `revenue_30d_eur`) para facilitar ejercicios de uplift y medición.
- `campanas_marketing.csv` combina planificación con métricas observadas agregadas.
- `creatividades_segmento.csv` y `guardrails_marca_genai.csv` permiten montar casos de GenAI con evaluación de performance y restricciones de marca.
- Los textos de `tickets_atencion_cliente.csv` y `feedback_clientes.csv` están pensados para clasificación temática, sentimiento, extracción de objeciones y síntesis con LLM.

## Recomendación de uso

Trabajar estos ficheros **como capa adicional** sobre el caso existente, no como sustitución:
- conservar notebooks 1-4 del caso original como capa de dato,
- utilizar estos datasets a partir del bloque de customer analytics / activación.

