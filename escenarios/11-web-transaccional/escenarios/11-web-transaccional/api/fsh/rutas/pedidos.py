"""Escenario 1 · compra online: carrito, checkout, pedidos y cupones del cliente."""
from __future__ import annotations

from datetime import datetime, timezone

from .. import cosmos, db
from ..auth import User
from ..util import an_id, field, lines, one_of, page
from ..web import HttpError, Request, forbidden, not_found, route

PAYMENT_METHODS = ["Tarjeta", "PayPal", "Bizum", "ApplePay", "Transferencia", "ContraReembolso"]
STAFF = {"atencion", "tienda", "direccion"}


def _customer(user: User) -> str:
    cid = user.customer_id
    if not cid:
        raise forbidden("Tu usuario no está asociado a un cliente.")
    return cid


def quote(store_id: str, customer_id: str | None, basket: list[dict], coupon: str | None) -> dict:
    sets = db.call("sales.usp_quote_basket", store_id=store_id, customer_id=customer_id, lines_json=basket,
                   coupon_code=coupon)
    detail, totals = sets[-2], sets[-1][0]
    out = {"lineas": detail, "totales": totals}
    if store_id == "ONLINE":
        out["totales"]["gastos_envio"] = db.scalar("SELECT sales.fn_shipping_amount(?, ?)", totals["net_total"],
                                                   totals["max_weight_kg"])
    return out


# ------------------------------------------------------------------ carrito

@route("GET", "/carrito", {"cliente"})
def carrito(req: Request):
    cid = _customer(req.user)
    doc = cosmos.read("carritos", cid, cid) or {"lineas": [], "cupon": None}
    if not doc["lineas"]:
        return {"lineas": [], "cupon": None, "presupuesto": None}
    basket = [{"product_id": li["product_id"], "quantity": li["cantidad"]} for li in doc["lineas"]]
    try:
        presupuesto = quote("ONLINE", cid, basket, doc.get("cupon"))
        aviso = None
    except HttpError as exc:   # p. ej. el cupón caducó desde que se guardó el carrito
        presupuesto = quote("ONLINE", cid, basket, None) if doc.get("cupon") else None
        aviso = exc.message
    return {"lineas": doc["lineas"], "cupon": doc.get("cupon"), "presupuesto": presupuesto, "aviso": aviso}


@route("PUT", "/carrito", {"cliente"})
def guardar_carrito(req: Request):
    cid = _customer(req.user)
    data = req.json()
    items = lines(data) if data.get("lineas") else []
    coupon = field(data, "cupon", required=False, max_len=30)
    presupuesto = None
    if items:
        presupuesto = quote("ONLINE", cid, items, coupon)   # valida productos y cupón antes de guardar
    doc = {"id": cid, "pk": cid, "customer_id": cid,
           "lineas": [{"product_id": i["product_id"], "cantidad": i["quantity"]} for i in items],
           "cupon": coupon.upper() if coupon else None,
           "actualizado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"), "origen": "web"}
    if items:
        cosmos.upsert_direct("carritos", doc)
    else:
        cosmos.delete_direct("carritos", cid, cid)
    return {"lineas": doc["lineas"], "cupon": doc["cupon"], "presupuesto": presupuesto}


@route("DELETE", "/carrito", {"cliente"})
def vaciar_carrito(req: Request):
    cid = _customer(req.user)
    cosmos.delete_direct("carritos", cid, cid)
    return {"ok": True}


# ------------------------------------------------------------------ checkout y pedidos

@route("POST", "/pedidos", {"cliente"}, idempotent=True)
def checkout(req: Request):
    cid = _customer(req.user)
    data = req.json()
    if data.get("lineas"):
        items, coupon = lines(data), field(data, "cupon", required=False, max_len=30)
    else:
        doc = cosmos.read("carritos", cid, cid)
        if not doc or not doc.get("lineas"):
            raise HttpError(422, "El carrito está vacío.", "carrito_vacio")
        items = [{"product_id": li["product_id"], "quantity": li["cantidad"]} for li in doc["lineas"]]
        coupon = data.get("cupon", doc.get("cupon"))
    row = db.call_one(
        "sales.usp_checkout", customer_id=cid, lines_json=items,
        shipping_address=field(data, "direccion", max_len=255), shipping_postal_code=field(data, "codigo_postal", max_len=5),
        shipping_city=field(data, "ciudad", max_len=100), shipping_province=field(data, "provincia", max_len=100),
        payment_method=one_of(data.get("metodo_pago"), PAYMENT_METHODS, "metodo_pago"), coupon_code=coupon,
        order_origin=one_of(data.get("origen", "web"), ["web", "app"], "origen"),
        session_id=field(data, "session_id", required=False, max_len=20), user_login=req.user.login)
    cosmos.delete_direct("carritos", cid, cid)
    return _order_detail(row["order_id"], req.user) | {"resumen": row}


