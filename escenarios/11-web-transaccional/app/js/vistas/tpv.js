// Escenario 2 · venta en tienda (TPV): abrir y cerrar caja, ticket con cobro mixto y cliente por tarjeta.
import { get, post } from "../api.js";
import { aviso, campo, cargando, conAviso, dialogo, eur, ficha, fecha, fechaHora, h, hoy, insignia, montar, num, pestanas,
  selector, tabla, vacio } from "../ui.js";
import { ambito, soloRol } from "../sesion.js";
import { devolverDeTicket } from "./devoluciones.js";

const COBROS = ["Tarjeta", "Efectivo", "Bizum", "Tarjeta regalo", "Vale", "Cupón", "Financiación"];
const redondea = (n) => Math.round(Number(n) * 100) / 100;

export async function render(cont, ctx) {
  const [sub, id] = ctx.partes;
  const cajero = soloRol("cajero");
  const tabs = [{ id: "", titulo: "Caja" }];
  if (cajero) tabs.push({ id: "ticket", titulo: "Nuevo ticket" });
  tabs.push({ id: "tickets", titulo: "Tickets" });
  const cuerpo = h("div", {}, cargando());
  const tiendas = ambito("store");
  montar(cont, h("p", { class: "ayuda" }, tiendas.length ? `Tienda ${tiendas.join(", ")}` : null),
    pestanas("tpv", tabs, sub === "ticket" ? "ticket" : sub === "tickets" ? "tickets" : ""), cuerpo);
  const tienda = ctx.params.get("tienda") || undefined;
  if (sub === "ticket" && cajero) return nuevoTicket(cuerpo, ctx, tienda);
  if (sub === "tickets" && id) return verTicket(cuerpo, id, ctx);
  if (sub === "tickets") return tickets(cuerpo, ctx, tienda);
  return caja(cuerpo, ctx, tienda);
}

// ------------------------------------------------------------------ caja

async function caja(cuerpo, ctx, tienda) {
  const abiertas = await get("/tpv/caja", { tienda });
  const cajero = soloRol("cajero");
  const recargar = () => caja(cuerpo, ctx, tienda);

  const cerrar = (c) => dialogo(`Cerrar ${c.till_id}`, [
    { k: "efectivo", etiqueta: "Efectivo contado (€)", tipo: "number", min: 0, step: 0.01, req: true },
  ], async (v) => {
    const r = await post("/tpv/caja/cerrar", { tienda, caja: c.till_id, efectivo_contado: v.efectivo });
    aviso("Caja cerrada.");
    resultadoCierre(cuerpo, r, recargar);
  }, { enviar: "Cerrar caja", intro: `Cuenta el efectivo del cajón. Efectivo inicial ${eur(c.opening_cash)}.` });

  const idCaja = h("input", { value: "CAJ01", pattern: "CAJ\\d{2}", maxlength: "5", required: true });
  const inicial = h("input", { type: "number", min: "0", max: "5000", step: "0.01", value: "100", required: true });
  montar(cuerpo,
    h("h1", {}, "Cajas abiertas"),
    tabla([
      { t: "Caja", k: "till_id" }, { t: "Cajero", f: (c) => c.cajero || c.cashier_id }, { t: "Apertura", f: (c) => fechaHora(c.opened_at) },
      { t: "Efectivo inicial", f: (c) => eur(c.opening_cash), cls: "num" }, { t: "Tickets", k: "tickets", cls: "num" },
      { t: "Ventas", f: (c) => eur(c.ventas), cls: "num" },
      cajero ? { t: "", f: (c) => h("button", { type: "button", onclick: () => cerrar(c) }, "Cerrar caja") } : null,
    ].filter(Boolean), abiertas, { sinDatos: "No hay ninguna caja abierta en la tienda." }),
    cajero ? h("section", { class: "tarjeta estrecha" }, h("h2", {}, "Abrir caja"),
      h("form", { onsubmit: conAviso(async (ev) => {
        ev.preventDefault();
        await post("/tpv/caja/abrir", { tienda, caja: idCaja.value.trim().toUpperCase(), efectivo_inicial: Number(inicial.value) });
        aviso("Caja abierta."); recargar();
      }) }, campo("Caja", idCaja, "Formato CAJ01"), campo("Efectivo inicial (€)", inicial),
        h("button", { type: "submit", class: "primary" }, "Abrir caja"))) : null);
}

