// Escenario 7 · gestión de campañas: brief, audiencia con grupo de control, creatividades con guardrails,
// cupones, lanzamiento, atribución y resultados a 30 días.
import { get, post, put } from "../api.js";
import { ahoraLocal, aLocal, aviso, cargando, confirmar, conAviso, dialogo, eur, fechaHora, ficha, h, insignia, montar, num,
  pestanas, selector, tabla, vacio } from "../ui.js";

const OBJETIVOS = ["trafico_tienda", "reactivacion", "cross_sell", "promocion", "upsell", "retencion", "captacion", "onboarding"];
const CANALES = ["EMAIL", "SMS", "PUSH"];
const SEGMENTOS = ["VIP_OMNICANAL", "LOCAL_STORE", "NUEVO_CONTACTABLE", "RIESGO_CHURN", "ALTO_TICKET_MUEBLES", "POST_DEVOLUCION",
  "PROMO_SENSIBLE_TEXTIL", "ACTIVO_BASE", "DECORACION_FRECUENTE", "TODOS"];
const OFERTAS = ["descuento_pct", "cupon_importe", "puntos", "acceso_anticipado", "financiacion"];
const TONOS = ["inspiracional", "cercano", "exclusivo", "práctico", "urgencia_suave"];
const ESTADOS = ["borrador", "audiencia", "activa", "finalizada", "cancelada"];
const CATEGORIAS = ["", "Muebles", "Decoración", "Iluminación", "Textil hogar"];
const PASOS = ["borrador", "audiencia", "activa", "finalizada"];

export async function render(cont, ctx) {
  const [id, tab] = ctx.partes;
  const cuerpo = h("div", {}, cargando());
  montar(cont, cuerpo);
  if (id) return detalle(cuerpo, id, tab || "", ctx);
  return lista(cuerpo, ctx);
}

// ------------------------------------------------------------------ brief

function camposBrief(c = {}) {
  const n = (v) => (v === null || v === undefined ? "" : v);
  return [
    { k: "nombre", etiqueta: "Nombre de la campaña", valor: n(c.campaign_name), maxlength: 200, req: true },
    { k: "objetivo", etiqueta: "Objetivo", tipo: "select", opciones: OBJETIVOS, valor: c.objective || "reactivacion" },
    { k: "canal", etiqueta: "Canal", tipo: "select", opciones: CANALES, valor: c.channel || "EMAIL" },
    { k: "inicio", etiqueta: "Inicio", tipo: "datetime-local", valor: c.starts_at ? aLocal(c.starts_at) : ahoraLocal(1), req: true },
    { k: "fin", etiqueta: "Fin", tipo: "datetime-local", valor: c.ends_at ? aLocal(c.ends_at) : ahoraLocal(15), req: true },
    { k: "segmento", etiqueta: "Segmento", tipo: "select", opciones: SEGMENTOS, valor: c.target_segment || "ACTIVO_BASE" },
    { k: "categoria", etiqueta: "Categoría objetivo", tipo: "select", opciones: CATEGORIAS, valor: n(c.target_category) },
    { k: "tienda", etiqueta: "Tienda objetivo (opcional)", valor: n(c.target_store_id), maxlength: 4, ayuda: "Por ejemplo S001" },
    { k: "oferta", etiqueta: "Oferta", tipo: "select", opciones: OFERTAS, valor: c.offer_type || "descuento_pct" },
    { k: "descuento", etiqueta: "Descuento (%)", tipo: "number", min: 0, max: 100, step: 0.5, valor: c.discount_pct ?? 10, req: true },
    { k: "presupuesto", etiqueta: "Presupuesto (€)", tipo: "number", min: 0, step: 1, valor: n(c.budget_eur) },
    { k: "grupo_control", etiqueta: "Grupo de control (0 a 0,5)", tipo: "number", min: 0, max: 0.5, step: 0.01, valor: c.control_group_pct ?? 0.1, req: true,
      ayuda: "Fracción de la audiencia que no recibe la campaña y sirve para medir el uplift." },
    { k: "kpi", etiqueta: "KPI principal", valor: n(c.primary_kpi), maxlength: 50 },
    { k: "eje_copy", etiqueta: "Eje del mensaje", valor: n(c.copy_axis), maxlength: 500 },
  ];
}

