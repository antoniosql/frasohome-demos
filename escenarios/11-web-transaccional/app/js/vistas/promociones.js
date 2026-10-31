// Escenario 8 · promociones: calendario por ámbito y canal, combinabilidad, umbral de cesta y margen mínimo.
import { get, post, put } from "../api.js";
import { ahoraLocal, aLocal, aviso, cargando, dialogo, eur, fechaHora, h, insignia, montar, num, selector, sino, tabla } from "../ui.js";

const TIPOS = ["descuento_pct", "bundle", "envio_gratis", "2a_unidad", "cupon_importe", "puntos", "regalo", "outlet"];
const AMBITOS = ["categoria", "categoria_tienda", "campana"];
const CANALES = ["EMAIL", "SMS", "PUSH", "WEB"];
const VIGENCIAS = [["todas", "Todas"], ["activas", "Vigentes ahora"], ["futuras", "Futuras"], ["pasadas", "Terminadas"]];

export async function render(cont, ctx) {
  const vigencia = ctx.params.get("vigencia") || "activas";
  const cuerpo = h("div", {}, cargando());
  montar(cont, cuerpo);
  await pintar(cuerpo, ctx, vigencia);
}

function campos(p = {}) {
  const n = (v) => (v === null || v === undefined ? "" : v);
  return [
    { k: "nombre", etiqueta: "Nombre", valor: n(p.promo_name), maxlength: 200, req: true },
    { k: "inicio", etiqueta: "Inicio", tipo: "datetime-local", valor: p.starts_at ? aLocal(p.starts_at) : ahoraLocal(0), req: true },
    { k: "fin", etiqueta: "Fin", tipo: "datetime-local", valor: p.ends_at ? aLocal(p.ends_at) : ahoraLocal(14), req: true },
    { k: "ambito", etiqueta: "Ámbito", tipo: "select", opciones: AMBITOS, valor: p.scope_type || "categoria" },
    { k: "ambito_id", etiqueta: "Ámbito: valor", valor: n(p.scope_id), maxlength: 150, req: true,
      ayuda: "Categoría (Muebles), categoría y tienda (Muebles|S001) o código de campaña (CAM-2026-001)." },
    { k: "tipo", etiqueta: "Tipo", tipo: "select", opciones: TIPOS, valor: p.promo_type || "descuento_pct" },
    { k: "descuento_pct", etiqueta: "Descuento (%)", tipo: "number", min: 0, max: 100, step: 0.5, valor: n(p.discount_pct) },
    { k: "descuento_eur", etiqueta: "Descuento (€)", tipo: "number", min: 0, step: 0.5, valor: n(p.discount_eur) },
    { k: "canal", etiqueta: "Canal", tipo: "select", opciones: CANALES, valor: p.channel || "WEB" },
    { k: "segmento", etiqueta: "Segmento (opcional)", valor: n(p.target_segment), maxlength: 50 },
    { k: "tienda", etiqueta: "Tienda (opcional)", valor: n(p.store_id), maxlength: 4 },
    { k: "combinable", etiqueta: "Combinable con otras promociones", tipo: "select", opciones: ["No", "Sí"], valor: sino(p.combinable) },
    { k: "umbral_cesta", etiqueta: "Umbral de cesta (€)", tipo: "number", min: 0, step: 1, valor: p.basket_threshold_eur ?? 0, req: true },
    { k: "margen_minimo", etiqueta: "Margen mínimo (%)", tipo: "number", min: 0, max: 80, step: 0.5, valor: n(p.min_margin_pct) },
    { k: "campana", etiqueta: "Campaña relacionada (opcional)", valor: n(p.related_campaign_id), maxlength: 16 },
  ];
}

async function pintar(cuerpo, ctx, vigencia) {
  const filas = await get("/promociones", { vigencia });
  const guardar = (id) => async (v) => {
    const cuerpoPromo = { ...v, combinable: v.combinable === "Sí" };
    const r = id ? await put(`/promociones/${id}`, cuerpoPromo) : await post("/promociones", cuerpoPromo);
    aviso(`Promoción ${r.promo_id} guardada.`);
    pintar(cuerpo, ctx, vigencia);
  };
  const sel = selector(VIGENCIAS, vigencia, { "aria-label": "Vigencia" });
  const ahora = Date.now();
  const estado = (p) => (new Date(p.ends_at + "Z") < ahora ? "Terminada" : new Date(p.starts_at + "Z") > ahora ? "Futura" : "Vigente");
  montar(cuerpo,
    h("div", { class: "fila entre" }, h("h1", {}, "Promociones"),
      h("button", { type: "button", class: "primary", onclick: () => dialogo("Nueva promoción", campos(), guardar(null), { enviar: "Crear promoción" }) }, "Nueva promoción")),
    h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); ctx.ir(`/promociones?vigencia=${sel.value}`); } }, sel, h("button", { type: "submit" }, "Ver")),
    tabla([
      { t: "Promoción", f: (p) => h("span", {}, h("strong", {}, p.promo_name), h("small", {}, ` ${p.promo_id}`)) },
      { t: "Vigencia", f: (p) => `${fechaHora(p.starts_at)} → ${fechaHora(p.ends_at)}` },
      { t: "Estado", f: (p) => h("span", { class: "insignia " + ({ Vigente: "ok", Futura: "aviso", Terminada: "" }[estado(p)]) }, estado(p)) },
      { t: "Ámbito", f: (p) => `${p.scope_type}: ${(p.scope_id || "").replace("|", " · ")}` }, { t: "Tipo", k: "promo_type" },
      { t: "Descuento", f: (p) => (p.discount_pct ? `${num(p.discount_pct)} %` : p.discount_eur ? eur(p.discount_eur) : "—"), cls: "num" },
      { t: "Canal", k: "channel" }, { t: "Combinable", f: (p) => sino(p.combinable) },
      { t: "Umbral", f: (p) => (p.basket_threshold_eur ? eur(p.basket_threshold_eur) : "—"), cls: "num" }, { t: "Margen mín.", f: (p) => (p.min_margin_pct ? `${num(p.min_margin_pct)} %` : "—"), cls: "num" },
      { t: "", f: (p) => h("button", { type: "button", onclick: () => dialogo(`Editar ${p.promo_id}`, campos(p), guardar(p.promo_id)) }, "Editar") },
    ], filas, { sinDatos: "No hay promociones con esa vigencia." }));
}
