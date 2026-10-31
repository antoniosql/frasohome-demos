# Fase 2 · Modelo y carga inicial

Los CSV de [`datos/`](../../../datos/README.md) entran una vez en Azure SQL y Cosmos DB, limpios, y desde ahí la web los opera. Los CSV originales no se tocan: siguen siendo el material sucio de las demos de calidad de datos.

## Qué hay

| Carpeta o fichero | Contenido |
| --- | --- |
| [`../sql/00_borrar.sql`](../sql/00_borrar.sql) | Borra los objetos de datos para recrearlos. Conserva los usuarios de la web |
| [`../sql/01_core.sql`](../sql/01_core.sql) | Retail: clientes, catálogo, tiendas, pedidos, TPV, pagos, devoluciones, stock y `quality.data_quality_issue` |
| [`../sql/02_hr_mkt_fin_ref_xref.sql`](../sql/02_hr_mkt_fin_ref_xref.sql) | Personas, marketing, costes, tablas de referencia y puentes entre dominios |
| [`../sql/03_procedimientos.sql`](../sql/03_procedimientos.sql) | Transacciones de la web (fase 3). Se aplica el último porque usa objetos de 04 y 05 |
| [`../sql/04_app.sql`](../sql/04_app.sql) | Usuarios y sesiones propios, contadores de identificadores, outbox hacia Cosmos, idempotencia y auditoría |
| [`../sql/05_rag_meta_lab.sql`](../sql/05_rag_meta_lab.sql) | Semilla de Copilot Studio, metadatos fila a fila y material de laboratorio |
| [`limpieza.py`](limpieza.py) | Reglas de limpieza: fechas, importes, identificadores y valores de categoría |
| [`fuentes_sql.py`](fuentes_sql.py), [`fuentes_cosmos.py`](fuentes_cosmos.py) | De cada CSV a sus tablas o documentos |
| [`load_sql.py`](load_sql.py), [`load_cosmos.py`](load_cosmos.py) | Cargas, con resumen en `.local/frasohome-live/` |
| [`verify.py`](verify.py) | Cuadra filas del CSV − rechazos = filas en la base, fichero a fichero |
| [`reset.py`](reset.py) | Deja las bases como recién cargadas antes de una demo |
| [`cargar_datos.ps1`](cargar_datos.ps1) | Lo ejecuta todo contra Azure desde tu equipo |
| [`tests/`](tests/test_limpieza.py) | Pruebas de las reglas con los casos sucios reales |

El número 06 (vistas de exportación) queda libre para la fase 5. `load_sql.py --solo-procedimientos` vuelve a aplicar 03 sin tocar los datos.

## Cómo cargar

Requisitos: haber completado la [fase 1](../infra/README.md), Python 3.10 o superior y la sesión de `az`.

```powershell
cd escenarios\11-web-transaccional\seed
az login
.\cargar_datos.ps1
```

El script prepara un entorno de Python en `.local\frasohome-live\venv`, abre el firewall de SQL a tu IP (regla `equipo-carga`), toma la clave de Cosmos con tu sesión y la contraseña del administrador SQL de `.local\fase0\secretos.json`, y ejecuta las tres etapas. Las credenciales viajan en variables de entorno que se borran al terminar.

| Modo | Qué hace |
| --- | --- |
| `.\cargar_datos.ps1` | Crea el esquema si no existe y carga sobre bases vacías. Si ya hay datos, se detiene sin tocar nada |
| `.\cargar_datos.ps1 -Reiniciar` | Pide escribir `reiniciar`, borra todos los datos y vuelve a cargar. Los usuarios de la web se conservan y sus sesiones se cierran |
| `.\cargar_datos.ps1 -SoloVerificar` | Solo compara recuentos |

Tiempos y cuota esperados:

- **SQL:** unos 38.500 filas en una transacción, con un `INSERT … SELECT FROM OPENJSON` por cada 1.500 filas. En local tarda 5 segundos; en Azure, menos de un minuto, más lo que tarde la base en despertarse de la autopausa.
- **Cosmos DB:** 18.600 documentos. El ritmo se limita a 700 RU por segundo (`-RU`) para no pasar de las 1.000 gratuitas que comparten los 9 contenedores; cuenta con unos 5 a 10 minutos.
- Después, cierra las herramientas conectadas a SQL para que la base se pause a la hora.

## Dónde va cada CSV

