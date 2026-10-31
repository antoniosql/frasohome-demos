# Fase 4 · Web

El código está en `escenarios/11-web-transaccional/app/`; esta ficha vive fuera de esa carpeta porque el sitio de documentación excluye `app/` (su `index.html` chocaría con el README).

La web de FraSoHome Live: HTML, CSS y JavaScript plano (módulos ES), sin framework ni dependencias, servida por Static Web Apps junto a la API de [`api/`](api/README.md). Todo el JavaScript es del mismo origen, porque la política de seguridad de contenido de `app/staticwebapp.config.json` (`script-src 'self'`) no admite scripts en línea ni CDN.

## Estado por escenarios

| Escenarios | Sección | Estado |
| --- | --- | --- |
| Acceso, cambio de contraseña, menú por rol | `acceso.js`, `main.js` | Publicado |
| 1 · Compra online | `tienda.js`, `pedidos.js` | Publicado |
| 2 · Venta en tienda | `tpv.js` | Publicado |
| 3 · Devoluciones | `devoluciones.js` | Publicado |
| 4 · Inventario y reposición | `inventario.js` | Publicado |
| 5 · Catálogo y tiendas | `maestros.js` | Publicado |
| 6–10 · CRM, campañas, promociones, atención, voz del cliente | | Pendiente |
| 11–16 · RR. HH., portal, paneles, administración, laboratorio | | Pendiente |

## Cómo está hecha

| Pieza | Qué hace |
| --- | --- |
| `app/index.html` | Cabecera, menú, zona de contenido y avisos. Un único `<script type="module">` |
| `app/js/main.js` | Enrutador por hash (`#/seccion/subruta?param=valor`), menú según el rol y control de acceso en el navegador. La API vuelve a comprobar rol y ámbito en cada petición |
| `app/js/nav.js` | Registro de secciones: título, escenario, roles que la ven y módulo que la pinta. Añadir un escenario es añadir una línea aquí y un fichero en `js/vistas/` |
| `app/js/api.js` | `fetch` con cookie de sesión y cabecera `X-FSH-CSRF`. En las operaciones con dinero o stock genera la `Idempotency-Key`; si se reintenta la misma petición, reutiliza la clave |
| `app/js/ui.js` | Construcción de DOM con `h()` (siempre `textContent`, nunca `innerHTML` con datos de la API), tablas, diálogos con formulario, avisos, formatos es-ES |
| `app/js/sesion.js` | Usuario de `/api/auth/me` y comprobaciones de rol |
| `app/js/vistas/` | Un módulo por sección, con `export async function render(contenedor, contexto)` |
| `app/css/app.css` | Una hoja de estilos, con modo oscuro, móvil e impresión del ticket |

## Reglas

- **Una vista no confía en el menú.** Ocultar un botón es comodidad; el control real está en la API.
- **Los errores de negocio se muestran tal cual** (la API devuelve 422 con el mensaje del procedimiento almacenado).
- **El carrito vive en Cosmos DB** (`carritos`) y los eventos de navegación del catálogo van a `eventos_web`: la tienda alimenta los mismos contenedores que la carga inicial.
- **Accesibilidad básica:** etiquetas en todos los campos, foco visible, `aria-current` en el menú y pestañas, avisos con `aria-live`.

## Probar

Contra el sitio publicado, con la sesión de un usuario de demo (`tools\usuarios.ps1 list`). El primer acceso obliga a cambiar la contraseña.

| Rol | Qué probar |
| --- | --- |
| Sin sesión | Catálogo, ficha, promociones, tiendas |
| `cliente` | Carrito, cupón, finalizar compra, seguimiento, cancelar, solicitar devolución |
| `tienda` (almacén `ONLINE`) | Preparar y entregar pedidos; inventario, alertas y movimientos |
| `cajero` | Abrir caja, ticket con cobro mixto y cliente, devolución desde el ticket, cierre |
| `atencion` | Aceptar y reembolsar devoluciones |
| `admin` | Alta, edición y baja de productos; ficha de tienda; cierre diario del stock |
