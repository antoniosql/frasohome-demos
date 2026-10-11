# Los problemas de datos

Los datos de FraSoHome están sucios **a propósito**. Cada error está ahí para que una demo tenga algo que descubrir, discutir o corregir. Esta página los reúne para que el presentador sepa qué va a encontrar.

## Silos

| Sistema | Lo que sabe | Lo que no sabe |
| --- | --- | --- |
| CRM | Quién es el cliente, su nivel y sus puntos | Qué compra en tienda si no se identifica |
| Ecommerce | Pedidos, líneas y devoluciones online | Si el cliente devolvió en tienda |
| TPV | Tickets, cajeros y pagos en tienda | Quién es el cliente en la mitad de los tickets |
| ERP | Productos, costes y stock diario | Qué se vende ni con qué margen real |
| Marketing | Campañas, contactos, cupones, navegación | Si la conversión se atribuye a la campaña |
| RR. HH. | Plantilla, clima, rotación, formación | En qué tienda del maestro retail trabaja cada persona |
| Base documental | Políticas, KPI y procedimientos | Qué versión está vigente si conviven dos |

## Calidad (retail omnicanal)

| Problema | Ejemplos |
| --- | --- |
| Duplicados de clave | Clientes, productos, pedidos, líneas, pagos, devoluciones, tiendas (`S003` y `S003 `) y snapshots de stock |
| Identificadores sin normalizar | `c0001` frente a `C0001`, `p1005`, espacios, `S03` frente a `S003` |
| Fechas heterogéneas | ISO, `dd/MM/yy`, `dd/MM/yyyy`, `2020/09/30` y texto (`10 de Enero de 2019`) |
| Importes mixtos | `€`, coma decimal, punto de miles, texto numérico |
| Integridad referencial incompleta | Ventas con clientes o productos que no existen en los maestros; devoluciones huérfanas |
| Lógica de negocio rota | Fechas futuras (2030, 2031), cantidades cero o negativas, stock negativo, costes negativos |
| Catálogos de valores sucios | Métodos de pago `CC`, `Visa/Mastercard`, `Vale`; niveles `Oro` y `Gold`; consentimientos `no`, `1`, `YES` |
| Descuadres | Pagos de ticket que no suman el importe del ticket |

El detalle por fichero está en el [perfil de datos retail](../escenarios/02-fabric-preparacion-datos/perfil-datos.md).

## Coherencia entre dominios

Los dominios se conectan mediante [tablas puente](../datos/relaciones/README.md), pero se conservan huecos para que las demos de calidad y atribución tengan sentido:

- Algunos productos y clientes de retail no están en los maestros.
- Algunos pedidos y tickets de marketing no existen en TPV ni ecommerce.
- RR. HH. tiene ubicaciones (sede, contact center, almacenes, ciudades sin tienda) que no corresponden a ninguna tienda retail: solo el 52,68 % de la plantilla se puede asignar a una tienda o canal.
- La base documental usa sus propios códigos (`MAD01`, `FSH-*`) que hay que traducir a los de retail (`S001`, `P*`).
- Los alias entre cajeros (`EMP###`) y empleados (`FSH####`) son sintéticos y solo sirven para la demo.

La auditoría completa está en [coherencia de datos](../datos/coherencia.md).

## Para qué sirve cada problema

| Problema | Demo que lo aprovecha |
| --- | --- |
| Duplicados, formatos y claves | [02 · Fabric](../escenarios/02-fabric-preparacion-datos/README.md) y [03 · SQL](../escenarios/03-sql-raw-core-analytics/README.md) |
| Clientes anónimos y omnicanalidad | [04 · Analítica de ventas](../escenarios/04-analitica-ventas-ml/README.md) y [05 · Marketing de precisión](../escenarios/05-marketing-precision/README.md) |
| Resolución de identidad | [05 · Marketing de precisión](../escenarios/05-marketing-precision/README.md) (notebook 09) |
| Maestro de empleados sucio | [06 · People Analytics](../escenarios/06-power-bi-people-analytics/README.md) |
| Documento obsoleto y documento malicioso | [07 · Copilot Studio](../escenarios/07-copilot-studio-rag/README.md) |
| Significado distinto para cosas parecidas | [08 · Fabric IQ](../escenarios/08-fabric-iq-ontologia/README.md) |
