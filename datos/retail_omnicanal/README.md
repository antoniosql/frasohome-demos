# Retail omnicanal

El negocio principal de FraSoHome: clientes, catálogo, tiendas, pedidos online, tickets de tienda, pagos, devoluciones, stock diario y una *fact table* integrada. Los once ficheros contienen errores de calidad intencionados (duplicados, IDs sin normalizar, fechas e importes en varios formatos, claves huérfanas, fechas futuras).

**Escenarios que lo usan**: [01](../../escenarios/01-empresa-con-silos/README.md) · [02](../../escenarios/02-fabric-preparacion-datos/README.md) · [03](../../escenarios/03-sql-raw-core-analytics/README.md) · [04](../../escenarios/04-analitica-ventas-ml/README.md) · [05](../../escenarios/05-marketing-precision/README.md) · [08](../../escenarios/08-fabric-iq-ontologia/README.md) · [09](../../escenarios/09-genai-interpretabilidad/README.md) · [10](../../escenarios/10-agentes-foundry/README.md)

## Ficheros

| Fichero | Descripción | Grano | Filas | Columnas |
| --- | --- | --- | ---: | ---: |
| [`crm.csv`](raw_csv/crm.csv) | Clientes del programa de fidelización | Cliente | 103 | 20 |
| [`devoluciones_online.csv`](raw_csv/devoluciones_online.csv) | Devoluciones de pedidos online | Devolución | 224 | 12 |
| [`devoluciones_tienda.csv`](raw_csv/devoluciones_tienda.csv) | Devoluciones registradas en tienda (de tienda u online) | Devolución | 211 | 16 |
| [`fact_transacciones.csv`](raw_csv/fact_transacciones.csv) | Fact integrada de ventas y devoluciones de todos los canales, con flags de normalización | Línea de venta o devolución | 4973 | 59 |
| [`lineas_pedido.csv`](raw_csv/lineas_pedido.csv) | Líneas de pedidos online | Línea de pedido | 1949 | 12 |
| [`pagos_tienda.csv`](raw_csv/pagos_tienda.csv) | Pagos por ticket, incluidos pagos mixtos | Pago | 1646 | 12 |
| [`pedidos.csv`](raw_csv/pedidos.csv) | Cabeceras de pedidos online | Pedido | 656 | 16 |
| [`productos.csv`](raw_csv/productos.csv) | Catálogo con categoría, marca, proveedor, precio y coste | Producto (SKU) | 101 | 18 |
| [`stock_diario.csv`](raw_csv/stock_diario.csv) | Stock al cierre por tienda y producto | Tienda × producto × día | 1940 | 9 |
| [`tiendas.csv`](raw_csv/tiendas.csv) | Tiendas físicas, ecommerce/almacén y apertura planificada | Tienda o ubicación | 8 | 19 |
| [`ventas_pos.csv`](raw_csv/ventas_pos.csv) | Líneas de ticket en tienda | Línea de ticket | 2521 | 19 |

## Relaciones principales

- `crm.customer_id` ← `pedidos.customer_id`, `ventas_pos.customer_id` (opcional en tienda)
- `pedidos.order_id` ← `lineas_pedido.order_id`, `devoluciones_online.order_id`
- `ventas_pos.ticket_id` ← `pagos_tienda.ticket_id`, `devoluciones_tienda.ticket_id`
- `productos.product_id` ← líneas, tickets, devoluciones y stock
- `tiendas.store_id` ← `ventas_pos`, `pagos_tienda`, `devoluciones_tienda`, `stock_diario`

El [perfil de datos](../../escenarios/02-fabric-preparacion-datos/perfil-datos.md) detalla filas, claves y problemas por fichero.
