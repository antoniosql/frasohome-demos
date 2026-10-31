# Fase 3 · API, autenticación y transacciones

La API de FraSoHome Live: 143 endpoints para los 16 escenarios, con usuarios y contraseñas propios, transacciones en procedimientos almacenados de Azure SQL y documentos en Cosmos DB. Corre en las managed Functions de Static Web Apps (Python 3.11). La web de la fase 4 ([web de la fase 4](../web.md)) la consume.

## Cómo está hecha

| Pieza | Dónde | Qué hace |
| --- | --- | --- |
| Entrada | [`function_app.py`](function_app.py) | Una sola función HTTP recibe `/api/*` y la pasa al enrutador. Así toda la API se prueba con pytest sin el host de Functions |
| Enrutador y HTTP | [`fsh/web.py`](fsh/web.py), [`fsh/app.py`](fsh/app.py) | Rutas con rol, cabecera CSRF, sesión, `Idempotency-Key` y envío del outbox tras cada escritura |
| Sesión | [`fsh/auth.py`](fsh/auth.py) | scrypt con sal por usuario, token de 32 bytes del que solo se guarda el hash, cookie `fsh_session` |
| SQL | [`fsh/db.py`](fsh/db.py) | `mssql-python`; los errores de negocio (`THROW 50000–50999`) llegan al usuario como 422 con su mensaje |
| Cosmos DB | [`fsh/cosmos.py`](fsh/cosmos.py) | Lecturas y outbox: primero SQL (la verdad del dinero), después Cosmos; si Cosmos falla, se reintenta |
| Escenarios | [`fsh/rutas/`](fsh/rutas/__init__.py) | Un módulo por área |
| Transacciones | [`../sql/03_procedimientos.sql`](../sql/03_procedimientos.sql) | 44 procedimientos: checkout, ticket de TPV, devoluciones, stock, CRM, campañas, promociones y RR. HH. |
| Usuarios | [`../tools/users.py`](../tools/users.py) | Alta, reinicio de contraseña, roles, ámbitos y usuarios de demo |

Reglas que cumple toda la API:

- **Escrituras solo por procedimientos.** El usuario de base de datos `fsh_api` tiene `SELECT` y `EXECUTE`, nada más. Las pruebas pasan con ese usuario.
- **Rol y ámbito en cada endpoint.** El rol decide qué se puede hacer y el ámbito, sobre qué: un cliente solo ve sus pedidos, un cajero solo su tienda y un manager solo su equipo.
- **Escrituras con `X-FSH-CSRF: 1`**, además de la cookie `SameSite=Strict`.
- **Dinero y stock con `Idempotency-Key`:** checkout, ticket de TPV y las dos devoluciones. Repetir la petición devuelve la misma respuesta sin volver a cobrar ni a mover stock.
- **Login con mensaje genérico** y bloqueo de 15 minutos tras 5 fallos. Contraseñas de 12 caracteres como mínimo, que el usuario cambia en el primer acceso.
- **Cookie con `Domain` explícito**, el hallazgo de la fase 0: sin él, Static Web Apps descarta la cabecera `Set-Cookie`.

## Endpoints por escenario

| # | Escenario | Rol | Módulo | Endpoints |
| --- | --- | --- | --- | --- |
| 1 | Compra online | cliente (catálogo público) | `catalogo`, `pedidos` | 15 |
| 2 | Venta en tienda (TPV) | cajero, tienda | `tpv` | 9 |
| 3 | Devoluciones | cliente, cajero, atencion, tienda | `devoluciones` | 5 |
| 4 | Inventario y reposición | tienda | `inventario` | 8 |
| 5 | Catálogo y tiendas | admin | `admin` | 5 |
| 6 | Clientes, fidelización e identidad | atencion, marketing, cliente | `clientes` | 11 |
| 7–8 | Campañas y promociones | marketing | `campanas` | 19 |
| 9 | Atención al cliente | atencion, cliente | `atencion` | 9 |
| 10 | Voz del cliente | cliente, atencion, marketing | `voz_cliente` | 5 |
| 11–12 | Ciclo de vida, tiempo y desempeño | rrhh, manager | `rrhh` | 17 |
| 13 | Portal del empleado | cualquier empleado | `portal` | 8 |
| 14 | Paneles | direccion | `paneles` | 5 |
| 15 | Administración de datos y usuarios | admin | `admin` | 14 |
| 16 | Laboratorio docente | profesor | `laboratorio` | 8 |
| | Sesión y salud | público o con sesión | `sesion` | 5 |

