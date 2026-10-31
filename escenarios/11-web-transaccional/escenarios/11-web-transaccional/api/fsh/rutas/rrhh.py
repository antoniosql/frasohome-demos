"""Escenarios 11 y 12 · ciclo de vida del empleado (alta, movimientos, salario, baja con
entrevista) y tiempo y desempeño (ausencias, horas extra, formación, evaluación).

RR. HH. ve a toda la plantilla; un manager solo a sus colaboradores directos y sin salarios."""
from __future__ import annotations

from .. import db
from ..auth import User
from ..util import a_date, an_id, field, like, number, one_of, page
from ..web import Request, forbidden, not_found, route

HR = {"rrhh"}
HR_OR_MANAGER = {"rrhh", "manager"}
EMPLOYEE_FIELDS = """e.employee_id, e.full_name, e.gender, e.birth_date, e.hired_at, e.left_at, e.employee_status, e.exit_type,
                     e.exit_reason, e.department, e.location, e.role_name, e.level_name, e.contract_type, e.work_schedule,
                     e.manager_id, m.full_name AS manager_name, e.remote_days_week, e.commute_km"""


def is_hr(user: User) -> bool:
    return user.has("rrhh")


def check_team(user: User, employee_id: str) -> None:
    """RR. HH. puede con todos; un manager solo con sus colaboradores directos."""
    if is_hr(user):
        return
    if not user.employee_id or not db.scalar("SELECT 1 FROM hr.employee WHERE employee_id = ? AND manager_id = ?",
                                             employee_id, user.employee_id):
        raise forbidden("Ese empleado no es de tu equipo.")


def ficha(employee_id: str, user: User, *, full: bool = False) -> dict:
    """Ficha del empleado. full=True (paneles de dirección) omite la comprobación de equipo e incluye salarios."""
    if not full:
        check_team(user, employee_id)
    e = db.one(f"SELECT {EMPLOYEE_FIELDS} FROM hr.employee e LEFT JOIN hr.employee m ON m.employee_id = e.manager_id "
               "WHERE e.employee_id = ?", employee_id)
    if e is None:
        raise not_found("El empleado no existe.")
    e["movimientos"] = db.query("""SELECT movement_id, moved_at, movement_type, department_from, department_to, level_from,
                                          level_to, reason FROM hr.employee_movement WHERE employee_id = ?
                                   ORDER BY moved_at DESC, movement_id DESC""", employee_id)
    e["ausencias"] = db.query("""SELECT TOP 20 absence_id, start_date, end_date, absence_type, working_days, justified
                                 FROM hr.absence WHERE employee_id = ? ORDER BY start_date DESC""", employee_id)
    e["horas_extra"] = db.query("""SELECT TOP 24 overtime_id, period_month, hours, reason, approval_status, approver_id
                                   FROM hr.overtime WHERE employee_id = ? ORDER BY period_month DESC""", employee_id)
    e["formacion"] = db.query("""SELECT training_id, course_id, course_name, category, start_date, end_date, planned_hours,
                                        completed_hours, training_status FROM hr.training WHERE employee_id = ?
                                 ORDER BY start_date DESC""", employee_id)
    e["evaluaciones"] = db.query("""SELECT review_id, review_cycle, reviewed_at, overall_score, objectives_pct, competencies_score,
                                           potential, reviewer_id, manager_comment FROM hr.performance_review
                                    WHERE employee_id = ? ORDER BY review_cycle DESC""", employee_id)
    if full or is_hr(user):
        e["compensacion"] = db.query("""SELECT payroll_id, period_month, base_salary_eur, variable_salary_eur, increase_pct
                                        FROM hr.compensation WHERE employee_id = ? ORDER BY period_month DESC""", employee_id)
    return e


