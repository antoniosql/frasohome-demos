// Escenario 11 · ciclo de vida del empleado: alta, movimientos, revisión salarial y baja con entrevista de salida.
// RR. HH. ve a toda la plantilla; un manager solo a su equipo y sin salarios (lo decide la API).
import { get, post } from "../api.js";
import { aviso, cargando, dialogo, eur, fecha, ficha, h, insignia, montar, num, paginador, selector, tabla } from "../ui.js";
import { soloRol, tieneRol } from "../sesion.js";

const TAMANO = 50;
const NIVELES = ["Junior", "Semi Senior", "Senior", "Manager"];
const CONTRATOS = ["Indefinido", "Temporal"];
const JORNADAS = ["Completa", "Parcial"];

export async function render(cont, ctx) {
  const [id] = ctx.partes;
  const cuerpo = h("div", {}, cargando());
  montar(cont, cuerpo);
  if (id) return ver(cuerpo, id, ctx);
  return lista(cuerpo, ctx);
}

const opcionesDepartamento = (deps) => deps.map((d) => d.departamento);

// ------------------------------------------------------------------ listado y alta

async function lista(cuerpo, ctx) {
  const p = ctx.params;
  const pagina = Number(p.get("pagina") || 1);
  const f = { q: p.get("q") || "", departamento: p.get("departamento") || "", estado: p.get("estado") || "" };
  const [deps, r] = await Promise.all([get("/rrhh/departamentos"), get("/rrhh/empleados", { ...f, pagina, tamano: TAMANO })]);
  const hr = tieneRol("rrhh");
  const texto = h("input", { type: "search", value: f.q, placeholder: "Nombre o código FSH0001", "aria-label": "Buscar" });
  const dep = selector([["", "Todos los departamentos"], ...opcionesDepartamento(deps)], f.departamento, { "aria-label": "Departamento" });
  const est = selector([["", "Todos los estados"], "Activo", "Baja"], f.estado, { "aria-label": "Estado" });
  const ir = (n) => {
    const s = new URLSearchParams();
    if (texto.value.trim()) s.set("q", texto.value.trim());
    if (dep.value) s.set("departamento", dep.value);
    if (est.value) s.set("estado", est.value);
    if (n > 1) s.set("pagina", n);
    ctx.ir("/personas" + (s.toString() ? "?" + s : ""));
  };
  montar(cuerpo,
    h("div", { class: "fila entre" }, h("h1", {}, soloRol("manager") && !hr ? "Mi equipo" : "Plantilla"),
      hr ? h("button", { type: "button", class: "primary", onclick: () => dialogo("Alta de empleado", [
        { k: "nombre", etiqueta: "Nombre y apellidos", maxlength: 200, req: true },
        { k: "genero", etiqueta: "Género", tipo: "select", opciones: [["", "—"], "M", "F", "Otro"], valor: "" },
        { k: "fecha_nacimiento", etiqueta: "Fecha de nacimiento", tipo: "date" },
        { k: "fecha_alta", etiqueta: "Fecha de alta", tipo: "date", ayuda: "Vacía = hoy" },
        { k: "departamento", etiqueta: "Departamento", tipo: "select", opciones: opcionesDepartamento(deps), valor: opcionesDepartamento(deps)[0] },
        { k: "ubicacion", etiqueta: "Ubicación", valor: "Madrid", maxlength: 100, req: true },
        { k: "rol", etiqueta: "Puesto", maxlength: 100, req: true },
        { k: "nivel", etiqueta: "Nivel", tipo: "select", opciones: NIVELES, valor: "Junior" },
        { k: "contrato", etiqueta: "Contrato", tipo: "select", opciones: CONTRATOS, valor: "Indefinido" },
        { k: "jornada", etiqueta: "Jornada", tipo: "select", opciones: JORNADAS, valor: "Completa" },
        { k: "manager_id", etiqueta: "Manager (opcional)", maxlength: 7, ayuda: "Código FSH0001" },
        { k: "teletrabajo", etiqueta: "Días de teletrabajo a la semana", tipo: "number", min: 0, max: 5, step: 1, valor: 0 },
        { k: "distancia_km", etiqueta: "Distancia casa-trabajo (km)", tipo: "number", min: 0, step: 0.1 },
        { k: "tienda", etiqueta: "Tienda (opcional)", maxlength: 4 },
      ], async (v) => {
        const e = await post("/rrhh/empleados", { ...v, manager_id: v.manager_id && v.manager_id.toUpperCase() });
        aviso(`Empleado ${e.employee_id} dado de alta.`);
        ctx.ir(`/personas/${e.employee_id}`);
      }, { enviar: "Dar de alta" }) }, "Nuevo empleado") : null),
    h("form", { class: "filtros", role: "search", onsubmit: (ev) => { ev.preventDefault(); ir(1); } }, texto, dep, est, h("button", { type: "submit" }, "Buscar")),
    tabla([
      { t: "Código", k: "employee_id" }, { t: "Nombre", k: "full_name" }, { t: "Departamento", f: (e) => e.department || "—" }, { t: "Puesto", f: (e) => e.role_name || "—" },
      { t: "Nivel", f: (e) => e.level_name || "—" }, { t: "Ubicación", f: (e) => e.location || "—" }, { t: "Alta", f: (e) => fecha(e.hired_at) }, { t: "Estado", f: (e) => insignia(e.employee_status) },
    ], r.empleados, { alClic: (e) => ctx.ir(`/personas/${e.employee_id}`), sinDatos: "Ningún empleado coincide." }),
    paginador(pagina, r.total, TAMANO, ir));
}