// ------------------------------------------------------------------ listado

async function lista(cuerpo, ctx) {
  const estado = ctx.params.get("estado") || "";
  const filas = await get("/campanas", { estado, tamano: 100 });
  const sel = selector([["", "Todos los estados"], ...ESTADOS], estado, { "aria-label": "Estado" });
  montar(cuerpo,
    h("div", { class: "fila entre" }, h("h1", {}, "Campañas"),
      h("button", { type: "button", class: "primary", onclick: () => dialogo("Nueva campaña", camposBrief(), async (v) => {
        const c = await post("/campanas", v);
        aviso(`Campaña ${c.campaign_id} creada.`);
        ctx.ir(`/campanas/${c.campaign_id}`);
      }, { enviar: "Crear borrador" }) }, "Nueva campaña")),
    h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); ctx.ir("/campanas" + (sel.value ? `?estado=${sel.value}` : "")); } },
      sel, h("button", { type: "submit" }, "Filtrar")),
    tabla([
      { t: "Campaña", k: "campaign_id" }, { t: "Nombre", k: "campaign_name" }, { t: "Objetivo", k: "objective" }, { t: "Canal", k: "channel" },
      { t: "Segmento", k: "target_segment" }, { t: "Inicio", f: (c) => fechaHora(c.starts_at) }, { t: "Contactos", k: "contactos", cls: "num" },
      { t: "Estado", f: (c) => insignia(c.campaign_status) },
    ], filas, { alClic: (c) => ctx.ir(`/campanas/${c.campaign_id}`), sinDatos: "No hay campañas." }));
}

// ------------------------------------------------------------------ detalle

