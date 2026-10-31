# Datos en vivo: modelo y conexión

Guía para crear **demos adicionales** que lean los datos de FraSoHome Live: qué hay en Azure SQL y en Cosmos DB, cómo se relacionan, cómo conectarse con seguridad y qué ejemplos de uso funcionan. Todo lo que aquí se describe es de **solo lectura**: las demos no deben escribir en las bases, porque quien escribe es la web (con sus reglas, procedimientos y auditoría).

## Qué hay y dónde

| | Azure SQL Database | Azure Cosmos DB |
| --- | --- | --- |
| Base | `frasohome-oltp` (oferta gratuita, se pausa sola) | `frasohome` (free tier, 1.000 RU/s compartidas) |
| Contenido | 59 tablas en 16 esquemas | 9 contenedores, clave de partición `/pk` |
| Volumen tras la carga inicial | 41.441 filas en 47 tablas (el resto empieza vacío) | 18.599 documentos |
| Qué guarda | Lo que debe cuadrar: clientes, catálogo, ventas, stock, devoluciones, campañas, personas y la aplicación | Lo que cambia de forma o de ritmo: eventos de navegación, opiniones, casos de atención, señales de identidad, creatividades, clima y entrevistas de salida |
| Modelo | Relacional, con claves foráneas | Documentos planos |

Los datos de la carga inicial salen de los CSV de [`datos/`](../../datos/README.md), limpios (lo corregido o rechazado queda en `quality.data_quality_issue`). Cuanto se opere después en la web se suma con fechas de 2026.

## Diagramas

### SQL

| Diagrama | Contenido |
| --- | --- |
| [Ventas](../../diagramas/datos-sql-ventas.drawio.svg) | Clientes, productos, tiendas, pedidos online, tickets, cobros y cajas |
| [Devoluciones e inventario](../../diagramas/datos-sql-devoluciones-inventario.drawio.svg) | Devoluciones, stock vivo, foto diaria y movimientos |
| [Personas](../../diagramas/datos-sql-personas.drawio.svg) | Plantilla, movimientos, ausencias, horas extra, formación, evaluaciones y salario |
| [Marketing](../../diagramas/datos-sql-marketing.drawio.svg) | Campañas, contactos, cupones, promociones, afinidad y costes |
| [Aplicación](../../diagramas/datos-sql-aplicacion.drawio.svg) | Usuarios, sesiones, outbox, idempotencia y auditoría |
| [Referencia, RAG, metadatos y laboratorio](../../diagramas/datos-sql-referencia.drawio.svg) | Tablas de apoyo |

[![Ventas](../../diagramas/datos-sql-ventas.drawio.svg)](../../diagramas/datos-sql-ventas.drawio.svg)

Las columnas completas de cada tabla están en la [referencia del esquema SQL](referencia-sql.md).

### Cosmos DB

[![Contenedores de Cosmos DB](../../diagramas/datos-cosmos.drawio.svg)](../../diagramas/datos-cosmos.drawio.svg)

### Cómo conectar

[![Cómo conectar](../../diagramas/datos-conexion.drawio.svg)](../../diagramas/datos-conexion.drawio.svg)

## Cómo se unen SQL y Cosmos

No hay claves foráneas entre las dos bases, pero los campos se corresponden. Con esta tabla se pueden unir en pandas o en Power BI:

| Contenedor de Cosmos | Campo | Tabla y columna de SQL |
| --- | --- | --- |
| `carritos` | `customer_id`; `lineas[].product_id` | `crm.customer.customer_id`; `catalog.product.product_id` |
| `eventos_web` | `customer_id`, `product_id`, `order_id` | `crm.customer`, `catalog.product`, `sales.online_order.order_id` |
| `feedback` | `customer_id`, `order_id`, `product_id` | `crm.customer`, `sales.online_order`, `catalog.product` |
| `atencion_cliente` | `customer_id`, `order_id`, `store_id` | `crm.customer`, `sales.online_order`, `store.store.store_id` |
| `senales_identidad` | `customer_id_candidato` (o `SIN_CLIENTE`), `store_id` | `crm.customer`, `store.store` |
| `eventos_campana` | `campaign_id`, `customer_id`, `contact_id` | `mkt.campaign.campaign_id`, `crm.customer`, `mkt.campaign_contact.contact_id` |
| `creatividades` | `campaign_id` | `mkt.campaign` |
| `encuesta_clima` | `employee_id` | `hr.employee.employee_id` |
| `entrevistas_salida` | `employee_id` | `hr.employee` |

