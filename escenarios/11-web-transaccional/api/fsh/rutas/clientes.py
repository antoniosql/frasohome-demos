"""Escenario 6 · clientes y fidelización: CRM, puntos, consentimientos y consola de identidad."""
from __future__ import annotations

from datetime import datetime, timezone

from .. import cosmos, db
from ..util import a_date, an_id, field, flag, like, number, one_of, page
from ..web import HttpError, Request, forbidden, not_found, route

ROLES = {"atencion", "marketing"}
CUSTOMER_FIELDS = """customer_id, first_name, last_name, email, email_is_valid, phone, loyalty_joined_at, loyalty_tier,
                     loyalty_points, birth_date, gender, city, province, postal_code, country_code, marketing_consent,
                     customer_status, churned_at, acquisition_source, preferred_channel, updated_at"""


@route("GET", "/clientes", ROLES)
def listado(req: Request):
    offset, size = page(req, 30, 200)
    q = like(req.query.get("q"))
    status = req.query.get("estado") or None
    where = ("(? IS NULL OR customer_id = ? OR email LIKE ? OR (first_name + N' ' + last_name) LIKE ? OR phone LIKE ?) "
             "AND (? IS NULL OR customer_status = ?)")
    args = (q, (req.query.get("q") or "").strip().upper(), q, q, q, status, status)
    return {"total": db.scalar(f"SELECT COUNT(*) FROM crm.customer WHERE {where}", *args),
            "clientes": db.query(f"""SELECT customer_id, first_name, last_name, email, city, loyalty_tier, loyalty_points,
                                            customer_status, marketing_consent
                                     FROM crm.customer WHERE {where} ORDER BY customer_id
                                     OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""", *args, offset, size)}


def ficha(customer_id: str) -> dict:
    c = db.one(f"SELECT {CUSTOMER_FIELDS} FROM crm.customer WHERE customer_id = ?", customer_id)
    if c is None:
        raise not_found("El cliente no existe.")
    c["resumen"] = db.one("""
        SELECT (SELECT COUNT(*) FROM sales.online_order WHERE customer_id = ? AND order_status <> N'Cancelado') AS pedidos,
               (SELECT ISNULL(SUM(order_total), 0) FROM sales.online_order WHERE customer_id = ? AND order_status <> N'Cancelado') AS gasto_online,
               (SELECT COUNT(*) FROM sales.pos_ticket WHERE customer_id = ?) AS tickets,
               (SELECT ISNULL(SUM(ticket_net_amount), 0) FROM sales.pos_ticket WHERE customer_id = ?) AS gasto_tienda,
               (SELECT COUNT(*) FROM [returns].return_header WHERE customer_id = ?) AS devoluciones,
               (SELECT COUNT(*) FROM mkt.coupon WHERE customer_id = ? AND coupon_status = N'emitido') AS cupones_vigentes,
               (SELECT MAX(x) FROM (SELECT MAX(ordered_at) AS x FROM sales.online_order WHERE customer_id = ?
                                    UNION ALL SELECT MAX(ticket_at) FROM sales.pos_ticket WHERE customer_id = ?) u) AS ultima_compra""",
        *([customer_id] * 8))
    c["afinidad"] = db.one("""SELECT preferred_store_id, nearest_store_id, nearest_store_km, store_visits_12m, store_spend_12m_eur,
                                     online_spend_12m_eur, click_collect_propensity, visit_probability_30d, local_cluster
                              FROM mkt.customer_store_affinity WHERE customer_id = ?""", customer_id)
    return c


@route("GET", "/clientes/{customer_id}", ROLES)
def ver(req: Request):
    return ficha(an_id(req.params["customer_id"], "customer"))


def _upsert(data: dict, customer_id: str | None, user_login: str) -> str:
    row = db.call_one(
        "crm.usp_customer_upsert", customer_id=customer_id,
        first_name=field(data, "nombre", max_len=100), last_name=field(data, "apellidos", max_len=150),
        email=field(data, "email", required=False, max_len=255), phone=field(data, "telefono", required=False, max_len=50),
        birth_date=a_date(data.get("fecha_nacimiento"), "fecha_nacimiento", required=False),
        gender=field(data, "genero", required=False, max_len=30), city=field(data, "ciudad", required=False, max_len=100),
        province=field(data, "provincia", required=False, max_len=100),
        postal_code=field(data, "codigo_postal", required=False, max_len=20),
        marketing_consent=flag(data.get("consentimiento_marketing")),
        preferred_channel=field(data, "canal_preferido", required=False, max_len=50),
        acquisition_source=one_of(data.get("origen_alta", "tienda"), ["tienda", "online", "importación"], "origen_alta"),
        loyalty_tier=field(data, "nivel", required=False, max_len=50), user_login=user_login)
    return row["customer_id"]


@route("POST", "/clientes", ROLES)
def alta(req: Request):
    return ficha(_upsert(req.json(), None, req.user.login))


@route("PUT", "/clientes/{customer_id}", ROLES)
def editar(req: Request):
    return ficha(_upsert(req.json(), an_id(req.params["customer_id"], "customer"), req.user.login))


@route("POST", "/clientes/{customer_id}/estado", ROLES)
def estado(req: Request):
    cid = an_id(req.params["customer_id"], "customer")
    db.call("crm.usp_customer_set_status", customer_id=cid,
            customer_status=one_of(req.json().get("estado"), ["Activo", "Inactivo", "Bloqueado"], "estado"),
            user_login=req.user.login)
    return ficha(cid)


@route("POST", "/clientes/{customer_id}/puntos", ROLES)
def puntos(req: Request):
    cid = an_id(req.params["customer_id"], "customer")
    data = req.json()
    db.call("crm.usp_customer_adjust_points", customer_id=cid,
            delta=number(data.get("delta"), "delta", lo=-100_000, hi=100_000, integer=True),
            reason=field(data, "motivo", max_len=300), user_login=req.user.login)
    return ficha(cid)