| | Ficheros | Cómo |
| --- | --- | --- |
| Azure SQL, datos que opera la web | 27 | Tablas tipadas con nombres en inglés (`crm.customer`, `sales.pos_ticket`, `hr.employee`…) |
| Azure SQL, semillas y referencia | 23 | Costes, afinidad, calendario, people analytics, rotación, Copilot Studio (`rag.*`), laboratorio (`lab.*`) y 7 ficheros de metadatos en `meta.reference_row` |
| Cosmos DB | 8 | Un documento por fila, plano, con los nombres de columna del CSV |
| Se recalculan en la exportación (fase 5) | 6 | `fact_transacciones`, comentarios de clima y de salida, validaciones, coherencia y `catalogo-datos.csv` |

`ventas_pos.csv` se separa en cabecera (`sales.pos_ticket`) y líneas, y las dos devoluciones en `returns.return_header` y `return_line`. La última foto de `stock_diario.csv` de cada tienda y producto inicia el stock vivo (`inventory.stock_level`). El cajero del TPV conserva su código (`EMP049`) y además se guarda el empleado al que corresponde (`FSH0040`) según `employee_operational_aliases.csv`.

## Reglas de limpieza

Son las del notebook 3 del [escenario 02](../../02-fabric-preparacion-datos/README.md), ampliadas a marketing y personas. Cada decisión queda en `quality.data_quality_issue` con la fila original en JSON:

| Gravedad | Cuándo | Ejemplos |
| --- | --- | --- |
| `rechazo` | La fila no entra | Duplicado exacto o de clave, cantidad cero o negativa, línea de un pedido que no existe, pago negativo (devolución mal registrada), empleado con fecha de alta imposible |
| `corregido` | Entra con el valor arreglado | `c0077` → `C0077`, `SKU-1019` → `P1019`, `500031` → `T-500031`, `EM070` → `EMP070`, importe negativo en valor absoluto, fecha futura o porcentaje fuera de rango a vacío |
| `aviso` | Entra, pero hay algo que revisar | Cliente `GUEST` o que no está en el CRM (venta de invitado), producto `P101Z` irreconocible, código postal de 4 cifras |

Resultado con los CSV actuales: 306 rechazos, unas 2.500 correcciones y 485 avisos. Los empleados limpios coinciden campo a campo con `frasohome_people_analytics.csv` (departamento, ubicación, rol, nivel, contrato, jornada, estado, salida, fechas).

Para verlas:

```sql
SELECT source_table, issue_severity, issue_type, COUNT(*) AS filas
FROM quality.data_quality_issue
GROUP BY source_table, issue_severity, issue_type
ORDER BY source_table, filas DESC;
```

## Comprobado en local

Con SQL Server 2022 y el emulador de Cosmos DB en Docker:

| Comprobación | Resultado |
| --- | --- |
| `load_sql.py --recrear` | 38.523 filas en 4,5 s, con `mssql-python` y también con `pyodbc` |
| `load_cosmos.py --recrear` | 18.599 documentos |
| `verify.py` | Los 58 ficheros guardados cuadran; con los 6 recalculados suman los 64 de `datos/` |
| Recuentos de `catalogo-datos.csv` | Coinciden con los CSV |
| Volver a cargar sin `--recrear` | Se detiene sin tocar nada |
| `reset.py` | Recarga todo y conserva un usuario de la web con su rol y su ámbito |
| `cargar_datos.ps1` en sus tres modos (con `az` simulado) | Correcto |
| `pytest tests` | 62 pruebas de limpieza correctas |

## Cambios respecto al plan

- **Procedimientos y vistas, a su fase.** Los procedimientos de las transacciones (`03`) se prueban con la API en la fase 3, y las vistas de exportación (`06`) con el script de exportación en la fase 5.
- **Las métricas de las creatividades se guardan.** El plan las recalculaba, pero los eventos de campaña no dicen qué creatividad se envió: `open_rate`, `ctr`, `cvr` y `revenue_por_1000_envios_eur` quedan en cada documento como históricas.
- **Más ficheros guardados que recalculados.** La afinidad cliente-tienda, la muestra de prompts y las alertas de rotura de Copilot Studio se guardan como semilla, porque no se pueden reconstruir igual desde lo operado.
- **Fechas en `DATETIME2(0)` en vez de `(3)`.** Los datos llegan al segundo, y se sigue evitando `datetime2(7)` por el mirroring futuro a Fabric.