async function detalle(cuerpo, id, tab, ctx) {
  const c = await get(`/campanas/${encodeURIComponent(id)}`);
  const recargar = () => detalle(cuerpo, id, tab, ctx);
  const e = c.campaign_status;
  const usaCupones = ["descuento_pct", "cupon_importe"].includes(c.offer_type);
  const accion = (texto, fn, opciones = {}) => h("button", { type: "button", class: opciones.primary ? "primary" : "", disabled: opciones.off,
    title: opciones.nota, onclick: conAviso(fn) }, texto);
  const pasos = h("ol", { class: "pasos", "aria-label": "Estado de la campaña" }, PASOS.map((p, i) =>
    h("li", { class: PASOS.indexOf(e) >= i ? "hecho" : "", "aria-current": p === e ? "step" : null }, ["Borrador", "Audiencia", "Activa", "Finalizada"][i])));

  const acciones = [];
  if (e === "borrador") {
    acciones.push(h("button", { type: "button", onclick: () => dialogo("Editar el brief", camposBrief(c), async (v) => {
      await put(`/campanas/${c.campaign_id}`, v); aviso("Brief actualizado."); recargar();
    }) }, "Editar brief"));
  }
  if (e === "borrador" || e === "audiencia") {
    acciones.push(h("button", { type: "button", class: e === "borrador" ? "primary" : "", onclick: () => dialogo(e === "borrador" ? "Construir la audiencia" : "Rehacer la audiencia", [
      { k: "maximo", etiqueta: "Máximo de contactos", tipo: "number", min: 1, max: 2000, step: 1, valor: 300, req: true }], async (v) => {
      const r = await post(`/campanas/${c.campaign_id}/audiencia`, { maximo: v.maximo });
      aviso("Audiencia preparada con grupo de control."); recargar(); return r;
    }, { enviar: "Construir", intro: `Segmento ${c.target_segment}, grupo de control del ${num(Math.round(c.control_group_pct * 100))} %.` }) }, e === "borrador" ? "1 · Construir audiencia" : "Rehacer audiencia"));
  }
  if (e === "audiencia" && usaCupones) {
    acciones.push(h("button", { type: "button", onclick: () => dialogo("Emitir cupones", [
      { k: "dias_validez", etiqueta: "Días de validez", tipo: "number", min: 1, max: 90, step: 1, valor: 15, req: true },
      { k: "gasto_minimo", etiqueta: "Gasto mínimo (€)", tipo: "number", min: 0, step: 1, valor: 0, req: true }], async (v) => {
      await post(`/campanas/${c.campaign_id}/cupones`, v); aviso("Cupones emitidos al grupo de tratamiento."); recargar();
    }, { enviar: "Emitir" }) }, "2 · Emitir cupones"));
  }
  if (e === "audiencia") acciones.push(accion("3 · Lanzar", async () => {
    if (!confirmar("¿Lanzar la campaña? Se simulan entregas, aperturas y clics.")) return;
    await post(`/campanas/${c.campaign_id}/lanzar`, {}); aviso("Campaña lanzada."); recargar();
  }, { primary: true, nota: "Necesita al menos una creatividad" }));
  if (e === "activa" || e === "finalizada") acciones.push(accion("Atribuir conversiones a 30 días", async () => {
    await post(`/campanas/${c.campaign_id}/atribuir`, {}); aviso("Conversiones atribuidas."); ctx.ir(`/campanas/${c.campaign_id}/resultados`);
  }, { primary: e === "activa" }));
  if (["borrador", "audiencia", "activa"].includes(e)) acciones.push(accion(e === "activa" ? "Cerrar campaña" : "Cancelar campaña", async () => {
    if (!confirmar(e === "activa" ? "¿Cerrar la campaña? Los cupones sin canjear caducan." : "¿Cancelar la campaña?")) return;
    await post(`/campanas/${c.campaign_id}/cerrar`, {}); aviso(e === "activa" ? "Campaña finalizada." : "Campaña cancelada."); recargar();
  }));

  const cuerpoTab = h("div", {}, cargando());
  montar(cuerpo,
    h("p", {}, h("a", { href: "#/campanas" }, "‹ Campañas")),
    h("h1", {}, `${c.campaign_name} `, insignia(e)),
    h("p", { class: "ayuda" }, `${c.campaign_id} · ${c.objective} · ${c.channel} · ${c.target_segment}`),
    pasos, h("div", { class: "fila" }, acciones),
    pestanas(`campanas/${c.campaign_id}`, [{ id: "", titulo: "Resumen" }, { id: "contactos", titulo: "Contactos" },
      { id: "creatividades", titulo: "Creatividades" }, { id: "resultados", titulo: "Resultados" }], tab), cuerpoTab);
  if (tab === "contactos") return contactos(cuerpoTab, c, ctx);
  if (tab === "creatividades") return creatividades(cuerpoTab, c, recargar);
  if (tab === "resultados") return resultados(cuerpoTab, c.resultados);
  return resumen(cuerpoTab, c);
}

function resumen(cuerpo, c) {
  montar(cuerpo, ficha([
    ["Periodo", `${fechaHora(c.starts_at)} → ${fechaHora(c.ends_at)}`], ["Categoría", c.target_category || "Multicategoría"], ["Tienda", c.target_store_id || "Todas"],
    ["Oferta", `${c.offer_type}${c.discount_pct ? ` · ${num(c.discount_pct)} %` : ""}`], ["Presupuesto", c.budget_eur ? eur(c.budget_eur) : "—"],
    ["Grupo de control", `${num(Math.round(c.control_group_pct * 100))} %`], ["KPI principal", c.primary_kpi], ["Eje del mensaje", c.copy_axis],
    ["Creada por", c.created_by], ["Actualizada", fechaHora(c.updated_at)]]));
}

// ------------------------------------------------------------------ contactos

