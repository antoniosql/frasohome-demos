"""Escenarios 6 a 10: clientes e identidad, campañas, promociones, atención al cliente y voz del cliente."""
import uuid
from datetime import datetime, timedelta

from fsh import cosmos, db


def _dt(days: int) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")


def test_clientes_alta_edicion_puntos_y_ambito(as_role, people):
    c = as_role("atencion")
    tag = uuid.uuid4().hex[:8]
    r = c.post("/clientes", {"nombre": "Lucía", "apellidos": "Prueba Pérez", "email": f"Lucia.{tag}@Example.com",
                             "telefono": "+34 600 000 000", "ciudad": "A Coruña", "provincia": "A Coruña",
                             "codigo_postal": "15001", "consentimiento_marketing": True, "origen_alta": "tienda"})
    assert r.status == 200, r.json
    cid = r.json["customer_id"]
    assert cid.startswith("C") and r.json["email"] == f"lucia.{tag}@example.com" and r.json["email_is_valid"]
    # Los correos inválidos solo existen en los datos históricos: la web no los admite.
    bad = c.put(f"/clientes/{cid}", {"nombre": "Lucía", "apellidos": "Prueba Pérez", "email": "no-es-un-email",
                                     "origen_alta": "tienda"})
    assert bad.status == 422 and bad.json["codigo"].startswith("regla_")
    r = c.put(f"/clientes/{cid}", {"nombre": "Lucía", "apellidos": "Prueba Pérez", "email": f"lucia.{tag}@example.org",
                                   "ciudad": "Vigo", "origen_alta": "tienda"})
    assert r.status == 200 and r.json["city"] == "Vigo" and r.json["email"] == f"lucia.{tag}@example.org"
    assert c.post(f"/clientes/{cid}/puntos", {"delta": 250, "motivo": "Bienvenida"}).json["loyalty_points"] == 250
    neg = c.post(f"/clientes/{cid}/puntos", {"delta": -1000, "motivo": "Error"})
    assert neg.status == 422 and neg.json["codigo"].startswith("regla_")
    assert c.post(f"/clientes/{cid}/estado", {"estado": "Bloqueado"}).json["customer_status"] == "Bloqueado"
    found = c.get(f"/clientes?q={cid}").json
    assert found["total"] == 1 and found["clientes"][0]["customer_id"] == cid
    # El cliente solo ve y cambia lo suyo, y no el nombre.
    me = as_role("cliente")
    mine = me.get("/mi-cuenta").json
    assert mine["customer_id"] == people["customer"] and "resumen" in mine
    upd = me.put("/mi-cuenta", {"telefono": "+34 611 111 111", "nombre": "Otro"})
    assert upd.status == 200 and upd.json["phone"] == "+34 611 111 111" and upd.json["first_name"] == mine["first_name"]
    assert me.get(f"/clientes/{cid}").status == 403


def test_consola_de_identidad(as_role):
    c = as_role("marketing")
    loose = c.get("/identidad/senales?tamano=50").json
    assert loose["particion"] == "SIN_CLIENTE" and loose["senales"]
    signal = loose["senales"][0]
    cands = c.get(f"/identidad/senales/{signal['id']}/candidatos").json
    assert cands["senal"]["id"] == signal["id"] and isinstance(cands["candidatos"], list)
    target = db.scalar("SELECT TOP 1 customer_id FROM crm.customer ORDER BY customer_id")
    moved = c.post(f"/identidad/senales/{signal['id']}/asignar", {"customer_id": target})
    assert moved.status == 200 and moved.json["pk"] == target
    assert cosmos.read("senales_identidad", signal["id"], target)["customer_id_candidato"] == target
    assert cosmos.read("senales_identidad", signal["id"], "SIN_CLIENTE") is None
    back = c.post(f"/identidad/senales/{signal['id']}/asignar", {"customer_id": None})
    assert back.json["pk"] == "SIN_CLIENTE" and cosmos.read("senales_identidad", signal["id"], target) is None
    # El profesor consulta, pero no asigna.
    prof = as_role("profesor")
    assert prof.get("/identidad/senales").status == 200
    assert prof.post(f"/identidad/senales/{signal['id']}/asignar", {"customer_id": target}).status == 403


