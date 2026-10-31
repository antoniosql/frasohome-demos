// Escenario 6 · clientes y fidelización: CRM, consentimientos, puntos y consola de identidad.
import { get, post, put } from "../api.js";
import { aviso, cargando, conAviso, corta, dialogo, eur, fecha, fechaHora, ficha, h, insignia, montar, num, paginador, pestanas,
  selector, sino, tabla } from "../ui.js";
import { tieneRol } from "../sesion.js";

const TAMANO = 30;
const ESTADOS = ["Activo", "Inactivo", "Bloqueado"];
const ORIGENES = ["tienda", "online", "importación"];

export async function render(cont, ctx) {
  const [sub, id] = ctx.partes;
  const cuerpo = h("div", {}, cargando());
  const identidad = sub === "identidad";
  montar(cont, pestanas("clientes", [{ id: "", titulo: "Clientes" }, { id: "identidad", titulo: "Identidad" }], identidad ? "identidad" : ""), cuerpo);
  if (identidad && id) return candidatos(cuerpo, id, ctx);
  if (identidad) return senales(cuerpo, ctx);
  if (sub) return ver(cuerpo, sub, ctx);
  return lista(cuerpo, ctx);
}

// ------------------------------------------------------------------ campos compartidos con «Mi cuenta»

export function camposCliente(c = {}, { completo = true } = {}) {
  const n = (v) => (v === null || v === undefined ? "" : v);
  const contacto = [
    { k: "email", etiqueta: "Email", tipo: "email", valor: n(c.email), maxlength: 255 },
    { k: "telefono", etiqueta: "Teléfono", valor: n(c.phone), maxlength: 50 },
    { k: "ciudad", etiqueta: "Ciudad", valor: n(c.city), maxlength: 100 },
    { k: "provincia", etiqueta: "Provincia", valor: n(c.province), maxlength: 100 },
    { k: "codigo_postal", etiqueta: "Código postal", valor: n(c.postal_code), maxlength: 20 },
    { k: "canal_preferido", etiqueta: "Canal preferido", tipo: "select", opciones: ["", "EMAIL", "SMS", "PUSH", "Tienda"], valor: n(c.preferred_channel) },
    { k: "consentimiento", etiqueta: "Acepta comunicaciones comerciales", tipo: "select", opciones: ["Sí", "No"], valor: sino(c.marketing_consent) },
  ];
  if (!completo) return contacto;
  return [
    { k: "nombre", etiqueta: "Nombre", valor: n(c.first_name), maxlength: 100, req: true },
    { k: "apellidos", etiqueta: "Apellidos", valor: n(c.last_name), maxlength: 150, req: true },
    ...contacto,
    { k: "fecha_nacimiento", etiqueta: "Fecha de nacimiento", tipo: "date", valor: c.birth_date ? String(c.birth_date).slice(0, 10) : "" },
    { k: "genero", etiqueta: "Género", valor: n(c.gender), maxlength: 30 },
    { k: "nivel", etiqueta: "Nivel de fidelización", valor: n(c.loyalty_tier), maxlength: 50 },
    { k: "origen_alta", etiqueta: "Origen del alta", tipo: "select", opciones: ORIGENES, valor: ORIGENES.includes(c.acquisition_source) ? c.acquisition_source : "tienda" },
  ];
}

/** De los valores del diálogo al cuerpo que espera la API. */
export function cuerpoCliente(v) {
  const { consentimiento, ...resto } = v;
  return { ...resto, consentimiento_marketing: consentimiento === "Sí" };
}

// ------------------------------------------------------------------ listado