function resultadoCierre(cuerpo, r, recargar) {
  const etiquetas = { till_session_id: "Sesión", expected_cash: "Efectivo esperado", counted_cash: "Efectivo contado",
    cash_difference: "Descuadre", cash_diff: "Descuadre", tickets: "Tickets", sales_total: "Ventas" };
  montar(cuerpo, h("h1", {}, "Caja cerrada"),
    ficha(Object.entries(r).map(([k, v]) => [etiquetas[k] || k, typeof v === "number" && /cash|total|diff/.test(k) ? eur(v) : String(v)])),
    h("button", { type: "button", class: "primary", onclick: recargar }, "Volver a las cajas"));
}

// ------------------------------------------------------------------ nuevo ticket

async function nuevoTicket(cuerpo, ctx, tienda) {
  const abiertas = (await get("/tpv/caja", { tienda }));
  if (!abiertas.length) {
    return montar(cuerpo, h("h1", {}, "Nuevo ticket"), vacio("Abre una caja antes de vender."),
      h("a", { class: "boton primary", href: "#/tpv" }, "Ir a la caja"));
  }
  const e = { caja: abiertas[0].till_id, cliente: null, lineas: [], cupon: "", presupuesto: null, pagos: [] };
  const zona = h("div", {});
  montar(cuerpo, h("h1", {}, "Nuevo ticket"), zona);

  async function calcular() {
    if (!e.lineas.length) { e.presupuesto = null; return; }
    e.presupuesto = await post("/tpv/presupuesto", { tienda, customer_id: e.cliente && e.cliente.customer_id,
      lineas: e.lineas.map((l) => ({ product_id: l.product_id, cantidad: l.cantidad })), cupon: e.cupon || null });
  }
  const refrescar = async () => { try { await calcular(); } catch (err) { e.presupuesto = null; aviso(err.message, "ko"); } pintar(); };
  const neto = () => (e.presupuesto ? redondea(e.presupuesto.totales.net_total) : 0);
  const cobrado = () => redondea(e.pagos.reduce((s, p) => s + (Number(p.importe) || 0), 0));

  // --- cliente
  const qCli = h("input", { placeholder: "Tarjeta de fidelización, email, teléfono o nombre", "aria-label": "Buscar cliente" });
  const resultadosCli = h("div", { class: "fila" });
  const buscarCliente = conAviso(async () => {
    const t = qCli.value.trim();
    if (!t) return;
    const esTarjeta = /^[A-Za-z]{2,4}-?\d{4,}$/.test(t) && !/@/.test(t) && !/^C\d{4}$/i.test(t);
    const r = await get("/tpv/clientes", esTarjeta ? { tarjeta: t } : { q: t });
    montar(resultadosCli, r.length ? r.map((c) => h("button", { type: "button", class: "chip", onclick: async () => {
      e.cliente = c; qCli.value = ""; montar(resultadosCli); await refrescar();
    } }, `${c.customer_id} · ${c.first_name} ${c.last_name} · ${c.loyalty_tier || "sin nivel"}`)) : h("small", {}, "Sin coincidencias."));
  });

  // --- productos
  const qProd = h("input", { placeholder: "Producto: nombre, marca o código P1020", "aria-label": "Buscar producto" });
  const resultadosProd = h("div", { class: "lista-plana" });
  const buscarProducto = conAviso(async () => {
    const t = qProd.value.trim();
    if (!t) return;
    const r = await get("/catalogo/productos", { q: t, tamano: 8 });
    montar(resultadosProd, r.productos.length ? r.productos.map((p) => h("div", { class: "fila entre" },
      h("span", {}, `${p.product_id} · ${p.product_name} · ${eur(p.sale_price)}`),
      h("button", { type: "button", onclick: async () => {
        const l = e.lineas.find((x) => x.product_id === p.product_id);
        if (l) l.cantidad = Math.min(20, l.cantidad + 1); else e.lineas.push({ product_id: p.product_id, nombre: p.product_name, cantidad: 1 });
        await refrescar();
      } }, "Añadir"))) : h("small", {}, "Sin coincidencias."));
  });

  function pintar() {
    const t = e.presupuesto && e.presupuesto.totales;
    const det = {};
    for (const l of (e.presupuesto && e.presupuesto.lineas) || []) det[l.product_id] = l;
    const pendiente = redondea(neto() - cobrado());
    const cuponTxt = h("input", { value: e.cupon, placeholder: "Cupón", maxlength: "30", "aria-label": "Cupón" });
    const cajaSel = selector(abiertas.map((c) => [c.till_id, `${c.till_id} · ${c.cajero || c.cashier_id}`]), e.caja, { "aria-label": "Caja" });
    cajaSel.addEventListener("change", () => { e.caja = cajaSel.value; });

    montar(zona,
      h("div", { class: "dos" },
        h("section", {},
          h("h2", {}, "1 · Cliente (opcional)"),
          e.cliente
            ? h("div", { class: "fila" }, h("strong", {}, `${e.cliente.first_name} ${e.cliente.last_name}`), h("small", {}, `${e.cliente.customer_id} · ${e.cliente.loyalty_tier || "sin nivel"} · ${num(e.cliente.loyalty_points)} puntos`),
              h("button", { type: "button", onclick: async () => { e.cliente = null; await refrescar(); } }, "Quitar"))
            : [h("form", { class: "fila", onsubmit: (ev) => { ev.preventDefault(); buscarCliente(ev); } }, qCli, h("button", { type: "submit" }, "Buscar")), resultadosCli],
          h("h2", {}, "2 · Productos"),
          h("form", { class: "fila", onsubmit: (ev) => { ev.preventDefault(); buscarProducto(ev); } }, qProd, h("button", { type: "submit" }, "Buscar")),
          resultadosProd),
        h("section", { class: "tarjeta" },
          h("h2", {}, "Ticket"),
          campo("Caja", cajaSel),
          e.lineas.length ? h("div", { class: "tabla-caja" }, h("table", {}, h("tbody", {}, e.lineas.map((l) => {
            const d = det[l.product_id] || {};
            const cant = h("input", { type: "number", min: "1", max: "20", value: l.cantidad, "aria-label": `Cantidad de ${l.nombre}` });
            cant.addEventListener("change", async () => { l.cantidad = Math.max(1, Math.min(20, Number(cant.value) || 1)); await refrescar(); });
            return h("tr", {}, h("td", {}, l.nombre, d.discount_amount ? h("small", {}, ` −${eur(d.discount_amount)} promo`) : null),
              h("td", {}, cant), h("td", { class: "num" }, eur(d.line_amount)),
              h("td", {}, h("button", { type: "button", "aria-label": `Quitar ${l.nombre}`, onclick: async () => { e.lineas = e.lineas.filter((x) => x !== l); await refrescar(); } }, "✕")));
          })))) : vacio("Añade productos."),
          h("div", { class: "fila" }, cuponTxt, h("button", { type: "button", onclick: async () => { e.cupon = cuponTxt.value.trim().toUpperCase(); await refrescar(); } }, "Aplicar cupón")),
          t ? h("dl", { class: "ficha total" },
            h("dt", {}, "Subtotal"), h("dd", {}, eur(t.gross_total)),
            h("dt", {}, "Promociones"), h("dd", {}, `−${eur(t.promo_discount)}`),
            t.coupon_discount ? [h("dt", {}, "Cupón"), h("dd", {}, `−${eur(t.coupon_discount)}`)] : null,
            h("dt", {}, "Total"), h("dd", { class: "grande" }, eur(t.net_total))) : null)),
      t ? h("section", {},
        h("h2", {}, "3 · Cobro"),
        e.pagos.map((p, i) => h("div", { class: "fila" },
          selector(COBROS, p.metodo, { "aria-label": "Método", onchange: (ev) => { p.metodo = ev.target.value; } }),
          h("input", { type: "number", min: "0.01", step: "0.01", value: p.importe, "aria-label": "Importe", onchange: (ev) => { p.importe = Number(ev.target.value); pintar(); } }),
          h("input", { value: p.referencia || "", placeholder: "Referencia", maxlength: "100", "aria-label": "Referencia", onchange: (ev) => { p.referencia = ev.target.value; } }),
          h("button", { type: "button", "aria-label": "Quitar cobro", onclick: () => { e.pagos.splice(i, 1); pintar(); } }, "✕"))),
        h("div", { class: "fila" },
          h("button", { type: "button", onclick: () => { e.pagos = [{ metodo: "Tarjeta", importe: neto() }]; pintar(); } }, "Cobrar todo con tarjeta"),
          h("button", { type: "button", disabled: e.pagos.length >= 5, onclick: () => { e.pagos.push({ metodo: "Efectivo", importe: Math.max(0, pendiente) || 0.01 }); pintar(); } }, "Añadir cobro")),
        h("p", { class: pendiente === 0 && e.pagos.length ? "msg ok" : "msg" }, e.pagos.length ? (pendiente === 0 ? "Cobro completo." : `Pendiente de cobrar: ${eur(pendiente)}`) : "Añade el cobro."),
        h("button", { type: "button", class: "primary", disabled: !e.pagos.length || pendiente !== 0, onclick: conAviso(async () => {
          const cuerpoTicket = { tienda, caja: e.caja, customer_id: e.cliente && e.cliente.customer_id,
            lineas: e.lineas.map((l) => ({ product_id: l.product_id, cantidad: l.cantidad })), cupon: e.cupon || null,
            pagos: e.pagos.map((p) => ({ metodo: p.metodo, importe: redondea(p.importe), referencia: p.referencia || null })) };
          const r = await post("/tpv/tickets", cuerpoTicket, { idem: true });
          aviso(`Ticket ${r.ticket_id} emitido.`);
          ctx.ir(`/tpv/tickets/${r.ticket_id}`);
        }) }, "Cobrar y emitir ticket")) : null);
  }
  pintar();
}

