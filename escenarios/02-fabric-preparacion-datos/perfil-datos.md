# Perfil de Datos FraSoHome

Perfilado ejecutado sobre `datos/retail_omnicanal/raw_csv/*.csv` el 2026-05-30.

| Fuente | Filas | Grano | Clave natural observada | Observaciones |
| --- | ---: | --- | --- | --- |
| `crm.csv` | 103 | Cliente CRM | `customer_id` | 101 clientes distintos; hay duplicados. Consentimiento marketing con valores heterogeneos (`no`, `1`, `YES`). Fechas en varios formatos. |
| `productos.csv` | 101 | SKU/producto | `product_id` | 100 productos distintos; catalogo con un duplicado. Atributos de proveedor/material/color parcialmente nulos. |
| `tiendas.csv` | 8 | Tienda/ubicacion | `store_id` | Incluye tiendas fisicas y ubicacion online/almacen. Fechas de apertura en varios formatos. |
| `pedidos.csv` | 656 | Cabecera pedido online | `order_id` | 652 pedidos distintos; algunos clientes no existen en CRM o vienen nulos. Importes con simbolos y formatos mixtos. |
| `lineas_pedido.csv` | 1.949 | Linea pedido online | `order_line_id` | 1.929 lineas distintas; productos no siempre alineados con maestro. Importes con coma decimal en algunos casos. |
| `ventas_pos.csv` | 2.521 | Linea ticket tienda | `ticket_line_id` | 2.481 lineas distintas; clientes opcionales, IDs con casing inconsistente y observaciones de caja. |
| `pagos_tienda.csv` | 1.646 | Pago de ticket | `payment_id` | 1.631 pagos distintos; soporta pagos mixtos por ticket. Metodos de pago muy heterogeneos (`CC`, `Visa/Mastercard`, `Vale`, etc.). |
| `devoluciones_online.csv` | 224 | Devolucion online | `return_id` | 219 devoluciones distintas; referencias a pedido/linea no siempre completas. |
| `devoluciones_tienda.csv` | 211 | Devolucion tienda | `return_id` | 206 devoluciones distintas; puede referenciar ticket POS u order online. Incluye cantidades 0 e importes con `€`. |
| `stock_diario.csv` | 1.940 | Snapshot tienda-producto-fecha | `fecha`, `store_id`, `product_id` | Productos y tiendas con casing/IDs no normalizados; comentarios indican duplicados de carga. |
| `fact_transacciones.csv` | 4.973 | Movimiento comercial integrado | `fact_id` | 4.931 IDs distintos. Une ventas y devoluciones; ya contiene flags de parseo y normalizacion. |

## Problemas de Calidad Relevantes

- **Duplicados de clave:** aparecen en CRM, productos, pedidos, lineas, pagos, devoluciones y fact integrada.
- **Normalizacion de IDs:** `customer_id`, `product_id` y `store_id` requieren `TRIM` y `UPPER`; hay ejemplos como `c0001` y `p1005`.
- **Fechas mixtas:** ISO, `dd/MM/yy`, `dd/MM/yyyy`, texto en espanol y timestamps parciales.
- **Importes mixtos:** valores con `€`, coma decimal, punto decimal y texto numerico.
- **Referencialidad incompleta:** algunos clientes/productos de transacciones no existen en maestros.
- **Canales y metodos:** canales y pagos necesitan diccionarios de equivalencia para consolidar POS, online, marketplace, tarjeta, efectivo, vales y transferencia.
- **Inventario:** hay snapshots duplicados y ubicaciones no siempre presentes en maestro de tiendas.

## Decisiones de Modelado

- Mantener `FraSoHome_Raw` como landing tolerante y auditable.
- Usar `FraSoHome_Core` como sistema limpio con claves naturales estandarizadas y FKs.
- Publicar `FraSoHome_Analytics` con dimensiones historizables para cliente/producto y hechos preparados para KPIs:
  ventas netas, devoluciones, margen bruto, stock disponible, stock bajo minimo, metodos de pago y rendimiento por canal.
