"""Escenarios 7 y 8 · gestión de campañas (brief, audiencia, creatividades, cupones, lanzamiento,
resultados a 30 días) y calendario de promociones."""
from __future__ import annotations

from datetime import datetime, timezone

from .. import cosmos, db, guardrails
from ..util import a_datetime, an_id, field, flag, number, one_of, page
from ..web import HttpError, Request, not_found, route

ROLES = {"marketing"}
OBJECTIVES = ["trafico_tienda", "reactivacion", "cross_sell", "promocion", "upsell", "retencion", "captacion", "onboarding"]
CHANNELS = ["EMAIL", "SMS", "PUSH"]
SEGMENTS = ["VIP_OMNICANAL", "LOCAL_STORE", "NUEVO_CONTACTABLE", "RIESGO_CHURN", "ALTO_TICKET_MUEBLES", "POST_DEVOLUCION",
            "PROMO_SENSIBLE_TEXTIL", "ACTIVO_BASE", "DECORACION_FRECUENTE", "TODOS"]
OFFERS = ["descuento_pct", "cupon_importe", "puntos", "acceso_anticipado", "financiacion"]
TONES = ["inspiracional", "cercano", "exclusivo", "práctico", "urgencia_suave"]
CAMPAIGN_FIELDS = """campaign_id, campaign_name, objective, channel, starts_at, ends_at, target_segment, target_category,
                     target_store_id, offer_type, discount_pct, budget_eur, control_group_pct, primary_kpi, campaign_status,
                     copy_axis, created_by, created_at, updated_at"""


def _campaign(campaign_id: str) -> dict:
    c = db.one(f"SELECT {CAMPAIGN_FIELDS} FROM mkt.campaign WHERE campaign_id = ?", campaign_id)
    if c is None:
        raise not_found("La campaña no existe.")
    return c


@route("GET", "/campanas", ROLES)
def listado(req: Request):
    offset, size = page(req, 30, 100)
    status = req.query.get("estado") or None
    return db.query(f"""SELECT {CAMPAIGN_FIELDS},
                               (SELECT COUNT(*) FROM mkt.campaign_contact cc WHERE cc.campaign_id = c.campaign_id) AS contactos
                        FROM mkt.campaign c WHERE (? IS NULL OR campaign_status = ?)
                        ORDER BY starts_at DESC, campaign_id DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
                    status, status, offset, size)


@route("GET", "/campanas/{campaign_id}", ROLES)
def ver(req: Request):
    c = _campaign(an_id(req.params["campaign_id"], "campaign"))
    c["resultados"] = resultados_de(c["campaign_id"])
    return c


def _brief(data: dict, campaign_id: str | None, login: str) -> str:
    starts = a_datetime(data.get("inicio"), "inicio")
    ends = a_datetime(data.get("fin"), "fin")
    row = db.call_one(
        "mkt.usp_campaign_upsert", campaign_id=campaign_id, campaign_name=field(data, "nombre", max_len=200),
        objective=one_of(data.get("objetivo"), OBJECTIVES, "objetivo"), channel=one_of(data.get("canal"), CHANNELS, "canal"),
        starts_at=starts, ends_at=ends, target_segment=one_of(data.get("segmento"), SEGMENTS, "segmento"),
        target_category=field(data, "categoria", required=False, max_len=100),
        target_store_id=an_id(data.get("tienda"), "store", required=False),
        offer_type=one_of(data.get("oferta"), OFFERS, "oferta"),
        discount_pct=number(data.get("descuento", 0), "descuento", lo=0, hi=100),
        budget_eur=number(data.get("presupuesto"), "presupuesto", lo=0, hi=1_000_000, required=False),
        control_group_pct=number(data.get("grupo_control", 0.10), "grupo_control", lo=0, hi=0.5),
        primary_kpi=field(data, "kpi", required=False, max_len=50), copy_axis=field(data, "eje_copy", required=False),
        user_login=login)
    return row["campaign_id"]


@route("POST", "/campanas", ROLES)
def crear(req: Request):
    return _campaign(_brief(req.json(), None, req.user.login))


@route("PUT", "/campanas/{campaign_id}", ROLES)
def editar(req: Request):
    return _campaign(_brief(req.json(), an_id(req.params["campaign_id"], "campaign"), req.user.login))


@route("POST", "/campanas/{campaign_id}/audiencia", ROLES)
def audiencia(req: Request):
    cid = an_id(req.params["campaign_id"], "campaign")
    row = db.call_one("mkt.usp_campaign_build_audience", campaign_id=cid,
                      max_contacts=number(req.json().get("maximo", 300), "maximo", lo=1, hi=2000, integer=True),
                      user_login=req.user.login)
    return {"campana": _campaign(cid), "audiencia": row}


@route("GET", "/campanas/{campaign_id}/contactos", ROLES)
def contactos(req: Request):
    cid = an_id(req.params["campaign_id"], "campaign")
    offset, size = page(req, 50, 500)
    return db.query("""SELECT cc.contact_id, cc.customer_id, c.first_name, c.last_name, cc.experiment_group, cc.delivery_status,
                              cc.contacted_at, cc.coupon_instance_id, cc.personalized_store_id, cc.recommended_product_1,
                              cc.recommended_product_2, cc.conversion_30d, cc.revenue_30d_eur, cc.margin_30d_eur
                       FROM mkt.campaign_contact cc JOIN crm.customer c ON c.customer_id = cc.customer_id
                       WHERE cc.campaign_id = ? ORDER BY cc.contact_id OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
                    cid, offset, size)


