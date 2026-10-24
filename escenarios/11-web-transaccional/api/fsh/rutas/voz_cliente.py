"""Escenario 10 · voz del cliente: reseñas y NPS tras la compra, moderación, respuesta, temas y sentimiento."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from .. import cosmos, db, texto
from ..util import an_id, field, flag, number, one_of
from ..web import HttpError, Request, forbidden, not_found, route

TYPES = ["review_producto", "nps_relacional"]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


@route("POST", "/opiniones", {"cliente"})
def opinar(req: Request):
    cid = req.user.customer_id
    if not cid:
        raise forbidden("Tu usuario no está asociado a un cliente.")
    data = req.json()
    kind = one_of(data.get("tipo"), TYPES, "tipo")
    text = field(data, "texto", max_len=1500)
    product = an_id(data.get("product_id"), "product", required=kind == "review_producto")
    order = an_id(data.get("order_id"), "order", required=False)
    if kind == "review_producto":
        bought = db.scalar("""SELECT CASE WHEN EXISTS (SELECT 1 FROM sales.online_order_line l
                                                       JOIN sales.online_order o ON o.order_id = l.order_id
                                                       WHERE o.customer_id = ? AND l.product_id = ? AND o.order_status <> N'Cancelado')
                                          OR EXISTS (SELECT 1 FROM sales.pos_ticket_line l JOIN sales.pos_ticket t ON t.ticket_id = l.ticket_id
                                                     WHERE t.customer_id = ? AND l.product_id = ?)
                                     THEN 1 ELSE 0 END""", cid, product, cid, product)
        if not bought:
            raise HttpError(422, "Solo puedes opinar sobre productos que has comprado.", "sin_compra")
        rating, nps = number(data.get("rating"), "rating", lo=1, hi=5, integer=True), None
    else:
        rating, nps = None, number(data.get("nps"), "nps", lo=0, hi=10, integer=True)
    if order and db.scalar("SELECT customer_id FROM sales.online_order WHERE order_id = ?", order) != cid:
        raise HttpError(422, "Ese pedido no es tuyo.", "referencia")
    fid = cosmos.next_ids("feedback")[0]
    doc = {"id": fid, "pk": cid, "feedback_id": fid, "fecha_feedback": _now(), "customer_id": cid, "order_id": order,
           "product_id": product, "store_id": None,
           "canal_feedback": "web_review" if kind == "review_producto" else "nps_app",
           "tipo_feedback": kind, "rating_1_5": rating, "nps_0_10": nps, "sentimiento": texto.sentiment(text),
           "tema_principal": texto.topic(text), "texto_feedback": text, "publicado_flag": False,
           "respondido_flag": False, "respuesta_marca": None, "origen": "web"}
    cosmos.enqueue("feedback", doc)
    return doc


@route("GET", "/mis-opiniones", {"cliente"})
def mis_opiniones(req: Request):
    if not req.user.customer_id:
        raise forbidden("Tu usuario no está asociado a un cliente.")
    return cosmos.query("feedback", "SELECT * FROM c ORDER BY c.fecha_feedback DESC", pk=req.user.customer_id)


@route("GET", "/opiniones", {"atencion", "marketing"})
def listado(req: Request):
    conds, params = [], {}
    for arg, path in (("tema", "tema_principal"), ("sentimiento", "sentimiento"), ("tipo", "tipo_feedback")):
        if req.query.get(arg):
            conds.append(f"c.{path} = @{arg}")
            params[arg] = req.query[arg]
    if req.query.get("publicado") in ("0", "1"):
        conds.append("c.publicado_flag = @pub")
        params["pub"] = req.query["publicado"] == "1"
    if req.query.get("pendiente") == "1":
        conds.append("c.publicado_flag = false AND c.respondido_flag = false")
    sql = "SELECT * FROM c" + (" WHERE " + " AND ".join(conds) if conds else "") + " ORDER BY c.fecha_feedback DESC"
    return cosmos.query("feedback", sql, params, max_items=req.int_arg("tamano", 100, 1, 1000))


@route("POST", "/opiniones/{feedback_id}/moderar", {"atencion"})
def moderar(req: Request):
    doc = cosmos.find_by_id("feedback", req.params["feedback_id"].upper())
    if doc is None:
        raise not_found("La opinión no existe.")
    data = req.json()
    doc["publicado_flag"] = flag(data.get("publicar"))
    answer = field(data, "respuesta", required=False, max_len=1000)
    if answer:
        doc["respuesta_marca"] = answer
        doc["respondido_flag"] = True
        doc["fecha_respuesta"] = _now()
    doc["moderado_por"] = req.user.login
    cosmos.enqueue("feedback", doc)
    return doc


@route("GET", "/opiniones/resumen", {"atencion", "marketing", "direccion"})
def resumen(req: Request):
    rows = cosmos.query("feedback", "SELECT c.tipo_feedback, c.tema_principal, c.sentimiento, c.rating_1_5, c.nps_0_10, "
                        "c.publicado_flag FROM c", max_items=100_000)
    nps = [r["nps_0_10"] for r in rows if r.get("nps_0_10") is not None]
    ratings = [r["rating_1_5"] for r in rows if r.get("rating_1_5") is not None]
    promoters = sum(1 for n in nps if n >= 9)
    detractors = sum(1 for n in nps if n <= 6)
    by_topic: dict[str, Counter] = {}
    for r in rows:
        by_topic.setdefault(r.get("tema_principal") or "sin_tema", Counter())[r.get("sentimiento") or "Neutral"] += 1
    return {"opiniones": len(rows), "publicadas": sum(1 for r in rows if r.get("publicado_flag")),
            "valoracion_media": round(sum(ratings) / len(ratings), 2) if ratings else None,
            "nps": round(100 * (promoters - detractors) / len(nps), 1) if nps else None, "respuestas_nps": len(nps),
            "por_tema": {k: dict(v) for k, v in sorted(by_topic.items())}}