// ------------------------------------------------------------------ tickets

async function tickets(cuerpo, ctx, tienda) {
  const dia = ctx.params.get("fecha") || hoy();
  const lista = await get("/tpv/tickets", { tienda, fecha: dia });
  const f = h("input", { type: "date", value: dia, "aria-label": "Fecha" });
  montar(cuerpo, h("h1", {}, "Tickets del día"),
    h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); ctx.ir(`/tpv/tickets?fecha=${f.value}`); } },
      f, h("button", { type: "submit" }, "Ver")),
    tabla([
      { t: "Ticket", k: "ticket_id" }, { t: "Hora", f: (t) => fechaHora(t.ticket_at) }, { t: "Caja", k: "till_id" },
      { t: "Cliente", f: (t) => t.customer_id || "—" }, { t: "Líneas", k: "lineas", cls: "num" },
      { t: "Importe", f: (t) => eur(t.ticket_net_amount), cls: "num" },
    ], lista, { alClic: (t) => ctx.ir(`/tpv/tickets/${t.ticket_id}`), sinDatos: `No hay tickets el ${fecha(dia)}.` }),
    h("p", { class: "ayuda" }, `${num(lista.length)} tickets · ${eur(lista.reduce((s, t) => s + Number(t.ticket_net_amount || 0), 0))}`));
}