@route("GET", "/rrhh/empleados", HR_OR_MANAGER)
def listado(req: Request):
    offset, size = page(req, 50, 200)
    q = like(req.query.get("q"))
    dep = req.query.get("departamento") or None
    status = req.query.get("estado") or None
    team = None if is_hr(req.user) else req.user.employee_id
    if team is None and not is_hr(req.user):
        raise forbidden("Tu usuario no está asociado a un empleado.")
    where = ("(? IS NULL OR e.full_name LIKE ? OR e.employee_id = ?) AND (? IS NULL OR e.department = ?) "
             "AND (? IS NULL OR e.employee_status = ?) AND (? IS NULL OR e.manager_id = ?)")
    args = (q, q, (req.query.get("q") or "").strip().upper(), dep, dep, status, status, team, team)
    return {"total": db.scalar(f"SELECT COUNT(*) FROM hr.employee e WHERE {where}", *args),
            "empleados": db.query(f"""SELECT e.employee_id, e.full_name, e.department, e.location, e.role_name, e.level_name,
                                            e.employee_status, e.hired_at, e.manager_id
                                     FROM hr.employee e WHERE {where} ORDER BY e.employee_id
                                     OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""", *args, offset, size)}


@route("GET", "/rrhh/empleados/{employee_id}", HR_OR_MANAGER)
def ver(req: Request):
    return ficha(an_id(req.params["employee_id"], "employee"), req.user)


@route("GET", "/rrhh/departamentos", HR_OR_MANAGER)
def departamentos(req: Request):
    return db.query("""SELECT department_std AS departamento, MAX(hr_area) AS area, MAX(business_channel) AS canal,
                              CAST(MAX(CAST(critical_turnover_default AS INT)) AS BIT) AS area_critica
                       FROM ref.department_map WHERE department_std <> N'Sin clasificar'
                       GROUP BY department_std ORDER BY department_std""")


@route("POST", "/rrhh/empleados", HR)
def alta(req: Request):
    d = req.json()
    row = db.call_one(
        "hr.usp_employee_hire", full_name=field(d, "nombre", max_len=200),
        gender=field(d, "genero", required=False, max_len=20),
        birth_date=a_date(d.get("fecha_nacimiento"), "fecha_nacimiento", required=False),
        hired_at=a_date(d.get("fecha_alta"), "fecha_alta", required=False),
        department=field(d, "departamento", max_len=100), location=field(d, "ubicacion", max_len=100),
        role_name=field(d, "rol", max_len=100), level_name=field(d, "nivel", required=False, max_len=50) or "Junior",
        contract_type=field(d, "contrato", required=False, max_len=50) or "Indefinido",
        work_schedule=field(d, "jornada", required=False, max_len=20) or "Completa",
        manager_id=an_id(d.get("manager_id"), "employee", required=False),
        remote_days_week=number(d.get("teletrabajo", 0), "teletrabajo", lo=0, hi=5, integer=True),
        commute_km=number(d.get("distancia_km"), "distancia_km", lo=0, hi=500, required=False),
        store_id=an_id(d.get("tienda"), "store", required=False), user_login=req.user.login)
    return ficha(row["employee_id"], req.user)


@route("POST", "/rrhh/empleados/{employee_id}/movimientos", HR)
def movimiento(req: Request):
    eid = an_id(req.params["employee_id"], "employee")
    d = req.json()
    db.call("hr.usp_employee_move", employee_id=eid,
            movement_type=one_of(d.get("tipo"), ["Promoción", "Movilidad interna"], "tipo"),
            department_to=field(d, "departamento", required=False, max_len=100),
            level_to=field(d, "nivel", required=False, max_len=50), role_to=field(d, "rol", required=False, max_len=100),
            location_to=field(d, "ubicacion", required=False, max_len=100),
            manager_to=an_id(d.get("manager_id"), "employee", required=False), reason=field(d, "motivo", max_len=200),
            effective_date=a_date(d.get("fecha"), "fecha", required=False), user_login=req.user.login)
    return ficha(eid, req.user)


@route("POST", "/rrhh/empleados/{employee_id}/salario", HR)
def salario(req: Request):
    eid = an_id(req.params["employee_id"], "employee")
    d = req.json()
    row = db.call_one("hr.usp_salary_review", employee_id=eid,
                      base_salary_eur=number(d.get("salario_base"), "salario_base", lo=0, hi=1_000_000),
                      variable_salary_eur=number(d.get("variable", 0), "variable", lo=0, hi=1_000_000),
                      period_month=field(d, "periodo", required=False, max_len=7),
                      reason=field(d, "motivo", required=False, max_len=200) or "Revisión salarial", user_login=req.user.login)
    return {"revision": row, "empleado": ficha(eid, req.user)}


