// Escenario 12 · tiempo y desempeño: ausencias, horas extra con aprobación del manager, formación y evaluación anual.
import { get, post } from "../api.js";
import { aviso, cargando, conAviso, corta, dialogo, fecha, fechaHora, h, hoy, insignia, montar, num, pestanas, selector, tabla } from "../ui.js";
import { soloRol, tieneRol } from "../sesion.js";

const TIPOS_AUSENCIA = ["Enfermedad común", "Permiso retribuido", "Cuidado familiar", "Accidente laboral", "Ausencia injustificada", "Vacaciones"];
const ESTADOS_HORAS = [["", "Todas"], ["Pendiente", "Pendientes"], ["Aprobada", "Aprobadas"], ["Rechazada", "Rechazadas"]];

export async function render(cont, ctx) {
  const [sub] = ctx.partes;
  const tabs = [];
  if (soloRol("manager")) tabs.push({ id: "", titulo: "Mi equipo" });
  tabs.push({ id: "ausencias", titulo: "Ausencias" }, { id: "horas", titulo: "Horas extra" }, { id: "formacion", titulo: "Formación" }, { id: "evaluaciones", titulo: "Evaluaciones" });
  const activa = sub || (soloRol("manager") ? "" : "ausencias");
  const cuerpo = h("div", {}, cargando());
  montar(cont, pestanas("tiempo", tabs, activa), cuerpo);
  if (activa === "") return equipo(cuerpo, ctx);
  if (activa === "horas") return horas(cuerpo, ctx);
  if (activa === "formacion") return formacion(cuerpo, ctx);
  if (activa === "evaluaciones") return evaluaciones(cuerpo, ctx);
  return ausencias(cuerpo, ctx);
}

const empleado = (e, nombre) => h("a", { href: `#/personas/${e}` }, nombre ? `${e} · ${nombre}` : e);

// ------------------------------------------------------------------ equipo

async function equipo(cuerpo, ctx) {
  const filas = await get("/equipo");
  montar(cuerpo, h("h1", {}, "Mi equipo"),
    tabla([
      { t: "Empleado", f: (e) => empleado(e.employee_id, e.full_name) }, { t: "Puesto", f: (e) => e.role_name || "—" }, { t: "Nivel", f: (e) => e.level_name || "—" },
      { t: "Ubicación", f: (e) => e.location || "—" }, { t: "Antigüedad", f: (e) => fecha(e.hired_at) },
      { t: "Horas extra pendientes", f: (e) => (e.horas_extra_pendientes ? h("strong", {}, num(e.horas_extra_pendientes)) : "0"), cls: "num" },
      { t: "Última nota", f: (e) => (e.ultima_evaluacion === null || e.ultima_evaluacion === undefined ? "—" : num(e.ultima_evaluacion)), cls: "num" },
      { t: "", f: (e) => h("button", { type: "button", onclick: () => evaluar(ctx, e.employee_id, () => equipo(cuerpo, ctx)) }, "Evaluar") },
    ], filas, { sinDatos: "No tienes colaboradores directos activos." }));
}

// ------------------------------------------------------------------ ausencias

