"""Escenarios 11 a 14: ciclo de vida del empleado, tiempo y desempeño, portal del empleado y paneles."""
from datetime import date, timedelta

from fsh import cosmos, db
from fsh.rutas.portal import QUESTIONS, current_wave


def test_ciclo_de_vida_del_empleado(as_role, people):
    hr = as_role("rrhh")
    r = hr.post("/rrhh/empleados", {"nombre": "Prueba Alta Gómez", "genero": "F", "fecha_nacimiento": "1995-04-12",
                                    "departamento": "Tienda física", "ubicacion": "A Coruña", "rol": "Vendedor/a",
                                    "nivel": "Junior", "contrato": "Temporal", "jornada": "Parcial",
                                    "manager_id": people["manager"], "tienda": "S001"})
    assert r.status == 200, r.json
    eid = r.json["employee_id"]
    assert eid.startswith("FSH") and r.json["employee_status"] == "Activo"
    assert db.scalar("SELECT COUNT(*) FROM hr.employee_movement WHERE employee_id = ? AND movement_type = N'Alta'", eid) == 1
    moved = hr.post(f"/rrhh/empleados/{eid}/movimientos", {"tipo": "Promoción", "nivel": "Semi Senior", "motivo": "Buen desempeño"})
    assert moved.status == 200 and moved.json["level_name"] == "Semi Senior"
    sal = hr.post(f"/rrhh/empleados/{eid}/salario", {"salario_base": 24000, "variable": 1200})
    assert sal.status == 200, sal.json
    assert db.scalar("SELECT COUNT(*) FROM hr.compensation WHERE employee_id = ?", eid) >= 1
    out = hr.post(f"/rrhh/empleados/{eid}/baja", {"tipo": "Voluntaria", "motivo": "Mejor oferta externa",
                                                  "entrevista": {"comentario": "Me voy por una oferta mejor", "recomendaria": 7,
                                                                 "canal": "Teams", "entrevistador": "HRBP Retail"}})
    assert out.status == 200 and out.json["employee_status"] == "Baja" and out.json["exit_type"] == "Voluntaria"
    interviews = cosmos.query("entrevistas_salida", "SELECT * FROM c", pk=eid)
    assert interviews and interviews[0]["recomendaria_empresa_1_10"] == 7
    again = hr.post(f"/rrhh/empleados/{eid}/baja", {"tipo": "Voluntaria", "motivo": "otra vez"})
    assert again.status == 422
    assert hr.get(f"/rrhh/empleados?q={eid}").json
    assert hr.get("/rrhh/departamentos").json
    # Sin rol de RR. HH. no hay ficha de empleados.
    assert as_role("marketing").get("/rrhh/empleados").status == 403


