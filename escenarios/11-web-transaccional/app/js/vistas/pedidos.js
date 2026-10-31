// Escenario 1 · seguimiento del pedido (cliente) y preparación (almacén online, atención).
import { get, post } from "../api.js";
import { aviso, cargando, confirmar, conAviso, dialogo, eur, ficha, fechaHora, fecha, h, insignia, montar, num,
  paginador, pestanas, selector, tabla } from "../ui.js";
import { soloRol, tieneRol } from "../sesion.js";

const TAMANO = 20;
const ESTADOS = ["", "Pendiente", "En preparación", "Entregado", "Cancelado", "Devuelto Parcial", "Devuelto Total"];
const SIGUIENTES = { "Pendiente": ["En preparación", "Cancelado"], "En preparación": ["Entregado", "Cancelado"] };
const METODOS_DEVOLUCION = ["Envío", "Tienda", "Punto Pack"];

export async function render(cont, ctx) {
  const [sub] = ctx.partes;
  const cliente = soloRol("cliente");
  const cuerpo = h("div", {}, cargando());
  const activa = sub === "cupones" ? "cupones" : "";
  montar(cont, cliente && !(sub && sub.startsWith("O-"))
    ? pestanas("pedidos", [{ id: "", titulo: "Mis pedidos" }, { id: "cupones", titulo: "Mis cupones" }], activa) : null, cuerpo);
  if (sub === "cupones") return cupones(cuerpo);
  if (sub) return detalle(cuerpo, sub, ctx);
  return lista(cuerpo, ctx);
}

async function lista(cuerpo, ctx) {
  const p = ctx.params;
  const pagina = Number(p.get("pagina") || 1);
  const estado = p.get("estado") || "";
  const clienteFiltro = (p.get("cliente") || "").toUpperCase();
  const staff = !soloRol("cliente") || tieneRol("atencion", "tienda");
  const r = await get("/pedidos", { pagina, tamano: TAMANO, estado, cliente: staff ? clienteFiltro : undefined });
  const ir = (n, e = estado, c = clienteFiltro) => {
    const s = new URLSearchParams();
    if (e) s.set("estado", e);
    if (c) s.set("cliente", c);
    if (n > 1) s.set("pagina", n);
    ctx.ir("/pedidos" + (s.toString() ? "?" + s : ""));
  };
  const sel = selector(ESTADOS.map((e) => [e, e || "Todos los estados"]), estado, { "aria-label": "Estado" });
  const cli = staff ? h("input", { value: clienteFiltro, placeholder: "Cliente (C0001)", maxlength: "5", "aria-label": "Cliente" }) : null;
  const columnas = [
    { t: "Pedido", k: "order_id" }, { t: "Fecha", f: (o) => fechaHora(o.ordered_at) },
    staff ? { t: "Cliente", k: "customer_id" } : null,
    { t: "Estado", f: (o) => insignia(o.order_status) }, { t: "Pago", k: "payment_method" },
    { t: "Líneas", k: "lineas", cls: "num" }, { t: "Total", f: (o) => eur(o.order_total), cls: "num" },
  ].filter(Boolean);
  montar(cuerpo,
    h("h1", {}, staff ? "Pedidos online" : "Mis pedidos"),
    h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); ir(1, sel.value, cli ? cli.value.trim().toUpperCase() : ""); } },
      sel, cli, h("button", { type: "submit" }, "Filtrar")),
    tabla(columnas, r.pedidos, { alClic: (o) => ctx.ir(`/pedidos/${o.order_id}`),
      sinDatos: staff ? "No hay pedidos con esos filtros." : "Todavía no has hecho ningún pedido." }),
    paginador(pagina, r.total, TAMANO, (n) => ir(n)));
}