async function ausencias(cuerpo, ctx) {
  const emp = (ctx.params.get("empleado") || "").toUpperCase();
  const filas = await get("/rrhh/ausencias", { empleado: emp || undefined, tamano: 100 });
  const f = h("input", { value: emp, placeholder: "Empleado (FSH0001)", maxlength: "7", "aria-label": "Empleado" });
  montar(cuerpo,
    h("div", { class: "fila entre" }, h("h1", {}, "Ausencias"),
      tieneRol("rrhh") ? h("button", { type: "button", class: "primary", onclick: () => dialogo("Registrar ausencia", [
        { k: "employee_id", etiqueta: "Empleado", maxlength: 7, req: true, ayuda: "Código FSH0001" },
        { k: "inicio", etiqueta: "Primer día", tipo: "date", req: true, valor: hoy() }, { k: "fin", etiqueta: "Último día", tipo: "date", req: true, valor: hoy() },
        { k: "tipo", etiqueta: "Tipo", tipo: "select", opciones: TIPOS_AUSENCIA, valor: "Vacaciones" },
        { k: "justificada", etiqueta: "Justificada", tipo: "select", opciones: ["Pendiente", "Sí", "No"], valor: "Pendiente" },
        { k: "notas", etiqueta: "Notas", maxlength: 300 },
      ], async (v) => { await post("/rrhh/ausencias", { ...v, employee_id: v.employee_id.toUpperCase() }); aviso("Ausencia registrada."); ausencias(cuerpo, ctx); }, { enviar: "Registrar" }) }, "Registrar ausencia") : null),
    h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); ctx.ir("/tiempo/ausencias" + (f.value.trim() ? `?empleado=${f.value.trim().toUpperCase()}` : "")); } }, f, h("button", { type: "submit" }, "Filtrar")),
    tabla([
      { t: "Empleado", f: (a) => empleado(a.employee_id, a.full_name) }, { t: "Inicio", f: (a) => fecha(a.start_date) }, { t: "Fin", f: (a) => fecha(a.end_date) },
      { t: "Tipo", k: "absence_type" }, { t: "Días", f: (a) => num(a.working_days), cls: "num" }, { t: "Justificada", f: (a) => a.justified || "—" }, { t: "Notas", f: (a) => corta(a.notes, 60) },
    ], filas, { sinDatos: "No hay ausencias." }));
}

// ------------------------------------------------------------------ horas extra

async function horas(cuerpo, ctx) {
  const estado = ctx.params.get("estado") ?? "Pendiente";
  const filas = await get("/rrhh/horas-extra", { estado: estado || undefined, tamano: 100 });
  const sel = selector(ESTADOS_HORAS, estado, { "aria-label": "Estado" });
  const decidir = (o, aprobar) => conAviso(async () => {
    await post(`/rrhh/horas-extra/${o.overtime_id}/decision`, { aprobar });
    aviso(aprobar ? "Horas extra aprobadas." : "Horas extra rechazadas."); horas(cuerpo, ctx);
  });
  montar(cuerpo, h("h1", {}, "Horas extra"),
    h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); ctx.ir(`/tiempo/horas?estado=${sel.value}`); } }, sel, h("button", { type: "submit" }, "Filtrar")),
    tabla([
      { t: "Empleado", f: (o) => empleado(o.employee_id, o.full_name) }, { t: "Periodo", k: "period_month" }, { t: "Horas", f: (o) => num(o.hours), cls: "num" },
      { t: "Motivo", f: (o) => o.reason || "—" }, { t: "Solicitada", f: (o) => fechaHora(o.requested_at) }, { t: "Estado", f: (o) => insignia(o.approval_status) },
      { t: "Decidida por", f: (o) => o.approver_id || "—" },
      { t: "", f: (o) => (o.approval_status === "Pendiente"
        ? h("div", { class: "fila" }, h("button", { type: "button", class: "primary", onclick: decidir(o, true) }, "Aprobar"), h("button", { type: "button", onclick: decidir(o, false) }, "Rechazar")) : "") },
    ], filas, { sinDatos: "No hay horas extra con ese estado." }));
}

// ------------------------------------------------------------------ formación