def test_campana_completa(as_role):
    c = as_role("marketing")
    brief = {"nombre": "Prueba iluminación otoño", "objetivo": "cross_sell", "canal": "EMAIL", "inicio": _dt(-1), "fin": _dt(20),
             "segmento": "TODOS", "categoria": "Iluminación", "oferta": "descuento_pct", "descuento": 10,
             "presupuesto": 500, "grupo_control": 0.2, "kpi": "cvr_compra", "eje_copy": "Luz cálida para casa"}
    r = c.post("/campanas", brief)
    assert r.status == 200, r.json
    cid = r.json["campaign_id"]
    assert r.json["campaign_status"] == "borrador"
    bad = c.post("/campanas", {**brief, "fin": _dt(-5)})
    assert bad.status in (400, 422)
    aud = c.post(f"/campanas/{cid}/audiencia", {"maximo": 40})
    assert aud.status == 200, aud.json
    contacts = c.get(f"/campanas/{cid}/contactos?tamano=500").json
    assert contacts and {x["experiment_group"] for x in contacts} == {"treatment", "control"}
    # Creatividades validadas contra los guardrails de marca.
    assert c.get("/guardrails").json
    risky = {"tono": "urgencia_suave", "beneficio_principal": "El precio más bajo del mercado, garantizado",
             "cta": "Compra ya", "copy_corto": "¡¡ÚLTIMA OPORTUNIDAD!! El mejor precio garantizado, 100% gratis"}
    blocked = c.post(f"/campanas/{cid}/creatividades", risky)
    assert blocked.status == 422 and blocked.json["codigo"] == "guardrails" and blocked.json["infracciones"]
    assert c.post(f"/campanas/{cid}/lanzar").status == 422      # sin creatividad
    good = {"tono": "cercano", "beneficio_principal": "Ideas de luz cálida para tu salón", "cta": "Descubrir",
            "asunto": "Tu salón, con otra luz", "copy_corto": "Lámparas que crean ambiente. Descúbrelas en tu tienda FraSoHome."}
    saved = c.post(f"/campanas/{cid}/creatividades", good)
    assert saved.status == 200 and saved.json["guardada"], saved.json
    crid = saved.json["creatividad"]["creative_id"]
    assert any(x["creative_id"] == crid for x in c.get(f"/campanas/{cid}/creatividades").json)
    edited = c.put(f"/campanas/{cid}/creatividades/{crid}", {**good, "cta": "Ver ideas"})
    assert edited.status == 200 and cosmos.read("creatividades", crid, cid)["cta"] == "Ver ideas"
    coupons = c.post(f"/campanas/{cid}/cupones", {"dias_validez": 15, "gasto_minimo": 50})
    assert coupons.status == 200, coupons.json
    issued = db.scalar("SELECT COUNT(*) FROM mkt.coupon WHERE campaign_id = ?", cid)
    treated = db.scalar("SELECT COUNT(*) FROM mkt.campaign_contact WHERE campaign_id = ? AND experiment_group = N'treatment'", cid)
    assert issued == treated
    launched = c.post(f"/campanas/{cid}/lanzar")
    assert launched.status == 200, launched.json
    assert launched.json["campana"]["campaign_status"] == "activa"
    events = cosmos.query("eventos_campana", "SELECT VALUE COUNT(1) FROM c", pk=cid)
    assert events[0] > 0
    assert c.put(f"/campanas/{cid}/creatividades/{crid}", good).status == 422   # ya lanzada
    attr = c.post(f"/campanas/{cid}/atribuir")
    assert attr.status == 200 and "grupos" in attr.json["resultados"]
    res = c.get(f"/campanas/{cid}/resultados").json
    assert res["cupones"]["emitidos"] == issued and res["eventos"]
    closed = c.post(f"/campanas/{cid}/cerrar")
    assert closed.status == 200 and closed.json["campaign_status"] == "finalizada"
    assert any(x["campaign_id"] == cid for x in c.get("/campanas").json)
    assert c.post("/marketing/afinidad/recalcular").status == 200
    # Otros roles no gestionan campañas.
    assert as_role("atencion").get("/campanas").status == 403


def test_promociones(as_role, anon):
    c = as_role("marketing")
    body = {"nombre": "Prueba textil -15 %", "inicio": _dt(-1), "fin": _dt(10), "ambito": "categoria", "ambito_id": "Textil hogar",
            "tipo": "descuento_pct", "descuento_pct": 15, "canal": "WEB", "segmento": "ACTIVO_BASE", "combinable": False,
            "umbral_cesta": 40, "margen_minimo": 20}
    r = c.post("/promociones", body)
    assert r.status == 200, r.json
    pid = r.json["promo_id"]
    upd = c.put(f"/promociones/{pid}", {**body, "descuento_pct": 12})
    assert upd.status == 200 and float(upd.json["discount_pct"]) == 12
    assert any(p["promo_id"] == pid for p in c.get("/promociones?vigencia=activas").json)
    assert any(p["promo_id"] == pid for p in anon.get("/catalogo/promociones").json)
    wrong = c.post("/promociones", {**body, "fin": _dt(-3)})
    assert wrong.status in (400, 422)