@route("POST", "/campanas/{campaign_id}/cupones", ROLES)
def cupones(req: Request):
    cid = an_id(req.params["campaign_id"], "campaign")
    data = req.json()
    row = db.call_one("mkt.usp_campaign_issue_coupons", campaign_id=cid,
                      valid_days=number(data.get("dias_validez", 15), "dias_validez", lo=1, hi=90, integer=True),
                      min_spend_eur=number(data.get("gasto_minimo", 0), "gasto_minimo", lo=0, hi=10_000),
                      user_login=req.user.login)
    return {"campana": _campaign(cid), "cupones": row}


@route("POST", "/campanas/{campaign_id}/lanzar", ROLES)
def lanzar(req: Request):
    cid = an_id(req.params["campaign_id"], "campaign")
    creatives = cosmos.query("creatividades", "SELECT VALUE COUNT(1) FROM c", pk=cid)
    if not creatives or creatives[0] == 0:
        raise HttpError(422, "Añade al menos una creatividad antes de lanzar.", "sin_creatividad")
    row = db.call_one("mkt.usp_campaign_launch", campaign_id=cid, user_login=req.user.login)
    return {"campana": _campaign(cid), "lanzamiento": row}


@route("POST", "/campanas/{campaign_id}/atribuir", ROLES)
def atribuir(req: Request):
    cid = an_id(req.params["campaign_id"], "campaign")
    row = db.call_one("mkt.usp_campaign_attribute", campaign_id=cid, user_login=req.user.login)
    return {"atribucion": row, "resultados": resultados_de(cid)}


@route("POST", "/campanas/{campaign_id}/cerrar", ROLES)
def cerrar(req: Request):
    cid = an_id(req.params["campaign_id"], "campaign")
    db.call("mkt.usp_campaign_close", campaign_id=cid, user_login=req.user.login)
    return _campaign(cid)