async function formacion(cuerpo, ctx) {
  const cursos = await get("/rrhh/cursos");
  const inscribir = (curso) => dialogo("Inscribir en un curso", [
    { k: "employee_id", etiqueta: "Empleado", maxlength: 7, req: true, ayuda: "Código FSH0001" },
    { k: "curso", etiqueta: "Curso", tipo: "select", opciones: cursos.map((c) => [c.course_id, `${c.course_id} · ${c.course_name}`]), valor: curso || cursos[0]?.course_id },
    { k: "inicio", etiqueta: "Inicio", tipo: "date", req: true, valor: hoy() }, { k: "fin", etiqueta: "Fin", tipo: "date", req: true, valor: hoy() },
    { k: "horas", etiqueta: "Horas previstas", tipo: "number", min: 0.5, max: 200, step: 0.5, req: true, valor: 8 },
  ], async (v) => { await post("/rrhh/formacion", { ...v, employee_id: v.employee_id.toUpperCase() }); aviso("Inscripción registrada."); }, { enviar: "Inscribir" });
  montar(cuerpo, h("h1", {}, "Catálogo de formación"),
    h("p", { class: "ayuda" }, "Inscribe a un empleado de tu equipo; RR. HH. registra el cierre del curso desde la ficha del empleado."),
    tabla([
      { t: "Curso", k: "course_id" }, { t: "Nombre", k: "course_name" }, { t: "Categoría", f: (c) => c.category || "—" }, { t: "Proveedor", f: (c) => c.provider || "—" },
      { t: "Horas típicas", f: (c) => num(c.horas_tipicas), cls: "num" }, { t: "Ediciones", k: "ediciones", cls: "num" },
      { t: "", f: (c) => h("button", { type: "button", onclick: () => inscribir(c.course_id) }, "Inscribir") },
    ], cursos));
}

// ------------------------------------------------------------------ evaluaciones

function evaluar(ctx, empleadoId, alTerminar) {
  return dialogo("Evaluación del desempeño", [
    { k: "employee_id", etiqueta: "Empleado", maxlength: 7, req: true, valor: empleadoId || "", ayuda: "Código FSH0001" },
    { k: "ciclo", etiqueta: "Ciclo (año)", patron: "\\d{4}", maxlength: 4, req: true, valor: String(new Date().getFullYear()) },
    { k: "puntuacion", etiqueta: "Puntuación global (1 a 5)", tipo: "number", min: 1, max: 5, step: 0.1, req: true },
    { k: "objetivos_pct", etiqueta: "Objetivos cumplidos (%)", tipo: "number", min: 0, max: 200, step: 1 },
    { k: "competencias", etiqueta: "Competencias (1 a 5)", tipo: "number", min: 1, max: 5, step: 0.1 },
    { k: "potencial", etiqueta: "Potencial", tipo: "select", opciones: [["", "—"], "Alto", "Medio", "Bajo"], valor: "" },
    { k: "comentario", etiqueta: "Comentario del manager", tipo: "textarea", maxlength: 500 },
  ], async (v) => { await post("/rrhh/evaluaciones", { ...v, employee_id: v.employee_id.toUpperCase() }); aviso("Evaluación guardada."); alTerminar(); }, { enviar: "Guardar" });
}

async function evaluaciones(cuerpo, ctx) {
  const ciclo = ctx.params.get("ciclo") || "";
  const filas = await get("/rrhh/evaluaciones", { ciclo: ciclo || undefined, tamano: 100 });
  const f = h("input", { value: ciclo, placeholder: "Ciclo (2025)", maxlength: "4", "aria-label": "Ciclo" });
  montar(cuerpo,
    h("div", { class: "fila entre" }, h("h1", {}, "Evaluaciones"),
      h("button", { type: "button", class: "primary", onclick: () => evaluar(ctx, "", () => evaluaciones(cuerpo, ctx)) }, "Nueva evaluación")),
    h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); ctx.ir("/tiempo/evaluaciones" + (f.value.trim() ? `?ciclo=${f.value.trim()}` : "")); } }, f, h("button", { type: "submit" }, "Filtrar")),
    tabla([
      { t: "Empleado", f: (r) => empleado(r.employee_id, r.full_name) }, { t: "Ciclo", k: "review_cycle" }, { t: "Fecha", f: (r) => fecha(r.reviewed_at) },
      { t: "Nota", f: (r) => num(r.overall_score), cls: "num" }, { t: "Objetivos", f: (r) => (r.objectives_pct === null || r.objectives_pct === undefined ? "—" : `${num(r.objectives_pct)} %`), cls: "num" },
      { t: "Competencias", f: (r) => num(r.competencies_score), cls: "num" }, { t: "Potencial", f: (r) => r.potential || "—" }, { t: "Evaluador", f: (r) => r.reviewer_id || "—" },
    ], filas, { sinDatos: "No hay evaluaciones." }));
}
