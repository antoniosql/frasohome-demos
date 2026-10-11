# LAB 4 — Dataverse: crear tablas e importar datos estructurados (CSV)

Objetivo: crear las tablas en Dataverse a partir de los CSV del caso FraSoHome y dejar el entorno listo para que el agente consulte métricas en el LAB 5.

| Duración estimada | 75–120 min |
| --- | --- |
| Entregables | 1) 7 tablas creadas en Dataverse con datos cargados. 2) Verificación de recuento de filas por tabla. 3) (Opcional) relaciones lookup creadas entre tablas. |
| Prerrequisitos | Acceso al Maker Portal (make.powerapps.com) con permisos para crear tablas en Dataverse. Debes usar el MISMO entorno que tu agente de Copilot Studio. |

## Archivos que vas a usar

Ubicación en el pack: Datos_Estructurados/

| CSV | Tabla Dataverse (nombre recomendado) | Filas esperadas | Notas |
| --- | --- | --- | --- |
| FS_Tiendas.csv | FS Tiendas | 3 | Dimensión de tiendas. (StoreID, StoreName, City, Region) |
| FS_Productos.csv | FS Productos | 32 | Dimensión de productos. (ProductID, Category, precios) |
| FS_Clientes.csv | FS Clientes | 60 | Dimensión de clientes y consentimientos. |
| FS_VentasResumenDiario.csv | FS Ventas Resumen Diario | 204 | Hechos de ventas agregadas por día/canal/tienda. |
| FS_DevolucionesFact.csv | FS Devoluciones | 248 | Hechos de devoluciones (línea). |
| FS_StockDiario.csv | FS Stock Diario | 2295 | Inventario diario por tienda y producto (tabla grande). |
| FS_Alertas_Stockout.csv | FS Alertas Stockout | 15 | Alertas ya filtradas (tabla pequeña). |

## Paso a paso

### 0) Verifica el entorno (muy importante)

- Abre make.powerapps.com e inicia sesión.

- En la esquina superior derecha, selecciona el Environment (Entorno) del curso.

- Comprueba que es el MISMO entorno donde está tu agente de Copilot Studio (si no, cambiarás de base de datos y luego no podrás consultar).

### 1) Crear tablas desde archivos CSV (método recomendado)

Vamos a usar el método 'New table > Create with external data > File (Excel, .CSV)'.

- En el menú izquierdo del Maker Portal, entra en Tables (Tablas).

- En la barra superior, selecciona New table (Nueva tabla) > Create with external data (Crear con datos externos).

- Elige File (Excel, .CSV) / Archivo (Excel, .CSV).

- Arrastra y suelta el CSV o selecciona 'select from device' para cargarlo.

- Revisa la vista previa (verás solo las primeras ~20 filas).

- Si lo necesitas, ajusta nombres/tipos de columna: selecciona el encabezado de una columna > Edit column (Editar columna).

- Pulsa Create (Crear) para que Dataverse cree la tabla y termine de ingerir el dataset.

### 2) Repite la creación para los 7 CSV (orden recomendado)

Crea las tablas en este orden (dimensiones primero, hechos después):

- FS Tiendas  ←  FS_Tiendas.csv  (filas esperadas: 3)

- FS Productos  ←  FS_Productos.csv  (filas esperadas: 32)

- FS Clientes  ←  FS_Clientes.csv  (filas esperadas: 60)

- FS Ventas Resumen Diario  ←  FS_VentasResumenDiario.csv  (filas esperadas: 204)

- FS Devoluciones  ←  FS_DevolucionesFact.csv  (filas esperadas: 248)

- FS Stock Diario  ←  FS_StockDiario.csv  (filas esperadas: 2295)

- FS Alertas Stockout  ←  FS_Alertas_Stockout.csv  (filas esperadas: 15)

### 3) Checklist de tipos de datos (revísalo al menos en Ventas y Devoluciones)

Consejo: aunque el asistente funcione con columnas como texto, los filtros y cálculos son más fiables si fechas e importes tienen el tipo correcto.

| Tabla | Qué revisar |
| --- | --- |
| FS Ventas Resumen Diario | Date = Date only (Fecha), importes = Currency/Decimal, Orders = Whole number. |
| FS Devoluciones | ReturnDate = Date only, RefundAmountEUR = Currency/Decimal, Units = Whole number, Approved = Yes/No (si quieres). |
| FS Stock Diario | Date = Date only, unidades = Whole number. |

### 4) Verificar recuento de filas (control rápido)

- En Tables, abre una de las tablas (por ejemplo, FS Ventas Resumen Diario).

- Selecciona Data (Datos) o View data (Ver datos).

- Comprueba que hay registros y que el número de filas coincide aproximadamente con la tabla de 'Filas esperadas'.

- Repite para las 7 tablas. Si una tabla aparece vacía, espera 1–2 minutos y refresca; la ingesta puede tardar.

### (Opcional) 5) Crear relaciones Lookup entre tablas (mejor experiencia, no obligatorio)

Si tienes tiempo, crea relaciones para que Dataverse entienda que StoreID/ProductID/CustomerID apuntan a dimensiones. Esto facilita joins y reduce errores.

- Abre la tabla FS Devoluciones > Columns (Columnas) > New column (Nueva columna).

- Tipo de columna: Lookup (Búsqueda).

- Nombre sugerido: Store (o Tienda) y tabla relacionada: FS Tiendas.

- Repite para Product (FS Productos) y Customer (FS Clientes).

- En FS Ventas Resumen Diario y FS Stock Diario, crea también Lookup a FS Tiendas y a FS Productos si aplica.

## Checklist de entrega

- ✅ 7 tablas creadas en Dataverse usando los 7 CSV.

- ✅ Recuento de filas validado (aprox.): Tiendas=3, Productos=32, Clientes=60, Ventas=204, Devoluciones=248, Stock Diario=2295, Alertas=15.

- ✅ (Opcional) Lookups creados para Store/Product/Customer.