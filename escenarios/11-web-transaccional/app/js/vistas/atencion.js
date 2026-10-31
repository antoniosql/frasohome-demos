// Escenario 9 · atención al cliente: bandeja por prioridad y SLA, conversación, resolución con compensación y CSAT.
import { get, post } from "../api.js";
import { aviso, campo, cargando, conAviso, dialogo, eur, fechaHora, ficha, h, insignia, montar, selector, tabla } from "../ui.js";

export const TIPOS = ["devolucion", "info_producto", "entrega", "defecto", "stock_tienda", "cupon", "fidelizacion"];
export const CANALES = ["Chat", "WhatsApp", "Email", "Tienda", "Teléfono", "Web"];
const PRIORIDADES = ["Alta", "Media", "Baja"];
const ESTADOS = [["", "Abiertos"], ["Pendiente", "Pendientes"], ["Escalado", "Escalados"], ["Resuelto", "Resueltos"]];

export async function render(cont, ctx) {
  const [id] = ctx.partes;
  const cuerpo = h("div", {}, cargando());
  montar(cont, cuerpo);
  if (id) return detalle(cuerpo, id, ctx);
  return bandeja(cuerpo, ctx);
}

/** Conversación del caso como lista de mensajes. */
export function conversacion(caso) {
  return h("div", { class: "conversacion" }, (caso.conversacion || []).map((m) => h("div", { class: "mensaje " + (m.autor === "agente" ? "agente" : "") },
    h("small", {}, `${m.autor === "agente" ? `Atención${m.agente_id ? " · " + m.agente_id : ""}` : "Cliente"} · ${fechaHora(m.fecha)}`), h("p", {}, m.texto))));
}

export const sla = (c) => (c.estado_resolucion === "Resuelto"
  ? h("span", {}, c.sla_horas === null || c.sla_horas === undefined ? "Resuelto" : `Resuelto en ${c.sla_horas} h`)
  : c.vencido ? h("span", { class: "insignia ko" }, "Vencido") : h("span", {}, `Vence ${fechaHora(c.vence)}`));

// ------------------------------------------------------------------ bandeja

function nuevoCaso(ctx, cliente) {
  return dialogo("Abrir un caso", [
    { k: "customer_id", etiqueta: "Cliente", valor: cliente || "", patron: "C\\d{4}", maxlength: 5, req: true, ayuda: "Por ejemplo C0006" },
    { k: "tipo_caso", etiqueta: "Tipo de caso", tipo: "select", opciones: TIPOS, valor: "info_producto" },
    { k: "canal", etiqueta: "Canal", tipo: "select", opciones: CANALES, valor: "Teléfono" },
    { k: "prioridad", etiqueta: "Prioridad", tipo: "select", opciones: PRIORIDADES, valor: "Media" },
    { k: "order_id", etiqueta: "Pedido (opcional)", maxlength: 11, ayuda: "O-202600001" },
    { k: "ticket_id", etiqueta: "Ticket (opcional)", maxlength: 8 },
    { k: "store_id", etiqueta: "Tienda (opcional)", maxlength: 6 },
    { k: "texto", etiqueta: "Qué cuenta el cliente", tipo: "textarea", maxlength: 2000, req: true },
  ], async (v) => {
    const c = await post("/atencion/casos", { ...v, customer_id: v.customer_id.toUpperCase() });
    aviso(`Caso ${c.id} abierto.`);
    ctx.ir(`/atencion/${c.id}`);
  }, { enviar: "Abrir caso" });
}

async function bandeja(cuerpo, ctx) {
  const p = ctx.params;
  const estado = p.get("estado") || "", prioridad = p.get("prioridad") || "", cliente = (p.get("cliente") || "").toUpperCase();
  const filas = await get("/atencion/casos", { estado, prioridad, cliente: cliente || undefined, tamano: 200 });
  const e = selector(ESTADOS, estado, { "aria-label": "Estado" });
  const pr = selector([["", "Todas las prioridades"], ...PRIORIDADES], prioridad, { "aria-label": "Prioridad" });
  const cl = h("input", { value: cliente, placeholder: "Cliente (C0001)", maxlength: "5", "aria-label": "Cliente" });
  montar(cuerpo,
    h("div", { class: "fila entre" }, h("h1", {}, "Bandeja de atención"),
      h("button", { type: "button", class: "primary", onclick: () => nuevoCaso(ctx, "") }, "Abrir caso")),
    h("form", { class: "filtros", onsubmit: (ev) => {
      ev.preventDefault();
      const s = new URLSearchParams();
      if (e.value) s.set("estado", e.value);
      if (pr.value) s.set("prioridad", pr.value);
      if (cl.value.trim()) s.set("cliente", cl.value.trim().toUpperCase());
      ctx.ir("/atencion" + (s.toString() ? "?" + s : ""));
    } }, e, pr, cl, h("button", { type: "submit" }, "Filtrar")),
    h("p", { class: "ayuda" }, "Primero los vencidos, luego por prioridad y antigüedad. Objetivos de SLA: Alta 4 h, Media 24 h, Baja 72 h."),
    tabla([
      { t: "Caso", k: "service_ticket_id" }, { t: "Apertura", f: (c) => fechaHora(c.fecha_apertura) }, { t: "Cliente", k: "customer_id" },
      { t: "Canal", k: "canal_soporte" }, { t: "Tipo", k: "tipo_caso" }, { t: "Prioridad", f: (c) => insignia(c.prioridad) },
      { t: "Estado", f: (c) => insignia(c.estado_resolucion) }, { t: "Sentimiento", f: (c) => (c.sentimiento_inicial ? insignia(c.sentimiento_inicial) : "—") },
      { t: "SLA", f: sla }, { t: "Agente", f: (c) => c.agente_id || "—" },
    ], filas, { alClic: (c) => ctx.ir(`/atencion/${c.id}`), sinDatos: "No hay casos con esos filtros." }));
  if (p.get("nuevo")) nuevoCaso(ctx, p.get("nuevo"));
}