## Convenciones

### Identificadores

| Entidad | Formato | Ejemplo |
| --- | --- | --- |
| Cliente | `C` y 4 dígitos | `C0017` |
| Producto | `P` y 4 dígitos | `P1020` |
| Tienda | `S` y 3 dígitos, o `ONLINE` | `S001` |
| Pedido online y su línea | `O-` y 9 dígitos · `OL-` y 7 | `O-202600001` |
| Ticket y su línea | `T-` y 6 dígitos · `TL-` y 6 | `T-501200` |
| Devolución | `RO-AAAA-nnnnn` (online) o `RT-AAAA-nnnnn` (tienda) | `RO-2026-00001` |
| Caja | `CAJ` y 2 dígitos | `CAJ01` |
| Empleado | `FSH` y 4 dígitos | `FSH0002` |
| Campaña | `CAM-AAAA-nnn` | `CAM-2026-001` |
| Promoción | `PROMO-nnnn` | `PROMO-0001` |
| Cupón (código) | `FSH` y 8 dígitos | `FSH20260001` |

### Fechas, estados y origen

- **Fechas y horas en UTC**, `datetime2` sin zona. En Cosmos, cadenas ISO (`2026-10-31T08:45:00`).
- **Estados habituales**
  - Pedido: `Pendiente`, `En preparación`, `Entregado`, `Cancelado`, `Devuelto Parcial`, `Devuelto Total`.
  - Devolución: `Pendiente`, `Aceptada`, `Rechazada`, `Reembolsada`.
  - Campaña: `borrador`, `audiencia`, `activa`, `finalizada`, `cancelada`.
  - Cupón: `emitido`, `canjeado`, `expirado`, `anulado`.
  - Empleado: `Activo`, `Baja`.
- **Dato de carga o dato de la web.** En Cosmos, el campo `origen` es `carga_inicial` o `web`. En SQL, `hr.employee.source_row_id` vale `WEB` para los empleados dados de alta en la aplicación, y los pedidos, tickets y devoluciones nuevos llevan fechas de 2026. Úsalo para separar la fotografía de 2024–2025 de lo operado después.
- **Datos sintéticos.** Los nombres, correos y salarios no son reales. En las señales de identidad (`senales_identidad`), el correo y el teléfono están como hash.

## Conectar con Azure SQL

### 1. Datos de conexión

Los valores reales no se publican en el repositorio. En la instalación donde se desplegó la web están en `.local\frasohome-live\estado.json` (Git lo ignora): `sqlServerFqdn`, `cosmosEndpoint`, `cosmosAccountName` y `resourceGroup`. También se consultan con `az sql server list` y `az cosmosdb list`.

```powershell
$e = Get-Content .local\frasohome-live\estado.json -Raw | ConvertFrom-Json
$e.sqlServerFqdn      # sql-frasohome-xxxx.database.windows.net
$e.cosmosEndpoint     # https://cosmos-frasohome-xxxx.documents.azure.com:443/
```

### 2. Abrir el firewall

El servidor deja entrar a los servicios de Azure (regla `AllowAllWindowsAzureIps`, la que usan Functions, Power BI Service o Fabric). Desde tu equipo hay que añadir tu IP pública:

```powershell
az sql server firewall-rule create -g rg-frasohome-live -s <servidor> -n mi-equipo `
  --start-ip-address <tu-ip> --end-ip-address <tu-ip>
# al terminar:
az sql server firewall-rule delete -g rg-frasohome-live -s <servidor> -n mi-equipo
```

### 3. Crear un usuario de solo lectura

No uses el administrador ni `fsh_api` (este escribe, por procedimientos). Crea un usuario de lectura **dentro de la base `frasohome-oltp`** (no en `master`), conectado como administrador. Excluye el esquema `app`, que tiene hashes de contraseñas y sesiones, y la solución del ejercicio de identidad:

```sql
CREATE USER fsh_demo WITH PASSWORD = '<contraseña de 16 caracteres o más>';
CREATE ROLE demo_lectura;

