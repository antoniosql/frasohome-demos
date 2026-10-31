// Escenario 3 · devoluciones: solicitud online (desde Pedidos), devolución en tienda, reembolso y reingreso a stock.
import { get, post } from "../api.js";
import { aviso, cargando, conAviso, dialogo, eur, ficha, fechaHora, h, insignia, montar, paginador, pestanas,
  selector, tabla } from "../ui.js";
import { soloRol, tieneRol } from "../sesion.js";

const TAMANO = 30;
const ESTADOS = ["", "Pendiente", "Aceptada", "Rechazada", "Reembolsada"];
const SIGUIENTES = { Pendiente: ["Aceptada", "Rechazada"], Aceptada: ["Reembolsada"] };
const REEMBOLSOS = ["Tarjeta", "Efectivo", "Vale", "Tarjeta regalo", "Transferencia", "Cupón"];

export async function render(cont, ctx) {
  const [sub] = ctx.partes;
  const cajero = soloRol("cajero");
  const tabs = [{ id: "", titulo: "Devoluciones" }];
  if (cajero) tabs.push({ id: "nueva", titulo: "Devolver en tienda" });
  const cuerpo = h("div", {}, cargando());
  montar(cont, pestanas("devoluciones", tabs, sub === "nueva" ? "nueva" : ""), cuerpo);
  if (sub === "nueva" && cajero) return nueva(cuerpo, ctx);
  if (sub && /^R[OT]-/.test(sub)) return detalle(cuerpo, sub, ctx);
  return lista(cuerpo, ctx);
}

// ------------------------------------------------------------------ listado y detalle

async function lista(cuerpo, ctx) {
  const p = ctx.params;
  const pagina = Number(p.get("pagina") || 1);
  const estado = p.get("estado") || "";
  const staff = tieneRol("atencion", "direccion");
  const cliente = (p.get("cliente") || "").toUpperCase();
  const r = await get("/devoluciones", { pagina, tamano: TAMANO, estado, cliente: staff ? cliente : undefined });
  const ir = (n, e = estado, c = cliente) => {
    const s = new URLSearchParams();
    if (e) s.set("estado", e);
    if (c) s.set("cliente", c);
    if (n > 1) s.set("pagina", n);
    ctx.ir("/devoluciones" + (s.toString() ? "?" + s : ""));
  };
  const sel = selector(ESTADOS.map((e) => [e, e || "Todos los estados"]), estado, { "aria-label": "Estado" });
  const cli = staff ? h("input", { value: cliente, placeholder: "Cliente (C0001)", maxlength: "5", "aria-label": "Cliente" }) : null;
  montar(cuerpo, h("h1", {}, "Devoluciones"),
    soloRol("cliente") ? h("p", { class: "ayuda" }, "Para devolver un artículo abre el pedido entregado en ", h("a", { href: "#/pedidos" }, "Pedidos"), " y pulsa «Devolver».") : null,
    h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); ir(1, sel.value, cli ? cli.value.trim().toUpperCase() : ""); } },
      sel, cli, h("button", { type: "submit" }, "Filtrar")),
    tabla([
      { t: "Devolución", k: "return_id" }, { t: "Fecha", f: (d) => fechaHora(d.returned_at) },
      { t: "Canal", k: "return_channel" }, { t: "Tienda", f: (d) => d.store_id || "Online" }, { t: "Cliente", f: (d) => d.customer_id || "—" },
      { t: "Origen", f: (d) => d.original_order_id || d.original_ticket_id || "—" },
      { t: "Estado", f: (d) => insignia(d.return_status) }, { t: "Importe", f: (d) => eur(d.importe), cls: "num" },
    ], r.devoluciones, { alClic: (d) => ctx.ir(`/devoluciones/${d.return_id}`), sinDatos: "No hay devoluciones." }),
    paginador(pagina, r.total, TAMANO, (n) => ir(n)));
}

