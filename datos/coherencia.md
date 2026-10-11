# Coherencia de Datos FraSoHome

Auditoria ejecutada sobre `datos` para asegurar que las demos pueden seguir un hilo común entre retail, People Analytics, RAG y Marketing Precision.

## Resultado Ejecutivo

- `retail_omnicanal` es el dominio operacional base: clientes, productos, tiendas, pedidos, tickets, pagos, devoluciones, stock y fact integrada.
- `marketing_precision` ya está incorporado desde los paquetes antiguos y enlaza mayoritariamente con retail por `customer_id`, `order_id`, `ticket_id`, `product_id` y `store_id`.
- `rag_copilot_studio` mantenía IDs propios para productos y tiendas. Se resolvió con crosswalks en `relaciones`.
- `people_analytics` no contiene comentarios que mencionen productos o ventas concretas; sí contiene ubicaciones y departamentos que ahora pueden mapearse a tiendas/canales cuando procede.
- Se conserva cierta incoherencia intencional para demos de data quality: clientes/pedidos/tickets/productos mal capturados, códigos cortos de tienda, valores `??`, IDs huerfanos y fuentes con granularidad distinta.

## Nuevos Dominios y Relaciones

Se añadió:

- `marketing_precision/raw_csv`: datasets operacionales de campañas, eventos, cupones, feedback, atención cliente, identidad, costes, afinidad local y creatividades.
- `relaciones/store_aliases.csv`: normaliza tiendas y ubicaciones.
- `relaciones/product_aliases_rag_to_retail.csv`: conecta productos RAG con catálogo retail.
- `relaciones/employee_store_assignment.csv`: conecta empleados con tienda/canal cuando la ubicación lo permite.
- `relaciones/employee_operational_aliases.csv`: permite cruzar cajeros POS (`EMP###`) con empleados People Analytics (`FSH####`) para demos.
- `relaciones/marketing_precision_operational_links.csv`: inventario de enlaces marketing-retail.
- `relaciones/coherence_check_summary.csv`: checks después de aplicar alias.

## Checks Relevantes Tras Alias

| Relación | Resultado |
| --- | --- |
| RAG productos `FSH-*` -> retail productos `P*` | 100% cubierto por `product_aliases_rag_to_retail.csv` |
| RAG tiendas `MAD01/BCN01/VLC01` -> retail tiendas | 100% cubierto por `store_aliases.csv` |
| Marketing contactos -> clientes retail | 100% |
| Marketing eventos web/app -> clientes, pedidos y productos retail | 100% |
| Marketing afinidad tienda-cliente -> clientes y tiendas | 100% tras alias |
| People empleados -> tiendas/canal retail | 52,68% asignable; el resto son sedes, contact center, ubicaciones corporativas o ciudades sin tienda retail directa |

## Brechas Conservadas a Propósito

- Algunos productos y clientes en retail están fuera de maestro para ejercicios de calidad.
- Algunos tickets/pedidos de marketing no existen en POS/ecommerce para demos de atribución incompleta y soporte.
- Algunas ubicaciones People Analytics no tienen tienda retail equivalente, porque representan sede, contact center o almacenes.
- Los alias `EMP###` -> `FSH####` son sintéticos para demostración, no un maestro HR oficial.

## Hilos de Demo Soportados

1. **Customer 360 / Marketing Precision:** CRM retail + identidad + eventos web/app + campañas + cupones + feedback.
2. **Next Best Action:** ventas retail + productos + stock + afinidad tienda + propensión/campañas.
3. **Voz de Cliente:** feedback/tickets + productos/pedidos/tiendas + políticas RAG.
4. **People Analytics y Operaciones:** empleados por ubicación + tiendas + cajeros POS + ventas por tienda.
5. **Copilot Studio RAG:** knowledge base + structured CSV + crosswalks para explicar tiendas/productos con el mismo universo retail.
