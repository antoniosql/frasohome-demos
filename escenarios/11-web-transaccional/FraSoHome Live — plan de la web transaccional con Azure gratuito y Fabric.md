# FraSoHome Live — plan de la web transaccional con servicios gratuitos de Azure

Oct 17, 2026 · @Antonio Soto

## Resumen y decisiones clave

FraSoHome Live es una web en **frasohome.dataging.com** que cubre en 16 escenarios toda la operación de FraSoHome: venta online y en tienda, devoluciones, stock, CRM, gestión de campañas, promociones, soporte, voz del cliente y RR. HH. **Azure SQL y Cosmos DB son la única fuente de verdad**: los 64 CSV se cargan una vez y, a partir de ahí, un script los regenera desde las bases con el mismo formato para el resto de escenarios. Todo en niveles gratuitos de Azure, con usuarios y contraseñas propios. La carga en Fabric queda para después.

Decisiones que tomo en este plan:

1. **Hosting**: Azure Static Web Apps (plan Free) con API en *managed Functions* en Python 3.11. Sin App Service ni contenedores.
2. **Reparto de datos por naturaleza, no por dominio**: lo que mueve dinero, stock o requiere integridad (pedidos, tickets, pagos, cupones, empleados) va a **Azure SQL**; lo que es evento, texto libre o documento de esquema flexible (clics, feedback, casos de soporte, encuestas, creatividades, carritos) va a **Cosmos DB**.
3. **Los 64 CSV viven en las bases**: 35 como datos que la web opera (27 en SQL y 8 en Cosmos) y 29 como vistas, tablas de referencia o de laboratorio que se recalculan desde lo operado.
4. **Exportación a CSV con contrato**: `tools/export_csv.py` regenera los 64 ficheros con las mismas rutas, columnas y orden que `datos/`, para que los escenarios 02–10 (y Fabric después) funcionen sin cambios sobre datos vivos.
5. **Autenticación propia**: usuarios creados a mano con un script, contraseñas con `scrypt`, sesiones en SQL. Sin GitHub, Microsoft ni ningún proveedor externo.
6. **Base operacional limpia, suciedad preservada**: la carga inicial pasa los CSV por las reglas de limpieza del escenario 02 y registra cada rechazo en `quality.data_quality_issue`. Los CSV originales quedan congelados en `datos/` para las demos de calidad.
7. **Se reutiliza el esquema core del escenario 03** (`01_FraSoHome_Core.sql`), ampliado con `hr`, `mkt`, `fin`, `ref`, `xref`, `rag`, `meta`, `lab`, `exp` y `app`.
8. **Diseño compatible con la fase analítica**: tipos y patrones que el mirroring de Fabric admite, para no rehacer el modelo cuando llegue.

## Arquitectura

Tres servicios gratuitos de Azure: el navegador habla con Static Web Apps, y la API escribe en SQL o en Cosmos según la naturaleza del dato.

&#91;embedded content: arquitectura operacional · servicios gratuitos de Azure\]

Toda escritura pasa por la API, también la del generador de tráfico; solo la carga inicial y la exportación hablan directamente con las bases.

