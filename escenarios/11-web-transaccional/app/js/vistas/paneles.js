// Escenario 14 · paneles operativos de dirección (solo lectura): ventas, ficha 360 de cliente y de empleado,
// rotación mensual y comentarios de clima y salida.
import { get } from "../api.js";
import { cargando, corta, eur, fecha, ficha, h, hoy, insignia, montar, num, pestanas, selector, tabla, vacio } from "../ui.js";
import { columnas, linea } from "../grafico.js";

export async function render(cont, ctx) {
  const [sub, id] = ctx.partes;
  const cuerpo = h("div", {}, cargando());
  const activa = sub || "ventas";
  montar(cont, pestanas("paneles", [{ id: "ventas", titulo: "Ventas" }, { id: "cliente", titulo: "Cliente 360" }, { id: "empleado", titulo: "Empleado 360" },
    { id: "rotacion", titulo: "Rotación" }, { id: "comentarios", titulo: "Comentarios" }], activa), cuerpo);
  if (activa === "cliente") return cliente360(cuerpo, id, ctx);
  if (activa === "empleado") return empleado360(cuerpo, id, ctx);
  if (activa === "rotacion") return rotacion(cuerpo, ctx);
  if (activa === "comentarios") return comentarios(cuerpo, ctx);
  return ventas(cuerpo, ctx);
}

const restaDias = (n) => new Date(Date.now() - n * 864e5).toISOString().slice(0, 10);
const tablaAlt = (titulo, nodo) => h("details", { class: "tabla-alt" }, h("summary", {}, titulo), nodo);

// ------------------------------------------------------------------ ventas

/** Si el periodo es largo, agrupa por mes para que el gráfico se lea. */
function agrupar(dias) {
  if (dias.length <= 120) return { etiquetas: dias.map((d) => fecha(d.dia).slice(0, 5)), filas: dias, unidad: "día" };
  const meses = new Map();
  for (const d of dias) {
    const k = String(d.dia).slice(0, 7);
    const m = meses.get(k) || { dia: k, online: 0, tienda: 0, devoluciones: 0, neto: 0, pedidos: 0, tickets: 0 };
    for (const c of ["online", "tienda", "devoluciones", "neto", "pedidos", "tickets"]) m[c] += Number(d[c]) || 0;
    meses.set(k, m);
  }
  const filas = [...meses.values()];
  return { etiquetas: filas.map((m) => m.dia), filas, unidad: "mes" };
}