@route("POST", "/rrhh/empleados/{employee_id}/baja", HR)
def baja(req: Request):
    eid = an_id(req.params["employee_id"], "employee")
    d = req.json()
    interview = d.get("entrevista") or {}
    db.call("hr.usp_employee_terminate", employee_id=eid, left_at=a_date(d.get("fecha"), "fecha", required=False),
            exit_type=one_of(d.get("tipo"), ["Voluntaria", "Involuntaria/fin contrato"], "tipo"),
            exit_reason=field(d, "motivo", max_len=200),
            interview_comment=field(interview, "comentario", required=False, max_len=2000),
            recommend_1_10=number(interview.get("recomendaria"), "entrevista.recomendaria", lo=0, hi=10, integer=True, required=False),
            interview_channel=field(interview, "canal", required=False, max_len=50),
            interviewer=field(interview, "entrevistador", required=False, max_len=100), user_login=req.user.login)
    return ficha(eid, req.user)


# ------------------------------------------------------------------ tiempo y desempeño

def _team_filter(user: User) -> str | None:
    if is_hr(user):
        return None
    if not user.employee_id:
        raise forbidden("Tu usuario no está asociado a un empleado.")
    return user.employee_id


@route("GET", "/equipo", {"manager"})
def equipo(req: Request):
    me = _team_filter(req.user) or req.user.employee_id
    return db.query("""SELECT e.employee_id, e.full_name, e.role_name, e.level_name, e.location, e.hired_at,
                              (SELECT COUNT(*) FROM hr.overtime o WHERE o.employee_id = e.employee_id AND o.approval_status = N'Pendiente') AS horas_extra_pendientes,
                              (SELECT TOP 1 overall_score FROM hr.performance_review r WHERE r.employee_id = e.employee_id ORDER BY review_cycle DESC) AS ultima_evaluacion
                       FROM hr.employee e WHERE e.manager_id = ? AND e.employee_status = N'Activo' ORDER BY e.full_name""", me)


@route("GET", "/rrhh/ausencias", HR_OR_MANAGER)
def ausencias(req: Request):
    team = _team_filter(req.user)
    emp = an_id(req.query.get("empleado"), "employee", required=False)
    since = a_date(req.query.get("desde"), "desde", required=False)
    offset, size = page(req, 50, 500)
    return db.query("""SELECT a.absence_id, a.employee_id, e.full_name, a.start_date, a.end_date, a.absence_type, a.working_days,
                              a.justified, a.notes
                       FROM hr.absence a JOIN hr.employee e ON e.employee_id = a.employee_id
                       WHERE (? IS NULL OR a.employee_id = ?) AND (? IS NULL OR a.end_date >= ?) AND (? IS NULL OR e.manager_id = ?)
                       ORDER BY a.start_date DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
                    emp, emp, since, since, team, team, offset, size)


@route("POST", "/rrhh/ausencias", HR)
def registrar_ausencia(req: Request):
    d = req.json()
    return db.call_one("hr.usp_absence_register", employee_id=an_id(d.get("employee_id"), "employee"),
                       start_date=a_date(d.get("inicio"), "inicio"), end_date=a_date(d.get("fin"), "fin"),
                       absence_type=field(d, "tipo", max_len=50),
                       justified=one_of(d.get("justificada", "Pendiente"), ["Sí", "No", "Pendiente"], "justificada"),
                       notes=field(d, "notas", required=False, max_len=300), user_login=req.user.login)


@route("GET", "/rrhh/horas-extra", HR_OR_MANAGER)
def horas_extra(req: Request):
    team = _team_filter(req.user)
    status = req.query.get("estado") or None
    month = req.query.get("periodo") or None
    offset, size = page(req, 50, 500)
    return db.query("""SELECT o.overtime_id, o.employee_id, e.full_name, o.period_month, o.department_reported, o.hours, o.reason,
                              o.approval_status, o.approver_id, o.requested_at, o.decided_at
                       FROM hr.overtime o JOIN hr.employee e ON e.employee_id = o.employee_id
                       WHERE (? IS NULL OR o.approval_status = ?) AND (? IS NULL OR o.period_month = ?) AND (? IS NULL OR e.manager_id = ?)
                       ORDER BY o.period_month DESC, o.overtime_id DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
                    status, status, month, month, team, team, offset, size)


