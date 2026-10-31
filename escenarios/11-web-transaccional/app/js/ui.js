// FraSoHome Live · utilidades de interfaz. Todo el HTML se construye con nodos DOM y textContent:
// nunca se interpola texto de la API en innerHTML.

/** Crea un elemento: h("button", { class: "primary", onclick: fn }, "Texto", hijo, ...) */
export function h(tag, props, ...hijos) {
  const el = document.createElement(tag);
  let valor;
  for (const [k, v] of Object.entries(props || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "value") valor = v;
    else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2), v);
    else if (k === "dataset") Object.assign(el.dataset, v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  anadir(el, hijos);
  if (valor !== undefined) el.value = valor;   // en <select> hay que fijarlo después de crear las opciones
  return el;
}

function anadir(el, hijos) {
  for (const hijo of hijos.flat(Infinity)) {
    if (hijo === null || hijo === undefined || hijo === false) continue;
    el.append(hijo instanceof Node ? hijo : document.createTextNode(String(hijo)));
  }
}

export function vaciar(el) { while (el.firstChild) el.removeChild(el.firstChild); return el; }
export function montar(el, ...hijos) { vaciar(el); anadir(el, hijos); return el; }

// ------------------------------------------------------------------ formatos

const EUR = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" });
const NUM = new Intl.NumberFormat("es-ES");
const FECHA = new Intl.DateTimeFormat("es-ES", { day: "2-digit", month: "2-digit", year: "numeric" });
const FECHA_HORA = new Intl.DateTimeFormat("es-ES", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });

export const eur = (n) => (n === null || n === undefined || n === "" ? "—" : EUR.format(Number(n)));
export const num = (n) => (n === null || n === undefined || n === "" ? "—" : NUM.format(Number(n)));

function aFecha(s) {
  if (!s) return null;
  const d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(String(s)) || String(s).length <= 10 ? s : s + "Z");   // la API entrega UTC sin zona
  return Number.isNaN(d.getTime()) ? null : d;
}
export const fecha = (s) => { const d = aFecha(s); return d ? FECHA.format(d) : "—"; };
export const fechaHora = (s) => { const d = aFecha(s); return d ? FECHA_HORA.format(d) : "—"; };
export const hoy = () => new Date().toISOString().slice(0, 10);

// ------------------------------------------------------------------ avisos

export function aviso(texto, tipo = "ok") {
  const cont = document.getElementById("avisos");
  const el = h("div", { class: "aviso " + tipo, role: tipo === "ko" ? "alert" : "status" }, texto);
  cont.append(el);
  setTimeout(() => el.remove(), tipo === "ko" ? 9000 : 4500);
}

/** Envuelve un manejador: desactiva el botón mientras corre y muestra el error de la API como aviso. */
export function conAviso(fn) {
  return async (ev) => {
    const boton = ev && ev.currentTarget && ev.currentTarget.tagName === "BUTTON" ? ev.currentTarget : null;
    if (ev && ev.preventDefault && ev.type === "submit") ev.preventDefault();
    if (boton) boton.disabled = true;
    try { await fn(ev); }
    catch (e) { aviso(e.message || "Algo ha fallado.", "ko"); }
    finally { if (boton) boton.disabled = false; }
  };
}

export const cargando = (texto = "Cargando…") => h("p", { class: "cargando", role: "status" }, texto);
export const vacio = (texto) => h("p", { class: "vacio" }, texto);

// ------------------------------------------------------------------ componentes

const TONOS = {
  ok: ["Activo", "Activa", "Entregado", "Aceptada", "Reembolsada", "Abierta", "Cerrada", "emitido"],
  aviso: ["Pendiente", "En preparación", "Planificada", "Devuelto Parcial", "Media"],
  ko: ["Cancelado", "Rechazada", "Descatalogado", "Devuelto Total", "Alta", "caducado"],
};
export function insignia(texto) {
  const t = Object.keys(TONOS).find((k) => TONOS[k].includes(texto)) || "neutro";
  return h("span", { class: "insignia " + t }, texto ?? "—");
}

/** Tabla. columnas: [{ t: "Título", k: "campo" | f: (fila) => nodo|texto, cls: "num" }] */
export function tabla(columnas, filas, { alClic, sinDatos = "No hay resultados." } = {}) {
  if (!filas || !filas.length) return vacio(sinDatos);
  const cuerpo = filas.map((fila) => {
    const tr = h("tr", alClic ? { class: "clicable", tabindex: "0", onclick: () => alClic(fila),
      onkeydown: (ev) => { if (ev.key === "Enter") alClic(fila); } } : {});
    for (const c of columnas) tr.append(h("td", { class: c.cls }, c.f ? c.f(fila) : (fila[c.k] ?? "—")));
    return tr;
  });
  return h("div", { class: "tabla-caja" }, h("table", {},
    h("thead", {}, h("tr", {}, columnas.map((c) => h("th", { class: c.cls, scope: "col" }, c.t)))),
    h("tbody", {}, cuerpo)));
}