async function ventas(cuerpo, ctx) {
  const hasta = ctx.params.get("hasta") || hoy();
  const desde = ctx.params.get("desde") || restaDias(30);
  const r = await get("/paneles/ventas", { desde, hasta });
  const d1 = h("input", { type: "date", value: desde, "aria-label": "Desde" });
  const d2 = h("input", { type: "date", value: hasta, "aria-label": "Hasta" });
  const ir = (a, b) => ctx.ir(`/paneles/ventas?desde=${a}&hasta=${b}`);
  const preset = (txt, a, b) => h("button", { type: "button", class: "chip", onclick: () => ir(a, b) }, txt);
  const g = agrupar(r.dias);
  montar(cuerpo,
    h("h1", {}, "Ventas"),
    h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); ir(d1.value, d2.value); } }, d1, d2, h("button", { type: "submit" }, "Ver")),
    h("div", { class: "fila" }, preset("30 días", restaDias(30), hoy()), preset("90 días", restaDias(90), hoy()), preset("2025", "2025-01-01", "2025-12-31"), preset("2024", "2024-01-01", "2024-12-31")),
    h("div", { class: "kpis" },
      kpi("Ventas online", eur(r.totales.online)), kpi("Ventas en tienda", eur(r.totales.tienda)), kpi("Devoluciones", eur(r.totales.devoluciones)), kpi("Ventas netas", eur(r.totales.neto))),
    r.dias.length ? [
      h("h2", {}, `Ventas por ${g.unidad} · online y tienda`),
      columnas({ etiquetas: g.etiquetas, series: [{ nombre: "Tienda", valores: g.filas.map((x) => x.tienda) }, { nombre: "Online", valores: g.filas.map((x) => x.online) }],
        formato: eur, resumen: `Ventas por ${g.unidad} del ${fecha(r.desde)} al ${fecha(r.hasta)}` }),
      tablaAlt("Ver como tabla", tabla([{ t: g.unidad === "mes" ? "Mes" : "Día", f: (x) => (g.unidad === "mes" ? x.dia : fecha(x.dia)) }, { t: "Pedidos", f: (x) => num(x.pedidos), cls: "num" },
        { t: "Online", f: (x) => eur(x.online), cls: "num" }, { t: "Tickets", f: (x) => num(x.tickets), cls: "num" }, { t: "Tienda", f: (x) => eur(x.tienda), cls: "num" },
        { t: "Devoluciones", f: (x) => eur(x.devoluciones), cls: "num" }, { t: "Neto", f: (x) => eur(x.neto), cls: "num" }], g.filas)),
    ] : vacio("No hay ventas en ese periodo. Los datos de carga llegan hasta finales de 2025: prueba con «2025»."),
    h("div", { class: "dos" },
      h("section", {}, h("h2", {}, "Productos más vendidos"), tabla([{ t: "Producto", f: (p) => `${p.product_id} · ${p.product_name}` }, { t: "Uds.", f: (p) => num(p.unidades), cls: "num" },
        { t: "Ventas", f: (p) => eur(p.ventas), cls: "num" }], r.top_productos)),
      h("section", {}, h("h2", {}, "Tiendas"), tabla([{ t: "Tienda", f: (t) => `${t.store_id} · ${t.store_name}` }, { t: "Tickets", f: (t) => num(t.tickets), cls: "num" },
        { t: "Ventas", f: (t) => eur(t.ventas), cls: "num" }], r.tiendas))));
}

const kpi = (titulo, valor) => h("div", { class: "tarjeta" }, h("small", {}, titulo), h("p", { class: "grande" }, valor));

// ------------------------------------------------------------------ cliente 360

function buscador(ctx, ruta, placeholder, patron, valor) {
  const f = h("input", { value: valor || "", placeholder, maxlength: "7", "aria-label": placeholder, pattern: patron });
  return h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); if (f.value.trim()) ctx.ir(`/paneles/${ruta}/${f.value.trim().toUpperCase()}`); } }, f, h("button", { type: "submit", class: "primary" }, "Ver ficha"));
}