async function contactos(cuerpo, c, ctx) {
  const pagina = Number(ctx.params.get("pagina") || 1);
  const filas = await get(`/campanas/${c.campaign_id}/contactos`, { pagina, tamano: 50 });
  const ir = (n) => ctx.ir(`/campanas/${c.campaign_id}/contactos?pagina=${n}`);
  montar(cuerpo,
    filas.length || pagina > 1 ? null : h("p", { class: "ayuda" }, "Todavía no hay audiencia: pulsa «Construir audiencia»."),
    tabla([
      { t: "Cliente", f: (x) => h("a", { href: `#/clientes/${x.customer_id}` }, `${x.first_name} ${x.last_name}`) },
      { t: "Grupo", f: (x) => h("span", { class: "insignia " + (x.experiment_group === "control" ? "aviso" : "ok") }, x.experiment_group) }, { t: "Entrega", f: (x) => x.delivery_status ? insignia(x.delivery_status) : "—" },
      { t: "Cupón", f: (x) => x.coupon_instance_id || "—" }, { t: "Tienda", f: (x) => x.personalized_store_id || "—" },
      { t: "Reco.", f: (x) => [x.recommended_product_1, x.recommended_product_2].filter(Boolean).join(", ") || "—" },
      { t: "Compra 30 d", f: (x) => (x.conversion_30d ? `Sí · ${eur(x.revenue_30d_eur)}` : "No") },
    ], filas, { sinDatos: "Sin contactos en esta página." }),
    h("div", { class: "paginador" },
      h("button", { type: "button", disabled: pagina <= 1, onclick: () => ir(pagina - 1) }, "‹ Anterior"), h("span", {}, `Página ${pagina}`),
      h("button", { type: "button", disabled: filas.length < 50, onclick: () => ir(pagina + 1) }, "Siguiente ›")));
}

// ------------------------------------------------------------------ creatividades

function camposCreatividad(x = {}, c) {
  const n = (v) => (v === null || v === undefined ? "" : v);
  return [
    { k: "microsegmento", etiqueta: "Microsegmento", valor: n(x.microsegmento) || c.target_segment, maxlength: 50 },
    { k: "tono", etiqueta: "Tono", tipo: "select", opciones: TONOS, valor: x.tono || TONOS[0] },
    { k: "beneficio_principal", etiqueta: "Beneficio principal", valor: n(x.beneficio_principal), maxlength: 200, req: true },
    { k: "cta", etiqueta: "Llamada a la acción", valor: n(x.cta), maxlength: 60, req: true },
    { k: "asunto", etiqueta: "Asunto (email)", valor: n(x.asunto), maxlength: 150 },
    { k: "copy_corto", etiqueta: c.channel === "SMS" ? "Mensaje corto (SMS: máximo 160 caracteres)" : "Mensaje corto", tipo: "textarea", valor: n(x.copy_corto), maxlength: 400, req: true },
    { k: "copy_largo", etiqueta: "Mensaje largo", tipo: "textarea", valor: n(x.copy_largo), maxlength: 2000 },
    { k: "prueba_social", etiqueta: "Prueba social", valor: n(x.prueba_social), maxlength: 300 },
  ];
}