GRANT SELECT ON SCHEMA::crm       TO demo_lectura;
GRANT SELECT ON SCHEMA::catalog   TO demo_lectura;
GRANT SELECT ON SCHEMA::store     TO demo_lectura;
GRANT SELECT ON SCHEMA::sales     TO demo_lectura;
GRANT SELECT ON SCHEMA::[returns] TO demo_lectura;
GRANT SELECT ON SCHEMA::inventory TO demo_lectura;
GRANT SELECT ON SCHEMA::mkt       TO demo_lectura;
GRANT SELECT ON SCHEMA::fin       TO demo_lectura;
GRANT SELECT ON SCHEMA::hr        TO demo_lectura;
GRANT SELECT ON SCHEMA::ref       TO demo_lectura;
GRANT SELECT ON SCHEMA::xref      TO demo_lectura;
GRANT SELECT ON SCHEMA::rag       TO demo_lectura;
GRANT SELECT ON SCHEMA::meta      TO demo_lectura;
GRANT SELECT ON SCHEMA::lab       TO demo_lectura;
GRANT SELECT ON SCHEMA::quality   TO demo_lectura;

DENY SELECT ON OBJECT::lab.identity_ground_truth TO demo_lectura;   -- la solución del ejercicio
-- DENY SELECT ON OBJECT::hr.compensation TO demo_lectura;          -- si no quieres exponer salarios

ALTER ROLE demo_lectura ADD MEMBER fsh_demo;
```

Para retirarlo: `DROP USER fsh_demo;`. Guarda la contraseña en un gestor de secretos o en una variable de entorno, nunca en el código.

Con una identidad Microsoft Entra también vale: el servidor tiene un administrador Entra y se puede conectar con `sqlcmd -G` o con la autenticación de Entra de VS Code y Power BI.

### 4. Cadena de conexión

```
Server=tcp:<servidor>.database.windows.net,1433;Database=frasohome-oltp;UID=fsh_demo;PWD=<contraseña>;
Encrypt=yes;TrustServerCertificate=no;ConnectRetryCount=3;ConnectRetryInterval=10
```

- **La primera conexión puede tardar uno o dos minutos**: la base gratuita se pausa sola y la conexión la despierta. `ConnectRetryCount` y `ConnectRetryInterval` hacen que el driver espere en vez de fallar.
- **`mssql-python` no admite `Connection Timeout`** en la cadena; usa los dos parámetros de reintento de arriba, válidos también para `pyodbc` con ODBC Driver 18.
- Puerto 1433 y TLS obligatorio.

### 5. Ejemplos

**Python con pandas y `pyodbc`:**

```python
import os, pandas as pd, pyodbc

cs = ("Driver={ODBC Driver 18 for SQL Server};"
      f"Server=tcp:{os.environ['FSH_SQL_SERVER']},1433;Database=frasohome-oltp;"
      f"UID=fsh_demo;PWD={os.environ['FSH_SQL_PASSWORD']};"
      "Encrypt=yes;TrustServerCertificate=no;ConnectRetryCount=3;ConnectRetryInterval=10")
with pyodbc.connect(cs) as conn:
    ventas = pd.read_sql("""
        SELECT FORMAT(ordered_at, 'yyyy-MM') AS mes, SUM(order_total - ISNULL(shipping_amount, 0)) AS online
        FROM sales.online_order WHERE order_status <> N'Cancelado' GROUP BY FORMAT(ordered_at, 'yyyy-MM') ORDER BY mes""", conn)
