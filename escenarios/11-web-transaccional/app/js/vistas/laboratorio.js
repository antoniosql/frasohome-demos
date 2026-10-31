// Escenario 16 · laboratorio docente (rol profesor): corrección de la consola de identidad contra la verdad conocida,
// juegos de evaluación RAG editables, muestras para prompts, backlog de indicadores y tablas del escenario RAG.
import { borrar, get, post, put } from "../api.js";
import { aviso, cargando, confirmar, conAviso, corta, dialogo, fechaHora, h, montar, num, pestanas, selector, tabla, tablaDinamica } from "../ui.js";

const JUEGOS = [["Documental", "Documental"], ["Metrico_Mixto", "Métrico mixto"]];
const TABLAS = [["clientes", "Clientes"], ["productos", "Productos"], ["tiendas", "Tiendas"], ["stock", "Stock diario"], ["ventas", "Ventas diarias"], ["devoluciones", "Devoluciones"], ["alertas", "Alertas de rotura"]];

export async function render(cont, ctx) {
  const [sub] = ctx.partes;
  const cuerpo = h("div", {}, cargando());
  montar(cont, pestanas("laboratorio", [{ id: "", titulo: "Identidad" }, { id: "rag", titulo: "Juegos RAG" }, { id: "prompts", titulo: "Muestras de prompt" },
    { id: "backlog", titulo: "Backlog de indicadores" }, { id: "tablas", titulo: "Tablas RAG" }], sub || ""), cuerpo);
  if (sub === "rag") return rag(cuerpo, ctx);
  if (sub === "prompts") return prompts(cuerpo);
  if (sub === "backlog") return backlog(cuerpo);
  if (sub === "tablas") return tablas(cuerpo, ctx);
  return identidad(cuerpo);
}

async function identidad(cuerpo) {
  const r = await get("/lab/identidad/evaluacion");
  const pct = r.exactitud === null ? "—" : `${num(Math.round(r.exactitud * 1000) / 10)} %`;
  const k = (t, v, nota) => h("div", { class: "tarjeta" }, h("small", {}, t), h("p", { class: "grande" }, v), nota ? h("small", {}, nota) : null);
  montar(cuerpo, h("h1", {}, "Evaluación de la consola de identidad"),
    h("p", { class: "ayuda" }, "Compara el cliente asignado a cada señal con la verdad conocida (solo la ve el profesor). Los alumnos asignan desde la consola de identidad con el rol de atención o marketing."),
    h("div", { class: "kpis" }, k("Exactitud", pct, `${num(r.correctas)} de ${num(r.senales_evaluadas)} señales`), k("Sin asignar", num(r.sin_asignar)), k("Erróneas", num(r.erroneas)),
      k("Asignadas a mano", num(r.asignadas_a_mano), `${num(r.aciertos_a_mano)} acertadas`)),
    h("h2", {}, "Asignaciones erróneas"),
    tabla([{ t: "Señal", k: "senal" }, { t: "Asignado", f: (e) => e.asignado || "—" }, { t: "Correcto", k: "correcto" }, { t: "ID en bruto", f: (e) => e.id_en_bruto || "—" }, { t: "Fuente", f: (e) => e.fuente || "—" }],
      r.errores, { sinDatos: "Ninguna asignación errónea." }),
    h("h2", {}, "Pendientes de asignar"),
    tabla([{ t: "Señal", k: "senal" }, { t: "Cliente correcto", k: "correcto" }, { t: "ID en bruto", f: (e) => e.id_en_bruto || "—" }], r.pendientes, { sinDatos: "No queda ninguna señal por asignar." }));
}

async function rag(cuerpo, ctx) {
  const juego = ctx.params.get("juego") || "";
  const filas = await get("/lab/rag/casos", { juego: juego || undefined });
  const sel = selector([["", "Todos los juegos"], ...JUEGOS], juego, { "aria-label": "Juego", onchange: (ev) => ctx.ir(`/laboratorio/rag${ev.target.value ? `?juego=${ev.target.value}` : ""}`) });
  const campos = (c = {}) => [
    ...(c.test_set ? [] : [{ k: "juego", etiqueta: "Juego", tipo: "select", opciones: JUEGOS, valor: juego || "Documental" }]),
    { k: "pregunta", etiqueta: "Pregunta", tipo: "textarea", maxlength: 1000, req: true, valor: c.question || "" },
    { k: "respuesta", etiqueta: "Respuesta esperada", tipo: "textarea", maxlength: 2000, req: true, valor: c.expected_response || "" },
  ];
  montar(cuerpo,
    h("div", { class: "fila entre" }, h("h1", {}, "Juegos de evaluación RAG"),
      h("button", { type: "button", class: "primary", onclick: () => dialogo("Nuevo caso de prueba", campos(), async (v) => { await post("/lab/rag/casos", v); aviso("Caso creado."); rag(cuerpo, ctx); }, { enviar: "Crear" }) }, "Nuevo caso")),
    h("div", { class: "filtros" }, sel),
    tabla([{ t: "Juego", k: "test_set" }, { t: "Fila", k: "row_num", cls: "num" }, { t: "Pregunta", f: (c) => corta(c.question, 110) }, { t: "Respuesta esperada", f: (c) => corta(c.expected_response, 110) },
      { t: "Editado por", f: (c) => (c.updated_by ? `${c.updated_by} · ${fechaHora(c.updated_at)}` : "—") },
      { t: "", f: (c) => h("div", { class: "fila" },
        h("button", { type: "button", onclick: () => dialogo(`${c.test_set} · fila ${c.row_num}`, campos(c), async (v) => { await put(`/lab/rag/casos/${c.test_set}/${c.row_num}`, v); aviso("Caso actualizado."); rag(cuerpo, ctx); }) }, "Editar"),
        h("button", { type: "button", onclick: conAviso(async () => { if (!confirmar("¿Borrar este caso de prueba?")) return; await borrar(`/lab/rag/casos/${c.test_set}/${c.row_num}`); aviso("Caso borrado."); rag(cuerpo, ctx); }) }, "Borrar")) },
    ], filas, { sinDatos: "No hay casos." }));
}

async function prompts(cuerpo) {
  const filas = await get("/lab/prompts");
  montar(cuerpo, h("h1", {}, "Muestras para prompts"), h("p", { class: "ayuda" }, "Salidas de empleados con su comentario, listas para probar prompts de clasificación y resumen."), tablaDinamica(filas, { max: 140 }));
}

async function backlog(cuerpo) {
  const filas = await get("/lab/backlog");
  montar(cuerpo, h("h1", {}, "Backlog de indicadores"), h("p", { class: "ayuda" }, "Plantilla de indicadores pendientes de construir en los escenarios de analítica."), tablaDinamica(filas, { max: 140 }));
}

async function tablas(cuerpo, ctx) {
  const t = ctx.params.get("tabla") || "clientes";
  const filas = await get(`/lab/rag/tablas/${t}`, { tamano: 100 });
  const sel = selector(TABLAS, t, { "aria-label": "Tabla", onchange: (ev) => ctx.ir(`/laboratorio/tablas?tabla=${ev.target.value}`) });
  montar(cuerpo, h("div", { class: "fila entre" }, h("h1", {}, "Tablas del escenario RAG"), sel),
    h("p", { class: "ayuda" }, `Primeras ${num(filas.length)} filas de rag.${t}.`), tablaDinamica(filas, { max: 60 }));
}
