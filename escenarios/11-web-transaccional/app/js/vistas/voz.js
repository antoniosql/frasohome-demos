// Escenario 10 · voz del cliente: reseñas y NPS tras la compra (cliente); moderar, publicar y responder; temas y sentimiento.
import { get, post } from "../api.js";
import { aviso, campo, cargando, conAviso, corta, dialogo, fecha, h, insignia, montar, num, pestanas, selector, tabla, vacio } from "../ui.js";
import { soloRol, tieneRol } from "../sesion.js";

export async function render(cont, ctx) {
  const [sub] = ctx.partes;
  const staff = tieneRol("atencion", "marketing");
  const cliente = soloRol("cliente");
  const cuerpo = h("div", {}, cargando());
  const tabs = [];
  if (cliente) tabs.push({ id: "", titulo: "Mis opiniones" }, { id: "nueva", titulo: "Opinar" });
  if (staff && !cliente) tabs.push({ id: "", titulo: "Moderación" }, { id: "resumen", titulo: "Temas y sentimiento" });
  if (staff && cliente) tabs.push({ id: "moderacion", titulo: "Moderación" }, { id: "resumen", titulo: "Temas y sentimiento" });
  montar(cont, pestanas("voz", tabs, sub || ""), cuerpo);
  if (sub === "resumen" && staff) return resumen(cuerpo);
  if (sub === "moderacion" && staff) return moderacion(cuerpo, ctx);
  if (cliente && sub === "nueva") return nueva(cuerpo, ctx);
  if (cliente) return mias(cuerpo);
  return moderacion(cuerpo, ctx);
}

const estrellas = (n) => (n ? "★".repeat(n) + "☆".repeat(5 - n) : "—");
const estadoOpinion = (o) => insignia(o.publicado_flag ? "Publicada" : o.respondido_flag ? "Respondida" : "Pendiente");

// ------------------------------------------------------------------ cliente

async function mias(cuerpo) {
  const filas = await get("/mis-opiniones");
  montar(cuerpo, h("h1", {}, "Mis opiniones"),
    h("p", { class: "ayuda" }, "Las opiniones pasan por una moderación antes de publicarse en la ficha del producto."),
    tabla([
      { t: "Fecha", f: (o) => fecha(o.fecha_feedback) }, { t: "Tipo", f: (o) => (o.tipo_feedback === "nps_relacional" ? "NPS" : "Reseña") },
      { t: "Producto", f: (o) => o.product_id || "—" }, { t: "Valoración", f: (o) => (o.nps_0_10 !== null && o.nps_0_10 !== undefined ? `${o.nps_0_10} / 10` : estrellas(o.rating_1_5)) },
      { t: "Opinión", f: (o) => corta(o.texto_feedback, 80) }, { t: "Estado", f: estadoOpinion },
      { t: "Respuesta de la marca", f: (o) => corta(o.respuesta_marca, 80) },
    ], filas, { sinDatos: "Todavía no has opinado." }));
}

function nueva(cuerpo, ctx) {
  const producto = (ctx.params.get("producto") || "").toUpperCase();
  const pedido = (ctx.params.get("pedido") || "").toUpperCase();
  const tipo = selector([["review_producto", "Reseña de un producto"], ["nps_relacional", "¿Recomendarías FraSoHome?"]], "review_producto", { id: "v-tipo" });
  const prod = h("input", { id: "v-prod", value: producto, maxlength: "5", placeholder: "P1020" });
  const ped = h("input", { id: "v-ped", value: pedido, maxlength: "11", placeholder: "O-202600001" });
  const nota = selector([["", "Elige…"], ...[5, 4, 3, 2, 1].map((n) => [n, `${"★".repeat(n)} (${n})`])], "", { id: "v-nota" });
  const nps = h("input", { id: "v-nps", type: "number", min: "0", max: "10", step: "1" });
  const texto = h("textarea", { id: "v-texto", rows: 4, maxlength: 1500, required: true });
  const bloqueReview = h("div", {}, campo("Producto", prod, "El código está en el detalle de tu pedido."), campo("Valoración", nota));
  const bloqueNps = h("div", { class: "oculto" }, campo("De 0 a 10: ¿recomendarías FraSoHome a un amigo?", nps));
  tipo.addEventListener("change", () => { const r = tipo.value === "review_producto"; bloqueReview.classList.toggle("oculto", !r); bloqueNps.classList.toggle("oculto", r); });
  const msg = h("p", { class: "msg ko", role: "alert" });
  montar(cuerpo, h("h1", {}, "Opinar"),
    h("form", { class: "estrecho", onsubmit: conAviso(async (ev) => {
      ev.preventDefault();
      msg.textContent = "";
      const review = tipo.value === "review_producto";
      const cuerpoOp = { tipo: tipo.value, texto: texto.value, order_id: ped.value.trim() || null };
      if (review) Object.assign(cuerpoOp, { product_id: prod.value.trim().toUpperCase(), rating: Number(nota.value) || null });
      else cuerpoOp.nps = nps.value === "" ? null : Number(nps.value);
      try { await post("/opiniones", cuerpoOp); } catch (e) { msg.textContent = e.message; return; }
      aviso("Gracias, tu opinión se publicará tras la moderación.");
      ctx.ir("/voz");
    }) }, campo("Tipo de opinión", tipo), bloqueReview, bloqueNps, campo("Pedido (opcional)", ped), campo("Tu opinión", texto), msg,
    h("button", { type: "submit", class: "primary" }, "Enviar opinión")));
}

