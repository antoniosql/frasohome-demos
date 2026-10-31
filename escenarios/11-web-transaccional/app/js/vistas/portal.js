// Escenario 13 · portal del empleado: mis datos, ausencias, horas extra, cursos y la encuesta de clima.
import { get, post } from "../api.js";
import { aviso, cargando, conAviso, dialogo, eur, fecha, fechaHora, ficha, h, hoy, insignia, montar, num, pestanas, tabla } from "../ui.js";

const MOTIVOS = ["Inventario", "Pico e-commerce", "Cobertura de turnos", "Proyecto interno", "Campaña comercial"];

export async function render(cont, ctx) {
  const [sub] = ctx.partes;
  const cuerpo = h("div", {}, cargando());
  montar(cont, pestanas("portal", [{ id: "", titulo: "Mis datos" }, { id: "ausencias", titulo: "Ausencias" }, { id: "horas", titulo: "Horas extra" },
    { id: "formacion", titulo: "Formación" }, { id: "encuesta", titulo: "Encuesta de clima" }], sub || ""), cuerpo);
  if (sub === "ausencias") return ausencias(cuerpo);
  if (sub === "horas") return horas(cuerpo);
  if (sub === "formacion") return formacion(cuerpo);
  if (sub === "encuesta") return encuesta(cuerpo, ctx);
  return yo(cuerpo);
}

async function yo(cuerpo) {
  const e = await get("/portal/yo");
  montar(cuerpo, h("h1", {}, e.full_name), h("p", { class: "ayuda" }, `${e.employee_id} · ${e.role_name || ""} · ${e.department || ""}`),
    h("div", { class: "dos" },
      h("section", {}, h("h2", {}, "Tu puesto"), ficha([["Departamento", e.department], ["Puesto", e.role_name], ["Nivel", e.level_name], ["Ubicación", e.location],
        ["Contrato", e.contract_type], ["Jornada", e.work_schedule], ["Manager", e.manager_name], ["Alta", fecha(e.hired_at)], ["Teletrabajo", `${num(e.remote_days_week)} días/semana`]])),
      h("section", { class: "kpis" },
        h("div", { class: "tarjeta" }, h("small", {}, "Días de ausencia este año"), h("p", { class: "grande" }, num(e.dias_ausencia_anio))),
        e.salario ? h("div", { class: "tarjeta" }, h("small", {}, `Salario base (${e.salario.period_month})`), h("p", { class: "grande" }, eur(e.salario.base_salary_eur)),
          h("small", {}, `Variable ${eur(e.salario.variable_salary_eur)}`)) : null)));
}

async function ausencias(cuerpo) {
  const filas = await get("/portal/ausencias");
  montar(cuerpo, h("h1", {}, "Mis ausencias"), tabla([
    { t: "Inicio", f: (a) => fecha(a.start_date) }, { t: "Fin", f: (a) => fecha(a.end_date) }, { t: "Tipo", k: "absence_type" },
    { t: "Días laborables", f: (a) => num(a.working_days), cls: "num" }, { t: "Justificada", f: (a) => a.justified || "—" }, { t: "Notas", f: (a) => a.notes || "—" },
  ], filas, { sinDatos: "No tienes ausencias registradas." }),
  h("p", { class: "ayuda" }, "Las ausencias las registra RR. HH.: si falta alguna, avísales."));
}

async function horas(cuerpo) {
  const filas = await get("/portal/horas-extra");
  const mes = new Date().toISOString().slice(0, 7);
  montar(cuerpo,
    h("div", { class: "fila entre" }, h("h1", {}, "Mis horas extra"),
      h("button", { type: "button", class: "primary", onclick: () => dialogo("Solicitar horas extra", [
        { k: "periodo", etiqueta: "Mes (AAAA-MM)", patron: "\\d{4}-\\d{2}", maxlength: 7, req: true, valor: mes },
        { k: "horas", etiqueta: "Horas", tipo: "number", min: 0.5, max: 80, step: 0.5, req: true, valor: 2 },
        { k: "motivo", etiqueta: "Motivo", tipo: "select", opciones: MOTIVOS, valor: MOTIVOS[0] },
      ], async (v) => { await post("/portal/horas-extra", v); aviso("Solicitud enviada a tu manager."); horas(cuerpo); }, { enviar: "Solicitar" }) }, "Solicitar horas")),
    tabla([
      { t: "Mes", k: "period_month" }, { t: "Horas", f: (o) => num(o.hours), cls: "num" }, { t: "Motivo", f: (o) => o.reason || "—" },
      { t: "Estado", f: (o) => insignia(o.approval_status) }, { t: "Solicitada", f: (o) => fechaHora(o.requested_at) }, { t: "Decidida", f: (o) => (o.decided_at ? fechaHora(o.decided_at) : "—") },
    ], filas, { sinDatos: "No has pedido horas extra." }));
}