async function cliente360(cuerpo, id, ctx) {
  if (!id) return montar(cuerpo, h("h1", {}, "Cliente 360"), buscador(ctx, "cliente", "Cliente (C0017)", "[Cc]\\d{4}"), h("p", { class: "ayuda" }, "Todo lo que sabe la empresa de un cliente en una sola pantalla."));
  const c = await get(`/paneles/cliente/${encodeURIComponent(id)}`);
  const r = c.resumen, a = c.afinidad;
  montar(cuerpo, buscador(ctx, "cliente", "Cliente (C0017)", "[Cc]\\d{4}", c.customer_id),
    h("h1", {}, `${c.first_name} ${c.last_name} `, insignia(c.customer_status)),
    h("p", { class: "ayuda" }, `${c.customer_id} · ${c.loyalty_tier || "sin nivel"} · ${num(c.loyalty_points)} puntos · ${c.city || ""}`),
    h("div", { class: "kpis" }, kpi("Pedidos online", `${num(r.pedidos)} · ${eur(r.gasto_online)}`), kpi("Tickets en tienda", `${num(r.tickets)} · ${eur(r.gasto_tienda)}`),
      kpi("Devoluciones", num(r.devoluciones)), kpi("Última compra", r.ultima_compra ? fecha(r.ultima_compra) : "—"), kpi("Señales de identidad", num(c.senales_identidad))),
    a ? ficha([["Tienda preferida", a.preferred_store_id], ["Tienda más cercana", a.nearest_store_id ? `${a.nearest_store_id} (${num(a.nearest_store_km)} km)` : null],
      ["Gasto tienda 12 m", eur(a.store_spend_12m_eur)], ["Gasto online 12 m", eur(a.online_spend_12m_eur)], ["Clúster", a.local_cluster]]) : null,
    h("div", { class: "dos" },
      h("section", {}, h("h2", {}, "Últimos pedidos"), tabla([{ t: "Pedido", f: (o) => h("a", { href: `#/pedidos/${o.order_id}` }, o.order_id) }, { t: "Fecha", f: (o) => fecha(o.ordered_at) },
        { t: "Total", f: (o) => eur(o.order_total), cls: "num" }, { t: "Estado", f: (o) => insignia(o.order_status) }], c.pedidos, { sinDatos: "Sin pedidos." })),
      h("section", {}, h("h2", {}, "Últimos tickets"), tabla([{ t: "Ticket", k: "ticket_id" }, { t: "Fecha", f: (t) => fecha(t.ticket_at) }, { t: "Tienda", k: "store_id" },
        { t: "Importe", f: (t) => eur(t.ticket_net_amount), cls: "num" }], c.tickets, { sinDatos: "Sin tickets." }))),
    h("h2", {}, "Devoluciones"), tabla([{ t: "Devolución", f: (d) => h("a", { href: `#/devoluciones/${d.return_id}` }, d.return_id) }, { t: "Fecha", f: (d) => fecha(d.returned_at) },
      { t: "Canal", k: "return_channel" }, { t: "Estado", f: (d) => insignia(d.return_status) }], c.devoluciones, { sinDatos: "Sin devoluciones." }),
    h("h2", {}, "Campañas recibidas"), tabla([{ t: "Campaña", f: (m) => `${m.campaign_id} · ${m.campaign_name}` }, { t: "Grupo", k: "experiment_group" },
      { t: "Entrega", f: (m) => m.delivery_status || "—" }, { t: "Compró", f: (m) => (m.conversion_30d ? `Sí · ${eur(m.revenue_30d_eur)}` : "No") }], c.campanas, { sinDatos: "Sin campañas." }),
    h("div", { class: "dos" },
      h("section", {}, h("h2", {}, "Opiniones"), tabla([{ t: "Fecha", f: (o) => fecha(o.fecha_feedback) }, { t: "Valoración", f: (o) => (o.nps_0_10 !== null && o.nps_0_10 !== undefined ? `NPS ${o.nps_0_10}` : `${o.rating_1_5 || "—"} / 5`) },
        { t: "Sentimiento", f: (o) => (o.sentimiento ? insignia(o.sentimiento) : "—") }, { t: "Tema", f: (o) => o.tema_principal || "—" }], c.opiniones, { sinDatos: "Sin opiniones." })),
      h("section", {}, h("h2", {}, "Casos de atención"), tabla([{ t: "Caso", k: "service_ticket_id" }, { t: "Fecha", f: (o) => fecha(o.fecha_apertura) }, { t: "Tipo", k: "tipo_caso" },
        { t: "Estado", f: (o) => insignia(o.estado_resolucion) }, { t: "CSAT", f: (o) => o.csat_1_5 || "—" }], c.casos, { sinDatos: "Sin casos." }))));
}

// ------------------------------------------------------------------ empleado 360