// ------------------------------------------------------------------ moderación

async function moderacion(cuerpo, ctx) {
  const p = ctx.params;
  const f = { pendiente: p.get("pendiente") ?? "1", tema: p.get("tema") || "", sentimiento: p.get("sentimiento") || "", tipo: p.get("tipo") || "" };
  const filas = await get("/opiniones", { pendiente: f.pendiente === "1" ? "1" : undefined, tema: f.tema, sentimiento: f.sentimiento, tipo: f.tipo, tamano: 100 });
  const pend = selector([["1", "Pendientes de moderar"], ["0", "Todas"]], f.pendiente, { "aria-label": "Estado" });
  const sent = selector([["", "Cualquier sentimiento"], "Positivo", "Neutral", "Negativo"], f.sentimiento, { "aria-label": "Sentimiento" });
  const tipo = selector([["", "Reseñas y NPS"], ["review_producto", "Reseñas"], ["nps_relacional", "NPS"]], f.tipo, { "aria-label": "Tipo" });
  const tema = h("input", { value: f.tema, placeholder: "Tema (precio, entrega…)", "aria-label": "Tema" });
  const modera = tieneRol("atencion");
  const base = soloRol("cliente") ? "/voz/moderacion" : "/voz";
  const moderar = (o) => dialogo(`Moderar ${o.feedback_id}`, [
    { k: "publicar", etiqueta: "Publicar en la ficha del producto", tipo: "select", opciones: ["Sí", "No"], valor: o.publicado_flag ? "Sí" : "No" },
    { k: "respuesta", etiqueta: "Respuesta de la marca (opcional)", tipo: "textarea", maxlength: 1000, valor: o.respuesta_marca || "" },
  ], async (v) => { await post(`/opiniones/${o.feedback_id}/moderar`, { publicar: v.publicar === "Sí", respuesta: v.respuesta }); aviso("Opinión moderada."); moderacion(cuerpo, ctx); },
  { intro: o.texto_feedback });
  montar(cuerpo, h("h1", {}, "Moderación de opiniones"),
    h("form", { class: "filtros", onsubmit: (ev) => {
      ev.preventDefault();
      const s = new URLSearchParams({ pendiente: pend.value });
      if (sent.value) s.set("sentimiento", sent.value);
      if (tipo.value) s.set("tipo", tipo.value);
      if (tema.value.trim()) s.set("tema", tema.value.trim());
      ctx.ir(`${base}?${s}`);
    } }, pend, tipo, sent, tema, h("button", { type: "submit" }, "Filtrar")),
    tabla([
      { t: "Fecha", f: (o) => fecha(o.fecha_feedback) }, { t: "Cliente", k: "customer_id" }, { t: "Producto", f: (o) => o.product_id || "—" },
      { t: "Valoración", f: (o) => (o.nps_0_10 !== null && o.nps_0_10 !== undefined ? `NPS ${o.nps_0_10}` : estrellas(o.rating_1_5)) },
      { t: "Sentimiento", f: (o) => insignia(o.sentimiento) }, { t: "Tema", f: (o) => o.tema_principal || "—" }, { t: "Opinión", f: (o) => corta(o.texto_feedback, 90) },
      { t: "Estado", f: estadoOpinion },
      modera ? { t: "", f: (o) => h("button", { type: "button", onclick: () => moderar(o) }, "Moderar") } : null,
    ].filter(Boolean), filas, { sinDatos: "No hay opiniones con esos filtros." }));
}

// ------------------------------------------------------------------ resumen

async function resumen(cuerpo) {
  const r = await get("/opiniones/resumen");
  const sentimientos = ["Positivo", "Neutral", "Negativo"];
  const temas = Object.entries(r.por_tema);
  montar(cuerpo, h("h1", {}, "Temas y sentimiento"),
    h("div", { class: "rejilla" },
      h("div", { class: "tarjeta" }, h("small", {}, "Opiniones"), h("p", { class: "grande" }, num(r.opiniones)), h("small", {}, `${num(r.publicadas)} publicadas`)),
      h("div", { class: "tarjeta" }, h("small", {}, "Valoración media"), h("p", { class: "grande" }, r.valoracion_media === null ? "—" : `${r.valoracion_media} / 5`)),
      h("div", { class: "tarjeta" }, h("small", {}, "NPS"), h("p", { class: "grande" }, r.nps === null ? "—" : num(r.nps)), h("small", {}, `${num(r.respuestas_nps)} respuestas`))),
    h("h2", {}, "Sentimiento por tema"),
    temas.length ? tabla([{ t: "Tema", f: ([t]) => t }, ...sentimientos.map((s) => ({ t: s, f: ([, v]) => num(v[s] || 0), cls: "num" })),
      { t: "Total", f: ([, v]) => num(Object.values(v).reduce((a, b) => a + b, 0)), cls: "num" }], temas.sort((a, b) => Object.values(b[1]).reduce((x, y) => x + y, 0) - Object.values(a[1]).reduce((x, y) => x + y, 0)))
      : vacio("Sin datos."));
}