// ------------------------------------------------------------------ ficha

async function ver(cuerpo, id, ctx) {
  const [e, deps] = await Promise.all([get(`/rrhh/empleados/${encodeURIComponent(id)}`), get("/rrhh/departamentos")]);
  const recargar = () => ver(cuerpo, id, ctx);
  const hr = tieneRol("rrhh");
  const activo = e.employee_status === "Activo";
  const acciones = [];
  if (hr && activo) {
    acciones.push(
      h("button", { type: "button", onclick: () => dialogo(`Movimiento de ${e.full_name}`, [
        { k: "tipo", etiqueta: "Tipo", tipo: "select", opciones: ["Promoción", "Movilidad interna"], valor: "Promoción" },
        { k: "departamento", etiqueta: "Nuevo departamento", tipo: "select", opciones: [["", "Sin cambio"], ...opcionesDepartamento(deps)], valor: "" },
        { k: "nivel", etiqueta: "Nuevo nivel", tipo: "select", opciones: [["", "Sin cambio"], ...NIVELES], valor: "" },
        { k: "rol", etiqueta: "Nuevo puesto", maxlength: 100, ayuda: "Vacío = sin cambio" },
        { k: "ubicacion", etiqueta: "Nueva ubicación", maxlength: 100 },
        { k: "manager_id", etiqueta: "Nuevo manager", maxlength: 7, ayuda: "Código FSH0001" },
        { k: "motivo", etiqueta: "Motivo", maxlength: 200, req: true },
        { k: "fecha", etiqueta: "Fecha efectiva", tipo: "date", ayuda: "Vacía = hoy" },
      ], async (v) => {
        await post(`/rrhh/empleados/${e.employee_id}/movimientos`, { ...v, manager_id: v.manager_id && v.manager_id.toUpperCase() });
        aviso("Movimiento registrado."); recargar();
      }, { enviar: "Registrar" }) }, "Movimiento"),
      h("button", { type: "button", onclick: () => dialogo(`Revisión salarial de ${e.full_name}`, [
        { k: "salario_base", etiqueta: "Salario base anual (€)", tipo: "number", min: 0, step: 100, req: true },
        { k: "variable", etiqueta: "Variable anual (€)", tipo: "number", min: 0, step: 100, valor: 0 },
        { k: "periodo", etiqueta: "Periodo (AAAA-MM)", patron: "\\d{4}-\\d{2}", maxlength: 7, ayuda: "Vacío = mes actual" },
        { k: "motivo", etiqueta: "Motivo", maxlength: 200, valor: "Revisión salarial" },
      ], async (v) => { await post(`/rrhh/empleados/${e.employee_id}/salario`, v); aviso("Revisión salarial registrada."); recargar(); }, { enviar: "Registrar" }) }, "Revisión salarial"),
      h("button", { type: "button", onclick: () => dialogo(`Baja de ${e.full_name}`, [
        { k: "fecha", etiqueta: "Fecha de baja", tipo: "date", ayuda: "Vacía = hoy" },
        { k: "tipo", etiqueta: "Tipo de baja", tipo: "select", opciones: ["Voluntaria", "Involuntaria/fin contrato"], valor: "Voluntaria" },
        { k: "motivo", etiqueta: "Motivo", maxlength: 200, req: true },
        { k: "comentario", etiqueta: "Entrevista de salida · comentario", tipo: "textarea", maxlength: 2000 },
        { k: "recomendaria", etiqueta: "¿Recomendaría la empresa? (0 a 10)", tipo: "number", min: 0, max: 10, step: 1 },
        { k: "canal", etiqueta: "Canal de la entrevista", maxlength: 50 },
        { k: "entrevistador", etiqueta: "Entrevistador", maxlength: 100 },
      ], async (v) => {
        const { comentario, recomendaria, canal, entrevistador, ...baja } = v;
        const entrevista = Object.fromEntries(Object.entries({ comentario, recomendaria, canal, entrevistador }).filter(([, x]) => x !== null));
        await post(`/rrhh/empleados/${e.employee_id}/baja`, { ...baja, entrevista });
        aviso("Baja registrada."); recargar();
      }, { enviar: "Dar de baja", intro: "La baja es definitiva: el empleado deja de poder pedir ausencias y horas." }) }, "Dar de baja"));
  }

  const tablaDe = (titulo, cols, filas, vacioTxt) => [h("h2", {}, titulo), tabla(cols, filas, { sinDatos: vacioTxt })];
  montar(cuerpo,
    h("p", {}, h("a", { href: "#/personas" }, "‹ Plantilla")),
    h("h1", {}, `${e.full_name} `, insignia(e.employee_status)),
    h("p", { class: "ayuda" }, `${e.employee_id} · ${e.role_name || "sin puesto"} · ${e.department || "sin departamento"}`),
    acciones.length ? h("div", { class: "fila" }, acciones) : null,
    ficha([["Departamento", e.department], ["Puesto", e.role_name], ["Nivel", e.level_name], ["Ubicación", e.location], ["Contrato", e.contract_type], ["Jornada", e.work_schedule],
      ["Manager", e.manager_id ? h("a", { href: `#/personas/${e.manager_id}` }, `${e.manager_id} · ${e.manager_name || ""}`) : null],
      ["Alta", fecha(e.hired_at)], e.left_at ? ["Baja", `${fecha(e.left_at)} · ${e.exit_type || ""} · ${e.exit_reason || ""}`] : null,
      ["Género", e.gender], ["Nacimiento", e.birth_date ? fecha(e.birth_date) : null], ["Teletrabajo", `${num(e.remote_days_week)} días/semana`],
      ["Distancia", e.commute_km === null || e.commute_km === undefined ? null : `${num(e.commute_km)} km`]]),
    e.compensacion ? tablaDe("Compensación", [
      { t: "Periodo", k: "period_month" }, { t: "Base", f: (c) => eur(c.base_salary_eur), cls: "num" },
      { t: "Variable", f: (c) => eur(c.variable_salary_eur), cls: "num" }, { t: "Subida", f: (c) => (c.increase_pct === null || c.increase_pct === undefined ? "—" : `${num(c.increase_pct)} %`), cls: "num" },
    ], e.compensacion, "Sin datos de compensación.") : null,
    tablaDe("Movimientos", [
      { t: "Fecha", f: (m) => fecha(m.moved_at) }, { t: "Tipo", k: "movement_type" },
      { t: "Departamento", f: (m) => (m.department_to ? `${m.department_from || "—"} → ${m.department_to}` : "—") },
      { t: "Nivel", f: (m) => (m.level_to ? `${m.level_from || "—"} → ${m.level_to}` : "—") }, { t: "Motivo", f: (m) => m.reason || "—" },
    ], e.movimientos, "Sin movimientos."),
    tablaDe("Evaluaciones", [
      { t: "Ciclo", k: "review_cycle" }, { t: "Nota", f: (r) => num(r.overall_score), cls: "num" }, { t: "Objetivos", f: (r) => (r.objectives_pct === null ? "—" : `${num(r.objectives_pct)} %`), cls: "num" },
      { t: "Competencias", f: (r) => num(r.competencies_score), cls: "num" }, { t: "Potencial", f: (r) => r.potential || "—" }, { t: "Comentario", f: (r) => r.manager_comment || "—" },
    ], e.evaluaciones, "Sin evaluaciones."),
    tablaDe("Ausencias recientes", [
      { t: "Inicio", f: (a) => fecha(a.start_date) }, { t: "Fin", f: (a) => fecha(a.end_date) }, { t: "Tipo", k: "absence_type" },
      { t: "Días", f: (a) => num(a.working_days), cls: "num" }, { t: "Justificada", f: (a) => a.justified || "—" },
    ], e.ausencias, "Sin ausencias."),
    tablaDe("Horas extra", [
      { t: "Periodo", k: "period_month" }, { t: "Horas", f: (o) => num(o.hours), cls: "num" }, { t: "Motivo", f: (o) => o.reason || "—" }, { t: "Estado", f: (o) => insignia(o.approval_status) },
    ], e.horas_extra, "Sin horas extra."),
    tablaDe("Formación", [
      { t: "Curso", f: (t) => `${t.course_id} · ${t.course_name}` }, { t: "Inicio", f: (t) => fecha(t.start_date) },
      { t: "Horas", f: (t) => `${num(t.completed_hours ?? 0)} / ${num(t.planned_hours)}`, cls: "num" }, { t: "Estado", f: (t) => insignia(t.training_status) },
      hr ? { t: "", f: (t) => h("button", { type: "button", onclick: () => dialogo(`Cerrar ${t.course_name}`, [
        { k: "horas", etiqueta: "Horas realizadas", tipo: "number", min: 0, max: 300, step: 0.5, valor: t.planned_hours, req: true },
        { k: "completado", etiqueta: "¿Completó el curso?", tipo: "select", opciones: ["Sí", "No"], valor: "Sí" },
      ], async (v) => { await post(`/rrhh/formacion/${t.training_id}/cierre`, { horas: v.horas, completado: v.completado === "Sí" }); aviso("Curso cerrado."); recargar(); }, { enviar: "Cerrar curso" }) }, "Cerrar") } : null,
    ].filter(Boolean), e.formacion, "Sin formación."));
}