async function empleado360(cuerpo, id, ctx) {
  if (!id) return montar(cuerpo, h("h1", {}, "Empleado 360"), buscador(ctx, "empleado", "Empleado (FSH0001)", "[Ff][Ss][Hh]\\d{4}"),
    h("p", { class: "ayuda" }, "Ficha, compensación, riesgo de abandono, clima y entrevista de salida de un empleado."));
  const e = await get(`/paneles/empleado/${encodeURIComponent(id)}`);
  const pa = e.people_analytics;
  const pct = (v) => (v === null || v === undefined ? "—" : `${num(Math.round(v * 100))} %`);
  montar(cuerpo, buscador(ctx, "empleado", "Empleado (FSH0001)", "[Ff][Ss][Hh]\\d{4}", e.employee_id),
    h("h1", {}, `${e.full_name} `, insignia(e.employee_status)),
    h("p", { class: "ayuda" }, `${e.employee_id} · ${e.role_name || ""} · ${e.department || ""} · ${e.location || ""}`),
    pa ? h("div", { class: "kpis" }, kpi("Probabilidad de abandono", pct(pa.probabilidad_abandono)), kpi("Riesgo", pa.riesgo_abandono || "—"), kpi("Talento clave", pa.talento_clave_flag ? "Sí" : "No"),
      kpi("Prioridad de retención", pa.prioridad_retencion || "—"), kpi("Satisfacción", pa.satisfaccion_1_10 ?? "—"), kpi("Engagement", pa.engagement_1_10 ?? "—")) : null,
    h("div", { class: "dos" },
      h("section", {}, h("h2", {}, "Ficha"), ficha([["Nivel", e.level_name], ["Contrato", e.contract_type], ["Jornada", e.work_schedule], ["Manager", e.manager_name],
        ["Alta", fecha(e.hired_at)], e.left_at ? ["Baja", `${fecha(e.left_at)} · ${e.exit_type || ""} · ${e.exit_reason || ""}`] : null, ["Teletrabajo", `${num(e.remote_days_week)} días/semana`]])),
      h("section", {}, h("h2", {}, "Clima por dimensión (1 a 5)"), Object.keys(e.clima).length
        ? ficha(Object.entries(e.clima).map(([k, v]) => [k, num(v)])) : vacio("No ha respondido encuestas."))),
    h("h2", {}, "Compensación"), tabla([{ t: "Periodo", k: "period_month" }, { t: "Base", f: (c) => eur(c.base_salary_eur), cls: "num" }, { t: "Variable", f: (c) => eur(c.variable_salary_eur), cls: "num" },
      { t: "Subida", f: (c) => (c.increase_pct === null || c.increase_pct === undefined ? "—" : `${num(c.increase_pct)} %`), cls: "num" }], e.compensacion || [], { sinDatos: "Sin datos." }),
    h("h2", {}, "Evaluaciones"), tabla([{ t: "Ciclo", k: "review_cycle" }, { t: "Nota", f: (r) => num(r.overall_score), cls: "num" }, { t: "Objetivos", f: (r) => (r.objectives_pct == null ? "—" : `${num(r.objectives_pct)} %`), cls: "num" },
      { t: "Potencial", f: (r) => r.potential || "—" }], e.evaluaciones, { sinDatos: "Sin evaluaciones." }),
    e.comentarios_clima.length ? [h("h2", {}, "Comentarios de clima"), h("ul", {}, e.comentarios_clima.map((c) => h("li", {}, c)))] : null,
    e.entrevista_salida.length ? [h("h2", {}, "Entrevista de salida"), e.entrevista_salida.map((x) => ficha([["Fecha", x.fecha_salida ? fecha(x.fecha_salida) : null], ["Tipo", x.tipo_salida], ["Motivo", x.motivo_salida_rrhh],
      ["Recomendaría (0-10)", x.recomendaria_empresa_1_10], ["Comentario", x.comentario_salida]]))] : null);
}

// ------------------------------------------------------------------ rotación