print(ventas.tail())
```

**`sqlcmd`:** `sqlcmd -S tcp:<servidor>.database.windows.net,1433 -d frasohome-oltp -U fsh_demo -P "$env:FSH_SQL_PASSWORD" -N -Q "SELECT COUNT(*) FROM sales.pos_ticket"`

**Power BI Desktop y Excel:** *Obtener datos → Azure SQL Database*, con el servidor, la base `frasohome-oltp` y autenticación de base de datos con `fsh_demo`. Importa tablas concretas en lugar de usar DirectQuery sobre todo el modelo: cada visual despierta la base y gasta cuota.

**VS Code:** extensión *SQL Server (mssql)* con la misma cadena. Cierra la conexión al terminar.

### Consultas de partida

```sql
-- Ventas netas por mes y canal
SELECT FORMAT(ordered_at, 'yyyy-MM') AS mes, N'online' AS canal, SUM(order_total - ISNULL(shipping_amount, 0)) AS ventas
FROM sales.online_order WHERE order_status <> N'Cancelado' GROUP BY FORMAT(ordered_at, 'yyyy-MM')
UNION ALL
SELECT FORMAT(ticket_at, 'yyyy-MM'), N'tienda', SUM(ticket_net_amount) FROM sales.pos_ticket GROUP BY FORMAT(ticket_at, 'yyyy-MM')
ORDER BY mes, canal;

-- Productos con el stock por debajo del mínimo en cada tienda
SELECT s.store_id, st.store_name, p.product_id, p.product_name, s.on_hand_qty - s.reserved_qty AS disponible, s.minimum_qty
FROM inventory.stock_level s
JOIN catalog.product p ON p.product_id = s.product_id
JOIN store.store st ON st.store_id = s.store_id
WHERE s.on_hand_qty - s.reserved_qty <= s.minimum_qty
ORDER BY disponible;

-- Efecto de una campaña: conversión de tratamiento frente a control
SELECT experiment_group, COUNT(*) AS contactos, SUM(CASE WHEN conversion_30d = 1 THEN 1 ELSE 0 END) AS conversiones,
       SUM(revenue_30d_eur) AS ingresos
FROM mkt.campaign_contact WHERE campaign_id = 'CAM-2026-001' GROUP BY experiment_group;

-- Rotación mensual por departamento (histórico)
SELECT periodo_mes, departamento, tasa_rotacion_total_pct FROM hr.turnover_monthly_seed ORDER BY periodo_mes, departamento;
```

## Conectar con Cosmos DB

### 1. Clave de solo lectura

La cuenta tiene una clave de solo lectura aparte de las de escritura. Con ella una demo puede consultar pero no escribir:

```powershell
$e = Get-Content .local\frasohome-live\estado.json -Raw | ConvertFrom-Json
$env:COSMOS_ENDPOINT = $e.cosmosEndpoint
$env:COSMOS_KEY = az cosmosdb keys list -g $e.resourceGroup -n $e.cosmosAccountName --type read-only-keys --query primaryReadonlyMasterKey -o tsv
```

No pegues la clave en notebooks ni en el repositorio. La cuenta admite conexiones públicas con esa clave, sin regla de IP.

### 2. Ejemplo en Python

```python
import os
from azure.cosmos import CosmosClient

cli = CosmosClient(os.environ["COSMOS_ENDPOINT"], credential=os.environ["COSMOS_KEY"])
feedback = cli.get_database_client("frasohome").get_container_client("feedback")

# Con la clave de partición (cliente): barato, una sola partición
mias = list(feedback.query_items("SELECT c.feedback_id, c.rating_1_5, c.texto_feedback FROM c",
                                 partition_key="C0017"))

# Entre particiones: úsalo con medida
negativas = list(feedback.query_items("SELECT VALUE COUNT(1) FROM c WHERE c.sentimiento = 'Negativo'",
                                      enable_cross_partition_query=True))
```

`pip install azure-cosmos`. También sirve el **Data Explorer** del portal de Azure para explorar y probar consultas.

### 3. Claves de partición y coste

| Contenedor | `/pk` contiene |
| --- | --- |
| `eventos_web` | `session_id` |
| `eventos_campana`, `creatividades` | `campaign_id` |
| `feedback`, `atencion_cliente`, `carritos` | `customer_id` |
| `senales_identidad` | `customer_id` asignado, o `SIN_CLIENTE` |
| `encuesta_clima`, `entrevistas_salida` | `employee_id` |

- La cuenta tiene **1.000 RU/s compartidas** con la propia web. Una consulta entre particiones sobre `eventos_web` (9.030 documentos) puede costar cientos de RU; hazla una vez y guarda el resultado en un DataFrame.
- Filtra por la clave de partición cuando puedas y proyecta solo los campos que necesitas (`SELECT c.campo …` en lugar de `SELECT *`).
- Si ves errores `429`, espera: es la cuota, no un fallo.

### Consultas de partida

```sql
-- eventos_web: embudo de navegación
SELECT c.tipo_evento, COUNT(1) AS n FROM c GROUP BY c.tipo_evento