def test_tiempo_y_desempeno_con_ambito_de_manager(as_role, people):
    hr, mgr = as_role("rrhh"), as_role("manager")
    # Después de la última ausencia registrada: la prueba se puede repetir sin solaparse.
    last = db.scalar("SELECT MAX(end_date) FROM hr.absence WHERE employee_id = ?", people["report"])
    start = max(date.today(), last or date.today()) + timedelta(days=10)
    abs_ = hr.post("/rrhh/ausencias", {"employee_id": people["report"], "inicio": start.isoformat(),
                                       "fin": (start + timedelta(days=2)).isoformat(), "tipo": "Permiso retribuido",
                                       "justificada": "Sí"})
    assert abs_.status == 200, abs_.json
    team = mgr.get("/equipo").json
    assert any(e["employee_id"] == people["report"] for e in team)
    seen = {a["employee_id"] for a in mgr.get("/rrhh/ausencias?tamano=500").json}
    assert people["report"] in seen
    assert all(db.scalar("SELECT manager_id FROM hr.employee WHERE employee_id = ?", e) == people["manager"] for e in seen)
    # El empleado pide horas extra desde su portal; su manager decide.
    emp = as_role("empleado")
    req = emp.post("/portal/horas-extra", {"periodo": date.today().strftime("%Y-%m"), "horas": 6, "motivo": "Inventario"})
    assert req.status == 200, req.json
    oid = req.json["overtime_id"]
    assert any(o["overtime_id"] == oid for o in mgr.get("/rrhh/horas-extra?estado=Pendiente").json)
    dec = mgr.post(f"/rrhh/horas-extra/{oid}/decision", {"aprobar": True})
    assert dec.status == 200 and dec.json["approval_status"] == "Aprobada" and dec.json["approver_id"] == people["manager"]
    assert mgr.post(f"/rrhh/horas-extra/{oid}/decision", {"aprobar": False}).status == 422     # ya decidida
    # Un manager no decide sobre quien no es de su equipo.
    foreign = db.call_one("hr.usp_overtime_request", employee_id=people["outsider"], period_month=date.today().strftime("%Y-%m"),
                          hours=2, reason="Inventario", user_login="pytest")
    assert mgr.post(f"/rrhh/horas-extra/{foreign['overtime_id']}/decision", {"aprobar": True}).status in (403, 422)
    assert hr.post(f"/rrhh/horas-extra/{foreign['overtime_id']}/decision", {"aprobar": False}).status == 200
    # Formación y evaluación.
    course = mgr.get("/rrhh/cursos").json[0]["course_id"]
    enr = mgr.post("/rrhh/formacion", {"employee_id": people["report"], "curso": course, "inicio": start.isoformat(),
                                       "fin": (start + timedelta(days=1)).isoformat(), "horas": 4})
    assert enr.status == 200, enr.json
    tid = enr.json["training_id"]
    assert mgr.post("/rrhh/formacion", {"employee_id": people["outsider"], "curso": course, "inicio": start.isoformat(),
                                        "fin": start.isoformat(), "horas": 2}).status == 403
    closed = hr.post(f"/rrhh/formacion/{tid}/cierre", {"horas": 4, "completado": True})
    assert closed.status == 200 and closed.json["training_status"] == "Completado"
    review = mgr.post("/rrhh/evaluaciones", {"employee_id": people["report"], "ciclo": str(date.today().year),
                                             "puntuacion": 4.2, "objetivos_pct": 105, "competencias": 4, "potencial": "Alto",
                                             "comentario": "Muy buen año"})
    assert review.status == 200, review.json
    assert any(r["employee_id"] == people["report"] for r in mgr.get(f"/rrhh/evaluaciones?ciclo={date.today().year}").json)


def test_portal_del_empleado(as_role, people):
    emp = as_role("empleado")
    me = emp.get("/portal/yo").json
    assert me["employee_id"] == people["report"] and "salario" in me
    assert isinstance(emp.get("/portal/ausencias").json, list)
    assert isinstance(emp.get("/portal/formacion").json, list)
    survey = emp.get("/portal/encuesta").json
    assert survey["oleada"] == current_wave() and len(survey["preguntas"]) == len(QUESTIONS)
    if not survey["respondida"]:
        answers = {code: 4 for code, _, _ in QUESTIONS}
        r = emp.post("/portal/encuesta", {"respuestas": answers, "comentario": "Buen ambiente en el equipo"})
        assert r.status == 200 and r.json["respuestas"] == len(QUESTIONS)
        docs = cosmos.query("encuesta_clima", "SELECT * FROM c WHERE c.oleada = @w", {"w": current_wave()}, pk=people["report"])
        assert len(docs) == len(QUESTIONS)
    again = emp.post("/portal/encuesta", {"respuestas": {code: 3 for code, _, _ in QUESTIONS}})
    assert again.status == 422
    incomplete = emp.post("/portal/encuesta", {"respuestas": {"CLIMA_SAT": 4}})
    assert incomplete.status in (400, 422)
    # Un cliente no tiene portal del empleado.
    assert as_role("cliente").get("/portal/yo").status == 403


def test_paneles_de_direccion(as_role, people):
    d = as_role("direccion")
    sales = d.get("/paneles/ventas?desde=2025-01-01&hasta=2025-12-31")
    assert sales.status == 200, sales.json
    c360 = d.get(f"/paneles/cliente/{people['customer']}")
    assert c360.status == 200 and c360.json
    e360 = d.get(f"/paneles/empleado/{people['report']}")
    assert e360.status == 200 and e360.json
    rot = d.get("/paneles/rotacion")
    assert rot.status == 200 and rot.json
    for kind in ("clima", "salida"):
        com = d.get(f"/paneles/comentarios?tipo={kind}")
        assert com.status == 200 and com.json, kind
    assert d.post("/clientes", {"nombre": "x"}).status == 403            # solo lectura
    assert as_role("rrhh").get("/paneles/ventas").status == 403
