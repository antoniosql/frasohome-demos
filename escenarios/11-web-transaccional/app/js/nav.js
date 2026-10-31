// FraSoHome Live · registro de secciones. Cada fase de la web añade sus escenarios aquí.
//   publica:   se puede ver sin sesión.
//   roles:     quién la ve en el menú (el administrador ve todas salvo las de `literal`).
//   literal:   exige alguno de esos roles de verdad (p. ej. el TPV necesita un empleado con caja).
export const SECCIONES = [
  { id: "tienda", titulo: "Tienda online", escenario: 1, publica: true, descr: "Catálogo, carrito, promociones y compra.",
    vista: () => import("./vistas/tienda.js") },
  { id: "pedidos", titulo: "Pedidos", escenario: 1, roles: ["cliente", "atencion", "tienda"],
    descr: "Seguimiento, cancelación, cupones y preparación del almacén online.", vista: () => import("./vistas/pedidos.js") },
  { id: "tpv", titulo: "Venta en tienda", escenario: 2, roles: ["cajero", "tienda"], literal: true,
    descr: "Caja, tickets con cobro mixto, cliente por tarjeta y cierre.", vista: () => import("./vistas/tpv.js") },
  { id: "devoluciones", titulo: "Devoluciones", escenario: 3, roles: ["cliente", "cajero", "atencion", "tienda"],
    descr: "Solicitud online, devolución en tienda, reembolso y reingreso a stock.", vista: () => import("./vistas/devoluciones.js") },
  { id: "inventario", titulo: "Inventario", escenario: 4, roles: ["tienda"],
    descr: "Stock vivo, ajustes, tránsito, mínimos, alertas y cierre diario.", vista: () => import("./vistas/inventario.js") },
  { id: "clientes", titulo: "Clientes", escenario: 6, roles: ["atencion", "marketing"],
    descr: "CRM, fidelización, consentimientos y consola de identidad.", vista: () => import("./vistas/clientes.js") },
  { id: "cuenta", titulo: "Mi cuenta", escenario: 6, roles: ["cliente"], literal: true,
    descr: "Tus datos, consentimientos y puntos de fidelización.", vista: () => import("./vistas/cuenta.js") },
  { id: "campanas", titulo: "Campañas", escenario: 7, roles: ["marketing"],
    descr: "Brief, audiencia con grupo de control, creatividades, cupones, lanzamiento y resultados.", vista: () => import("./vistas/campanas.js") },
  { id: "promociones", titulo: "Promociones", escenario: 8, roles: ["marketing"],
    descr: "Calendario por ámbito y canal, combinabilidad, umbral y margen mínimo.", vista: () => import("./vistas/promociones.js") },
  { id: "atencion", titulo: "Atención", escenario: 9, roles: ["atencion"],
    descr: "Bandeja por prioridad y SLA, conversación, compensación y CSAT.", vista: () => import("./vistas/atencion.js") },
  { id: "soporte", titulo: "Mis casos", escenario: 9, roles: ["cliente"], literal: true,
    descr: "Consultas a atención al cliente y su seguimiento.", vista: () => import("./vistas/soporte.js") },
  { id: "voz", titulo: "Opiniones", escenario: 10, roles: ["cliente", "atencion", "marketing"],
    descr: "Reseñas y NPS; moderación, respuesta, temas y sentimiento.", vista: () => import("./vistas/voz.js") },
  { id: "personas", titulo: "Plantilla", escenario: 11, roles: ["rrhh", "manager"],
    descr: "Alta, movimientos, revisión salarial y baja con entrevista de salida.", vista: () => import("./vistas/personas.js") },
  { id: "tiempo", titulo: "Tiempo y desempeño", escenario: 12, roles: ["rrhh", "manager"],
    descr: "Ausencias, horas extra con aprobación, formación y evaluación anual.", vista: () => import("./vistas/tiempo.js") },
  { id: "portal", titulo: "Portal del empleado", escenario: 13, literal: true, requiere: "employee",
    roles: ["empleado", "manager", "cajero", "tienda", "atencion", "marketing", "rrhh"],
    descr: "Tus ausencias, horas extra, cursos y la encuesta de clima.", vista: () => import("./vistas/portal.js") },
  { id: "paneles", titulo: "Paneles", escenario: 14, roles: ["direccion"],
    descr: "Ventas, ficha 360 de cliente y empleado, rotación y comentarios.", vista: () => import("./vistas/paneles.js") },
  { id: "maestros", titulo: "Catálogo y tiendas", escenario: 5, roles: ["admin"],
    descr: "Alta, precios y baja de productos; ficha de tienda.", vista: () => import("./vistas/maestros.js") },
  { id: "datos", titulo: "Datos", escenario: 15, roles: ["admin", "profesor"],
    descr: "Usuarios y roles, rechazos de la carga, metadatos, outbox y auditoría.", vista: () => import("./vistas/datos.js") },
  { id: "laboratorio", titulo: "Laboratorio", escenario: 16, roles: ["profesor"],
    descr: "Evaluación de la consola de identidad, juegos RAG, prompts y backlog.", vista: () => import("./vistas/laboratorio.js") },
];

export const seccion = (id) => SECCIONES.find((s) => s.id === id);

/** ¿Puede ver el usuario esta sección? `usuario` es el de /api/auth/me o null. */
export function visible(s, usuario) {
  if (s.publica) return true;
  if (!usuario) return false;
  if (s.requiere && !(usuario.ambitos[s.requiere] || []).length) return false;   // p. ej. el portal exige un empleado asociado
  const roles = usuario.roles;
  if (roles.includes("admin") && !s.literal) return true;
  return (s.roles || []).some((r) => roles.includes(r));
}
