# Fase 0 · Comprobaciones

Antes de construir FraSoHome Live hay que confirmar que la arquitectura funciona en los niveles gratuitos de Azure: una función Python en Static Web Apps que habla con Azure SQL y Cosmos DB, una cookie de sesión propia y la autenticación integrada de SWA bloqueada. Esta carpeta trae lo mínimo para comprobarlo en una tarde.

## Qué está comprobado ya en local

Probado con SQL Server 2022, el emulador de Cosmos DB y la imagen oficial `mcr.microsoft.com/azure-functions/python:4-python3.11` (Debian 11, la base de las Functions de Python 3.11):

| Comprobación | Resultado |
| --- | --- |
| `mssql-python` 1.15 conecta con su driver ODBC empaquetado | Correcto, sin instalar nada en el sistema |
| `pyodbc` 5.3 conecta con el ODBC Driver 18 de la imagen | Correcto |
| Dependencias para Linux descargadas desde Windows (`pip --platform`, 64 MB) | Cargan en la imagen de Functions |
| El host de Functions publica `/api/health` y `/api/cookie` | Correcto |
| Cookie `HttpOnly; Secure; SameSite=Strict` en Chromium | Se guarda, vuelve y JavaScript no la ve |
| CSP de `staticwebapp.config.json` con el JavaScript de la página | La página funciona con `script-src 'self'` |
| `desplegar.ps1` de principio a fin (con `az` simulado) | Correcto |
| Bicep (`bicep build` y `lint` 0.48) | Sin errores ni avisos |

Hallazgos que condicionan las fases siguientes:

- **`azure-functions` 2.x exige Python 3.13**; las managed Functions de SWA llegan a 3.11, así que la API se queda en `azure-functions` 1.25.
- **`mssql-python` rechaza `Connection Timeout`** en la cadena de conexión. Se usa `ConnectRetryCount` y `ConnectRetryInterval`, válidas para los dos drivers.
- **El host de Functions reescribe la cookie** y añade `domain=` vacío. Los navegadores lo ignoran (RFC 6265), pero `http.cookiejar` de Python descarta la cookie: los clientes Python de las pruebas y del generador de tráfico deben reenviarla a mano.
- **Los DNS de dataging.com están en Cloudflare** (`jose` y `meera.ns.cloudflare.com`) y `frasohome.dataging.com` todavía no existe.

## Resultado en Azure

Desplegado en `rg-frasohome-live` (SQL y Static Web App en West Europe, Cosmos DB en Sweden Central porque West Europe no tenía capacidad para la suscripción):

| Comprobación | Resultado |
| --- | --- |
| `/api/health` en las managed Functions | Python 3.11, `mssql-python` y `pyodbc` conectan con SQL; Cosmos lee y escribe |
| Cookie de sesión | Solo llega con `Domain` explícito: si el worker de Python emite `domain=` vacío, SWA descarta la cabecera `Set-Cookie`. Con `Domain` explícito, SWA lo reescribe al host público |
| `/.auth/login/*` | 404, sin redirección |
| `/.auth/me` | 200 con `clientPrincipal: null`: es interno de SWA y no se puede bloquear, pero nunca habrá nadie identificado |

Hallazgos de Azure que condicionan las fases siguientes:

- **La API siempre pone `Domain` en sus cookies**, tomado de `X-Forwarded-Host`.
- **Cosmos DB y SQL están en regiones distintas.** Cada llamada de la función a Cosmos cruza de West Europe a Sweden Central y suma unas decenas de milisegundos, así que la API debe agrupar las lecturas de Cosmos de cada petición.

## Lo que queda por comprobar en Azure

Necesita tu sesión de Azure, así que se ejecuta en tu equipo. Requisitos: CLI de Azure, Python 3.10+ y Node.js.

1. **Revisar la suscripción** (solo lectura):

   ```powershell
   cd escenarios\11-web-transaccional\fase0
   az login
   .\comprobar_suscripcion.ps1
   ```

   Dice si ya hay una base SQL gratuita (y por tanto una región fijada), una cuenta Cosmos con free tier, dónde están tus capacidades de Fabric y si faltan proveedores por registrar.

