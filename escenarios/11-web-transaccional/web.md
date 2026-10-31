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
| 6 · Clientes y fidelización | `clientes.js` (CRM e identidad), `cuenta.js` (mi cuenta) | Publicado |
| 7 · Gestión de campañas | `campanas.js` | Publicado |
| 8 · Promociones | `promociones.js` | Publicado |
| 9 · Atención al cliente | `atencion.js` (bandeja), `soporte.js` (mis casos) | Publicado |
| 10 · Voz del cliente | `voz.js` | Publicado |
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

## Detalles que conviene saber

- **Las creatividades pasan por los guardrails de marca.** Si incumplen una regla de severidad alta (por ejemplo, anunciar un descuento sin condiciones legibles, GR-006), la API las rechaza y la web muestra qué regla y por qué.
- **Una campaña sigue un orden:** borrador, audiencia (con grupo de control), cupones, lanzamiento, atribución a 30 días y cierre. Las creatividades solo se editan antes de lanzar.
- **Opinar** exige haber comprado el producto; desde el detalle de un pedido entregado el enlace «Opinar» ya lleva el producto y el pedido.
- **Mi cuenta, Mis casos y Opiniones** son las vistas del rol `cliente`; Clientes, Atención y la moderación son del personal.

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
| `atencion` | Bandeja con SLA, resolver con cupón, CRM, consola de identidad, moderar opiniones |
| `marketing` | Campaña completa (brief a resultados), promociones, CRM de solo consulta |
| `cliente` | Mi cuenta, consulta a atención y valoración (CSAT), opinar con NPS o reseña |