def _order_detail(order_id: str, user: User) -> dict:
    order = db.one("""SELECT order_id, ordered_at, customer_id, order_total, shipping_amount, currency_code, shipping_address,
                             shipping_postal_code, shipping_city, shipping_province, payment_method, order_status,
                             order_origin, coupon_instance_id, updated_at
                      FROM sales.online_order WHERE order_id = ?""", order_id)
    if order is None:
        raise not_found("El pedido no existe.")
    if not user.has(*STAFF) and order["customer_id"] != user.customer_id:
        raise not_found("El pedido no existe.")
    order["lineas"] = db.query("""SELECT l.order_line_id, l.product_id, l.product_description, l.category, l.quantity,
                                         l.unit_price, l.discount_amount, l.line_amount, l.promo_id,
                                         l.quantity - [returns].fn_returned_qty(l.order_line_id, NULL) AS devolvible
                                  FROM sales.online_order_line l WHERE l.order_id = ? ORDER BY l.order_line_id""", order_id)
    order["devoluciones"] = db.query("""SELECT h.return_id, h.returned_at, h.return_status, h.return_method,
                                               l.product_id, l.returned_quantity, l.refund_amount, l.return_reason
                                        FROM [returns].return_header h JOIN [returns].return_line l ON l.return_id = h.return_id
                                        WHERE h.original_order_id = ? ORDER BY h.returned_at""", order_id)
    return order


@route("GET", "/pedidos", "auth")
def mis_pedidos(req: Request):
    offset, size = page(req, 20, 100)
    if req.user.has(*STAFF):
        customer = an_id(req.query.get("cliente"), "customer", required=False)
    else:
        customer = _customer(req.user)
    status = req.query.get("estado") or None
    args = (customer, customer, status, status)
    where = "(? IS NULL OR customer_id = ?) AND (? IS NULL OR order_status = ?)"
    return {"total": db.scalar(f"SELECT COUNT(*) FROM sales.online_order WHERE {where}", *args),
            "pedidos": db.query(f"""SELECT order_id, ordered_at, customer_id, order_total, order_status, payment_method,
                                          (SELECT COUNT(*) FROM sales.online_order_line l WHERE l.order_id = o.order_id) AS lineas
                                   FROM sales.online_order o WHERE {where}
                                   ORDER BY ordered_at DESC, order_id DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
                                *args, offset, size)}


@route("GET", "/pedidos/{order_id}", "auth")
def pedido(req: Request):
    return _order_detail(an_id(req.params["order_id"], "order"), req.user)


@route("POST", "/pedidos/{order_id}/estado", {"atencion", "tienda"})
def estado_pedido(req: Request):
    oid = an_id(req.params["order_id"], "order")
    if "tienda" in req.user.roles and not req.user.has("atencion") and "ONLINE" not in req.user.stores:
        raise forbidden("Solo el almacén online prepara pedidos.")
    status = one_of(req.json().get("estado"), ["En preparación", "Entregado", "Cancelado"], "estado")
    db.call("sales.usp_order_set_status", order_id=oid, new_status=status, user_login=req.user.login)
    return _order_detail(oid, req.user)


@route("POST", "/pedidos/{order_id}/cancelar", {"cliente"})
def cancelar(req: Request):
    oid = an_id(req.params["order_id"], "order")
    order = db.one("SELECT customer_id, order_status FROM sales.online_order WHERE order_id = ?", oid)
    if order is None or order["customer_id"] != _customer(req.user):
        raise not_found("El pedido no existe.")
    if order["order_status"] != "Pendiente":
        raise HttpError(422, "Solo puedes cancelar un pedido pendiente. Si ya está en preparación, contacta con atención al cliente.",
                        "estado")
    db.call("sales.usp_order_set_status", order_id=oid, new_status="Cancelado", user_login=req.user.login)
    return _order_detail(oid, req.user)


@route("GET", "/mis-cupones", {"cliente"})
def mis_cupones(req: Request):
    cid = _customer(req.user)
    return db.query("""SELECT c.coupon_code, c.coupon_type, c.discount_pct, c.discount_eur, c.min_spend_eur,
                              c.restricted_category, c.restricted_store_id, c.valid_from, c.valid_to, c.coupon_status,
                              m.campaign_name
                       FROM mkt.coupon c LEFT JOIN mkt.campaign m ON m.campaign_id = c.campaign_id
                       WHERE c.customer_id = ? AND (c.coupon_status = N'emitido' OR c.redeemed_at >= DATEADD(DAY, -90, SYSUTCDATETIME()))
                       ORDER BY CASE c.coupon_status WHEN N'emitido' THEN 0 ELSE 1 END, c.valid_to""", cid)