def test_atencion_al_cliente(as_role, people):
    me = as_role("cliente")
    opened = me.post("/mis-casos", {"tipo_caso": "entrega", "texto": "Mi pedido no ha llegado todavía"})
    assert opened.status == 200, opened.json
    case_id = opened.json["id"]
    assert opened.json["pk"] == people["customer"] and opened.json["conversacion"][0]["autor"] == "cliente"
    agent = as_role("atencion")
    queue = agent.get("/atencion/casos?estado=Pendiente").json
    assert any(x["id"] == case_id for x in queue)
    assert any(x["id"] == case_id for x in agent.get(f"/atencion/casos?cliente={people['customer']}").json)
    assert agent.post(f"/atencion/casos/{case_id}/mensajes", {"texto": "Lo revisamos con el transportista"}).status == 200
    assert me.post(f"/mis-casos/{case_id}/csat", {"csat": 5}).status == 422     # aún no resuelto
    done = agent.post(f"/atencion/casos/{case_id}/resolver", {"resolucion": "Entregado mañana. Te dejamos un cupón.",
                                                              "compensacion": {"tipo": "cupon", "valor": 10}})
    assert done.status == 200, done.json
    code = done.json["cupon_compensacion"]
    assert db.scalar("SELECT customer_id FROM mkt.coupon WHERE coupon_code = ?", code) == people["customer"]
    assert me.post(f"/mis-casos/{case_id}/csat", {"csat": 4}).json["csat_1_5"] == 4
    stored = cosmos.read("atencion_cliente", case_id, people["customer"])
    assert stored["estado_resolucion"] == "Resuelto" and stored["csat_1_5"] == 4 and len(stored["conversacion"]) == 3
    # Otro cliente no ve el caso.
    other = as_role("cliente2")
    assert other.post(f"/mis-casos/{case_id}/mensajes", {"texto": "hola"}).status in (403, 404)
    detail = agent.get(f"/atencion/casos/{case_id}").json
    assert detail["id"] == case_id


def test_voz_del_cliente(as_role, people):
    me = as_role("cliente")
    never = db.scalar("""SELECT TOP 1 p.product_id FROM catalog.product p WHERE NOT EXISTS (
                             SELECT 1 FROM sales.online_order_line l JOIN sales.online_order o ON o.order_id = l.order_id
                             WHERE o.customer_id = ? AND l.product_id = p.product_id)
                         AND NOT EXISTS (SELECT 1 FROM sales.pos_ticket_line l JOIN sales.pos_ticket t ON t.ticket_id = l.ticket_id
                             WHERE t.customer_id = ? AND l.product_id = p.product_id) ORDER BY p.product_id""",
                      people["customer"], people["customer"])
    refused = me.post("/opiniones", {"tipo": "review_producto", "product_id": never, "rating": 4, "texto": "No lo compré"})
    assert refused.status == 422 and refused.json["codigo"] == "sin_compra"
    # Una compra que no se cancela le da derecho a opinar.
    product = db.scalar("""SELECT TOP 1 s.product_id FROM inventory.stock_level s JOIN catalog.product p ON p.product_id = s.product_id
                           WHERE s.store_id = N'ONLINE' AND s.on_hand_qty - s.reserved_qty >= 2 AND p.product_status = N'Activo'
                           AND p.sale_price IS NOT NULL ORDER BY s.product_id""")
    me.put("/carrito", {"lineas": [{"product_id": product, "cantidad": 1}]})
    order = me.post("/pedidos", {"direccion": "Calle Real 12", "codigo_postal": "15003", "ciudad": "A Coruña",
                                 "provincia": "A Coruña", "metodo_pago": "Tarjeta"})
    assert order.status == 200, order.json
    review = me.post("/opiniones", {"tipo": "review_producto", "product_id": product, "rating": 2,
                                    "texto": "La lámpara llegó con el cable dañado, mala experiencia"})
    assert review.status == 200, review.json
    fid = review.json["feedback_id"]
    assert review.json["sentimiento"] == "Negativo" and review.json["publicado_flag"] is False
    nps = me.post("/opiniones", {"tipo": "nps_relacional", "nps": 9, "texto": "Muy buena atención en tienda"})
    assert nps.status == 200 and nps.json["nps_0_10"] == 9
    assert {x["feedback_id"] for x in me.get("/mis-opiniones").json} >= {fid, nps.json["feedback_id"]}
    agent = as_role("atencion")
    assert any(x["feedback_id"] == fid for x in agent.get("/opiniones?pendiente=1").json)
    mod = agent.post(f"/opiniones/{fid}/moderar", {"publicar": True, "respuesta": "Sentimos el problema, te contactamos."})
    assert mod.status == 200 and mod.json["publicado_flag"] is True and mod.json["respondido_flag"] is True
    summary = as_role("direccion").get("/opiniones/resumen").json
    assert summary
    bad = me.post("/opiniones", {"tipo": "review_producto", "rating": 9, "texto": "x", "product_id": product})
    assert bad.status == 400