async function formacion(cuerpo) {
  const [filas, cursos] = await Promise.all([get("/portal/formacion"), get("/rrhh/cursos").catch(() => [])]);
  const campos = [
    cursos.length ? { k: "curso", etiqueta: "Curso", tipo: "select", opciones: cursos.map((c) => [c.course_id, `${c.course_id} · ${c.course_name}`]), valor: cursos[0].course_id }
      : { k: "curso", etiqueta: "Código del curso", maxlength: 20, req: true },
    { k: "inicio", etiqueta: "Inicio", tipo: "date", req: true, valor: hoy() }, { k: "fin", etiqueta: "Fin", tipo: "date", req: true, valor: hoy() },
    { k: "horas", etiqueta: "Horas previstas", tipo: "number", min: 0.5, max: 200, step: 0.5, req: true, valor: 8 },
  ];
  montar(cuerpo,
    h("div", { class: "fila entre" }, h("h1", {}, "Mi formación"),
      h("button", { type: "button", class: "primary", onclick: () => dialogo("Inscribirme en un curso", campos,
        async (v) => { await post("/portal/formacion", v); aviso("Inscripción registrada."); formacion(cuerpo); }, { enviar: "Inscribirme" }) }, "Inscribirme")),
    tabla([
      { t: "Curso", f: (t) => `${t.course_id} · ${t.course_name}` }, { t: "Categoría", f: (t) => t.category || "—" }, { t: "Inicio", f: (t) => fecha(t.start_date) }, { t: "Fin", f: (t) => fecha(t.end_date) },
      { t: "Horas", f: (t) => `${num(t.completed_hours ?? 0)} / ${num(t.planned_hours)}`, cls: "num" }, { t: "Estado", f: (t) => insignia(t.training_status) },
    ], filas, { sinDatos: "No estás inscrito en ningún curso." }));
}

async function encuesta(cuerpo, ctx) {
  const e = await get("/portal/encuesta");
  if (e.respondida) {
    return montar(cuerpo, h("h1", {}, e.oleada), h("p", { class: "msg ok" }, "Ya has respondido esta encuesta. ¡Gracias!"),
      h("p", { class: "ayuda" }, "La siguiente oleada se abre el próximo trimestre. Tus respuestas se tratan de forma agregada."));
  }
  const grupos = e.preguntas.map((p) => ({ p, radios: [1, 2, 3, 4, 5].map((n) => h("input", { type: "radio", name: p.codigo, value: n, id: `${p.codigo}-${n}`, required: true })) }));
  const comentario = h("textarea", { rows: 4, maxlength: 1500, id: "clima-comentario" });
  const msg = h("p", { class: "msg ko", role: "alert" });
  montar(cuerpo, h("h1", {}, e.oleada),
    h("p", { class: "ayuda" }, "Puntúa de 1 (muy en desacuerdo) a 5 (muy de acuerdo). Son 8 preguntas y se responde una vez por trimestre."),
    h("form", { class: "estrecho", onsubmit: conAviso(async (ev) => {
      ev.preventDefault();
      msg.textContent = "";
      const respuestas = {};
      for (const g of grupos) respuestas[g.p.codigo] = Number(g.radios.find((r) => r.checked).value);
      try { await post("/portal/encuesta", { respuestas, comentario: comentario.value.trim() || null }); }
      catch (err) { msg.textContent = err.message; return; }
      aviso("Gracias por responder la encuesta.");
      ctx.ir("/portal/encuesta");
    }) },
    grupos.map(({ p, radios }) => h("fieldset", { class: "pregunta" }, h("legend", {}, p.texto),
      h("div", { class: "escala" }, radios.map((r, i) => h("label", { for: r.id, class: "inline" }, r, ` ${i + 1}`))))),
    h("div", { class: "campo" }, h("label", { for: "clima-comentario" }, "Comentario libre (opcional)"), comentario), msg,
    h("button", { type: "submit", class: "primary" }, "Enviar respuestas")));
}