async function detalle(cuerpo, id, ctx) {
  const o = await get(`/pedidos/${encodeURIComponent(id)}`);
  const cliente = soloRol("cliente");
  const staff = tieneRol("atencion", "tienda");
  const puedeDevolver = cliente && ["Entregado", "Devuelto Parcial"].includes(o.order_status);
  const recargar = () => detalle(cuerpo, id, ctx);

  const acciones = [];
  if (cliente && o.order_status === "Pendiente") {
    acciones.push(h("button", { type: "button", onclick: conAviso(async () => {
      if (!confirmar("¿Cancelar este pedido?")) return;
      await post(`/pedidos/${o.order_id}/cancelar`, {});
      aviso("Pedido cancelado."); recargar();
    }) }, "Cancelar pedido"));
  }
  if (staff) {
    for (const nuevo of SIGUIENTES[o.order_status] || []) {
      acciones.push(h("button", { type: "button", class: nuevo === "Cancelado" ? "" : "primary", onclick: conAviso(async () => {
        await post(`/pedidos/${o.order_id}/estado`, { estado: nuevo });
        aviso(`Pedido pasado a «${nuevo}».`); recargar();
      }) }, `Pasar a «${nuevo}»`));
    }
  }

  const devolver = (l) => dialogo(`Devolver ${l.product_description}`, [
    { k: "cantidad", etiqueta: `Unidades (hasta ${l.devolvible})`, tipo: "number", min: 1, max: l.devolvible, step: 1, valor: 1, req: true },
    { k: "motivo", etiqueta: "Motivo", maxlength: 200, req: true },
    { k: "metodo", etiqueta: "Cómo lo devuelves", tipo: "select", opciones: METODOS_DEVOLUCION, valor: "Envío" },
  ], async (v) => {
    const r = await post("/devoluciones/online", { order_id: o.order_id, order_line_id: l.order_line_id, cantidad: v.cantidad,
      motivo: v.motivo, metodo: v.metodo }, { idem: true });
    aviso("Solicitud de devolución registrada.");
    ctx.ir(`/devoluciones/${r.return_id}`);
  }, { enviar: "Solicitar devolución" });

  montar(cuerpo,
    h("p", {}, h("a", { href: "#/pedidos" }, "‹ Pedidos")),
    h("h1", {}, `Pedido ${o.order_id} `, insignia(o.order_status)),
    ficha([["Fecha", fechaHora(o.ordered_at)], staff ? ["Cliente", o.customer_id] : null,
      ["Envío a", [o.shipping_address, o.shipping_postal_code, o.shipping_city, o.shipping_province].filter(Boolean).join(", ")],
      ["Pago", o.payment_method], ["Gastos de envío", eur(o.shipping_amount)], ["Total", h("strong", {}, eur(o.order_total))],
      o.coupon_instance_id ? ["Cupón", o.coupon_instance_id] : null]),
    h("div", { class: "fila" }, acciones),
    h("h2", {}, "Artículos"),
    tabla([
      { t: "Producto", f: (l) => h("a", { href: `#/tienda/producto/${l.product_id}` }, l.product_description) },
      { t: "Cant.", k: "quantity", cls: "num" }, { t: "Precio", f: (l) => eur(l.unit_price), cls: "num" },
      { t: "Descuento", f: (l) => (l.discount_amount ? `−${eur(l.discount_amount)}` : "—"), cls: "num" },
      { t: "Importe", f: (l) => eur(l.line_amount), cls: "num" },
      puedeDevolver ? { t: "", f: (l) => (l.devolvible > 0
        ? h("button", { type: "button", onclick: () => devolver(l) }, "Devolver")
        : h("small", {}, "Devuelto")) } : { t: "Devolvible", k: "devolvible", cls: "num" },
    ], o.lineas),
    o.devoluciones.length ? [h("h2", {}, "Devoluciones de este pedido"), tabla([
      { t: "Devolución", f: (d) => h("a", { href: `#/devoluciones/${d.return_id}` }, d.return_id) },
      { t: "Fecha", f: (d) => fecha(d.returned_at) }, { t: "Estado", f: (d) => insignia(d.return_status) },
      { t: "Producto", k: "product_id" }, { t: "Uds.", k: "returned_quantity", cls: "num" },
      { t: "Reembolso", f: (d) => eur(d.refund_amount), cls: "num" }, { t: "Motivo", k: "return_reason" },
    ], o.devoluciones)] : null);
}

async function cupones(cuerpo) {
  const lista = await get("/mis-cupones");
  montar(cuerpo, h("h1", {}, "Mis cupones"),
    h("p", { class: "ayuda" }, "Los cupones emitidos se aplican desde el carrito. También se muestran los canjeados en los últimos 90 días."),
    tabla([
      { t: "Código", k: "coupon_code" }, { t: "Campaña", k: "campaign_name" },
      { t: "Descuento", f: (c) => (c.discount_pct ? `${num(c.discount_pct)} %` : eur(c.discount_eur)) },
      { t: "Gasto mínimo", f: (c) => (c.min_spend_eur ? eur(c.min_spend_eur) : "—"), cls: "num" },
      { t: "Restricción", f: (c) => [c.restricted_category, c.restricted_store_id].filter(Boolean).join(" · ") || "—" },
      { t: "Válido hasta", f: (c) => fecha(c.valid_to) }, { t: "Estado", f: (c) => insignia(c.coupon_status) },
    ], lista, { sinDatos: "No tienes cupones." }));
}
