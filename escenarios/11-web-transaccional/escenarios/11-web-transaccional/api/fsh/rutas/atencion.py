"""Escenario 9 · atención al cliente: bandeja por prioridad y SLA, conversación,
resolución con compensación (cupón o reembolso) y CSAT."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .. import cosmos, db, texto
from ..auth import User
from ..util import an_id, field, number, one_of
from ..web import HttpError, Request, forbidden, not_found, route

CHANNELS = ["Chat", "WhatsApp", "Email", "Tienda", "Teléfono", "Web"]
CASE_TYPES = ["devolucion", "info_producto", "entrega", "defecto", "stock_tienda", "cupon", "fidelizacion"]
PRIORITIES = ["Alta", "Media", "Baja"]
SLA_TARGET_HOURS = {"Alta": 4, "Media": 24, "Baja": 72}
PRIORITY_ORDER = {"Alta": 0, "Media": 1, "Baja": 2}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _with_sla(case: dict) -> dict:
    opened = case.get("fecha_apertura")
    target = case.get("sla_objetivo_horas") or SLA_TARGET_HOURS.get(case.get("prioridad"), 24)
    if opened:
        due = datetime.fromisoformat(opened) + timedelta(hours=target)
        case["vence"] = due.strftime("%Y-%m-%dT%H:%M:%S")
        case["vencido"] = case.get("estado_resolucion") != "Resuelto" and datetime.now(timezone.utc).replace(tzinfo=None) > due
    return case


def _case(case_id: str, user: User) -> dict:
    case = cosmos.find_by_id("atencion_cliente", case_id.upper())
    if case is None:
        raise not_found("El caso no existe.")
    if not user.has("atencion") and case.get("customer_id") != user.customer_id:
        raise not_found("El caso no existe.")
    return _with_sla(case)


def _new_case(customer_id: str, data: dict, priority: str, agent: str | None) -> dict:
    text = field(data, "texto", max_len=2000)
    case_id = cosmos.next_ids("service")[0]
    now = _now()
    doc = {"id": case_id, "pk": customer_id, "service_ticket_id": case_id, "fecha_apertura": now, "fecha_cierre": None,
           "customer_id": customer_id, "order_id": an_id(data.get("order_id"), "order", required=False),
           "ticket_id": an_id(data.get("ticket_id"), "ticket", required=False),
           "store_id": an_id(data.get("store_id"), "store", required=False),
           "canal_soporte": one_of(data.get("canal", "Web"), CHANNELS, "canal"),
           "tipo_caso": one_of(data.get("tipo_caso"), CASE_TYPES, "tipo_caso"),
           "subtipo_caso": field(data, "subtipo_caso", required=False, max_len=60) or "Consulta",
           "motivo_contacto": field(data, "motivo", required=False, max_len=100) or data.get("tipo_caso"),
           "prioridad": priority, "sentimiento_inicial": texto.sentiment(text), "estado_resolucion": "Pendiente",
           "sla_horas": None, "sla_objetivo_horas": SLA_TARGET_HOURS[priority], "csat_1_5": None, "agente_id": agent,
           "importe_compensacion_eur": 0.0, "cupon_compensacion": None,
           "conversacion": [{"autor": "cliente", "fecha": now, "texto": text}], "origen": "web"}
    cosmos.enqueue("atencion_cliente", doc)
    return _with_sla(doc)


@route("GET", "/atencion/casos", {"atencion"})
def bandeja(req: Request):
    status = req.query.get("estado") or None
    priority = req.query.get("prioridad") or None
    conds, params = [], {}
    if status:
        conds.append("c.estado_resolucion = @s")
        params["s"] = status
    else:
        conds.append("c.estado_resolucion <> 'Resuelto'")
    if priority:
        conds.append("c.prioridad = @p")
        params["p"] = priority
    customer = an_id(req.query.get("cliente"), "customer", required=False)
    sql = ("SELECT c.id, c.service_ticket_id, c.fecha_apertura, c.customer_id, c.canal_soporte, c.tipo_caso, c.prioridad, "
           "c.estado_resolucion, c.sentimiento_inicial, c.sla_objetivo_horas, c.agente_id, c.order_id FROM c WHERE "
           + " AND ".join(conds) + " ORDER BY c.fecha_apertura DESC")
    rows = cosmos.query("atencion_cliente", sql, params, pk=customer, max_items=req.int_arg("tamano", 200, 1, 1000))
    rows = [_with_sla(r) for r in rows]
    rows.sort(key=lambda r: (not r.get("vencido", False), PRIORITY_ORDER.get(r.get("prioridad"), 9), r.get("fecha_apertura") or ""))
    return rows


@route("GET", "/atencion/casos/{case_id}", {"atencion"})
def ver(req: Request):
    case = _case(req.params["case_id"], req.user)
    case["cliente"] = db.one("""SELECT customer_id, first_name, last_name, email, phone, loyalty_tier, customer_status
                                FROM crm.customer WHERE customer_id = ?""", case["customer_id"])
    return case


@route("POST", "/atencion/casos", {"atencion"})
def abrir(req: Request):
    data = req.json()
    customer = an_id(data.get("customer_id"), "customer")
    if not db.scalar("SELECT 1 FROM crm.customer WHERE customer_id = ?", customer):
        raise HttpError(422, "El cliente no existe.", "referencia")
    return _new_case(customer, data, one_of(data.get("prioridad", "Media"), PRIORITIES, "prioridad"), req.user.login)


@route("POST", "/atencion/casos/{case_id}/mensajes", {"atencion"})
def mensaje(req: Request):
    case = _case(req.params["case_id"], req.user)
    if case["estado_resolucion"] == "Resuelto":
        raise HttpError(422, "El caso está cerrado.", "estado")
    case["conversacion"].append({"autor": "agente", "agente_id": req.user.login, "fecha": _now(),
                                 "texto": field(req.json(), "texto", max_len=2000)})
    case["agente_id"] = case.get("agente_id") or req.user.login
    cosmos.enqueue("atencion_cliente", {k: v for k, v in case.items() if k not in ("vence", "vencido")})
    return _with_sla(case)


@route("POST", "/atencion/casos/{case_id}/resolver", {"atencion"})
def resolver(req: Request):
    """Cierra (Resuelto) o escala el caso. Compensación: cupón de importe fijo (SQL) o reembolso anotado."""
    case = _case(req.params["case_id"], req.user)
    if case["estado_resolucion"] == "Resuelto":
        raise HttpError(422, "El caso ya está resuelto.", "estado")
    data = req.json()
    status = one_of(data.get("estado", "Resuelto"), ["Resuelto", "Escalado"], "estado")
    comp = data.get("compensacion") or {}
    kind = one_of(comp.get("tipo", "ninguna"), ["ninguna", "cupon", "reembolso"], "compensacion.tipo")
    amount = 0.0
    if kind != "ninguna":
        amount = number(comp.get("valor"), "compensacion.valor", lo=1, hi=100)
    if kind == "cupon":
        coupon = db.call_one("mkt.usp_coupon_issue_single", customer_id=case["customer_id"], coupon_type="importe_fijo",
                             value=amount, valid_days=30, issue_channel="ATENCION", user_login=req.user.login)
        case["cupon_compensacion"] = coupon["coupon_code"]
    now = _now()
    case["conversacion"].append({"autor": "agente", "agente_id": req.user.login, "fecha": now,
                                 "texto": field(data, "resolucion", max_len=2000)})
    case["estado_resolucion"] = status
    case["agente_id"] = req.user.login
    case["importe_compensacion_eur"] = float(case.get("importe_compensacion_eur") or 0) + amount
    case["tipo_compensacion"] = kind
    if status == "Resuelto":
        case["fecha_cierre"] = now
        opened = datetime.fromisoformat(case["fecha_apertura"])
        case["sla_horas"] = round((datetime.fromisoformat(now) - opened).total_seconds() / 3600, 1)
    cosmos.enqueue("atencion_cliente", {k: v for k, v in case.items() if k not in ("vence", "vencido")})
    db.call("app.usp_audit", user_login=req.user.login, action_name="case_resolve", entity_name="atencion_cliente",
            entity_id=case["id"], detail=f"{status} · {kind} {amount}")
    return _with_sla(case)


# ------------------------------------------------------------------ el propio cliente

def _customer(user: User) -> str:
    if not user.customer_id:
        raise forbidden("Tu usuario no está asociado a un cliente.")
    return user.customer_id


@route("GET", "/mis-casos", {"cliente"})
def mis_casos(req: Request):
    cid = _customer(req.user)
    rows = cosmos.query("atencion_cliente", "SELECT * FROM c ORDER BY c.fecha_apertura DESC", pk=cid, max_items=100)
    return [_with_sla(r) for r in rows]


@route("POST", "/mis-casos", {"cliente"})
def abrir_mio(req: Request):
    data = req.json()
    cid = _customer(req.user)
    if data.get("order_id"):
        oid = an_id(data["order_id"], "order")
        if db.scalar("SELECT customer_id FROM sales.online_order WHERE order_id = ?", oid) != cid:
            raise HttpError(422, "Ese pedido no es tuyo.", "referencia")
    data["canal"] = "Web"
    return _new_case(cid, data, "Media", None)


@route("POST", "/mis-casos/{case_id}/mensajes", {"cliente"})
def mensaje_mio(req: Request):
    case = _case(req.params["case_id"], req.user)
    if case["estado_resolucion"] == "Resuelto":
        raise HttpError(422, "El caso está cerrado. Abre uno nuevo si lo necesitas.", "estado")
    case["conversacion"].append({"autor": "cliente", "fecha": _now(), "texto": field(req.json(), "texto", max_len=2000)})
    cosmos.enqueue("atencion_cliente", {k: v for k, v in case.items() if k not in ("vence", "vencido")})
    return _with_sla(case)


@route("POST", "/mis-casos/{case_id}/csat", {"cliente"})
def csat(req: Request):
    case = _case(req.params["case_id"], req.user)
    if case["estado_resolucion"] != "Resuelto":
        raise HttpError(422, "Puedes valorar el caso cuando esté resuelto.", "estado")
    case["csat_1_5"] = number(req.json().get("csat"), "csat", lo=1, hi=5, integer=True)
    cosmos.enqueue("atencion_cliente", {k: v for k, v in case.items() if k not in ("vence", "vencido")})
    return _with_sla(case)
