"""Escenario 13 · portal del empleado: encuesta de clima, mis ausencias, mis horas extra y mis cursos."""
from __future__ import annotations

from datetime import date, datetime, timezone

from .. import cosmos, db
from ..auth import User
from ..util import a_date, field, number, one_of
from ..web import HttpError, Request, bad_request, forbidden, route

ROLES = {"empleado", "manager", "cajero", "tienda", "atencion", "marketing", "rrhh"}
QUESTIONS = [
    ("CLIMA_SAT", "Satisfacción", "Satisfacción general con la experiencia en FraSoHome"),
    ("CLIMA_ENG", "Engagement", "Compromiso y recomendación de FraSoHome como lugar para trabajar"),
    ("CLIMA_MAN", "Calidad manager", "Calidad del seguimiento y feedback del manager"),
    ("CLIMA_DEV", "Desarrollo carrera", "Claridad de oportunidades de desarrollo y carrera"),
    ("CLIMA_REC", "Reconocimiento", "Reconocimiento recibido por el trabajo realizado"),
    ("CLIMA_SAL", "Percepción salario", "Percepción de equidad y competitividad salarial"),
    ("CLIMA_BAL", "Balance vida trabajo", "Equilibrio entre vida personal y trabajo"),
    ("CLIMA_CAR", "Carga trabajo", "Carga de trabajo percibida"),
]
OVERTIME_REASONS = ["Inventario", "Pico e-commerce", "Cobertura de turnos", "Proyecto interno", "Campaña comercial"]


def _me(user: User) -> str:
    if not user.employee_id:
        raise forbidden("Tu usuario no está asociado a un empleado.")
    return user.employee_id


def current_wave(today: date | None = None) -> str:
    today = today or date.today()
    return f"Pulso {today.year} Q{(today.month - 1) // 3 + 1}"


@route("GET", "/portal/yo", ROLES)
def yo(req: Request):
    me = _me(req.user)
    e = db.one("""SELECT e.employee_id, e.full_name, e.department, e.location, e.role_name, e.level_name, e.contract_type,
                         e.work_schedule, e.hired_at, e.remote_days_week, m.full_name AS manager_name
                  FROM hr.employee e LEFT JOIN hr.employee m ON m.employee_id = e.manager_id WHERE e.employee_id = ?""", me)
    e["salario"] = db.one("""SELECT TOP 1 period_month, base_salary_eur, variable_salary_eur FROM hr.compensation
                             WHERE employee_id = ? ORDER BY period_month DESC""", me)
    e["dias_ausencia_anio"] = db.scalar("""SELECT ISNULL(SUM(working_days), 0) FROM hr.absence
                                           WHERE employee_id = ? AND YEAR(start_date) = YEAR(SYSUTCDATETIME())""", me)
    return e


@route("GET", "/portal/ausencias", ROLES)
def mis_ausencias(req: Request):
    return db.query("""SELECT absence_id, start_date, end_date, absence_type, working_days, justified, notes
                       FROM hr.absence WHERE employee_id = ? ORDER BY start_date DESC""", _me(req.user))


@route("GET", "/portal/horas-extra", ROLES)
def mis_horas(req: Request):
    return db.query("""SELECT overtime_id, period_month, hours, reason, approval_status, approver_id, requested_at, decided_at
                       FROM hr.overtime WHERE employee_id = ? ORDER BY period_month DESC, overtime_id DESC""", _me(req.user))


@route("POST", "/portal/horas-extra", ROLES)
def pedir_horas(req: Request):
    d = req.json()
    return db.call_one("hr.usp_overtime_request", employee_id=_me(req.user), period_month=field(d, "periodo", max_len=7),
                       hours=number(d.get("horas"), "horas", lo=0.5, hi=80),
                       reason=one_of(d.get("motivo"), OVERTIME_REASONS, "motivo"), user_login=req.user.login)


@route("GET", "/portal/formacion", ROLES)
def mis_cursos(req: Request):
    return db.query("""SELECT training_id, course_id, course_name, category, start_date, end_date, planned_hours, completed_hours,
                              training_status, provider FROM hr.training WHERE employee_id = ? ORDER BY start_date DESC""",
                    _me(req.user))


@route("POST", "/portal/formacion", ROLES)
def inscribirme(req: Request):
    d = req.json()
    return db.call_one("hr.usp_training_enroll", employee_id=_me(req.user), course_id=field(d, "curso", max_len=20).upper(),
                       start_date=a_date(d.get("inicio"), "inicio"), end_date=a_date(d.get("fin"), "fin"),
                       planned_hours=number(d.get("horas"), "horas", lo=0.5, hi=200), user_login=req.user.login)


@route("GET", "/portal/encuesta", ROLES)
def encuesta(req: Request):
    me = _me(req.user)
    wave = current_wave()
    answered = cosmos.query("encuesta_clima", "SELECT VALUE COUNT(1) FROM c WHERE c.oleada = @w", {"w": wave}, pk=me)
    return {"oleada": wave, "respondida": bool(answered and answered[0]), "escala": [1, 5],
            "preguntas": [{"codigo": c, "dimension": d, "texto": t} for c, d, t in QUESTIONS]}


@route("POST", "/portal/encuesta", ROLES)
def responder(req: Request):
    """Una respuesta por pregunta (como en los datos de origen), con la oleada del trimestre en curso."""
    me = _me(req.user)
    wave = current_wave()
    already = cosmos.query("encuesta_clima", "SELECT VALUE COUNT(1) FROM c WHERE c.oleada = @w", {"w": wave}, pk=me)
    if already and already[0]:
        raise HttpError(422, f"Ya has respondido la encuesta «{wave}».", "duplicado")
    d = req.json()
    answers = d.get("respuestas")
    if not isinstance(answers, dict) or set(answers) != {c for c, _, _ in QUESTIONS}:
        raise bad_request("«respuestas» debe tener una puntuación de 1 a 5 para cada pregunta.")
    comment = field(d, "comentario", required=False, max_len=1500)
    ids = cosmos.next_ids("survey", len(QUESTIONS))
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for (code, dimension, text), doc_id in zip(QUESTIONS, ids):
        cosmos.enqueue("encuesta_clima", {
            "id": doc_id, "pk": me, "respuesta_id": doc_id, "employee_id": me, "fecha_encuesta": today, "oleada": wave,
            "dimension": dimension, "question_code": code, "pregunta_texto": text,
            "score": number(answers[code], f"respuestas.{code}", lo=1, hi=5),
            "comentario_abierto": comment if code == "CLIMA_SAT" else None,
            "canal_respuesta": "Web", "fuente": "Encuesta clima", "origen": "web"})
    return {"oleada": wave, "respuestas": len(ids)}