@route("POST", "/rrhh/horas-extra/{overtime_id}/decision", HR_OR_MANAGER)
def decidir(req: Request):
    oid = req.params["overtime_id"].upper()
    approve = req.json().get("aprobar")
    if not isinstance(approve, bool):
        from ..web import bad_request
        raise bad_request("«aprobar» debe ser true o false.")
    # RR. HH. decide sin restricción; un manager solo sobre sus colaboradores (lo comprueba el procedimiento).
    db.call("hr.usp_overtime_decide", overtime_id=oid, approve=approve,
            manager_id=None if is_hr(req.user) else req.user.employee_id, user_login=req.user.login)
    return db.one("SELECT overtime_id, employee_id, approval_status, approver_id, decided_at FROM hr.overtime WHERE overtime_id = ?", oid)


@route("GET", "/rrhh/cursos", HR_OR_MANAGER | {"empleado"})
def cursos(req: Request):
    return db.query("""SELECT course_id, MAX(course_name) AS course_name, MAX(category) AS category, MAX(provider) AS provider,
                              CAST(AVG(planned_hours) AS DECIMAL(6,1)) AS horas_tipicas, COUNT(*) AS ediciones
                       FROM hr.training GROUP BY course_id ORDER BY course_id""")


@route("POST", "/rrhh/formacion", HR_OR_MANAGER)
def inscribir(req: Request):
    d = req.json()
    eid = an_id(d.get("employee_id"), "employee")
    check_team(req.user, eid)
    return db.call_one("hr.usp_training_enroll", employee_id=eid, course_id=field(d, "curso", max_len=20).upper(),
                       start_date=a_date(d.get("inicio"), "inicio"), end_date=a_date(d.get("fin"), "fin"),
                       planned_hours=number(d.get("horas"), "horas", lo=0.5, hi=200), user_login=req.user.login)


@route("POST", "/rrhh/formacion/{training_id}/cierre", HR)
def cerrar_formacion(req: Request):
    tid = req.params["training_id"].upper()
    d = req.json()
    db.call("hr.usp_training_complete", training_id=tid, completed_hours=number(d.get("horas"), "horas", lo=0, hi=300),
            completed=bool(d.get("completado", True)), user_login=req.user.login)
    return db.one("SELECT training_id, employee_id, course_name, completed_hours, training_status FROM hr.training WHERE training_id = ?", tid)


@route("GET", "/rrhh/evaluaciones", HR_OR_MANAGER)
def evaluaciones(req: Request):
    team = _team_filter(req.user)
    cycle = req.query.get("ciclo") or None
    offset, size = page(req, 50, 500)
    return db.query("""SELECT r.review_id, r.employee_id, e.full_name, r.review_cycle, r.reviewed_at, r.overall_score,
                              r.objectives_pct, r.competencies_score, r.potential, r.reviewer_id
                       FROM hr.performance_review r JOIN hr.employee e ON e.employee_id = r.employee_id
                       WHERE (? IS NULL OR r.review_cycle = ?) AND (? IS NULL OR e.manager_id = ?)
                       ORDER BY r.review_cycle DESC, r.employee_id OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
                    cycle, cycle, team, team, offset, size)


@route("POST", "/rrhh/evaluaciones", HR_OR_MANAGER)
def evaluar(req: Request):
    d = req.json()
    eid = an_id(d.get("employee_id"), "employee")
    check_team(req.user, eid)
    return db.call_one("hr.usp_review_upsert", employee_id=eid, review_cycle=field(d, "ciclo", max_len=4),
                       overall_score=number(d.get("puntuacion"), "puntuacion", lo=1, hi=5),
                       objectives_pct=number(d.get("objetivos_pct"), "objetivos_pct", lo=0, hi=200, required=False),
                       competencies_score=number(d.get("competencias"), "competencias", lo=1, hi=5, required=False),
                       potential=field(d, "potencial", required=False, max_len=20),
                       reviewer_id=req.user.employee_id, manager_comment=field(d, "comentario", required=False, max_len=500),
                       user_login=req.user.login)