# ------------------------------------------------------------------ el propio cliente

@route("GET", "/mi-cuenta", {"cliente"})
def mi_cuenta(req: Request):
    if not req.user.customer_id:
        raise forbidden("Tu usuario no está asociado a un cliente.")
    return ficha(req.user.customer_id)


@route("PUT", "/mi-cuenta", {"cliente"})
def editar_mi_cuenta(req: Request):
    """El cliente cambia sus datos de contacto y consentimientos; nombre, nivel y origen no."""
    cid = req.user.customer_id
    if not cid:
        raise forbidden("Tu usuario no está asociado a un cliente.")
    cur = db.one(f"SELECT {CUSTOMER_FIELDS} FROM crm.customer WHERE customer_id = ?", cid)
    data = req.json()
    merged = {"nombre": cur["first_name"], "apellidos": cur["last_name"],
              "email": data.get("email", cur["email"]), "telefono": data.get("telefono", cur["phone"]),
              "fecha_nacimiento": cur["birth_date"].isoformat() if cur["birth_date"] else None,
              "genero": cur["gender"], "ciudad": data.get("ciudad", cur["city"]),
              "provincia": data.get("provincia", cur["province"]),
              "codigo_postal": data.get("codigo_postal", cur["postal_code"]),
              "consentimiento_marketing": data.get("consentimiento_marketing", cur["marketing_consent"]),
              "canal_preferido": data.get("canal_preferido", cur["preferred_channel"]),
              "origen_alta": cur["acquisition_source"] if cur["acquisition_source"] in ("tienda", "online", "importación") else "tienda"}
    _upsert(merged, cid, req.user.login)
    return ficha(cid)


# ------------------------------------------------------------------ consola de identidad

SIGNAL_KEYS = ["email_hash", "telefono_hash", "tarjeta_fidelizacion_id", "cookie_id", "device_id", "app_user_id",
               "usuario_online_id"]


@route("GET", "/identidad/senales", {"marketing", "atencion", "profesor"})
def senales(req: Request):
    """Señales de un cliente (?cliente=C0041) o las que están sin asignar (por defecto)."""
    customer = an_id(req.query.get("cliente"), "customer", required=False)
    pk = customer or "SIN_CLIENTE"
    source = req.query.get("fuente") or None
    sql = "SELECT * FROM c" + (" WHERE c.fuente_sistema = @f" if source else "") + " ORDER BY c.fecha_evento DESC"
    rows = cosmos.query("senales_identidad", sql, {"f": source} if source else {}, pk=pk,
                        max_items=req.int_arg("tamano", 100, 1, 500))
    return {"particion": pk, "senales": rows}


@route("GET", "/identidad/senales/{signal_id}/candidatos", {"marketing", "atencion", "profesor"})
def candidatos(req: Request):
    """Clientes que comparten algún identificador (email, teléfono, tarjeta, cookie, dispositivo...) con la señal."""
    signal = cosmos.find_by_id("senales_identidad", req.params["signal_id"].upper())
    if signal is None:
        raise not_found("La señal no existe.")
    scores: dict[str, dict] = {}
    for key in SIGNAL_KEYS:
        value = signal.get(key)
        if not value:
            continue
        for other in cosmos.query("senales_identidad", f"SELECT c.id, c.customer_id_candidato FROM c WHERE c.{key} = @v",
                                  {"v": value}, max_items=100):
            cand = other.get("customer_id_candidato")
            if cand and other["id"] != signal["id"]:
                entry = scores.setdefault(cand, {"customer_id": cand, "coincidencias": set(), "senales": 0})
                entry["coincidencias"].add(key)
                entry["senales"] += 1
    raw, valid = signal.get("customer_id_raw"), None
    if raw:
        from ..util import ID_PATTERNS
        import re
        normalized = re.sub(r"[\s\-]", "", raw).upper().replace("CL", "C")
        if re.fullmatch(ID_PATTERNS["customer"], normalized):
            valid = normalized
    ranked = sorted(scores.values(), key=lambda e: (-len(e["coincidencias"]), -e["senales"], e["customer_id"]))
    return {"senal": signal, "id_en_bruto_normalizado": valid,
            "candidatos": [{**e, "coincidencias": sorted(e["coincidencias"])} for e in ranked[:10]]}


@route("POST", "/identidad/senales/{signal_id}/asignar", {"marketing", "atencion"})
def asignar(req: Request):
    """Asigna (o quita, con customer_id null) el cliente de una señal. Cambia de partición: borra y vuelve a crear."""
    signal = cosmos.find_by_id("senales_identidad", req.params["signal_id"].upper())
    if signal is None:
        raise not_found("La señal no existe.")
    customer = an_id(req.json().get("customer_id"), "customer", required=False)
    if customer and not db.scalar("SELECT 1 FROM crm.customer WHERE customer_id = ?", customer):
        raise HttpError(422, "El cliente no existe.", "referencia")
    new_pk = customer or "SIN_CLIENTE"
    updated = {**signal, "pk": new_pk, "customer_id_candidato": customer, "asignado_por": req.user.login,
               "asignado_en": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")}
    if new_pk != signal["pk"]:
        cosmos.enqueue("senales_identidad", {"id": signal["id"], "pk": signal["pk"]}, operation="delete")
    cosmos.enqueue("senales_identidad", updated)
    db.call("app.usp_audit", user_login=req.user.login, action_name="identity_assign", entity_name="senales_identidad",
            entity_id=signal["id"], detail=f"{signal['pk']} -> {new_pk}")
    return updated