## Desplegar en Azure

Requisitos: fases 1 y 2 hechas, Python 3.10+ y Node.js.

```powershell
cd escenarios\11-web-transaccional\tools
.\configurar_api.ps1      # procedimientos, usuario fsh_api, app settings y usuarios de demo
.\desplegar_api.ps1       # empaqueta para Python 3.11, publica y comprueba
```

`configurar_api.ps1` hace cinco cosas y se puede repetir:

1. Abre el firewall de SQL a tu IP.
2. Aplica `03_procedimientos.sql` sin tocar los datos (`seed/load_sql.py --solo-procedimientos`).
3. Crea el usuario `fsh_api` y guarda su cadena de conexión en `.local\frasohome-live\secretos_api.json`.
4. Cambia las app settings de la Static Web App al usuario nuevo.
5. Crea los usuarios de demostración: uno por rol y doce clientes del CRM.

Las contraseñas temporales se muestran una sola vez (con `-GuardarDemo` también quedan en `.local\frasohome-live\usuarios_demo.txt`) y cada usuario la cambia al entrar.

`desplegar_api.ps1` sustituye la web anterior por `app/` y la API, y lanza [`../tools/comprobar_api.py`](../tools/comprobar_api.py): salud, catálogo, CSRF, error genérico, rutas protegidas, `/.auth` bloqueado y cabeceras. Con `FSH_CHECK_LOGIN` y `FSH_CHECK_PASSWORD` de un usuario que ya cambió su contraseña, comprueba también la sesión completa.

El workflow [`frasohome-live-web`](../../../.github/workflows/frasohome-live-web.yml) publica lo mismo desde GitHub en cada cambio de `app/` o `api/` en `main`.

### Usuarios

```powershell
.\usuarios.ps1 list
.\usuarios.ps1 add --login cajero.coruna --nombre "Caja A Coruña" --rol cajero --rol empleado --tienda S001 --empleado FSH0040
.\usuarios.ps1 reset --login cajero.coruna
.\usuarios.ps1 disable --login cajero.coruna
```

Los roles cliente, cajero, tienda, empleado y manager exigen su ámbito (`--cliente`, `--tienda` o `--empleado`). Desactivar un usuario cierra sus sesiones. Los usuarios sobreviven a `seed\cargar_datos.ps1 -Reiniciar`.

## Pruebas en local

Contra SQL Server 2022 y el emulador de Cosmos DB en Docker, para no gastar la cuota gratuita:

```bash
docker run -d --name fsh-sql -e ACCEPT_EULA=Y -e 'MSSQL_SA_PASSWORD=<contraseña>' -p 1433:1433 mcr.microsoft.com/mssql/server:2022-latest
docker run -d --name fsh-cosmos -p 8081:8081 mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview
# crea la base frasohome-oltp y carga los datos con seed/reset.py --si
pytest api/tests
```

Variables: `SQL_CONNECTION_STRING`, `COSMOS_ENDPOINT` y `COSMOS_KEY`. Con `SQL_ADMIN_CONNECTION_STRING`, las pruebas corren con el usuario `fsh_api` y usan el administrador solo para preparar casos y limpiar.

| Prueba | Qué cubre |
| --- | --- |
| [`test_auth.py`](tests/test_auth.py) | Login, cookie, bloqueo, mensaje genérico, cambio obligatorio de contraseña, caducidad, CSRF, rol y ámbito |
| [`test_retail.py`](tests/test_retail.py) | Carrito y checkout idempotente con cupón, TPV con pago mixto y cierre de caja, devoluciones, inventario y catálogo |
| [`test_marketing.py`](tests/test_marketing.py) | CRM y consola de identidad, campaña completa con guardrails y grupo de control, promociones, atención con compensación y CSAT, opiniones |
| [`test_personas.py`](tests/test_personas.py) | Alta, promoción, salario y baja con entrevista; ausencias, horas extra con aprobación del manager, formación y evaluación; portal y encuesta; paneles |
| [`test_admin_lab.py`](tests/test_admin_lab.py) | Usuarios desde administración y desde `users.py`, calidad, metadatos, outbox, catálogo y laboratorio |

Resultado: las 30 pruebas pasan con datos recién cargados y al repetirlas, con el usuario `fsh_api`. Además se probó la API publicada en el host de Functions Python 3.11 detrás del emulador de Static Web Apps (11 de 11 en `comprobar_api.py`) y la consola en Chromium.