def resultados_de(campaign_id: str) -> dict:
    groups = db.query("""
        SELECT experiment_group AS grupo, COUNT(*) AS contactos,
               SUM(CASE WHEN delivery_status = N'entregado' THEN 1 ELSE 0 END) AS entregados,
               SUM(CASE WHEN conversion_30d = 1 THEN 1 ELSE 0 END) AS conversiones,
               SUM(revenue_30d_eur) AS ingresos, SUM(margin_30d_eur) AS margen, SUM(contact_cost_eur) AS coste_contacto
        FROM mkt.campaign_contact WHERE campaign_id = ? GROUP BY experiment_group""", campaign_id)
    by = {g["grupo"]: g for g in groups}
    for g in groups:
        g["tasa_conversion"] = round(g["conversiones"] / g["contactos"], 4) if g["contactos"] else None
    t, c = by.get("treatment"), by.get("control")
    uplift = None
    if t and c and t["tasa_conversion"] is not None and c["tasa_conversion"] is not None:
        uplift = round(t["tasa_conversion"] - c["tasa_conversion"], 4)
    coupons = db.one("""SELECT COUNT(*) AS emitidos, SUM(CASE WHEN coupon_status = N'canjeado' THEN 1 ELSE 0 END) AS canjeados,
                               SUM(discount_applied_eur) AS descuento_aplicado
                        FROM mkt.coupon WHERE campaign_id = ?""", campaign_id)
    events = cosmos.query("eventos_campana", "SELECT c.tipo_evento, COUNT(1) AS n FROM c GROUP BY c.tipo_evento",
                          pk=campaign_id, max_items=50)
    return {"grupos": groups, "uplift_conversion": uplift, "cupones": coupons,
            "eventos": {e["tipo_evento"]: e["n"] for e in events}}


@route("GET", "/campanas/{campaign_id}/resultados", ROLES)
def resultados(req: Request):
    cid = an_id(req.params["campaign_id"], "campaign")
    _campaign(cid)
    return resultados_de(cid)


# ------------------------------------------------------------------ creatividades

@route("GET", "/guardrails", ROLES)
def reglas(req: Request):
    return db.query("SELECT rule_id, rule_category, rule_description, applies_to_channel, severity FROM ref.brand_guardrail ORDER BY rule_id")


@route("GET", "/campanas/{campaign_id}/creatividades", ROLES)
def creatividades(req: Request):
    cid = an_id(req.params["campaign_id"], "campaign")
    return cosmos.query("creatividades", "SELECT * FROM c ORDER BY c.creative_id", pk=cid)


def _creative_doc(data: dict, campaign: dict, creative_id: str) -> dict:
    return {"id": creative_id, "pk": campaign["campaign_id"], "creative_id": creative_id,
            "campaign_id": campaign["campaign_id"],
            "microsegmento": field(data, "microsegmento", required=False, max_len=50) or campaign["target_segment"],
            "canal": campaign["channel"],
            "categoria_objetivo": campaign["target_category"] or "multicategoría",
            "tono": one_of(data.get("tono"), TONES, "tono"),
            "beneficio_principal": field(data, "beneficio_principal", max_len=200),
            "cta": field(data, "cta", max_len=60), "asunto": field(data, "asunto", required=False, max_len=150),
            "copy_corto": field(data, "copy_corto", max_len=400), "copy_largo": field(data, "copy_largo", required=False, max_len=2000),
            "prueba_social": field(data, "prueba_social", required=False, max_len=300),
            "prompt_base": field(data, "prompt_base", required=False, max_len=2000),
            "open_rate": None, "ctr": None, "cvr": None, "revenue_por_1000_envios_eur": None,
            "winning_variant_flag": False, "origen": "web"}


