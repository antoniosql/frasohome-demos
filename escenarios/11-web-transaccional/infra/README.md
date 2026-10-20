# Fase 1 · Infraestructura como código

Toda la infraestructura de FraSoHome Live queda descrita en Bicep y se despliega igual desde tu equipo o desde GitHub Actions. Los recursos de la [fase 0](../fase0/README.md) se adoptan con los mismos nombres: no se recrea nada ni se pierden datos.

## Qué se despliega

| Fichero | Contenido | Quién lo despliega |
| --- | --- | --- |
| [`main.bicep`](main.bicep) | Servidor y base SQL gratuita, cuenta Cosmos con free tier y base `frasohome` (1.000 RU/s compartidas), los 9 contenedores de la aplicación, la Static Web App Free, el grupo de acciones por correo y dos alertas | `desplegar_infra.ps1` o el workflow `frasohome-live-infra` |
| [`main.bicepparam`](main.bicepparam) | Parámetros. El correo y el administrador Entra se leen de variables de entorno: el repositorio es público | — |
| [`presupuesto.bicep`](presupuesto.bicep) | Presupuesto mensual de 1 con aviso por gasto real y previsto | `desplegar_infra.ps1`, una sola vez |
| [`github-oidc.bicep`](github-oidc.bicep) | Identidad `id-frasohome-live-github` con credencial federada para el entorno `frasohome-live` del repositorio y rol Colaborador en el grupo de recursos | `desplegar_infra.ps1` (asignar roles exige ser propietario) |

Contenedores de Cosmos DB, todos con clave de partición `/pk` y sin TTL (los borrados por caducidad no llegarían a un mirroring futuro):

| Contenedor | `pk` | Datos de origen |
| --- | --- | --- |
| `eventos_web` | sesión | `eventos_web_app.csv` |
| `eventos_campana` | campaña | `eventos_campana.csv` |
| `senales_identidad` | cliente o `SIN_CLIENTE` | `identidades_cliente.csv` |
| `feedback` | cliente | `feedback_clientes.csv` |
| `atencion_cliente` | cliente | `tickets_atencion_cliente.csv` |
| `creatividades` | campaña | `creatividades_segmento.csv` |
| `encuesta_clima` | empleado | `raw_encuesta_clima_respuestas.csv`, `frasohome_comentarios_clima.csv` |
| `entrevistas_salida` | empleado | `raw_exit_interviews.csv`, `frasohome_comentarios_salida.csv` |
| `carritos` | cliente | ninguno: lo crea la tienda web |

El contenedor `fase0` de las comprobaciones sigue existiendo (el despliegue es incremental). Se puede borrar cuando ya no haga falta la web de la fase 0.

## Alertas y coste

| Alerta | Condición | Por qué |
| --- | --- | --- |
| `alerta-sql-cuota-gratuita` | `free_amount_remaining` < 20.000 s de vCore, cada hora | Al agotar los 100.000 s del mes, la base se pausa hasta el mes siguiente |
| `alerta-cosmos-ru` | `NormalizedRUConsumption` > 90 %, cada 15 min | Por encima de las 1.000 RU/s gratuitas aparecen errores 429 |
| `presupuesto-frasohome-live` | Gasto real o previsto del mes > 1 | Red de seguridad si algo deja de ser gratuito |

Las dos alertas de métrica entran en las 10 series gratuitas al mes de Azure Monitor y los correos en los 1.000 gratuitos. Coste esperado de la fase: 0.

Algunas ofertas (patrocinios y ciertas suscripciones de Visual Studio) no admiten presupuestos; si es tu caso, el script avisa y sigue.

## Cómo desplegar

Requisitos: CLI de Azure 2.53 o superior (`az version`), la CLI de GitHub (`gh`) y haber completado la fase 0.

1. **Infraestructura** (muestra el what-if y pide escribir `desplegar`):

   ```powershell
   cd escenarios\11-web-transaccional\infra
   az login
   .\desplegar_infra.ps1 -AlertEmail tu@correo.com
   ```

   En el what-if lo esperado es crear los contenedores, el grupo de acciones, las alertas y modificar etiquetas. **Si aparece un `Delete` o un cambio en la SKU de la base, cancela.** Con `-SoloWhatIf` solo muestra los cambios.

   El correo queda en `.local\frasohome-live\estado.json` (Git lo ignora) y las siguientes ejecuciones lo reutilizan.

2. **GitHub** (entorno, variables y secretos):

   ```powershell
   gh auth login
   .\configurar_github.ps1
   ```

   En el entorno `frasohome-live` quedan:

   | Tipo | Nombre | Para qué |
   | --- | --- | --- |
   | Variable | `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` | Login OIDC. Identifican, no autentican |
   | Variable | `FSH_RESOURCE_GROUP`, `FSH_SWA_NAME` | Nombres de recursos |
   | Secreto | `FSH_ALERT_EMAIL`, `FSH_ENTRA_ADMIN_OBJECT_ID`, `FSH_ENTRA_ADMIN_LOGIN` | Datos personales que necesita `main.bicepparam` |

   Recomendado: añade tu usuario como revisor obligatorio del entorno (Settings → Environments → frasohome-live) para aprobar cada ejecución que toque Azure.

3. **Sube la rama y fusiónala en `main`.** Los workflows solo aparecen en Actions cuando están en la rama por defecto.

## Workflows

| Workflow | Cuándo | Qué hace |
| --- | --- | --- |
| [`frasohome-live-infra`](../../../.github/workflows/frasohome-live-infra.yml) | Pull request o push que toque `infra/` | Compila y valida los Bicep, sin entrar en Azure |
|  | A mano, `accion = what-if` | What-if contra `rg-frasohome-live` |
|  | A mano, `accion = desplegar` | What-if y despliegue de `main.bicep` |
| [`frasohome-live-web`](../../../.github/workflows/frasohome-live-web.yml) | Push a `main` que toque la web o la API, o a mano | Empaqueta la API para Python 3.11, obtiene el token de la Static Web App con OIDC, publica y lanza `comprobar_despliegue.py` |

En GitHub no se guarda ninguna contraseña de Azure ni el token de despliegue de la Static Web App: los dos workflows entran con la identidad federada, que solo acepta tokens del entorno `frasohome-live` de este repositorio.

Hasta la fase 4, `frasohome-live-web` publica la web de comprobaciones de la fase 0. La fase 4 cambiará `APP_DIR` y `API_DIR`.

## Qué no gestiona Bicep

- **Las app settings de la Static Web App** (cadenas de conexión de SQL y Cosmos). Viven solo en Azure; la fase 0 las crea y la fase 3 las ampliará. Un despliegue de Bicep que las incluyera borraría las que no estén en la plantilla.
- **La contraseña del administrador SQL.** `main.bicepparam` la deja vacía y el servidor conserva la actual (`.local\fase0\secretos.json`).
- **El dominio personalizado.** Lo configura `fase0\configurar_dominio.ps1` cuando existe el CNAME en Cloudflare.

## Ficheros

| Fichero | Para qué |
| --- | --- |
| `main.bicep`, `main.bicepparam` | Infraestructura principal |
| `presupuesto.bicep` | Presupuesto mensual |
| `github-oidc.bicep` | Identidad de GitHub Actions |
| `desplegar_infra.ps1` | What-if, despliegue, presupuesto e identidad desde tu equipo |
| `configurar_github.ps1` | Entorno, variables y secretos de GitHub |
| `comun.ps1` | Funciones compartidas por los scripts (compatibles con PowerShell 5.1) |