async function rotacion(cuerpo, ctx) {
  const dep = ctx.params.get("departamento") || "";
  const r = await get("/paneles/rotacion");
  const deps = [...new Set(r.meses.map((m) => m.departamento))].sort();
  const filas = r.meses.filter((m) => !dep || m.departamento === dep);
  const meses = new Map();
  for (const m of filas) {
    const k = String(m.periodo_mes).slice(0, 7);
    const a = meses.get(k) || { mes: k, base: 0, vol: 0, total: 0, altas: 0, fin: 0 };
    a.base += m.headcount_inicio_mes || 0; a.vol += m.bajas_voluntarias_mes || 0; a.total += m.bajas_totales_mes || 0; a.altas += m.altas_mes || 0; a.fin += m.headcount_fin_mes || 0;
    meses.set(k, a);
  }
  const serie = [...meses.values()].sort((a, b) => a.mes.localeCompare(b.mes));
  const tasa = (x, base) => (base ? Math.round((1000 * x) / base) / 10 : null);
  const sel = selector([["", "Toda la empresa"], ...deps], dep, { "aria-label": "Departamento", onchange: (ev) => ctx.ir(`/paneles/rotacion${ev.target.value ? `?departamento=${encodeURIComponent(ev.target.value)}` : ""}`) });
  const ultimo = serie[serie.length - 1];
  montar(cuerpo, h("div", { class: "fila entre" }, h("h1", {}, "Rotación mensual"), sel),
    h("p", { class: "ayuda" }, `Histórico hasta ${r.ultimo_mes_historico ? String(r.ultimo_mes_historico).slice(0, 7) : "—"}; los meses posteriores se calculan sobre la plantilla viva.`),
    ultimo ? h("div", { class: "kpis" }, kpi("Plantilla fin de mes", num(ultimo.fin)), kpi("Rotación total", `${num(tasa(ultimo.total, ultimo.base) ?? 0)} %`),
      kpi("Rotación voluntaria", `${num(tasa(ultimo.vol, ultimo.base) ?? 0)} %`), kpi("Altas del mes", num(ultimo.altas))) : null,
    serie.length ? [
      linea({ etiquetas: serie.map((s) => s.mes), series: [{ nombre: "Rotación total (%)", valores: serie.map((s) => tasa(s.total, s.base)) }, { nombre: "Rotación voluntaria (%)", valores: serie.map((s) => tasa(s.vol, s.base)) }],
        formato: (v) => (v === null || v === undefined ? "—" : `${num(v)} %`), resumen: "Rotación total y voluntaria por mes" }),
      tablaAlt("Ver como tabla", tabla([{ t: "Mes", k: "mes" }, { t: "Plantilla inicial", f: (s) => num(s.base), cls: "num" }, { t: "Altas", f: (s) => num(s.altas), cls: "num" }, { t: "Bajas", f: (s) => num(s.total), cls: "num" },
        { t: "Plantilla final", f: (s) => num(s.fin), cls: "num" }, { t: "Total %", f: (s) => num(tasa(s.total, s.base) ?? 0), cls: "num" }, { t: "Voluntaria %", f: (s) => num(tasa(s.vol, s.base) ?? 0), cls: "num" }], [...serie].reverse())),
    ] : vacio("Sin datos de rotación."));
}

// ------------------------------------------------------------------ comentarios

async function comentarios(cuerpo, ctx) {
  const tipo = ctx.params.get("tipo") || "clima";
  const dep = ctx.params.get("departamento") || "";
  const [filas, deps] = await Promise.all([get("/paneles/comentarios", { tipo, departamento: dep || undefined, tamano: 100 }), get("/rrhh/departamentos")]);
  const t = selector([["clima", "Encuesta de clima"], ["salida", "Entrevistas de salida"]], tipo, { "aria-label": "Tipo" });
  const d = selector([["", "Todos los departamentos"], ...deps.map((x) => x.departamento)], dep, { "aria-label": "Departamento" });
  montar(cuerpo, h("h1", {}, "Comentarios"),
    h("p", { class: "ayuda" }, "Solo lectura. Los comentarios son anónimos para el resto de la empresa; aquí se muestran con departamento y puesto, no con nombre."),
    h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); ctx.ir(`/paneles/comentarios?tipo=${t.value}${d.value ? `&departamento=${encodeURIComponent(d.value)}` : ""}`); } }, t, d, h("button", { type: "submit" }, "Filtrar")),
    tabla([
      { t: "Fecha", f: (c) => fecha(c.fecha_salida || c.fecha_encuesta) }, { t: "Departamento", f: (c) => c.departamento || "—" }, { t: "Puesto", f: (c) => c.rol || "—" },
      { t: tipo === "salida" ? "Motivo" : "Oleada", f: (c) => c.motivo_salida_rrhh || c.oleada || "—" },
      { t: "Comentario", f: (c) => corta(c.comentario_salida || c.comentario_abierto, 200) },
      tipo === "salida" ? { t: "Recomendaría", f: (c) => c.recomendaria_empresa_1_10 ?? "—", cls: "num" } : null,
    ].filter(Boolean), filas, { sinDatos: "No hay comentarios." }));
}