async function lista(cuerpo, ctx) {
  const p = ctx.params;
  const pagina = Number(p.get("pagina") || 1);
  const q = p.get("q") || "";
  const estado = p.get("estado") || "";
  const r = await get("/clientes", { q, estado, pagina, tamano: TAMANO });
  const texto = h("input", { type: "search", value: q, placeholder: "Nombre, email, teléfono o C0001", "aria-label": "Buscar" });
  const sel = selector([["", "Todos los estados"], ...ESTADOS], estado, { "aria-label": "Estado" });
  const ir = (n) => {
    const s = new URLSearchParams();
    if (texto.value.trim()) s.set("q", texto.value.trim());
    if (sel.value) s.set("estado", sel.value);
    if (n > 1) s.set("pagina", n);
    ctx.ir("/clientes" + (s.toString() ? "?" + s : ""));
  };
  montar(cuerpo,
    h("div", { class: "fila entre" }, h("h1", {}, "Clientes"),
      h("button", { type: "button", class: "primary", onclick: () => dialogo("Nuevo cliente", camposCliente(), async (v) => {
        const c = await post("/clientes", cuerpoCliente(v));
        aviso(`Cliente ${c.customer_id} creado.`);
        ctx.ir(`/clientes/${c.customer_id}`);
      }, { enviar: "Crear cliente" }) }, "Nuevo cliente")),
    h("form", { class: "filtros", role: "search", onsubmit: (ev) => { ev.preventDefault(); ir(1); } }, texto, sel, h("button", { type: "submit" }, "Buscar")),
    tabla([
      { t: "Cliente", k: "customer_id" }, { t: "Nombre", f: (c) => `${c.first_name} ${c.last_name}` }, { t: "Email", f: (c) => c.email || "—" },
      { t: "Ciudad", f: (c) => c.city || "—" }, { t: "Nivel", f: (c) => c.loyalty_tier || "—" }, { t: "Puntos", f: (c) => num(c.loyalty_points), cls: "num" },
      { t: "Comunicaciones", f: (c) => sino(c.marketing_consent) }, { t: "Estado", f: (c) => insignia(c.customer_status) },
    ], r.clientes, { alClic: (c) => ctx.ir(`/clientes/${c.customer_id}`), sinDatos: "Ningún cliente coincide." }),
    paginador(pagina, r.total, TAMANO, ir));
}

// ------------------------------------------------------------------ ficha

async function ver(cuerpo, id, ctx) {
  const c = await get(`/clientes/${encodeURIComponent(id)}`);
  const recargar = () => ver(cuerpo, id, ctx);
  const r = c.resumen, a = c.afinidad;
  const atencion = tieneRol("atencion");
  montar(cuerpo,
    h("p", {}, h("a", { href: "#/clientes" }, "‹ Clientes")),
    h("h1", {}, `${c.first_name} ${c.last_name} `, insignia(c.customer_status)),
    h("div", { class: "fila" },
      h("button", { type: "button", onclick: () => dialogo(`Editar ${c.customer_id}`, camposCliente(c), async (v) => {
        await put(`/clientes/${c.customer_id}`, cuerpoCliente(v)); aviso("Cliente actualizado."); recargar();
      }) }, "Editar"),
      h("button", { type: "button", onclick: () => dialogo("Estado del cliente", [
        { k: "estado", etiqueta: "Estado", tipo: "select", opciones: ESTADOS, valor: c.customer_status }], async (v) => {
        await post(`/clientes/${c.customer_id}/estado`, { estado: v.estado }); aviso("Estado actualizado."); recargar();
      }) }, "Cambiar estado"),
      h("button", { type: "button", onclick: () => dialogo("Ajustar puntos", [
        { k: "delta", etiqueta: "Puntos (+/−)", tipo: "number", step: 1, req: true, ayuda: `Saldo actual: ${num(c.loyalty_points)}` },
        { k: "motivo", etiqueta: "Motivo", req: true, maxlength: 300 }], async (v) => {
        await post(`/clientes/${c.customer_id}/puntos`, v); aviso("Puntos ajustados."); recargar();
      }, { enviar: "Ajustar" }) }, "Ajustar puntos"),
      atencion ? h("a", { class: "boton", href: `#/atencion?nuevo=${c.customer_id}` }, "Abrir caso") : null,
      h("a", { class: "boton", href: `#/pedidos?cliente=${c.customer_id}` }, "Pedidos")),
    h("div", { class: "dos" },
      h("section", {}, h("h2", {}, "Datos"),
        ficha([["Cliente", c.customer_id], ["Email", c.email ? `${c.email}${c.email_is_valid === false ? " (no válido)" : ""}` : null], ["Teléfono", c.phone],
          ["Ciudad", [c.postal_code, c.city, c.province].filter(Boolean).join(" · ")], ["Nacimiento", c.birth_date ? fecha(c.birth_date) : null],
          ["Género", c.gender], ["Canal preferido", c.preferred_channel], ["Comunicaciones comerciales", sino(c.marketing_consent)],
          ["Origen del alta", c.acquisition_source], ["Alta en fidelización", c.loyalty_joined_at ? fecha(c.loyalty_joined_at) : null],
          ["Nivel", c.loyalty_tier], ["Puntos", num(c.loyalty_points)], c.churned_at ? ["Baja", fecha(c.churned_at)] : null])),
      h("section", {}, h("h2", {}, "Actividad"),
        ficha([["Pedidos online", `${num(r.pedidos)} · ${eur(r.gasto_online)}`], ["Tickets en tienda", `${num(r.tickets)} · ${eur(r.gasto_tienda)}`],
          ["Devoluciones", num(r.devoluciones)], ["Cupones vigentes", num(r.cupones_vigentes)], ["Última compra", r.ultima_compra ? fechaHora(r.ultima_compra) : "Sin compras"]]),
        a ? [h("h2", {}, "Afinidad local"), ficha([["Tienda preferida", a.preferred_store_id], ["Tienda más cercana", a.nearest_store_id ? `${a.nearest_store_id} (${num(a.nearest_store_km)} km)` : null],
          ["Visitas 12 m", num(a.store_visits_12m)], ["Gasto tienda 12 m", eur(a.store_spend_12m_eur)], ["Gasto online 12 m", eur(a.online_spend_12m_eur)],
          ["Probabilidad de visita 30 d", a.visit_probability_30d === null ? null : `${num(Math.round(a.visit_probability_30d * 100))} %`], ["Clúster", a.local_cluster]])] : null)));
}