def _save_creative(req: Request, campaign_id: str, creative_id: str | None) -> dict:
    campaign = _campaign(campaign_id)
    if campaign["campaign_status"] not in ("borrador", "audiencia"):
        raise HttpError(422, "Las creatividades solo se editan antes de lanzar la campaña.", "estado")
    data = req.json()
    creative_id = creative_id or cosmos.next_ids("creative")[0]
    doc = _creative_doc(data, campaign, creative_id)
    issues = guardrails.check(doc, campaign)
    blocking = [i for i in issues if i["severidad"] == "alta"]
    if blocking and not flag(data.get("solo_validar")):
        return_body = {"error": "La creatividad incumple reglas de marca de severidad alta.", "codigo": "guardrails",
                       "infracciones": issues}
        from ..web import Response
        return Response(422, return_body)
    doc["guardrail_legal"] = "; ".join(f"{i['regla_id']}: {i['detalle']}" for i in issues) or "Sin avisos"
    doc["avisos_guardrails"] = issues
    if flag(data.get("solo_validar")):
        return {"creatividad": doc, "infracciones": issues, "guardada": False}
    doc["actualizado"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    doc["actualizado_por"] = req.user.login
    cosmos.enqueue("creatividades", doc)
    return {"creatividad": doc, "infracciones": issues, "guardada": True}


@route("POST", "/campanas/{campaign_id}/creatividades", ROLES)
def crear_creatividad(req: Request):
    return _save_creative(req, an_id(req.params["campaign_id"], "campaign"), None)


@route("PUT", "/campanas/{campaign_id}/creatividades/{creative_id}", ROLES)
def editar_creatividad(req: Request):
    cid = an_id(req.params["campaign_id"], "campaign")
    crid = req.params["creative_id"].upper()
    if cosmos.read("creatividades", crid, cid) is None:
        raise not_found("La creatividad no existe en esa campaña.")
    return _save_creative(req, cid, crid)


@route("POST", "/marketing/afinidad/recalcular", ROLES)
def afinidad(req: Request):
    return db.call_one("mkt.usp_affinity_recalculate", user_login=req.user.login)


# ------------------------------------------------------------------ promociones

PROMO_FIELDS = """promo_id, promo_name, starts_at, ends_at, scope_type, scope_id, promo_type, discount_pct, discount_eur, channel,
                  target_segment, store_id, combinable, basket_threshold_eur, min_margin_pct, related_campaign_id"""


@route("GET", "/promociones", ROLES)
def promociones(req: Request):
    when = req.query.get("vigencia") or "todas"
    cond = {"activas": "SYSUTCDATETIME() BETWEEN starts_at AND ends_at", "futuras": "starts_at > SYSUTCDATETIME()",
            "pasadas": "ends_at < SYSUTCDATETIME()"}.get(when, "1 = 1")
    return db.query(f"SELECT {PROMO_FIELDS} FROM mkt.promotion WHERE {cond} ORDER BY starts_at DESC, promo_id")


def _promo(data: dict, promo_id: str | None, login: str) -> dict:
    row = db.call_one(
        "mkt.usp_promotion_upsert", promo_id=promo_id, promo_name=field(data, "nombre", max_len=200),
        starts_at=a_datetime(data.get("inicio"), "inicio"), ends_at=a_datetime(data.get("fin"), "fin"),
        scope_type=one_of(data.get("ambito"), ["categoria", "categoria_tienda", "campana"], "ambito"),
        scope_id=field(data, "ambito_id", max_len=150),
        promo_type=one_of(data.get("tipo"), ["descuento_pct", "bundle", "envio_gratis", "2a_unidad", "cupon_importe", "puntos",
                                             "regalo", "outlet"], "tipo"),
        discount_pct=number(data.get("descuento_pct"), "descuento_pct", lo=0, hi=100, required=False),
        discount_eur=number(data.get("descuento_eur"), "descuento_eur", lo=0, hi=10_000, required=False),
        channel=one_of(data.get("canal"), ["EMAIL", "SMS", "PUSH", "WEB"], "canal"),
        target_segment=field(data, "segmento", required=False, max_len=50),
        store_id=an_id(data.get("tienda"), "store", required=False), combinable=flag(data.get("combinable")),
        basket_threshold_eur=number(data.get("umbral_cesta", 0), "umbral_cesta", lo=0, hi=100_000),
        min_margin_pct=number(data.get("margen_minimo"), "margen_minimo", lo=0, hi=80, required=False),
        related_campaign_id=an_id(data.get("campana"), "campaign", required=False), user_login=login)
    return db.one(f"SELECT {PROMO_FIELDS} FROM mkt.promotion WHERE promo_id = ?", row["promo_id"])


@route("POST", "/promociones", ROLES)
def crear_promocion(req: Request):
    return _promo(req.json(), None, req.user.login)


@route("PUT", "/promociones/{promo_id}", ROLES)
def editar_promocion(req: Request):
    return _promo(req.json(), an_id(req.params["promo_id"], "promo"), req.user.login)