async function verTicket(cuerpo, id, ctx) {
  const t = await get(`/tpv/tickets/${encodeURIComponent(id)}`);
  const cajero = soloRol("cajero");
  montar(cuerpo,
    h("p", {}, h("a", { href: "#/tpv/tickets" }, "‹ Tickets")),
    h("h1", {}, `Ticket ${t.ticket_id}`),
    ficha([["Fecha", fechaHora(t.ticket_at)], ["Tienda · caja", `${t.store_id} · ${t.till_id}`], ["Cajero", t.cashier_employee_id || t.cashier_id],
      ["Cliente", t.customer_id], ["Bruto", eur(t.ticket_gross_amount)], ["Descuentos", eur(t.ticket_discount_amount)],
      ["Total", h("strong", {}, eur(t.ticket_net_amount))], t.coupon_instance_id ? ["Cupón", t.coupon_instance_id] : null]),
    h("h2", {}, "Líneas"),
    tabla([
      { t: "Producto", f: (l) => `${l.product_id} · ${l.product_description}` }, { t: "Cant.", k: "quantity", cls: "num" },
      { t: "Precio", f: (l) => eur(l.unit_price), cls: "num" },
      { t: "Descuento", f: (l) => (l.discount_amount ? `−${eur(l.discount_amount)}` : "—"), cls: "num" },
      { t: "Importe", f: (l) => eur(l.line_amount), cls: "num" },
      cajero ? { t: "", f: (l) => (l.devolvible > 0
        ? h("button", { type: "button", onclick: () => devolverDeTicket(l, t, () => verTicket(cuerpo, id, ctx)) }, "Devolver") : h("small", {}, "Devuelto")) } : null,
    ].filter(Boolean), t.lineas),
    h("h2", {}, "Cobros"),
    tabla([{ t: "Método", k: "payment_method" }, { t: "Importe", f: (p) => eur(p.paid_amount), cls: "num" },
      { t: "Referencia", f: (p) => p.authorization_reference || "—" }, { t: "Estado", f: (p) => insignia(p.payment_status) }], t.pagos),
    h("div", { class: "fila no-imprimir" }, h("button", { type: "button", onclick: () => window.print() }, "Imprimir")));
}
