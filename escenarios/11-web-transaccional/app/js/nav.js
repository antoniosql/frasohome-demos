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
  { id: "maestros", titulo: "Catálogo y tiendas", escenario: 5, roles: ["admin"],
    descr: "Alta, precios y baja de productos; ficha de tienda.", vista: () => import("./vistas/maestros.js") },
];

export const seccion = (id) => SECCIONES.find((s) => s.id === id);

/** ¿Puede ver el usuario esta sección? `usuario` es el de /api/auth/me o null. */
export function visible(s, usuario) {
  if (s.publica) return true;
  if (!usuario) return false;
  const roles = usuario.roles;
  if (roles.includes("admin") && !s.literal) return true;
  return (s.roles || []).some((r) => roles.includes(r));
}