async function creatividades(cuerpo, c, recargar) {
  const [lista, reglas] = await Promise.all([get(`/campanas/${c.campaign_id}/creatividades`), get("/guardrails")]);
  const editable = ["borrador", "audiencia"].includes(c.campaign_status);
  const guardar = (id) => async (v) => {
    try {
      const r = id ? await put(`/campanas/${c.campaign_id}/creatividades/${id}`, v) : await post(`/campanas/${c.campaign_id}/creatividades`, v);
      aviso(r.infracciones.length ? `Creatividad guardada con ${r.infracciones.length} aviso(s) de marca.` : "Creatividad guardada.");
      recargar();
    } catch (e) {
      if (e.codigo === "guardrails" && e.datos && e.datos.infracciones) {
        throw new Error(`${e.message} ` + e.datos.infracciones.map((i) => `[${i.regla_id}] ${i.detalle || i.descripcion}`).join(" · "));
      }
      throw e;
    }
  };
  montar(cuerpo,
    editable ? h("button", { type: "button", class: "primary", onclick: () => dialogo("Nueva creatividad", camposCreatividad({}, c), guardar(null), { enviar: "Validar y guardar",
      intro: "Se valida contra las reglas de marca: las de severidad alta bloquean el guardado." }) }, "Nueva creatividad") : h("p", { class: "ayuda" }, "La campaña ya está lanzada: las creatividades no se editan."),
    lista.length ? h("div", { class: "rejilla" }, lista.map((x) => h("article", { class: "tarjeta" },
      h("strong", {}, x.beneficio_principal), h("small", {}, `${x.creative_id} · ${x.microsegmento} · tono ${x.tono}`),
      x.asunto ? h("span", {}, `Asunto: ${x.asunto}`) : null, h("p", {}, x.copy_corto), h("span", {}, `CTA: ${x.cta}`),
      h("small", { class: (x.avisos_guardrails || []).length ? "ko" : "ok" }, x.guardrail_legal || "Sin avisos"),
      x.winning_variant_flag ? insignia("Activo") : null,
      editable ? h("div", { class: "fila" }, h("button", { type: "button", onclick: () => dialogo(`Editar ${x.creative_id}`, camposCreatividad(x, c), guardar(x.creative_id)) }, "Editar")) : null)))
      : vacio("Todavía no hay creatividades. Hace falta al menos una para lanzar."),
    h("h2", {}, "Reglas de marca (guardrails)"),
    tabla([{ t: "Regla", k: "rule_id" }, { t: "Categoría", k: "rule_category" }, { t: "Descripción", k: "rule_description" },
      { t: "Canal", f: (r) => r.applies_to_channel || "Todos" }, { t: "Severidad", f: (r) => insignia(r.severity === "alta" ? "Alta" : r.severity === "media" ? "Media" : r.severity) }], reglas));
}

// ------------------------------------------------------------------ resultados

function resultados(cuerpo, r) {
  const grupos = r.grupos || [];
  const pct = (v) => (v === null || v === undefined ? "—" : `${num(Math.round(v * 1000) / 10)} %`);
  const t = grupos.find((g) => g.grupo === "treatment");
  const neto = t ? Number(t.margen || 0) - Number(t.coste_contacto || 0) : null;
  montar(cuerpo,
    grupos.length ? [
      tabla([
        { t: "Grupo", k: "grupo" }, { t: "Contactos", k: "contactos", cls: "num" }, { t: "Entregados", f: (g) => num(g.entregados), cls: "num" },
        { t: "Conversiones", f: (g) => num(g.conversiones), cls: "num" }, { t: "Conversión", f: (g) => pct(g.tasa_conversion), cls: "num" },
        { t: "Ingresos", f: (g) => eur(g.ingresos), cls: "num" }, { t: "Margen", f: (g) => eur(g.margen), cls: "num" }, { t: "Coste contacto", f: (g) => eur(g.coste_contacto), cls: "num" },
      ], grupos),
      h("div", { class: "rejilla" },
        h("div", { class: "tarjeta" }, h("small", {}, "Uplift de conversión"), h("p", { class: "grande" }, r.uplift_conversion === null ? "—" : `${r.uplift_conversion >= 0 ? "+" : ""}${num(Math.round(r.uplift_conversion * 1000) / 10)} pp`),
          h("small", {}, "Tratamiento menos control")),
        h("div", { class: "tarjeta" }, h("small", {}, "Margen neto del tratamiento"), h("p", { class: "grande" }, neto === null ? "—" : eur(neto)), h("small", {}, "Margen menos coste de contacto")),
        h("div", { class: "tarjeta" }, h("small", {}, "Cupones"), h("p", { class: "grande" }, `${num(r.cupones.canjeados || 0)} / ${num(r.cupones.emitidos || 0)}`),
          h("small", {}, `Descuento aplicado ${eur(r.cupones.descuento_aplicado || 0)}`))),
      Object.keys(r.eventos || {}).length ? [h("h2", {}, "Eventos de la campaña"), ficha(Object.entries(r.eventos).map(([k, v]) => [k, num(v)]))] : null,
    ] : vacio("Todavía no hay resultados: construye la audiencia, lanza la campaña y atribuye las conversiones."));
}