// ------------------------------------------------------------------ caso

async function detalle(cuerpo, id, ctx) {
  const c = await get(`/atencion/casos/${encodeURIComponent(id)}`);
  const recargar = () => detalle(cuerpo, id, ctx);
  const cl = c.cliente;
  const texto = h("textarea", { rows: 3, maxlength: 2000, placeholder: "Escribe una respuesta al cliente…" });
  const abierto = c.estado_resolucion !== "Resuelto";
  montar(cuerpo,
    h("p", {}, h("a", { href: "#/atencion" }, "‹ Bandeja")),
    h("h1", {}, `Caso ${c.id} `, insignia(c.estado_resolucion), " ", insignia(c.prioridad)),
    h("div", { class: "dos" },
      h("section", {}, h("h2", {}, "Caso"), ficha([
        ["Apertura", fechaHora(c.fecha_apertura)], ["SLA", sla(c)], ["Canal", c.canal_soporte], ["Tipo", `${c.tipo_caso} · ${c.subtipo_caso}`],
        ["Sentimiento inicial", c.sentimiento_inicial], ["Agente", c.agente_id],
        c.order_id ? ["Pedido", h("a", { href: `#/pedidos/${c.order_id}` }, c.order_id)] : null,
        c.ticket_id ? ["Ticket", h("a", { href: `#/tpv/tickets/${c.ticket_id}` }, c.ticket_id)] : null, c.store_id ? ["Tienda", c.store_id] : null,
        c.importe_compensacion_eur ? ["Compensación", `${eur(c.importe_compensacion_eur)}${c.cupon_compensacion ? ` · cupón ${c.cupon_compensacion}` : ""}`] : null,
        c.csat_1_5 ? ["CSAT", `${"★".repeat(c.csat_1_5)}${"☆".repeat(5 - c.csat_1_5)}`] : null])),
      cl ? h("section", {}, h("h2", {}, "Cliente"), ficha([["Cliente", h("a", { href: `#/clientes/${cl.customer_id}` }, `${cl.customer_id} · ${cl.first_name} ${cl.last_name}`)],
        ["Email", cl.email], ["Teléfono", cl.phone], ["Nivel", cl.loyalty_tier], ["Estado", insignia(cl.customer_status)]])) : null),
    h("h2", {}, "Conversación"), conversacion(c),
    abierto ? h("form", { onsubmit: conAviso(async (ev) => {
      ev.preventDefault();
      if (!texto.value.trim()) return;
      await post(`/atencion/casos/${c.id}/mensajes`, { texto: texto.value }); aviso("Mensaje enviado."); recargar();
    }) }, campo("Responder", texto), h("div", { class: "fila" },
      h("button", { type: "submit" }, "Enviar mensaje"),
      h("button", { type: "button", class: "primary", onclick: () => dialogo("Resolver el caso", [
        { k: "estado", etiqueta: "Resultado", tipo: "select", opciones: ["Resuelto", "Escalado"], valor: "Resuelto" },
        { k: "resolucion", etiqueta: "Mensaje de cierre al cliente", tipo: "textarea", maxlength: 2000, req: true },
        { k: "tipo", etiqueta: "Compensación", tipo: "select", opciones: [["ninguna", "Ninguna"], ["cupon", "Cupón de importe fijo"], ["reembolso", "Reembolso (anotado)"]], valor: "ninguna" },
        { k: "valor", etiqueta: "Importe de la compensación (€, 1 a 100)", tipo: "number", min: 1, max: 100, step: 1 }], async (v) => {
        await post(`/atencion/casos/${c.id}/resolver`, { estado: v.estado, resolucion: v.resolucion, compensacion: { tipo: v.tipo, valor: v.valor } });
        aviso(v.estado === "Resuelto" ? "Caso resuelto." : "Caso escalado."); recargar();
      }, { enviar: "Guardar", intro: "El cupón se emite en SQL con 30 días de validez." }) }, "Resolver o escalar"))) : null);
}