async function detalle(cuerpo, id, ctx) {
  const d = await get(`/devoluciones/${encodeURIComponent(id)}`);
  const gestiona = tieneRol("atencion", "tienda");
  const acciones = gestiona ? (SIGUIENTES[d.return_status] || []).map((nuevo) =>
    h("button", { type: "button", class: nuevo === "Rechazada" ? "" : "primary", onclick: conAviso(async () => {
      await post(`/devoluciones/${d.return_id}/estado`, { estado: nuevo });
      aviso(nuevo === "Reembolsada" ? "Reembolsada: la mercancía vuelve al stock." : `Devolución ${nuevo.toLowerCase()}.`);
      detalle(cuerpo, id, ctx);
    }) }, nuevo === "Aceptada" ? "Aceptar" : nuevo === "Rechazada" ? "Rechazar" : "Marcar como reembolsada")) : [];
  montar(cuerpo,
    h("p", {}, h("a", { href: "#/devoluciones" }, "‹ Devoluciones")),
    h("h1", {}, `Devolución ${d.return_id} `, insignia(d.return_status)),
    ficha([["Fecha", fechaHora(d.returned_at)], ["Canal", d.return_channel], ["Tienda", d.store_id || "Online"], ["Cliente", d.customer_id],
      d.original_order_id ? ["Pedido", h("a", { href: `#/pedidos/${d.original_order_id}` }, d.original_order_id)] : null,
      d.original_ticket_id ? ["Ticket", h("a", { href: `#/tpv/tickets/${d.original_ticket_id}` }, d.original_ticket_id)] : null,
      ["Método de devolución", d.return_method], ["Método de reembolso", d.refund_method], ["Notas", d.notes],
      ["Importe total", h("strong", {}, eur(d.importe_total))]]),
    acciones.length ? h("div", { class: "fila" }, acciones) : null,
    h("h2", {}, "Líneas"),
    tabla([{ t: "Producto", k: "product_id" }, { t: "Uds.", k: "returned_quantity", cls: "num" },
      { t: "Reembolso", f: (l) => eur(l.refund_amount), cls: "num" }, { t: "Motivo", k: "return_reason" },
      { t: "Línea original", f: (l) => l.original_ticket_line_id || l.original_order_line_id || "—" }], d.lineas));
}

// ------------------------------------------------------------------ devolver en tienda (cajero)

function dialogoTienda(linea, extra, alTerminar) {
  return dialogo(`Devolver ${linea.product_description}`, [
    { k: "cantidad", etiqueta: `Unidades (hasta ${linea.devolvible})`, tipo: "number", min: 1, max: linea.devolvible, step: 1, valor: 1, req: true },
    { k: "motivo", etiqueta: "Motivo", maxlength: 200, req: true },
    { k: "metodo", etiqueta: "Reembolso por", tipo: "select", opciones: REEMBOLSOS, valor: "Tarjeta" },
    { k: "notas", etiqueta: "Notas (opcional)", maxlength: 500 },
  ], async (v) => {
    const r = await post("/devoluciones/tienda", { ...extra, cantidad: v.cantidad, motivo: v.motivo, metodo_reembolso: v.metodo, notas: v.notas }, { idem: true });
    aviso(`Devolución ${r.return_id} registrada.`);
    if (alTerminar) alTerminar(r);
    location.hash = `#/devoluciones/${r.return_id}`;
  }, { enviar: "Registrar devolución" });
}

/** Devolución en tienda de una línea de ticket (se usa desde el detalle del ticket). */
export const devolverDeTicket = (linea, ticket, alTerminar) => dialogoTienda(linea, { ticket_line_id: linea.ticket_line_id }, alTerminar);

async function nueva(cuerpo, ctx) {
  const origen = h("input", { placeholder: "T-000123 (ticket) u O-000000123 (pedido online)", required: true, maxlength: "20", "aria-label": "Ticket o pedido" });
  const zona = h("div", {});
  const buscar = conAviso(async (ev) => {
    ev.preventDefault();
    const id = origen.value.trim().toUpperCase();
    montar(zona, cargando());
    if (/^T-\d{6}$/.test(id)) {
      const t = await get(`/tpv/tickets/${id}`);
      montar(zona, h("h2", {}, `Ticket ${t.ticket_id} · ${fechaHora(t.ticket_at)}`), lineas(t.lineas, "ticket_line_id",
        (l) => dialogoTienda(l, { ticket_line_id: l.ticket_line_id }, () => buscar(ev))));
    } else if (/^O-\d{9}$/.test(id)) {
      const o = await get(`/tpv/pedidos/${id}`);
      montar(zona, h("h2", {}, `Pedido online ${o.order_id} `, insignia(o.order_status)),
        o.order_status === "Entregado" || o.order_status === "Devuelto Parcial" ? null
          : h("p", { class: "msg ko" }, "Solo se pueden devolver pedidos entregados."),
        lineas(o.lineas, "order_line_id", (l) => dialogoTienda(l, { order_line_id: l.order_line_id }, () => buscar(ev))));
    } else {
      montar(zona, h("p", { class: "msg ko", role: "alert" }, "Escribe un ticket (T-000123) o un pedido online (O-000000123)."));
    }
  });
  montar(cuerpo, h("h1", {}, "Devolver en tienda"),
    h("p", { class: "ayuda" }, "Busca la compra original: un ticket de tienda o un pedido online ya entregado."),
    h("form", { class: "filtros", onsubmit: buscar }, origen, h("button", { type: "submit", class: "primary" }, "Buscar")), zona);
  origen.focus();
}

function lineas(filas, idCampo, devolver) {
  return tabla([
    { t: "Producto", f: (l) => `${l.product_id} · ${l.product_description}` }, { t: "Comprado", k: "quantity", cls: "num" },
    { t: "Importe", f: (l) => eur(l.line_amount), cls: "num" }, { t: "Por devolver", k: "devolvible", cls: "num" },
    { t: "", f: (l) => (l.devolvible > 0 ? h("button", { type: "button", onclick: () => devolver(l) }, "Devolver") : h("small", {}, "Devuelto")) },
  ], filas);
}
