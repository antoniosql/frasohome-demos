# Referencia del esquema SQL

Todas las tablas de la base `frasohome-oltp`, con sus columnas, tipos y claves. Está extraída de los DDL de [`sql/`](sql/01_core.sql) (`01_core`, `02_hr_mkt_fin_ref_xref`, `04_app` y `05_rag_meta_lab`).

- **Filas** son las de la carga inicial (24 de octubre de 2026) y cambian con el uso de la web. Las tablas del esquema `app` empiezan vacías.
- **Clave**: `PK` clave primaria, `FK` clave foránea (la tabla a la que apunta, entre paréntesis). `FK` solo aparece donde el DDL la declara; otras relaciones son lógicas y se explican en los [diagramas](../../diagramas/README.md#modelo-de-datos-sql).
- **Nulo**: `sí` si la columna admite `NULL`.
- Las fechas son `datetime2` en UTC. Los importes están en euros con dos decimales. Los identificadores siguen los formatos de [Datos en vivo](datos-en-vivo.md#identificadores).

## Esquemas

| Esquema | Contenido | Tablas |
| --- | --- | --- |
| [`crm`](#esquema-crm) | Clientes y fidelización | 1 |
| [`catalog`](#esquema-catalog) | Catálogo de productos | 1 |
| [`store`](#esquema-store) | Tiendas y cajas | 2 |
| [`sales`](#esquema-sales) | Ventas online y en tienda | 5 |
| [`returns`](#esquema-returns) | Devoluciones | 2 |
| [`inventory`](#esquema-inventory) | Stock vivo, foto diaria y movimientos | 3 |
| [`mkt`](#esquema-mkt) | Campañas, cupones, promociones y afinidad | 5 |
| [`fin`](#esquema-fin) | Costes por transacción | 1 |
| [`hr`](#esquema-hr) | Personas: plantilla, tiempo, formación, evaluación y salario | 9 |
| [`ref`](#esquema-ref) | Referencias | 4 |
| [`xref`](#esquema-xref) | Tablas puente entre sistemas origen y modelo canónico | 4 |
| [`rag`](#esquema-rag) | Tablas del escenario RAG | 7 |
| [`meta`](#esquema-meta) | Catálogo de datos y diccionarios | 2 |
| [`lab`](#esquema-lab) | Laboratorio docente | 3 |
| [`quality`](#esquema-quality) | Calidad de la carga | 1 |
| [`app`](#esquema-app) | Aplicación: usuarios, sesiones, outbox, auditoría | 9 |

## Esquema crm

Clientes y fidelización.

### `crm.customer`

Cliente del CRM: contacto, fidelización, consentimiento y estado. 100 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `customer_id` | `nvarchar(50)` | no | PK |
| `first_name` | `nvarchar(100)` | sí |  |
| `last_name` | `nvarchar(150)` | sí |  |
| `email` | `nvarchar(255)` | sí |  |
| `email_is_valid` | `bit` | sí |  |
| `phone` | `nvarchar(50)` | sí |  |
| `loyalty_joined_at` | `date` | sí |  |
| `loyalty_tier` | `nvarchar(50)` | sí |  |
| `loyalty_points` | `int` | sí |  |
| `birth_date` | `date` | sí |  |
| `gender` | `nvarchar(30)` | sí |  |
| `city` | `nvarchar(100)` | sí |  |
| `province` | `nvarchar(100)` | sí |  |
| `postal_code` | `nvarchar(20)` | sí |  |
| `country_code` | `char(2)` | sí |  |
| `marketing_consent` | `bit` | sí |  |
| `customer_status` | `nvarchar(50)` | no |  |
| `churned_at` | `date` | sí |  |
| `acquisition_source` | `nvarchar(50)` | sí |  |
| `preferred_channel` | `nvarchar(50)` | sí |  |
| `source_updated_at` | `datetime2(0)` | sí |  |
| `created_at` | `datetime2(0)` | no |  |
| `updated_at` | `datetime2(0)` | no |  |

## Esquema catalog

Catálogo de productos.

### `catalog.product`

Producto: nombre, categoría, precio, coste, IVA, medidas y estado. 100 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `product_id` | `nvarchar(50)` | no | PK |
| `product_name` | `nvarchar(255)` | no |  |
| `category` | `nvarchar(100)` | sí |  |
| `subcategory` | `nvarchar(100)` | sí |  |
| `brand` | `nvarchar(100)` | sí |  |
| `supplier` | `nvarchar(100)` | sí |  |
| `material` | `nvarchar(100)` | sí |  |
| `color` | `nvarchar(100)` | sí |  |
| `sale_price` | `decimal(18,2)` | sí |  |
| `unit_cost` | `decimal(18,2)` | sí |  |
| `vat_pct` | `decimal(9,4)` | sí |  |
| `weight_kg` | `decimal(18,3)` | sí |  |
| `length_cm` | `decimal(18,2)` | sí |  |
| `width_cm` | `decimal(18,2)` | sí |  |
| `height_cm` | `decimal(18,2)` | sí |  |
| `catalog_start_date` | `date` | sí |  |
| `product_status` | `nvarchar(50)` | no |  |
| `ean` | `nvarchar(30)` | sí |  |
| `created_at` | `datetime2(0)` | no |  |
| `updated_at` | `datetime2(0)` | no |  |

## Esquema store

Tiendas y cajas.

### `store.store`

Tienda física o almacén online (`ONLINE`), con horario, gerente y estado. 7 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `store_id` | `nvarchar(50)` | no | PK |
| `store_name` | `nvarchar(150)` | no |  |
| `location_type` | `nvarchar(50)` | sí |  |
| `channel` | `nvarchar(50)` | sí |  |
| `city` | `nvarchar(100)` | sí |  |
| `province` | `nvarchar(100)` | sí |  |
| `address_line` | `nvarchar(255)` | sí |  |
| `postal_code` | `nvarchar(20)` | sí |  |
| `country_code` | `char(2)` | sí |  |
| `opened_at` | `date` | sí |  |
| `square_meters` | `int` | sí |  |
| `phone` | `nvarchar(50)` | sí |  |
| `opening_hours` | `nvarchar(100)` | sí |  |
| `latitude` | `decimal(10,6)` | sí |  |
| `longitude` | `decimal(10,6)` | sí |  |
| `store_status` | `nvarchar(50)` | no |  |
| `region` | `nvarchar(100)` | sí |  |
| `manager_name` | `nvarchar(150)` | sí |  |
| `notes` | `nvarchar(500)` | sí |  |
| `created_at` | `datetime2(0)` | no |  |
| `updated_at` | `datetime2(0)` | no |  |

### `store.till_session`

Sesión de caja de una tienda: quién la abre, con cuánto efectivo y cómo cierra.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `till_session_id` | `bigint` | no | PK |
| `store_id` | `nvarchar(50)` | no | FK (store.store) |
| `till_id` | `nvarchar(50)` | no |  |
| `cashier_id` | `nvarchar(50)` | no |  |
| `opened_at` | `datetime2(0)` | no |  |
| `opening_cash` | `decimal(18,2)` | no |  |
| `closed_at` | `datetime2(0)` | sí |  |
| `expected_cash` | `decimal(18,2)` | sí |  |
| `counted_cash` | `decimal(18,2)` | sí |  |
| `session_status` | `nvarchar(20)` | no |  |

## Esquema sales

Ventas online y en tienda.

### `sales.online_order`

Pedido online: cliente, envío, pago, total, estado y cupón. 650 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `order_id` | `nvarchar(50)` | no | PK |
| `ordered_at` | `datetime2(0)` | sí |  |
| `customer_id` | `nvarchar(50)` | sí | FK (crm.customer) |
| `online_user_id` | `nvarchar(50)` | sí |  |
| `order_total` | `decimal(18,2)` | sí |  |
| `currency_code` | `char(3)` | no |  |
| `shipping_amount` | `decimal(18,2)` | sí |  |
| `shipping_address` | `nvarchar(255)` | sí |  |
| `shipping_postal_code` | `nvarchar(20)` | sí |  |
| `shipping_city` | `nvarchar(100)` | sí |  |
| `shipping_province` | `nvarchar(100)` | sí |  |
| `shipping_country_code` | `char(2)` | sí |  |
| `payment_method` | `nvarchar(50)` | sí |  |
| `order_status` | `nvarchar(50)` | no |  |
| `order_origin` | `nvarchar(50)` | sí |  |
| `coupon_instance_id` | `nvarchar(50)` | sí |  |
| `source_updated_at` | `datetime2(0)` | sí |  |
| `created_at` | `datetime2(0)` | no |  |
| `updated_at` | `datetime2(0)` | no |  |

### `sales.online_order_line`

Línea de pedido online: producto, cantidad, precio, descuento e importe. 1.883 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `order_line_id` | `nvarchar(50)` | no | PK |
| `order_id` | `nvarchar(50)` | no | FK (sales.online_order) |
| `product_id` | `nvarchar(50)` | sí | FK (catalog.product) |
| `product_description` | `nvarchar(255)` | sí |  |
| `category` | `nvarchar(100)` | sí |  |
| `subcategory` | `nvarchar(100)` | sí |  |
| `quantity` | `int` | no |  |
| `unit_price` | `decimal(18,2)` | sí |  |
| `discount_pct` | `decimal(9,4)` | sí |  |
| `discount_amount` | `decimal(18,2)` | sí |  |
| `line_amount` | `decimal(18,2)` | sí |  |
| `vat_pct` | `decimal(9,4)` | sí |  |
| `promo_id` | `nvarchar(50)` | sí |  |
| `created_at` | `datetime2(0)` | no |  |

### `sales.pos_ticket`

Ticket de venta en tienda: caja, cajero, cliente, bruto, descuento y neto. 1.196 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `ticket_id` | `nvarchar(50)` | no | PK |
| `ticket_at` | `datetime2(0)` | sí |  |
| `store_id` | `nvarchar(50)` | sí | FK (store.store) |
| `till_id` | `nvarchar(50)` | sí |  |
| `cashier_id` | `nvarchar(50)` | sí |  |
| `cashier_employee_id` | `nvarchar(20)` | sí |  |
| `customer_id` | `nvarchar(50)` | sí | FK (crm.customer) |
| `currency_code` | `char(3)` | no |  |
| `channel` | `nvarchar(50)` | no |  |
| `ticket_gross_amount` | `decimal(18,2)` | sí |  |
| `ticket_discount_amount` | `decimal(18,2)` | sí |  |
| `ticket_net_amount` | `decimal(18,2)` | sí |  |
| `coupon_instance_id` | `nvarchar(50)` | sí |  |
| `till_session_id` | `bigint` | sí |  |
| `created_at` | `datetime2(0)` | no |  |
| `updated_at` | `datetime2(0)` | no |  |

### `sales.pos_ticket_line`

Línea de ticket: producto, cantidad, precio, descuento e importe. 2.459 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `ticket_line_id` | `nvarchar(50)` | no | PK |
| `ticket_id` | `nvarchar(50)` | no | FK (sales.pos_ticket) |
| `product_id` | `nvarchar(50)` | sí | FK (catalog.product) |
| `product_description` | `nvarchar(255)` | sí |  |
| `category` | `nvarchar(100)` | sí |  |
| `subcategory` | `nvarchar(100)` | sí |  |
| `quantity` | `int` | no |  |
| `unit_price` | `decimal(18,2)` | sí |  |
| `discount_pct` | `decimal(9,4)` | sí |  |
| `discount_amount` | `decimal(18,2)` | sí |  |
| `line_amount` | `decimal(18,2)` | sí |  |
| `promo_id` | `nvarchar(50)` | sí |  |
| `notes` | `nvarchar(500)` | sí |  |
| `created_at` | `datetime2(0)` | no |  |

### `sales.store_payment`

Cobro de un ticket; un ticket puede tener varios (pago mixto). 1.590 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `payment_id` | `nvarchar(50)` | no | PK |
| `ticket_id` | `nvarchar(50)` | no | FK (sales.pos_ticket) |
| `paid_at` | `datetime2(0)` | sí |  |
| `store_id` | `nvarchar(50)` | sí | FK (store.store) |
| `till_id` | `nvarchar(50)` | sí |  |
| `cashier_id` | `nvarchar(50)` | sí |  |
| `cashier_employee_id` | `nvarchar(20)` | sí |  |
| `payment_method` | `nvarchar(50)` | sí |  |
| `paid_amount` | `decimal(18,2)` | sí |  |
| `currency_code` | `char(3)` | no |  |
| `authorization_reference` | `nvarchar(100)` | sí |  |
| `payment_status` | `nvarchar(50)` | no |  |
| `notes` | `nvarchar(500)` | sí |  |
| `created_at` | `datetime2(0)` | no |  |

## Esquema returns

Devoluciones.

### `returns.return_header`

Cabecera de devolución, online o en tienda: origen, estado y reembolso. 389 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `return_id` | `nvarchar(50)` | no | PK |
| `returned_at` | `datetime2(0)` | sí |  |
| `return_channel` | `nvarchar(50)` | no |  |
| `store_id` | `nvarchar(50)` | sí | FK (store.store) |
| `customer_id` | `nvarchar(50)` | sí | FK (crm.customer) |
| `original_ticket_id` | `nvarchar(50)` | sí |  |
| `original_order_id` | `nvarchar(50)` | sí |  |
| `return_status` | `nvarchar(50)` | no |  |
| `return_method` | `nvarchar(50)` | sí |  |
| `refund_method` | `nvarchar(50)` | sí |  |
| `currency_code` | `char(3)` | no |  |
| `notes` | `nvarchar(500)` | sí |  |
| `created_at` | `datetime2(0)` | no |  |
| `updated_at` | `datetime2(0)` | no |  |

### `returns.return_line`

Línea devuelta: producto, unidades, importe reembolsado y motivo. 395 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `return_line_id` | `nvarchar(80)` | no | PK |
| `return_id` | `nvarchar(50)` | no | FK (returns.return_header) |
| `product_id` | `nvarchar(50)` | sí | FK (catalog.product) |
| `original_ticket_line_id` | `nvarchar(50)` | sí |  |
| `original_order_line_id` | `nvarchar(50)` | sí |  |
| `returned_quantity` | `int` | no |  |
| `refund_amount` | `decimal(18,2)` | sí |  |
| `return_reason` | `nvarchar(200)` | sí |  |
| `original_sales_channel` | `nvarchar(50)` | sí |  |
| `created_at` | `datetime2(0)` | no |  |

## Esquema inventory

Stock vivo, foto diaria y movimientos.

### `inventory.stock_snapshot`

Foto diaria del stock por tienda y producto (la genera el cierre diario). 1.892 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `snapshot_date` | `date` | no | PK |
| `store_id` | `nvarchar(50)` | no | PK, FK (store.store) |
| `product_id` | `nvarchar(50)` | no | PK, FK (catalog.product) |
| `closing_stock_qty` | `decimal(18,2)` | sí |  |
| `reserved_stock_qty` | `decimal(18,2)` | sí |  |
| `in_transit_stock_qty` | `decimal(18,2)` | sí |  |
| `minimum_stock_qty` | `decimal(18,2)` | sí |  |
| `source_system` | `nvarchar(50)` | sí |  |
| `notes` | `nvarchar(500)` | sí |  |
| `created_at` | `datetime2(0)` | no |  |

### `inventory.stock_level`

Stock vivo por tienda y producto: en mano, reservado, en tránsito y mínimo. 567 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `store_id` | `nvarchar(50)` | no | PK, FK (store.store) |
| `product_id` | `nvarchar(50)` | no | PK, FK (catalog.product) |
| `on_hand_qty` | `int` | no |  |
| `reserved_qty` | `int` | no |  |
| `in_transit_qty` | `int` | no |  |
| `minimum_qty` | `int` | no |  |
| `updated_at` | `datetime2(0)` | no |  |

### `inventory.stock_movement`

Libro de movimientos de stock: ventas, ajustes, reposiciones, recepciones y devoluciones.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `movement_id` | `bigint` | no | PK |
| `moved_at` | `datetime2(0)` | no |  |
| `store_id` | `nvarchar(50)` | no |  |
| `product_id` | `nvarchar(50)` | no |  |
| `movement_type` | `nvarchar(30)` | no |  |
| `on_hand_delta` | `int` | no |  |
| `reserved_delta` | `int` | no |  |
| `in_transit_delta` | `int` | no |  |
| `document_type` | `nvarchar(30)` | sí |  |
| `document_id` | `nvarchar(50)` | sí |  |
| `user_login` | `nvarchar(100)` | sí |  |
| `notes` | `nvarchar(500)` | sí |  |

## Esquema mkt

Campañas, cupones, promociones y afinidad.

### `mkt.campaign`

Campaña de marketing: objetivo, canal, segmento, oferta, presupuesto, grupo de control y estado. 26 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `campaign_id` | `nvarchar(30)` | no | PK |
| `campaign_name` | `nvarchar(200)` | no |  |
| `objective` | `nvarchar(50)` | no |  |
| `channel` | `nvarchar(20)` | no |  |
| `starts_at` | `datetime2(0)` | no |  |
| `ends_at` | `datetime2(0)` | no |  |
| `target_segment` | `nvarchar(50)` | no |  |
| `target_category` | `nvarchar(100)` | sí |  |
| `target_subcategory` | `nvarchar(100)` | sí |  |
| `target_store_id` | `nvarchar(50)` | sí | FK (store.store) |
| `offer_type` | `nvarchar(30)` | no |  |
| `discount_pct` | `decimal(5,2)` | no |  |
| `budget_eur` | `decimal(12,2)` | sí |  |
| `control_group_pct` | `decimal(5,3)` | no |  |
| `primary_kpi` | `nvarchar(50)` | sí |  |
| `campaign_status` | `nvarchar(20)` | no |  |
| `copy_axis` | `nvarchar(500)` | sí |  |
| `created_by` | `nvarchar(100)` | sí |  |
| `created_at` | `datetime2(0)` | no |  |
| `updated_at` | `datetime2(0)` | no |  |

### `mkt.campaign_contact`

Cliente contactado en una campaña, con su grupo (tratamiento o control) y su resultado a 30 días. 480 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `contact_id` | `nvarchar(30)` | no | PK |
| `campaign_id` | `nvarchar(30)` | no | FK (mkt.campaign) |
| `customer_id` | `nvarchar(50)` | no | FK (crm.customer) |
| `contacted_at` | `datetime2(0)` | sí |  |
| `contact_channel` | `nvarchar(20)` | no |  |
| `experiment_group` | `nvarchar(20)` | no |  |
| `is_control` | `bit` | no |  |
| `assigned_segment` | `nvarchar(50)` | sí |  |
| `offer_code` | `nvarchar(30)` | sí |  |
| `coupon_instance_id` | `nvarchar(30)` | sí |  |
| `delivery_status` | `nvarchar(30)` | no |  |
| `contact_cost_eur` | `decimal(9,3)` | no |  |
| `contact_priority` | `nvarchar(20)` | sí |  |
| `personalized_store_id` | `nvarchar(50)` | sí |  |
| `recommended_product_1` | `nvarchar(50)` | sí |  |
| `recommended_product_2` | `nvarchar(50)` | sí |  |
| `app_user_id` | `nvarchar(30)` | sí |  |
| `conversion_30d` | `bit` | no |  |
| `conversion_order_id` | `nvarchar(50)` | sí |  |
| `conversion_ticket_id` | `nvarchar(50)` | sí |  |
| `revenue_30d_eur` | `decimal(12,2)` | no |  |
| `margin_30d_eur` | `decimal(12,2)` | no |  |
| `converted_at` | `datetime2(0)` | sí |  |

### `mkt.coupon`

Cupón emitido a un cliente y su canje. 367 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `coupon_instance_id` | `nvarchar(30)` | no | PK |
| `coupon_code` | `nvarchar(30)` | no |  |
| `campaign_id` | `nvarchar(30)` | sí | FK (mkt.campaign) |
| `customer_id` | `nvarchar(50)` | no | FK (crm.customer) |
| `issued_at` | `datetime2(0)` | no |  |
| `valid_from` | `datetime2(0)` | no |  |
| `valid_to` | `datetime2(0)` | no |  |
| `coupon_type` | `nvarchar(20)` | no |  |
| `discount_pct` | `decimal(5,2)` | sí |  |
| `discount_eur` | `decimal(10,2)` | sí |  |
| `min_spend_eur` | `decimal(10,2)` | no |  |
| `restricted_category` | `nvarchar(100)` | sí |  |
| `restricted_store_id` | `nvarchar(50)` | sí |  |
| `issue_channel` | `nvarchar(20)` | sí |  |
| `coupon_status` | `nvarchar(20)` | no |  |
| `redeemed_at` | `datetime2(0)` | sí |  |
| `order_id` | `nvarchar(50)` | sí |  |
| `ticket_id` | `nvarchar(50)` | sí |  |
| `basket_eur` | `decimal(12,2)` | sí |  |
| `discount_applied_eur` | `decimal(12,2)` | sí |  |
| `margin_after_discount_eur` | `decimal(12,2)` | sí |  |

### `mkt.promotion`

Promoción del calendario: ámbito, tipo, descuento, canal, umbral y margen mínimo. 98 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `promo_id` | `nvarchar(30)` | no | PK |
| `promo_name` | `nvarchar(200)` | no |  |
| `starts_at` | `datetime2(0)` | no |  |
| `ends_at` | `datetime2(0)` | no |  |
| `scope_type` | `nvarchar(30)` | no |  |
| `scope_id` | `nvarchar(150)` | no |  |
| `promo_type` | `nvarchar(30)` | no |  |
| `discount_pct` | `decimal(5,2)` | sí |  |
| `discount_eur` | `decimal(10,2)` | sí |  |
| `channel` | `nvarchar(20)` | no |  |
| `target_segment` | `nvarchar(50)` | sí |  |
| `store_id` | `nvarchar(50)` | sí | FK (store.store) |
| `combinable` | `bit` | no |  |
| `basket_threshold_eur` | `decimal(10,2)` | no |  |
| `min_margin_pct` | `decimal(5,2)` | sí |  |
| `related_campaign_id` | `nvarchar(30)` | sí | FK (mkt.campaign) |

### `mkt.customer_store_affinity`

Afinidad de un cliente con las tiendas: visitas, gasto y probabilidad de visita. 100 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `customer_id` | `nvarchar(50)` | no | PK, FK (crm.customer) |
| `preferred_store_id` | `nvarchar(50)` | sí |  |
| `nearest_store_id` | `nvarchar(50)` | sí |  |
| `nearest_store_km` | `decimal(9,1)` | sí |  |
| `store_visits_12m` | `int` | sí |  |
| `store_spend_12m_eur` | `decimal(12,2)` | sí |  |
| `online_spend_12m_eur` | `decimal(12,2)` | sí |  |
| `click_collect_propensity` | `decimal(6,3)` | sí |  |
| `visit_probability_30d` | `decimal(6,3)` | sí |  |
| `local_cluster` | `nvarchar(50)` | sí |  |
| `locally_capturable` | `bit` | sí |  |
| `home_city` | `nvarchar(100)` | sí |  |
| `home_province` | `nvarchar(100)` | sí |  |
| `recalculated_at` | `datetime2(0)` | sí |  |

## Esquema fin

Costes por transacción.

### `fin.transaction_cost`

Margen de contribución de cada pedido o ticket: ingresos, coste de producto y costes operativos por canal. 1.829 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `transaction_cost_id` | `nvarchar(30)` | no | PK |
| `document_type` | `nvarchar(10)` | no |  |
| `order_id` | `nvarchar(50)` | sí |  |
| `ticket_id` | `nvarchar(50)` | sí |  |
| `customer_id` | `nvarchar(50)` | sí |  |
| `transaction_at` | `datetime2(0)` | sí |  |
| `channel` | `nvarchar(20)` | no |  |
| `store_id` | `nvarchar(50)` | sí |  |
| `main_category` | `nvarchar(100)` | sí |  |
| `gross_revenue_eur` | `decimal(12,2)` | sí |  |
| `discount_eur` | `decimal(12,2)` | sí |  |
| `product_cost_eur` | `decimal(12,2)` | sí |  |
| `logistics_cost_eur` | `decimal(12,2)` | sí |  |
| `packaging_cost_eur` | `decimal(12,2)` | sí |  |
| `last_mile_cost_eur` | `decimal(12,2)` | sí |  |
| `payment_cost_eur` | `decimal(12,2)` | sí |  |
| `service_cost_eur` | `decimal(12,2)` | sí |  |
| `expected_return_cost_eur` | `decimal(12,2)` | sí |  |
| `cac_eur` | `decimal(12,2)` | sí |  |
| `attributed_campaign_id` | `nvarchar(30)` | sí |  |
| `net_contribution_eur` | `decimal(12,2)` | sí |  |

## Esquema hr

Personas: plantilla, tiempo, formación, evaluación y salario.

### `hr.employee`

Empleado: puesto, nivel, contrato, manager, ubicación y estado. 820 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `employee_id` | `nvarchar(20)` | no | PK |
| `full_name` | `nvarchar(200)` | no |  |
| `gender` | `nvarchar(20)` | sí |  |
| `birth_date` | `date` | sí |  |
| `hired_at` | `date` | sí |  |
| `left_at` | `date` | sí |  |
| `employee_status` | `nvarchar(20)` | no |  |
| `exit_type` | `nvarchar(50)` | sí |  |
| `exit_reason` | `nvarchar(200)` | sí |  |
| `department` | `nvarchar(100)` | sí |  |
| `location` | `nvarchar(100)` | sí |  |
| `role_name` | `nvarchar(100)` | sí |  |
| `level_name` | `nvarchar(50)` | sí |  |
| `contract_type` | `nvarchar(50)` | sí |  |
| `work_schedule` | `nvarchar(20)` | sí |  |
| `manager_id` | `nvarchar(20)` | sí | FK (hr.employee) |
| `remote_days_week` | `tinyint` | sí |  |
| `commute_km` | `decimal(9,1)` | sí |  |
| `source_row_id` | `nvarchar(50)` | sí |  |
| `created_at` | `datetime2(0)` | no |  |
| `updated_at` | `datetime2(0)` | no |  |

### `hr.employee_movement`

Promociones y movilidad interna de un empleado. 1.437 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `movement_id` | `nvarchar(20)` | no | PK |
| `employee_id` | `nvarchar(20)` | no | FK (hr.employee) |
| `moved_at` | `date` | sí |  |
| `movement_type` | `nvarchar(50)` | no |  |
| `department_from` | `nvarchar(100)` | sí |  |
| `department_to` | `nvarchar(100)` | sí |  |
| `level_from` | `nvarchar(50)` | sí |  |
| `level_to` | `nvarchar(50)` | sí |  |
| `reason` | `nvarchar(200)` | sí |  |
| `hr_comment` | `nvarchar(500)` | sí |  |
| `loaded_by` | `nvarchar(100)` | sí |  |
| `loaded_at` | `date` | sí |  |

### `hr.absence`

Ausencias: tipo, fechas, días laborables y justificación. 1.521 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `absence_id` | `nvarchar(20)` | no | PK |
| `employee_id` | `nvarchar(20)` | no | FK (hr.employee) |
| `start_date` | `date` | sí |  |
| `end_date` | `date` | sí |  |
| `absence_type` | `nvarchar(50)` | no |  |
| `working_days` | `int` | sí |  |
| `justified` | `nvarchar(20)` | sí |  |
| `notes` | `nvarchar(300)` | sí |  |

### `hr.overtime`

Horas extra por mes y su aprobación. 7.822 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `overtime_id` | `nvarchar(20)` | no | PK |
| `employee_id` | `nvarchar(20)` | no | FK (hr.employee) |
| `period_month` | `char(7)` | no |  |
| `department_reported` | `nvarchar(100)` | sí |  |
| `hours` | `decimal(6,2)` | sí |  |
| `reason` | `nvarchar(100)` | sí |  |
| `approval_status` | `nvarchar(20)` | no |  |
| `approver_id` | `nvarchar(20)` | sí |  |
| `requested_at` | `datetime2(0)` | sí |  |
| `decided_at` | `datetime2(0)` | sí |  |

### `hr.training`

Formación de un empleado: curso, horas previstas y realizadas, estado. 3.033 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `training_id` | `nvarchar(20)` | no | PK |
| `employee_id` | `nvarchar(20)` | no | FK (hr.employee) |
| `course_id` | `nvarchar(20)` | no |  |
| `course_name` | `nvarchar(200)` | sí |  |
| `category` | `nvarchar(50)` | sí |  |
| `start_date` | `date` | sí |  |
| `end_date` | `date` | sí |  |
| `planned_hours` | `decimal(6,1)` | sí |  |
| `completed_hours` | `decimal(6,1)` | sí |  |
| `training_status` | `nvarchar(30)` | no |  |
| `cost_eur` | `decimal(10,2)` | sí |  |
| `provider` | `nvarchar(100)` | sí |  |

### `hr.performance_review`

Evaluación anual del desempeño. 1.132 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `review_id` | `nvarchar(20)` | no | PK |
| `employee_id` | `nvarchar(20)` | no | FK (hr.employee) |
| `review_cycle` | `char(4)` | no |  |
| `reviewed_at` | `date` | sí |  |
| `overall_score` | `decimal(3,1)` | sí |  |
| `objectives_pct` | `decimal(6,1)` | sí |  |
| `competencies_score` | `decimal(3,1)` | sí |  |
| `potential` | `nvarchar(20)` | sí |  |
| `reviewer_id` | `nvarchar(20)` | sí |  |
| `manager_comment` | `nvarchar(500)` | sí |  |
| `source_system` | `nvarchar(50)` | sí |  |

### `hr.compensation`

Salario base y variable por periodo. 1.641 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `payroll_id` | `nvarchar(20)` | no | PK |
| `employee_id` | `nvarchar(20)` | no | FK (hr.employee) |
| `period_month` | `char(7)` | no |  |
| `base_salary_eur` | `decimal(12,2)` | sí |  |
| `variable_salary_eur` | `decimal(12,2)` | sí |  |
| `increase_pct` | `decimal(6,2)` | sí |  |
| `currency_code` | `char(3)` | no |  |
| `source_system` | `nvarchar(50)` | sí |  |
| `loaded_at` | `date` | sí |  |

### `hr.people_analytics_seed`

Ficha de People Analytics por empleado (riesgo de abandono, engagement…). Viene de los CSV; no la modifica la web. 820 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `employee_id` | `nvarchar(20)` | no | PK |
| `nombre_anonimizado` | `nvarchar(200)` | sí |  |
| `genero` | `nvarchar(20)` | sí |  |
| `edad` | `int` | sí |  |
| `departamento` | `nvarchar(100)` | sí |  |
| `ubicacion` | `nvarchar(100)` | sí |  |
| `rol` | `nvarchar(100)` | sí |  |
| `nivel` | `nvarchar(50)` | sí |  |
| `tipo_contrato` | `nvarchar(50)` | sí |  |
| `jornada` | `nvarchar(20)` | sí |  |
| `fecha_alta` | `date` | sí |  |
| `fecha_salida` | `date` | sí |  |
| `estado_actual` | `nvarchar(20)` | sí |  |
| `tipo_salida` | `nvarchar(50)` | sí |  |
| `motivo_salida` | `nvarchar(200)` | sí |  |
| `abandono_voluntario_24m` | `bit` | sí |  |
| `salida_24m` | `bit` | sí |  |
| `activo_actual` | `bit` | sí |  |
| `antiguedad_meses` | `int` | sí |  |
| `evaluacion_desempeno_1_5` | `decimal(3,1)` | sí |  |
| `promociones_24m` | `int` | sí |  |
| `incremento_salarial_12m_pct` | `decimal(6,2)` | sí |  |
| `salario_anual_eur` | `int` | sí |  |
| `horas_formacion_12m` | `int` | sí |  |
| `satisfaccion_1_10` | `decimal(4,1)` | sí |  |
| `engagement_1_10` | `decimal(4,1)` | sí |  |
| `enps` | `int` | sí |  |
| `calidad_manager_1_5` | `decimal(3,1)` | sí |  |
| `desarrollo_carrera_1_5` | `decimal(3,1)` | sí |  |
| `reconocimiento_1_5` | `decimal(3,1)` | sí |  |
| `percepcion_salario_1_5` | `decimal(3,1)` | sí |  |
| `balance_vida_trabajo_1_5` | `decimal(3,1)` | sí |  |
| `carga_trabajo_1_5` | `decimal(3,1)` | sí |  |
| `absentismo_dias_12m` | `int` | sí |  |
| `horas_extra_media_mes` | `decimal(6,1)` | sí |  |
| `teletrabajo_dias_semana` | `int` | sí |  |
| `distancia_casa_trabajo_km` | `decimal(9,1)` | sí |  |
| `probabilidad_abandono` | `decimal(6,3)` | sí |  |
| `riesgo_abandono` | `nvarchar(20)` | sí |  |
| `alto_riesgo_flag` | `bit` | sí |  |
| `talento_clave_flag` | `bit` | sí |  |
| `prioridad_retencion` | `nvarchar(30)` | sí |  |
| `conteo_empleado` | `int` | sí |  |
| `comentario_salida` | `nvarchar(1000)` | sí |  |
| `comentario_clima` | `nvarchar(1000)` | sí |  |

### `hr.turnover_monthly_seed`

Rotación mensual por departamento hasta abril de 2026. Viene de los CSV. 280 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `periodo_mes` | `date` | no | PK |
| `departamento` | `nvarchar(100)` | no | PK |
| `headcount_inicio_mes` | `int` | sí |  |
| `altas_mes` | `int` | sí |  |
| `bajas_voluntarias_mes` | `int` | sí |  |
| `bajas_no_voluntarias_mes` | `int` | sí |  |
| `bajas_totales_mes` | `int` | sí |  |
| `headcount_fin_mes` | `int` | sí |  |
| `tasa_rotacion_voluntaria_pct` | `decimal(9,2)` | sí |  |
| `tasa_rotacion_total_pct` | `decimal(9,2)` | sí |  |
| `empleados_alto_riesgo_fin_mes` | `int` | sí |  |
| `talento_clave_alto_riesgo_fin_mes` | `int` | sí |  |
| `salario_medio_activos_mes_eur` | `int` | sí |  |
| `satisfaccion_media_activos_mes` | `decimal(4,2)` | sí |  |
| `engagement_medio_activos_mes` | `decimal(4,2)` | sí |  |
| `area_critica_rotacion_flag` | `bit` | sí |  |

## Esquema ref

Referencias.

### `ref.department_map`

De los nombres de departamento en bruto al estándar, con su área. 36 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `department_raw` | `nvarchar(100)` | no | PK |
| `department_std` | `nvarchar(100)` | no |  |
| `hr_area` | `nvarchar(100)` | sí |  |
| `business_channel` | `nvarchar(100)` | sí |  |
| `critical_turnover_default` | `bit` | no |  |

### `ref.brand_guardrail`

Reglas de marca que validan las creatividades de las campañas. 12 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `rule_id` | `nvarchar(20)` | no | PK |
| `rule_category` | `nvarchar(50)` | no |  |
| `rule_description` | `nvarchar(500)` | no |  |
| `applies_to_channel` | `nvarchar(100)` | no |  |
| `severity` | `nvarchar(20)` | no |  |

### `ref.calendar`

Calendario: fecha, año, mes, trimestre y periodo. 1.096 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `date_key` | `date` | no | PK |
| `year_num` | `smallint` | no |  |
| `month_num` | `tinyint` | no |  |
| `month_name` | `nvarchar(20)` | no |  |
| `quarter_name` | `char(2)` | no |  |
| `period_month` | `date` | no |  |
| `month_end` | `date` | no |  |

### `ref.cost_rule`

Reglas de coste por canal: logística, embalaje, última milla, pago, servicio, devoluciones esperadas y CAC.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `channel` | `nvarchar(20)` | no | PK |
| `logistics_eur` | `decimal(9,2)` | no |  |
| `packaging_eur` | `decimal(9,2)` | no |  |
| `last_mile_eur` | `decimal(9,2)` | no |  |
| `payment_pct` | `decimal(9,4)` | no |  |
| `service_eur` | `decimal(9,2)` | no |  |
| `expected_return_pct` | `decimal(9,4)` | no |  |
| `cac_pct` | `decimal(9,4)` | no |  |

## Esquema xref

Tablas puente entre sistemas origen y modelo canónico.

### `xref.store_alias`

Alias de tienda en los sistemas origen. 41 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `alias` | `nvarchar(100)` | no | PK |
| `canonical_store_id` | `nvarchar(50)` | sí |  |
| `source_context` | `nvarchar(100)` | sí |  |
| `confidence` | `nvarchar(20)` | sí |  |
| `note` | `nvarchar(300)` | sí |  |

### `xref.product_alias`

Equivalencia entre códigos de producto del escenario RAG y del retail. 32 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `source_system` | `nvarchar(50)` | no | PK |
| `source_product_id` | `nvarchar(50)` | no | PK |
| `source_product_name` | `nvarchar(150)` | sí |  |
| `source_category_code` | `nvarchar(20)` | sí |  |
| `source_category_name` | `nvarchar(100)` | sí |  |
| `canonical_product_id` | `nvarchar(50)` | sí |  |
| `canonical_product_name` | `nvarchar(255)` | sí |  |
| `canonical_category` | `nvarchar(100)` | sí |  |
| `canonical_subcategory` | `nvarchar(100)` | sí |  |
| `match_method` | `nvarchar(50)` | sí |  |
| `confidence` | `nvarchar(20)` | sí |  |
| `note` | `nvarchar(300)` | sí |  |

### `xref.employee_alias`

Identificadores operativos de empleado en cada sistema origen. 106 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `source_system` | `nvarchar(50)` | no | PK |
| `operational_employee_id` | `nvarchar(50)` | no | PK |
| `canonical_employee_id` | `nvarchar(50)` | no |  |
| `canonical_employee_location` | `nvarchar(100)` | sí |  |
| `canonical_employee_department` | `nvarchar(100)` | sí |  |
| `match_method` | `nvarchar(50)` | sí |  |
| `confidence` | `nvarchar(20)` | sí |  |
| `note` | `nvarchar(300)` | sí |  |

### `xref.employee_store`

Tienda en la que trabaja cada empleado. 820 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `employee_id` | `nvarchar(50)` | no | PK |
| `department` | `nvarchar(100)` | sí |  |
| `location` | `nvarchar(100)` | sí |  |
| `canonical_store_id` | `nvarchar(50)` | sí |  |
| `assignment_type` | `nvarchar(100)` | sí |  |
| `confidence` | `nvarchar(20)` | sí |  |

## Esquema rag

Tablas del escenario RAG.

### `rag.customer`

Clientes con los nombres de columna del escenario RAG. 60 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `CustomerID` | `nvarchar(20)` | no | PK |
| `Tier` | `nvarchar(20)` | sí |  |
| `JoinDate` | `date` | sí |  |
| `City` | `nvarchar(100)` | sí |  |
| `ConsentMarketing` | `nvarchar(5)` | sí |  |

### `rag.product`

Productos del escenario RAG. 32 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `ProductID` | `nvarchar(30)` | no | PK |
| `ProductName` | `nvarchar(150)` | sí |  |
| `CategoryFamily` | `nvarchar(10)` | sí |  |
| `CategoryCode` | `nvarchar(10)` | sí |  |
| `CategoryName` | `nvarchar(50)` | sí |  |
| `Material` | `nvarchar(50)` | sí |  |
| `Color` | `nvarchar(50)` | sí |  |
| `BulkyFlag` | `nvarchar(5)` | sí |  |
| `StandardCostEUR` | `decimal(12,2)` | sí |  |
| `ListPriceEUR` | `decimal(12,2)` | sí |  |
| `Status` | `nvarchar(20)` | sí |  |

### `rag.store`

Tiendas del escenario RAG. 3 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `StoreID` | `nvarchar(20)` | no | PK |
| `StoreName` | `nvarchar(100)` | sí |  |
| `City` | `nvarchar(100)` | sí |  |
| `Region` | `nvarchar(50)` | sí |  |

### `rag.stock_daily`

Stock diario del escenario RAG. 2.295 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `Date` | `date` | no | PK |
| `StoreID` | `nvarchar(20)` | no | PK |
| `ProductID` | `nvarchar(30)` | no | PK |
| `OnHandUnits` | `int` | sí |  |
| `ReservedUnits` | `int` | sí |  |
| `BlockedUnits` | `int` | sí |  |
| `AvailableUnits` | `int` | sí |  |

### `rag.sales_daily`

Ventas diarias por canal y tienda del escenario RAG. 204 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `Date` | `date` | no | PK |
| `Channel` | `nvarchar(20)` | no | PK |
| `StoreID` | `nvarchar(20)` | no | PK |
| `GrossSalesEUR` | `decimal(12,2)` | sí |  |
| `DiscountsEUR` | `decimal(12,2)` | sí |  |
| `PointsDiscountEUR` | `decimal(12,2)` | sí |  |
| `ReturnsEUR` | `decimal(12,2)` | sí |  |
| `NetSalesEUR` | `decimal(12,2)` | sí |  |
| `Orders` | `int` | sí |  |

### `rag.return_fact`

Devoluciones del escenario RAG. 248 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `ReturnID` | `nvarchar(30)` | no | PK |
| `ReturnDate` | `date` | sí |  |
| `Channel` | `nvarchar(20)` | sí |  |
| `StoreID` | `nvarchar(20)` | sí |  |
| `CustomerID` | `nvarchar(20)` | sí |  |
| `ProductID` | `nvarchar(30)` | sí |  |
| `Units` | `int` | sí |  |
| `RefundAmountEUR` | `decimal(12,2)` | sí |  |
| `ReasonCode` | `nvarchar(10)` | sí |  |
| `ReasonDesc` | `nvarchar(100)` | sí |  |
| `Condition` | `nvarchar(20)` | sí |  |
| `Approved` | `nvarchar(5)` | sí |  |

### `rag.stockout_alert`

Alertas de rotura del escenario RAG. 15 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `AlertDate` | `date` | no | PK |
| `StoreID` | `nvarchar(20)` | no | PK |
| `ProductID` | `nvarchar(30)` | no | PK |
| `AvailableUnits` | `int` | sí |  |
| `SalesUnitsLast7d` | `int` | sí |  |
| `Priority` | `nvarchar(10)` | sí |  |

## Esquema meta

Catálogo de datos y diccionarios.

### `meta.reference_file`

Ficheros de metadatos (catálogo, diccionarios, mapeos) con sus columnas. 7 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `file_path` | `nvarchar(260)` | no | PK |
| `column_list` | `nvarchar(2000)` | no |  |
| `has_bom` | `bit` | no |  |
| `description` | `nvarchar(300)` | sí |  |

### `meta.reference_row`

Filas de esos ficheros, como JSON. 415 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `file_path` | `nvarchar(260)` | no | PK, FK (meta.reference_file) |
| `row_num` | `int` | no | PK |
| `row_json` | `nvarchar(max)` | no |  |

## Esquema lab

Laboratorio docente.

### `lab.identity_ground_truth`

Verdad conocida de la consola de identidad: solo para el profesor. 411 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `identity_signal_id` | `nvarchar(30)` | no | PK |
| `customer_id_canonico` | `nvarchar(20)` | no |  |

### `lab.rag_test_case`

Casos de prueba de los juegos de evaluación RAG, editables. 16 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `test_set` | `nvarchar(30)` | no | PK |
| `row_num` | `int` | no | PK |
| `question` | `nvarchar(1000)` | no |  |
| `expected_response` | `nvarchar(2000)` | no |  |
| `updated_by` | `nvarchar(100)` | sí |  |
| `updated_at` | `datetime2(0)` | sí |  |

### `lab.prompt_sample`

Muestra de salidas con comentario para probar prompts. 40 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `employee_id` | `nvarchar(20)` | no | PK |
| `departamento` | `nvarchar(100)` | sí |  |
| `ubicacion` | `nvarchar(100)` | sí |  |
| `rol` | `nvarchar(100)` | sí |  |
| `nivel` | `nvarchar(50)` | sí |  |
| `fecha_salida` | `date` | sí |  |
| `tipo_salida` | `nvarchar(50)` | sí |  |
| `motivo_salida_sistema` | `nvarchar(200)` | sí |  |
| `comentario_salida` | `nvarchar(1000)` | sí |  |
| `satisfaccion_1_10` | `decimal(4,1)` | sí |  |
| `probabilidad_abandono` | `decimal(6,3)` | sí |  |

## Esquema quality

Calidad de la carga.

### `quality.data_quality_issue`

Lo que la carga corrigió, rechazó o avisó, con el fichero y la fila de origen. 2.918 filas tras la carga inicial.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `issue_id` | `bigint` | no | PK |
| `source_database` | `nvarchar(128)` | no |  |
| `source_schema` | `nvarchar(128)` | no |  |
| `source_table` | `nvarchar(128)` | no |  |
| `source_file` | `nvarchar(260)` | sí |  |
| `source_key` | `nvarchar(255)` | sí |  |
| `issue_type` | `nvarchar(100)` | no |  |
| `issue_severity` | `nvarchar(20)` | no |  |
| `issue_description` | `nvarchar(1000)` | no |  |
| `source_row` | `nvarchar(max)` | sí |  |
| `detected_at` | `datetime2(0)` | no |  |
| `resolved_at` | `datetime2(0)` | sí |  |

## Esquema app

Aplicación: usuarios, sesiones, outbox, auditoría.

### `app.id_counter`

Contador por tipo de identificador y periodo.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `kind` | `nvarchar(30)` | no | PK |
| `period_key` | `smallint` | no | PK |
| `prefix_template` | `nvarchar(30)` | no |  |
| `number_width` | `tinyint` | no |  |
| `next_value` | `bigint` | no |  |

### `app.id_kind`

Tipos de identificador (prefijo, anchura, si reinicia cada año).

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `kind` | `nvarchar(30)` | no | PK |
| `prefix_template` | `nvarchar(30)` | no |  |
| `number_width` | `tinyint` | no |  |
| `per_year` | `bit` | no |  |

### `app.app_user`

Usuario de la web: contraseña con scrypt, intentos fallidos y bloqueo.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `user_id` | `int` | no | PK |
| `login` | `nvarchar(100)` | no |  |
| `display_name` | `nvarchar(200)` | no |  |
| `password_hash` | `varbinary(64)` | no |  |
| `password_salt` | `varbinary(32)` | no |  |
| `scrypt_n` | `int` | no |  |
| `scrypt_r` | `int` | no |  |
| `scrypt_p` | `int` | no |  |
| `is_active` | `bit` | no |  |
| `must_change_password` | `bit` | no |  |
| `failed_attempts` | `int` | no |  |
| `locked_until` | `datetime2(0)` | sí |  |
| `created_at` | `datetime2(0)` | no |  |
| `password_changed_at` | `datetime2(0)` | sí |  |
| `last_login_at` | `datetime2(0)` | sí |  |

### `app.user_role`

Roles de cada usuario.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `user_id` | `int` | no | PK, FK (app.app_user) |
| `role_name` | `nvarchar(30)` | no | PK |

### `app.user_scope`

Ámbito de cada usuario: cliente, empleado o tienda.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `user_id` | `int` | no | PK, FK (app.app_user) |
| `scope_type` | `nvarchar(20)` | no | PK |
| `scope_value` | `nvarchar(50)` | no | PK |

### `app.user_session`

Sesiones activas (solo el hash del token).

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `session_hash` | `varbinary(32)` | no | PK |
| `user_id` | `int` | no | FK (app.app_user) |
| `created_at` | `datetime2(0)` | no |  |
| `expires_at` | `datetime2(0)` | no |  |
| `user_agent` | `nvarchar(300)` | sí |  |

### `app.outbox`

Eventos pendientes de enviar a Cosmos DB.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `outbox_id` | `bigint` | no | PK |
| `container_name` | `nvarchar(50)` | no |  |
| `operation` | `nvarchar(10)` | no |  |
| `document_json` | `nvarchar(max)` | no |  |
| `created_at` | `datetime2(0)` | no |  |
| `attempts` | `int` | no |  |
| `last_error` | `nvarchar(1000)` | sí |  |
| `sent_at` | `datetime2(0)` | sí |  |

### `app.idempotency_key`

Respuestas guardadas por Idempotency-Key.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `idempotency_key` | `nvarchar(100)` | no | PK |
| `user_id` | `int` | no | PK |
| `request_path` | `nvarchar(200)` | no |  |
| `status_code` | `int` | no |  |
| `response_body` | `nvarchar(max)` | no |  |
| `created_at` | `datetime2(0)` | no |  |

### `app.audit_log`

Auditoría de cambios hechos desde la web.

| Columna | Tipo | Nulo | Clave |
| --- | --- | --- | --- |
| `audit_id` | `bigint` | no | PK |
| `logged_at` | `datetime2(0)` | no |  |
| `user_login` | `nvarchar(100)` | sí |  |
| `action_name` | `nvarchar(100)` | no |  |
| `entity_name` | `nvarchar(100)` | sí |  |
| `entity_id` | `nvarchar(100)` | sí |  |
| `detail` | `nvarchar(2000)` | sí |  |