let _n = 0;
/** Campo de formulario con su etiqueta. */
export function campo(etiqueta, control, ayuda) {
  if (!control.id) control.id = "c" + (++_n);
  return h("div", { class: "campo" }, h("label", { for: control.id }, etiqueta), control, ayuda ? h("small", {}, ayuda) : null);
}

export function opciones(lista, valor) {
  return lista.map((o) => {
    const [v, t] = Array.isArray(o) ? o : [o, o];
    return h("option", { value: v, selected: String(v) === String(valor ?? "") }, t);
  });
}

export function selector(lista, valor, props = {}) {
  return h("select", props, opciones(lista, valor));
}

/** Pestañas: elementos [{ id, titulo }]; devuelve la barra con enlaces #/ruta/id. */
export function pestanas(base, elementos, activa, sufijo = "") {
  return h("nav", { class: "pestanas", "aria-label": "Secciones" }, elementos.map((e) =>
    h("a", { href: `#/${base}${e.id ? "/" + e.id : ""}${sufijo}`, "aria-current": e.id === activa ? "page" : null }, e.titulo)));
}

export function paginador(pagina, total, tamano, alCambiar) {
  const paginas = Math.max(1, Math.ceil(total / tamano));
  if (paginas === 1) return null;
  return h("div", { class: "paginador" },
    h("button", { type: "button", disabled: pagina <= 1, onclick: () => alCambiar(pagina - 1) }, "‹ Anterior"),
    h("span", {}, `Página ${pagina} de ${paginas} · ${num(total)} resultados`),
    h("button", { type: "button", disabled: pagina >= paginas, onclick: () => alCambiar(pagina + 1) }, "Siguiente ›"));
}

/** Pares etiqueta/valor en una lista de definición. */
export function ficha(pares) {
  return h("dl", { class: "ficha" }, pares.filter((p) => p).map(([k, v]) => [h("dt", {}, k), h("dd", {}, v ?? "—")]));
}

/**
 * Diálogo con formulario. campos: [{ k, etiqueta, tipo, opciones, valor, min, max, step, req, ayuda, maxlength }].
 * alEnviar(valores) puede lanzar: el error se muestra dentro del diálogo y no se cierra.
 */
export function dialogo(titulo, campos, alEnviar, { enviar = "Guardar", intro } = {}) {
  const error = h("p", { class: "msg ko", role: "alert" });
  const controles = {};
  const filas = campos.map((c) => {
    let control;
    if (c.tipo === "select") control = selector(c.opciones, c.valor, { name: c.k });
    else if (c.tipo === "textarea") control = h("textarea", { name: c.k, rows: 3, maxlength: c.maxlength, required: c.req }, c.valor ?? "");
    else control = h("input", { name: c.k, type: c.tipo || "text", value: c.valor ?? "", min: c.min, max: c.max, step: c.step,
      required: c.req, maxlength: c.maxlength, pattern: c.patron, autocomplete: "off" });
    controles[c.k] = control;
    return campo(c.etiqueta, control, c.ayuda);
  });
  const dlg = h("dialog", { class: "dialogo" });
  const form = h("form", { method: "dialog", onsubmit: conAviso(async (ev) => {
    ev.preventDefault();
    error.textContent = "";
    const valores = {};
    for (const c of campos) {
      const v = controles[c.k].value.trim();
      valores[c.k] = v === "" ? null : (c.tipo === "number" ? Number(v) : v);
    }
    const boton = form.querySelector("button.primary");
    boton.disabled = true;
    try { await alEnviar(valores); dlg.close(); dlg.remove(); }
    catch (e) { error.textContent = e.message || "No se pudo guardar."; }
    finally { boton.disabled = false; }
  }) },
    h("h2", {}, titulo), intro ? h("p", { class: "ayuda" }, intro) : null, filas, error,
    h("div", { class: "acciones" },
      h("button", { type: "button", onclick: () => { dlg.close(); dlg.remove(); } }, "Cancelar"),
      h("button", { type: "submit", class: "primary" }, enviar)));
  dlg.append(form);
  dlg.addEventListener("cancel", () => dlg.remove());
  document.body.append(dlg);
  dlg.showModal();
  const primero = form.querySelector("input, select, textarea");
  if (primero) primero.focus();
  return dlg;
}

export function confirmar(texto) { return window.confirm(texto); }