2. **Decidir la región de datos.** Es la única decisión irreversible de la fase: la oferta gratuita de SQL fija la región para todas las bases gratuitas de la suscripción. Recomendación: **`westeurope`**, la misma región que la Static Web App, para que la función y las bases estén en el mismo centro de datos. Cámbiala solo si tu capacidad de Fabric está en otra región (el script lo detecta).

3. **Desplegar y comprobar** (pide escribir la región otra vez antes de crear nada):

   ```powershell
   .\desplegar.ps1 -Region westeurope
   ```

   Crea `rg-frasohome-live` con la base `frasohome-oltp` (gratuita, autopausa al agotar la cuota), la cuenta Cosmos con free tier y la base compartida `frasohome` (1.000 RU/s), y la Static Web App Free. Después crea el usuario `fsh_fase0` (solo conecta), configura las app settings, publica la función y lanza `comprobar_despliegue.py`. La contraseña del administrador SQL queda en `.local\fase0\secretos.json`, que Git ignora.

   Si la CLI de SWA no consigue publicar la función, la alternativa es [`github-actions-fase0.yml`](github-actions-fase0.yml).

4. **Abrir la web de prueba** en el navegador y pulsar los tres botones. La cookie solo se puede confirmar del todo en un navegador real.

5. **Medir la cuota de SQL**: una vez justo después de una sesión de trabajo y otra al día siguiente sin tocar nada.

   ```powershell
   .\medir_cuota.ps1 -Horas 24
   ```

   Hay 100.000 segundos de vCore al mes, unos 3.300 al día. La base debe quedar en pausa una hora después de la última conexión; si la proyección pasa de 100.000, algo la mantiene despierta.

6. **Dominio.** En Cloudflare, crea `CNAME frasohome → <nombre>.azurestaticapps.net` con el **proxy desactivado** (nube gris, «DNS only»); con el proxy activo, Azure no valida el dominio ni emite el certificado. Luego:

   ```powershell
   .\configurar_dominio.ps1
   ```

## Criterio para pasar a la fase 1

| Comprobación | Resultado esperado |
| --- | --- |
| `comprobar_despliegue.py` contra `*.azurestaticapps.net` | 9 de 9 correctas (8 si solo falla uno de los dos drivers SQL) |
| Driver SQL que usará la API | `mssql-python` si conecta; si no, `pyodbc` |
| Cookie en el navegador | Enviada, recibida e invisible para JavaScript |
| `/.auth/*` | 404, sin redirección |
| Consumo de vCore en un día sin uso | Por debajo de 3.300 segundos |
| `comprobar_despliegue.py` contra `frasohome.dataging.com` | 9 de 9 correctas |

## Ficheros

| Fichero | Para qué |
| --- | --- |
| [`infra/fase0.bicep`](infra/fase0.bicep) | SQL gratuita, Cosmos free tier y SWA Free; los reutiliza la fase 1 |
| [`api/function_app.py`](api/function_app.py) | Función de prueba: `/api/health` y `/api/cookie` |
| [`app/staticwebapp.config.json`](app/staticwebapp.config.json) | Python 3.11, `/.auth/*` a 404 y cabeceras de seguridad; junto a la página de prueba |
| [`comprobar_suscripcion.ps1`](comprobar_suscripcion.ps1) | Revisión de la suscripción, solo lectura |
| [`desplegar.ps1`](desplegar.ps1) | Despliegue y comprobación |
| [`crear_usuario_sql.py`](crear_usuario_sql.py) | Usuario contenido `fsh_fase0` sin permisos |
| [`comprobar_despliegue.py`](comprobar_despliegue.py) | Comprobaciones desde fuera, solo biblioteca estándar |
| [`medir_cuota.ps1`](medir_cuota.ps1) | Consumo de la cuota gratuita de SQL |
| [`configurar_dominio.ps1`](configurar_dominio.ps1) | CNAME, enlace del dominio y comprobación |
| [`tests/test_function_local.py`](tests/test_function_local.py) | Prueba local con SQL Server y el emulador de Cosmos en Docker |

## Coste

Cero mientras se respeten las cuotas: la base gratuita se pausa sola al agotar los 100.000 segundos, el free tier de Cosmos cubre 1.000 RU/s y 25 GB, y SWA Free no tiene coste. Para borrarlo todo: `az group delete -n rg-frasohome-live`. Borrar la base gratuita no libera la región, que sigue fijada para la suscripción.