-- feedback: sentimiento por tema (publicado)
SELECT c.tema_principal, c.sentimiento, COUNT(1) AS n FROM c WHERE c.publicado_flag = true GROUP BY c.tema_principal, c.sentimiento

-- atencion_cliente: casos de un cliente con su conversación (va anidada)
SELECT c.service_ticket_id, c.prioridad, c.estado_resolucion, c.conversacion FROM c WHERE c.customer_id = 'C0017'
```

## Unir las dos bases

Un Customer 360 con pedidos de SQL y opiniones de Cosmos:

```python
import os, pandas as pd, pyodbc
from azure.cosmos import CosmosClient

cliente = "C0017"
with pyodbc.connect(cs) as conn:                       # cs: cadena de SQL, como arriba
    pedidos = pd.read_sql("SELECT order_id, ordered_at, order_total, order_status FROM sales.online_order WHERE customer_id = ?", conn, params=[cliente])

cos = CosmosClient(os.environ["COSMOS_ENDPOINT"], credential=os.environ["COSMOS_KEY"]).get_database_client("frasohome")
opiniones = pd.DataFrame(cos.get_container_client("feedback").query_items(
    "SELECT c.feedback_id, c.order_id, c.rating_1_5, c.sentimiento FROM c", partition_key=cliente))

print(pedidos.merge(opiniones, on="order_id", how="left"))   # order_id es la clave que une las dos bases
```

## Ideas de demos adicionales

| Idea | Datos | Qué enseña |
| --- | --- | --- |
| Cuadro de mando de ventas y stock en Power BI | `sales`, `inventory`, `catalog`, `store` | Modelo en estrella sobre datos que cambian |
| Notebook de Customer 360 | `crm`, `sales`, `returns`, `mkt` en SQL; `feedback` y `atencion_cliente` en Cosmos | Unir dos bases por clave de negocio |
| Análisis de opiniones con IA | `feedback` (texto, sentimiento, tema) | Clasificación y resumen de texto libre |
| Agente de texto a SQL | Esquemas de negocio con el usuario `fsh_demo` | Gobierno: un agente solo con permisos de lectura |
| Aplicación Streamlit de seguimiento de campañas | `mkt.*` y `eventos_campana` | Uplift y atribución en vivo |
| Detección de anomalías en la navegación | `eventos_web` | Series de eventos y umbrales |
| Rotación y riesgo de abandono | `hr.*` y `encuesta_clima` | People Analytics con datos que cambian |
| Mirroring a Fabric (futuro) | Todo SQL y Cosmos | El modelo se diseñó con tipos y reglas compatibles: `datetime2`, sin columnas calculadas, JSON como `nvarchar(max)` |

## Cuidados

- **Solo lectura.** Si una demo necesita crear algo, hazlo en su propia base o en un lakehouse. No escribas en estas bases: perderías las reglas de negocio y la auditoría.
- **Cuota.** SQL gratuita: 100.000 segundos de vCore al mes. Una conexión abierta impide la pausa. Cierra herramientas, evita refrescos automáticos y no dejes un notebook con la conexión viva.
- **No compartas credenciales.** Ni en el repositorio, ni en capturas, ni en notebooks publicados.
- **Datos que cambian.** Los recuentos de este documento son los de la carga inicial. Quien opere la web los modifica; si necesitas resultados estables, exporta una fotografía y trabaja sobre ella. La exportación a los mismos CSV de `datos/` es la fase 5 del [escenario 11](README.md) y todavía no está construida.
- **Esquema `app`.** No se concede lectura: tiene hashes de contraseñas, sesiones y la cola de eventos.