| Componente | Plan | Límite gratuito | Uso en FraSoHome Live |
| --- | --- | --- | --- |
| [Azure Static Web Apps](https://learn.microsoft.com/en-us/azure/static-web-apps/plans) | Free | 2 dominios propios por app, SSL automático, 250 MB, solo *managed Functions* HTTP (Python hasta 3.11, sin identidad administrada), sin SLA; sus proveedores de autenticación integrados no se usan y se bloquean | Web + API Python con login propio; `frasohome.dataging.com` por CNAME |
| [Azure SQL Database](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer) | Oferta gratuita (serverless General Purpose) | 100.000 s de vCore, 32 GB de datos y 32 GB de copias al mes por base; hasta 10 bases por suscripción; región fija para todas | Base `frasohome-oltp`, comportamiento «Auto-pause until next month» |
| [Azure Cosmos DB for NoSQL](https://learn.microsoft.com/en-us/azure/cosmos-db/free-tier) | Free tier (solo al crear la cuenta; no admite serverless) | 1.000 RU/s y 25 GB; una cuenta por suscripción; base compartida de hasta 25 contenedores | Base `frasohome` con 9 contenedores a 1.000 RU/s compartidas |
| GitHub Actions | Repo público | Gratis | Despliegue de SWA y Bicep |
| DNS de dataging.com | El proveedor actual | Sin coste añadido | Registro CNAME `frasohome` hacia la SWA |

La suscripción MSDN (grupo `Demos`) sirve: la oferta SQL admite cualquier tipo de suscripción. Recomiendo un grupo de recursos propio, `rg-frasohome-live`, y un servidor lógico nuevo con identidad administrada del sistema y administrador Entra, sin reutilizar los inicios de sesión SQL de demos anteriores.

## Mapa de datos: dónde va cada CSV

Los 64 CSV de `datos/` entran en las bases y ninguno se queda solo en el repo: 35 como datos que la web opera y 29 como vistas o tablas de referencia que se recalculan desde lo operado. El volumen total ronda los 10 MB, así que ni los 32 GB de SQL ni los 25 GB de Cosmos son una restricción; lo escaso es el cómputo (segundos de vCore y RU/s).

Criterio: la web **opera** lo que es una entidad o un evento de negocio. Lo que es un cálculo (KPI, agregados, scores) no se guarda dos veces: es una vista o lo calcula el script de exportación, así nunca contradice a los datos operados.

**Se operan (35 CSV + 1 contenedor nuevo)**

| Dominio | CSV | Destino | Tabla o contenedor | Qué hace la web |
| --- | --- | --- | --- | --- |
| Retail | `crm.csv` | Azure SQL | `crm.customer` | Alta y edición de clientes, puntos, consentimientos |
| Retail | `productos.csv` | Azure SQL | `catalog.product` | Mantenimiento del catálogo y precios |
| Retail | `tiendas.csv` | Azure SQL | `store.store` | Consulta; edición solo admin |
| Retail | `pedidos.csv` | Azure SQL | `sales.online_order` | Checkout de la tienda online, cambio de estado |
| Retail | `lineas_pedido.csv` | Azure SQL | `sales.online_order_line` | Líneas del checkout |
| Retail | `ventas_pos.csv` | Azure SQL | `sales.pos_ticket` + `sales.pos_ticket_line` | TPV: ticket con líneas (se separa cabecera y línea) |
| Retail | `pagos_tienda.csv` | Azure SQL | `sales.store_payment` | Cobro del ticket, pagos mixtos |
| Retail | `devoluciones_online.csv` | Azure SQL | `returns.return_header` + `return_line` | Devolución de un pedido online |
| Retail | `devoluciones_tienda.csv` | Azure SQL | `returns.return_header` + `return_line` | Devolución en tienda, también de compra online |
| Retail | `stock_diario.csv` | Azure SQL | `inventory.stock_snapshot` (histórico) + `inventory.stock_level` y `stock_movement` (nuevos) | Cada venta, devolución o ajuste mueve stock; el cierre diario genera la foto |
| Marketing | `campanas_marketing.csv` | Azure SQL | `mkt.campaign` (solo definición) | Crear y lanzar campañas |
| Marketing | `contactos_campana.csv` | Azure SQL | `mkt.campaign_contact` | Asignar audiencia y grupo de control |
| Marketing | `cupones_clientes.csv` | Azure SQL | `mkt.coupon` | Emitir cupones y canjearlos en el checkout o el TPV |
| Marketing | `promociones_calendario.csv` | Azure SQL | `mkt.promotion` | Calendario de promociones aplicado al precio |
| Marketing | `guardrails_marca_genai.csv` | Azure SQL | `ref.brand_guardrail` | Reglas que valida el editor de creatividades |
| People | `raw_hris_empleados.csv` | Azure SQL | `hr.employee` | Altas, bajas y datos de empleado |
| People | `raw_movimientos_personal.csv` | Azure SQL | `hr.employee_movement` | Promociones y traslados |
| People | `raw_absentismo.csv` | Azure SQL | `hr.absence` | Registro de ausencias |
| People | `raw_horas_extra.csv` | Azure SQL | `hr.overtime` | Solicitud y aprobación de horas extra |
| People | `raw_formacion.csv` | Azure SQL | `hr.training` | Inscripción y cierre de cursos |
| People | `raw_evaluaciones_desempeno.csv` | Azure SQL | `hr.performance_review` | Evaluación anual |
| People | `raw_salarios_beneficios.csv` | Azure SQL | `hr.compensation` | Revisión salarial (solo rol RR. HH.) |
| People | `dim_departamentos_mapeo.csv` | Azure SQL | `ref.department_map` | Normaliza departamentos al dar de alta |
| Relaciones | `store_aliases.csv` | Azure SQL | `xref.store_alias` | Resuelve códigos de tienda cortos |
| Relaciones | `product_aliases_rag_to_retail.csv` | Azure SQL | `xref.product_alias` | Enlaza productos `FSH-*` con `P*` |
| Relaciones | `employee_operational_aliases.csv` | Azure SQL | `xref.employee_alias` | Cajero `EMP###` del TPV ↔ empleado `FSH####` |
| Relaciones | `employee_store_assignment.csv` | Azure SQL | `xref.employee_store` | Qué tiendas puede operar cada empleado |
| Marketing | `eventos_web_app.csv` | Cosmos DB | `eventos_web` (pk `/sessionId`) | Cada vista, búsqueda, carrito y compra de la tienda online |
| Marketing | `eventos_campana.csv` | Cosmos DB | `eventos_campana` (pk `/campaignId`) | Entrega, apertura, clic, canje |
| Marketing | `identidades_cliente.csv` | Cosmos DB | `senales_identidad` (pk `/customerId`) | Señal por login, tarjeta de fidelización o compra |
| Marketing | `feedback_clientes.csv` | Cosmos DB | `feedback` (pk `/customerId`) | Reseñas y NPS tras la compra |
| Marketing | `tickets_atencion_cliente.csv` | Cosmos DB | `atencion_cliente` (pk `/customerId`) | Casos de soporte con conversación |
| Marketing | `creatividades_segmento.csv` | Cosmos DB | `creatividades` (pk `/campaignId`) | Editor de copys por microsegmento |
| People | `raw_encuesta_clima_respuestas.csv` | Cosmos DB | `encuesta_clima` (pk `/employeeId`) | Formulario de encuesta de clima |
| People | `raw_exit_interviews.csv` | Cosmos DB | `entrevistas_salida` (pk `/employeeId`) | Entrevista al registrar una baja |
| — | (nuevo, sin CSV) | Cosmos DB | `carritos` (pk `/customerId`) | Carrito vivo; se borra al pagar o abandonar |

Campos derivados dentro de CSV operados (`conversion_30d_flag`, `revenue_30d_eur`, `cnt_*` de campañas, métricas de creatividades) no se guardan: los calcula la exportación a partir de contactos, eventos y pedidos.

**Se recalculan o son referencia (29 CSV)**

| CSV | Cómo vive en la base | Quién lo usa en la web |
| --- | --- | --- |
| `fact_transacciones.csv` | Vista `exp.fact_transacciones`: une pedidos, tickets y devoluciones con las 58 columnas originales | Panel de ventas |
| `costes_operativos_transaccion.csv` | Tabla `fin.transaction_cost` que escriben el checkout y el TPV con las reglas de `ref.cost_rule` | Resultados de campaña |
| `afinidad_tienda_cliente.csv` | Tabla `mkt.customer_store_affinity`, sembrada y recalculada cada noche por un procedimiento a partir de compras y tiendas | Segmentación local de campañas |
| `frasohome_rotacion_mensual.csv` | Vista `exp.rotacion_mensual` sobre `hr.*` | Panel de RR. HH. |
| `frasohome_people_analytics.csv` | Lo calcula la exportación (une `hr.*` con la encuesta de clima de Cosmos) | Ficha 360 del empleado |
| `frasohome_comentarios_clima.csv`, `frasohome_comentarios_salida.csv` | Los calcula la exportación desde Cosmos y `hr.employee` | Panel de RR. HH. |
| `dim_calendario.csv` | Tabla `ref.calendar` generada | Filtros de fecha |
| `FS_Productos`, `FS_Tiendas`, `FS_StockDiario`, `FS_VentasResumenDiario`, `FS_DevolucionesFact` | Tablas `rag.*` con la semilla + vistas `exp_rag.*` que añaden la actividad nueva traducida con `xref` | Exportación para Copilot Studio |
| `FS_Clientes` | Tabla `rag.customer` (sin alias hacia el CRM: queda como semilla) | Exportación para Copilot Studio |
| `FS_Alertas_Stockout` | Vista `exp_rag.alertas_stockout` sobre stock por debajo del mínimo | Inventario: alertas de rotura |
| `identidades_cliente_ground_truth.csv` | Tabla `lab.identity_ground_truth`, solo rol `profesor` | Laboratorio: corrige la consola de identidad |
| `frasohome_muestra_prompt_chatgpt.csv` | Lo calcula la exportación (muestra de salidas con comentario) | Laboratorio |
| `FS_TestSet_Documental.csv`, `FS_TestSet_Metrico_Mixto.csv` | Tabla `lab.rag_test_case` | Laboratorio: juegos de evaluación editables |
| `catalogo-datos.csv`, `validacion_datasets_marketing_precision.csv`, `coherence_check_summary.csv` | Los recalcula la exportación (recuentos, nulos y coherencia reales) | Administración de datos |
| `catalogo_datasets_marketing_precision.csv`, `diccionario_columnas_marketing_precision.csv`, `mapeo_casos_marketing_precision.csv`, `marketing_precision_operational_links.csv`, `diccionario_fuentes_brutas.csv`, `frasohome_diccionario_datos.csv`, `plantilla_backlog_indicadores.csv` | Tablas `meta.*` | Administración de datos: diccionario y catálogo |

## Exportación a CSV

`tools/export_csv.py` vuelca las bases a los mismos 64 CSV que hay hoy en `datos/`, de modo que cualquier escenario que lea CSV (notebooks del 02, Power BI del 06, Copilot Studio del 07, y Fabric más adelante) funciona sobre datos vivos sin tocar su código.

- **Contrato de formato**: mismas rutas relativas, nombres de columna, orden de columnas, codificación (con BOM donde el original lo lleva) y separador. Una prueba compara las cabeceras exportadas con las de `datos/` y falla si alguna cambia.
- **Destino**: `exports/AAAA-MM-DD/` con la estructura de `datos/` (ignorado por Git). Nunca sobrescribe `datos/` salvo con `--reemplazar-datos`, porque esos CSV son material docente sucio a propósito.
- **Opciones**: `--hasta AAAA-MM-DD` para una foto a una fecha, `--dominio retail|marketing|people|rag|relaciones` para exportar solo una parte, `--zip` para entregar a alumnos.
- **Dónde se ejecuta**: en local con las credenciales de lectura, o desde un workflow manual de GitHub Actions que deja el ZIP como artefacto de la ejecución.
- **Datos limpios**: la exportación sale limpia. Las demos de calidad de datos siguen usando los CSV originales congelados en `datos/`.
- **Lectura con usuario propio**: `fsh_export`, con solo `SELECT` sobre las tablas y vistas, y una clave de solo lectura de Cosmos.

## Funcionalidad de la web

Dieciséis escenarios cubren los 64 CSV: cada fichero aparece en al menos uno, como dato que se opera o como resultado que se consulta. El catálogo es público; todo lo demás exige sesión y el rol indicado.

| # | Escenario | Rol | Flujo en la web | Datos (CSV) |
| --- | --- | --- | --- | --- |
| 1 | Compra online | `cliente` | Catálogo y búsqueda, carrito, promoción y cupón aplicados, checkout, seguimiento del pedido | `productos`, `promociones_calendario`, `cupones_clientes`, `pedidos`, `lineas_pedido`, `eventos_web_app` |
| 2 | Venta en tienda (TPV) | `cajero` | Abrir caja, ticket con líneas, cliente por tarjeta de fidelización, cobro mixto, cierre de caja | `ventas_pos`, `pagos_tienda`, `tiendas`, `store_aliases`, `employee_operational_aliases`, `employee_store_assignment` |
| 3 | Devoluciones | `cliente`, `cajero` | Solicitud online con motivo y método; devolución en tienda de compra online o física; reembolso y reingreso a stock | `devoluciones_online`, `devoluciones_tienda` |
| 4 | Inventario y reposición | `tienda` | Ajustes, recepción de tránsito, cierre diario, alertas de rotura | `stock_diario`, `FS_Alertas_Stockout` |
| 5 | Catálogo y tiendas | `admin` | Alta y baja de productos, precios y costes, ficha de tienda | `productos`, `tiendas`, `product_aliases_rag_to_retail` |
| 6 | Clientes y fidelización | `atencion`, `marketing` | Alta y edición, consentimientos, puntos, baja; consola de identidad para unificar señales de un cliente | `crm`, `identidades_cliente` |
| 7 | Gestión de campañas | `marketing` | Brief (objetivo, canal, segmento, oferta, presupuesto, KPI); audiencia con grupo de control y afinidad local; creatividades por microsegmento validadas contra *guardrails*; emisión de cupones; lanzamiento que simula entregas, aperturas y clics; resultados a 30 días con ingresos, margen y coste | `campanas_marketing`, `contactos_campana`, `creatividades_segmento`, `guardrails_marca_genai`, `cupones_clientes`, `eventos_campana`, `afinidad_tienda_cliente`, `costes_operativos_transaccion` |
| 8 | Promociones | `marketing` | Calendario por ámbito y canal, combinabilidad, umbral de cesta y margen mínimo | `promociones_calendario` |
| 9 | Atención al cliente | `atencion` | Bandeja por prioridad y SLA; abrir caso desde un pedido, ticket o tienda; conversación; resolución con compensación (cupón o reembolso); CSAT | `tickets_atencion_cliente`, `cupones_clientes`, `devoluciones_*` |
| 10 | Voz del cliente | `cliente`, `atencion` | Reseña y NPS tras la compra; moderar, publicar y responder; temas y sentimiento | `feedback_clientes` |
| 11 | Ciclo de vida del empleado | `rrhh` | Alta, movimientos, revisión salarial, baja con entrevista de salida | `raw_hris_empleados`, `raw_movimientos_personal`, `raw_salarios_beneficios`, `raw_exit_interviews`, `dim_departamentos_mapeo` |
| 12 | Tiempo y desempeño | `rrhh`, `manager` | Ausencias, horas extra con aprobación del manager, formación, evaluación anual | `raw_absentismo`, `raw_horas_extra`, `raw_formacion`, `raw_evaluaciones_desempeno` |
| 13 | Portal del empleado | `empleado` | Encuesta de clima, mis ausencias, mis horas extra, mis cursos | `raw_encuesta_clima_respuestas` |
| 14 | Paneles operativos | `direccion` | Ventas del día, ficha 360 de cliente y de empleado, rotación mensual, comentarios de clima y salida (solo lectura) | `fact_transacciones`, `frasohome_people_analytics`, `frasohome_rotacion_mensual`, `frasohome_comentarios_*`, `dim_calendario`, `FS_VentasResumenDiario` |
| 15 | Administración de datos | `admin` | Usuarios y roles, exportación a CSV, reinicio de demo, rechazos de la carga, catálogo y diccionarios | `catalogo-datos`, diccionarios, `validacion_*`, `coherence_check_summary`, `marketing_precision_operational_links`, `mapeo_casos_*`, `catalogo_datasets_*` |
| 16 | Laboratorio docente | `profesor` | Corregir la consola de identidad contra la verdad conocida, editar juegos de evaluación RAG, muestras para prompts, backlog de indicadores | `identidades_cliente_ground_truth`, `FS_TestSet_*`, `frasohome_muestra_prompt_chatgpt`, `plantilla_backlog_indicadores`, `FS_Clientes`, `FS_Productos`, `FS_Tiendas`, `FS_StockDiario`, `FS_DevolucionesFact` |

Reglas de construcción:

- **Transacciones en procedimientos almacenados**: `sales.usp_checkout` inserta pedido y líneas, descuenta stock y canjea el cupón en una sola transacción. Lo mismo para `usp_pos_ticket`, `usp_return` y `usp_hr_leave`.
- **Escrituras a dos bases sin transacción distribuida**: primero SQL (la verdad del dinero), después Cosmos. Si Cosmos falla, el evento queda en `app.outbox` y se reintenta. Cada operación lleva un `Idempotency-Key`.
- **Autenticación y ámbito**: login propio (sección siguiente). Además del rol, cada usuario se ata a su entidad: un cliente solo ve sus pedidos, un cajero solo su tienda, un manager solo su equipo.
- **Frontend sin framework**: HTML, CSS y JavaScript plano con htmx; la API en Python 3.11 (apiRuntime python:3.11, la versión más alta que admiten las managed Functions; modelo v2 de Azure Functions) con `mssql-python` y `azure-cosmos`.
- **Datos sintéticos pero con nombres, salarios y correos**: el módulo RR. HH. y el CRM solo se ven con su rol; la solución del ejercicio de identidad solo la ve el rol profesor.
- **Generador de tráfico**: un script que usa la propia API para simular pedidos, tickets y eventos. Sirve para rellenar 2026 (los CSV acaban en 2025) y para que haya movimiento durante una charla.

## Autenticación con usuario y contraseña

Usuarios creados a mano por el administrador, sin registro abierto ni proveedores externos. Toda la lógica vive en la API y en Azure SQL.

- **Alta manual**: `tools/users.py add --login cajero.coruna --rol cajero --tienda S01` genera una contraseña aleatoria de 16 caracteres y la muestra una sola vez. También `reset`, `disable`, `list` y `add-role`. El usuario cambia la contraseña en el primer acceso.
- **Tablas**: `app.app_user` (login, nombre, hash, sal, activo, intentos fallidos, bloqueado hasta, debe cambiar contraseña), `app.user_role` (un usuario puede tener varios roles) y `app.user_scope` (cliente, empleado o tienda a la que se ata).
- **Contraseñas**: `hashlib.scrypt` de la biblioteca estándar de Python, con sal por usuario. Nunca en claro en la base, en logs ni en el repo.
- **Sesión**: `POST /api/auth/login` crea un token aleatorio de 32 bytes, guarda solo su hash en `app.session` y lo envía en la cookie `fsh_session` (HttpOnly, Secure, SameSite=Strict, 8 horas). `POST /api/auth/logout` la borra.
- **Protección**: bloqueo de 15 minutos tras 5 fallos, mensaje de error genérico, cabecera obligatoria en las escrituras contra CSRF, comprobación de rol y ámbito en cada endpoint.
- **SWA**: las rutas `/.auth/*` de la autenticación integrada devuelven 404 desde `staticwebapp.config.json`, para que no exista otra puerta de entrada.
- **Roles**: `cliente`, `cajero`, `tienda`, `atencion`, `marketing`, `rrhh`, `manager`, `empleado`, `direccion`, `profesor`, `admin`. Para las demos, un usuario por rol y una docena de clientes del CRM con acceso.

## Reglas de diseño para no rehacer nada después

Cinco reglas que no cuestan nada ahora y evitan rehacer el modelo cuando llegue la carga en Fabric:

- **Tipos SQL compatibles con mirroring**: JSON en `nvarchar(max)` (nunca el tipo `json`), `datetime2(3)` en todo el modelo, sin columnas calculadas, sin `xml`, `text` ni `image`.
- **Tablas sencillas**: sin tablas temporales, *ledger*, in-memory ni columnstore agrupado, y sin activar CDC en la base.
- **Servidor lógico con identidad administrada del sistema** desde el primer día.
- **Documentos Cosmos planos** en los campos que se van a analizar; solo se anida lo que no se analiza (por ejemplo, la conversación de un caso de soporte). Borrados explícitos, sin TTL.
- **Región elegida pensando en la futura capacidad Fabric**: la oferta SQL fija la región de todas las bases gratuitas de la suscripción.

## Plan por fases

Ocho fases en línea recta y entre 18 y 23 días de trabajo. Lo que más pesa es la web: 16 escenarios.

**Fase 0 · Comprobaciones (1 día)**

Kit en `escenarios/11-web-transaccional/fase0`, probado en local el 18 de octubre de 2026 con SQL Server, el emulador de Cosmos y la imagen de Functions Python 3.11: los dos drivers SQL, Cosmos y la cookie funcionan. Pendiente de ejecutar en Azure. Los DNS de dataging.com están en Cloudflare: el CNAME irá con el proxy desactivado.

- [ ] Elegir la región (la oferta SQL la fija para todas las bases gratuitas de la suscripción), pensando ya en la futura capacidad Fabric
- [ ] Comprobar que la suscripción MSDN no tiene ya una cuenta Cosmos con free tier (solo se admite una)
- [ ] Desplegar en SWA Free una *managed Function* Python 3.11 que lea de SQL con `mssql-python`, escriba en Cosmos y fije una cookie `HttpOnly` que llegue de vuelta en la siguiente llamada
- [ ] Comprobar que las rutas `/.auth/*` quedan bloqueadas
- [ ] Medir con la métrica «Free amount remaining» cuántos segundos de vCore consume una sesión de trabajo normal
- [ ] Validar el CNAME `frasohome` en el DNS de dataging.com

**Fase 1 · Infraestructura como código (1 día)**

- [ ] `infra/main.bicep`: grupo de recursos, servidor SQL con identidad del sistema y administrador Entra, base gratuita con autopausa, cuenta Cosmos (free tier, base compartida de 1.000 RU/s, 9 contenedores), SWA Free
- [ ] Alerta de presupuesto a 1 € y alerta sobre «Free amount remaining» al 20 %
- [ ] Workflow de GitHub Actions para Bicep y SWA, con secretos en GitHub y en la configuración de SWA

**Fase 2 · Modelo y carga inicial (3–4 días)**

- [ ] DDL operacional: `01_core.sql` (el core del escenario 03 ajustado a las reglas de diseño), `02_hr_mkt_fin_ref_xref.sql`, `03_procedimientos.sql`, `04_app.sql` (usuarios, sesiones, outbox, idempotencia, auditoría)
- [ ] DDL de referencia y laboratorio: `05_rag_meta_lab.sql` y `06_exp_vistas.sql`
- [ ] `seed/load_sql.py`: carga los CSV que van a SQL, aplica las reglas de limpieza del notebook 3 y registra rechazos en `quality.data_quality_issue`
- [ ] `seed/load_cosmos.py`: carga masiva de los 8 CSV en sus contenedores, con documentos planos y ritmo limitado para no pasar de 1.000 RU/s
- [ ] `seed/verify.py`: compara recuentos con `catalogo-datos.csv` y lista las diferencias explicadas por limpieza
- [ ] `seed/reset.py`: deja las bases como recién cargadas antes de una demo

**Fase 3 · API, autenticación y transacciones (4–5 días)**

- [ ] `/api/auth/*` y `tools/users.py`, con pruebas de bloqueo, caducidad y ámbito
- [ ] Endpoints por escenario sobre los procedimientos almacenados
- [ ] Outbox hacia Cosmos y cabecera `Idempotency-Key`
- [ ] Pruebas con pytest contra SQL Server y el emulador de Cosmos en local, para no gastar la cuota gratuita

**Fase 4 · Web (5–7 días)**

- [ ] Login, cambio de contraseña y menú según rol
- [ ] Escenarios 1–5 (venta, devoluciones, stock, catálogo)
- [ ] Escenarios 6–10 (CRM, campañas, promociones, soporte, voz del cliente)
- [ ] Escenarios 11–16 (RR. HH., portal del empleado, paneles, administración, laboratorio)

**Fase 5 · Exportación a CSV (2 días)**

- [ ] `tools/export_csv.py` con las opciones `--hasta`, `--dominio`, `--zip` y `--reemplazar-datos`
- [ ] Prueba de contrato: cabeceras, orden y codificación iguales a `datos/` en los 64 ficheros
- [ ] Prueba de ida y vuelta: cargar, exportar y comprobar que los notebooks 1–8 del escenario 02 se ejecutan sobre el export
- [ ] Workflow manual de GitHub Actions que deja el ZIP como artefacto

**Fase 6 · Tráfico, dominio y operación (1 día)**

- [ ] `tools/traffic.py` con perfiles «relleno 2026» y «charla en directo», que inicia sesión con usuarios demo y usa la API
- [ ] Dominio `frasohome.dataging.com` con SSL automático
- [ ] Guía corta de operación: alta de usuarios, revisar cuotas, cerrar herramientas para que la base pause, reiniciar datos, exportar

**Fase 7 · Documentación (1–2 días)**

- [ ] Ficha `escenarios/11-web-transaccional/README.md` con un guion por cada uno de los 16 escenarios y diagrama draw.io
- [ ] Añadir el escenario a la tabla de escenarios y a `recursos-por-escenario.csv`, y anotar en los escenarios 02–10 cómo usar el export

## Riesgos y costes

La parte operacional cuesta 0 € mientras se respeten las cuotas, y las alertas de la fase 1 avisan antes del primer euro. El recurso escaso es la base SQL: 100.000 segundos de vCore al mes dan para unas 55 horas activas al mínimo de 0,5 vCore.

| Riesgo | Impacto | Mitigación |
| --- | --- | --- |
| Herramientas abiertas (SSMS, VS Code) o el generador de tráfico impiden la autopausa de la base SQL | Se agotan los segundos de vCore y la base queda pausada hasta el mes siguiente | Alerta al 20 % de cuota; cerrar conexiones al terminar; generador por ráfagas; desarrollo y pruebas contra SQL Server local |
| Autenticación hecha en casa | Un fallo expone datos o permite escribir sin permiso | Sin registro abierto; `scrypt` con sal; bloqueo por intentos; cookie HttpOnly y SameSite=Strict; pruebas automáticas de rol y ámbito por endpoint; los datos son sintéticos |
| Contraseñas iniciales compartidas por canales inseguros | Acceso de quien no debería | Se muestran una sola vez, cambio obligatorio en el primer acceso, `disable` inmediato |
| La exportación se desvía del formato de `datos/` | Los escenarios 02–10 dejan de funcionar con el export | Prueba de contrato en cada cambio y prueba de ida y vuelta con los notebooks del 02 |
| Ráfagas de escritura por encima de 1.000 RU/s en Cosmos | Errores 429 en eventos | El SDK reintenta; carga inicial y generador con ritmo limitado; los eventos fallidos esperan en `app.outbox` |
| Las *managed Functions* no usan identidad administrada ni referencias a Key Vault | Secretos de conexión en la configuración de SWA | Usuario SQL de la app con solo `EXECUTE` sobre procedimientos; usuario de exportación con solo `SELECT`; clave de Cosmos exclusiva de la app. Si se quiere identidad administrada: plan Standard con Functions propias |
| La suscripción ya tiene una cuenta Cosmos con free tier | No se puede crear la nueva gratis | Se comprueba en la fase 0; si existe, se reutiliza esa cuenta con una base nueva |
| La oferta SQL fija la región para todas las bases gratuitas de la suscripción | Región incoherente con la futura capacidad Fabric | Decidir la región en la fase 0, antes de crear la primera base gratuita |
| CSV de 2024–2025 y transacciones de 2026 | Hueco de 10 meses en las series | Perfil «relleno 2026» del generador de tráfico |
| SWA Free sin SLA | Caída puntual | Aceptable para demos; Standard si llega a uso docente continuado |

Una nota de higiene: `conexion SQL Azure.txt`, en la raíz del repo, está excluido por `.gitignore` y no se sube, pero guarda usuario y contraseña en claro. No los reutilizaría aquí: el plan crea inicios de sesión nuevos con mínimo privilegio.

## Estructura en el repositorio

Todo vive en `frasohome-demos` como escenario 11, para que los datos de `datos/` sigan siendo la única fuente. El workflow de SWA despliega solo cuando cambia esta carpeta, y `mkdocs.yml` excluye `app/` y `api/` del sitio de GitHub Pages. La fase analítica añadirá después su propia carpeta `fabric/`.

```
escenarios/11-web-transaccional/
  README.md            ficha del escenario y guion de los 16 escenarios
  infra/               main.bicep, parámetros, alertas
  sql/                 01_core · 02_hr_mkt_fin_ref_xref · 03_procedimientos · 04_app
                       05_rag_meta_lab · 06_exp_vistas
  seed/                load_sql.py · load_cosmos.py · verify.py · reset.py · reglas_limpieza.py
  api/                 Azure Functions Python (auth + un blueprint por escenario)
  app/                 HTML + htmx, staticwebapp.config.json
  tools/               users.py · export_csv.py · traffic.py
  tests/               contrato de exportación, roles y ámbito, transacciones
  diagramas/           arquitectura.drawio + .drawio.svg
```

## Fuentes

- [Azure SQL Database free offer](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer) y [FAQ](https://learn.microsoft.com/en-gb/azure/azure-sql/database/free-offer-faq?view=azuresql)
- [Azure SQL Database serverless](https://learn.microsoft.com/en-us/azure/azure-sql/database/serverless-tier-overview)
- [Azure Cosmos DB lifetime free tier](https://learn.microsoft.com/en-us/azure/cosmos-db/free-tier)
- [Azure Static Web Apps: planes](https://learn.microsoft.com/en-us/azure/static-web-apps/plans), [API con Azure Functions](https://learn.microsoft.com/en-us/azure/static-web-apps/apis-functions) y [runtimes admitidos](https://learn.microsoft.com/en-us/azure/static-web-apps/languages-runtimes)
- [Limitaciones del mirroring de Azure SQL](https://learn.microsoft.com/en-us/fabric/mirroring/azure-sql-database-limitations), origen de las reglas de diseño
- Repositorio `C:\repos\frasohome-demos`: `datos/`, `catalogo-datos.csv`, escenario 03 (`fabric_databases`, `sql_database_consolidated`)