// ------------------------------------------------------------------ consola de identidad

const ID_COLUMNAS = ["id", "fuente_sistema", "fecha_evento", "customer_id_raw", "tarjeta_fidelizacion_id", "email_hash"];

async function senales(cuerpo, ctx) {
  const cliente = (ctx.params.get("cliente") || "").toUpperCase();
  const r = await get("/identidad/senales", { cliente: cliente || undefined, tamano: 100 });
  const f = h("input", { value: cliente, placeholder: "Cliente (C0041); vacío = sin asignar", maxlength: "5", "aria-label": "Cliente" });
  montar(cuerpo,
    h("h1", {}, "Consola de identidad"),
    h("p", { class: "ayuda" }, "Cada señal (email, teléfono, tarjeta, cookie, dispositivo…) debe acabar en un cliente. Abre una señal, revisa los candidatos que comparten identificadores y asígnala."),
    h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); ctx.ir("/clientes/identidad" + (f.value.trim() ? `?cliente=${f.value.trim().toUpperCase()}` : "")); } },
      f, h("button", { type: "submit" }, "Ver")),
    h("p", { class: "ayuda" }, `Partición: ${r.particion} · ${num(r.senales.length)} señales`),
    tabla([
      { t: "Señal", k: "id" }, { t: "Fuente", f: (s) => s.fuente_sistema || "—" }, { t: "Fecha", f: (s) => fechaHora(s.fecha_evento) },
      { t: "ID en bruto", f: (s) => s.customer_id_raw || "—" }, { t: "Tarjeta", f: (s) => s.tarjeta_fidelizacion_id || "—" },
      { t: "Candidato", f: (s) => s.customer_id_candidato || "—" },
    ], r.senales, { alClic: (s) => ctx.ir(`/clientes/identidad/${s.id}`), sinDatos: "No hay señales en esa partición." }));
}

async function candidatos(cuerpo, id, ctx) {
  const r = await get(`/identidad/senales/${encodeURIComponent(id)}/candidatos`);
  const s = r.senal;
  const asignar = async (cliente) => {
    await post(`/identidad/senales/${s.id}/asignar`, { customer_id: cliente });
    aviso(cliente ? `Señal asignada a ${cliente}.` : "Señal dejada sin asignar.");
    ctx.ir("/clientes/identidad");
  };
  const manual = h("input", { placeholder: "C0041", maxlength: "5", "aria-label": "Cliente" });
  const visibles = Object.entries(s).filter(([k, v]) => !k.startsWith("_") && !["pk"].includes(k) && v !== null && v !== "" && typeof v !== "object");
  montar(cuerpo,
    h("p", {}, h("a", { href: "#/clientes/identidad" }, "‹ Señales")),
    h("h1", {}, `Señal ${s.id}`),
    ficha(visibles.map(([k, v]) => [k, corta(String(v), 80)])),
    r.id_en_bruto_normalizado ? h("p", { class: "msg ok" }, `El ID en bruto «${s.customer_id_raw}» normalizado es ${r.id_en_bruto_normalizado}.`) : null,
    tieneRol("atencion", "marketing") ? h("div", { class: "fila" },
      manual, h("button", { type: "button", onclick: conAviso(async () => asignar(manual.value.trim().toUpperCase())) }, "Asignar a este cliente"),
      s.customer_id_candidato ? h("button", { type: "button", onclick: conAviso(async () => asignar(null)) }, "Dejar sin asignar") : null) : null,
    h("h2", {}, "Candidatos"),
    tabla([
      { t: "Cliente", f: (c) => h("a", { href: `#/clientes/${c.customer_id}` }, c.customer_id) },
      { t: "Coincidencias", f: (c) => c.coincidencias.join(", ") }, { t: "Señales compartidas", k: "senales", cls: "num" },
      { t: "", f: (c) => h("button", { type: "button", class: "primary", onclick: conAviso(async () => asignar(c.customer_id)) }, "Asignar") },
    ], r.candidatos, { sinDatos: "Ningún cliente comparte identificadores con esta señal." }));
}
