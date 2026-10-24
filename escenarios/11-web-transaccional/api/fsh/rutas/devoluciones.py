"""Escenario 3 · devoluciones online y en tienda, con reembolso y reingreso a stock."""
from __future__ import annotations

from .. import db
from ..auth import User, store_for
from ..util import an_id, field, number, one_of, page
from ..web import Request, bad_request, forbidden, not_found, route

ONLINE_METHODS = ["Envío", "Tienda", "Punto Pack"]
REFUND_METHODS = ["Tarjeta", "Efectivo", "Vale", "Tarjeta regalo", "Transferencia", "Cupón"]
STAFF = {"atencion", "tienda", "direccion"}


def _detail(return_id: str, user: User) -> dict:
    h = db.one("""SELECT return_id, returned_at, return_channel, store_id, customer_id, original_ticket_id, original_order_id,
                         return_status, return_method, refund_method, notes, updated_at
                  FROM [returns].return_header WHERE return_id = ?""", return_id)
    if h is None:
        raise not_found("La devolución no existe.")
    allowed = (user.has("atencion", "direccion")
               or ("tienda" in user.roles and (h["store_id"] in user.stores or (h["store_id"] is None and "ONLINE" in user.stores)))
               or ("cajero" in user.roles and h["store_id"] in user.stores)
               or ("cliente" in user.roles and h["customer_id"] == user.customer_id))
    if not allowed:
        raise not_found("La devolución no existe.")
    h["lineas"] = db.query("""SELECT return_line_id, product_id, original_ticket_line_id, original_order_line_id,
                                     returned_quantity, refund_amount, return_reason, original_sales_channel
                              FROM [returns].return_line WHERE return_id = ? ORDER BY return_line_id""", return_id)
    h["importe_total"] = sum(float(li["refund_amount"] or 0) for li in h["lineas"])
    return h


@route("POST", "/devoluciones/online", {"cliente"}, idempotent=True)
def online(req: Request):
    data = req.json()
    if not req.user.customer_id:
        raise forbidden("Tu usuario no está asociado a un cliente.")
    row = db.call_one("[returns].usp_return_online_request",
                      order_id=an_id(data.get("order_id"), "order"), order_line_id=an_id(data.get("order_line_id"), "order_line"),
                      quantity=number(data.get("cantidad"), "cantidad", lo=1, hi=20, integer=True),
                      return_reason=field(data, "motivo", max_len=200),
                      return_method=one_of(data.get("metodo"), ONLINE_METHODS, "metodo"),
                      customer_id=req.user.customer_id, user_login=req.user.login)
    return _detail(row["return_id"], req.user)


@route("POST", "/devoluciones/tienda", {"cajero"}, idempotent=True)
def tienda(req: Request):
    data = req.json()
    store = store_for(req.user, data.get("tienda"))
    ticket_line = an_id(data.get("ticket_line_id"), "ticket_line", required=False)
    order_line = an_id(data.get("order_line_id"), "order_line", required=False)
    if bool(ticket_line) == bool(order_line):
        raise bad_request("Indica «ticket_line_id» (compra en tienda) u «order_line_id» (compra online), uno de los dos.")
    row = db.call_one("[returns].usp_return_store", store_id=store, original_ticket_line_id=ticket_line,
                      original_order_line_id=order_line,
                      quantity=number(data.get("cantidad"), "cantidad", lo=1, hi=20, integer=True),
                      return_reason=field(data, "motivo", max_len=200),
                      refund_method=one_of(data.get("metodo_reembolso"), REFUND_METHODS, "metodo_reembolso"),
                      cashier_id=req.user.employee_id, user_login=req.user.login,
                      notes=field(data, "notas", required=False, max_len=500))
    return _detail(row["return_id"], req.user)


@route("POST", "/devoluciones/{return_id}/estado", {"atencion", "tienda"})
def estado(req: Request):
    rid = an_id(req.params["return_id"], "return")
    _detail(rid, req.user)  # comprueba el ámbito
    status = one_of(req.json().get("estado"), ["Aceptada", "Rechazada", "Reembolsada"], "estado")
    db.call("[returns].usp_return_set_status", return_id=rid, new_status=status, user_login=req.user.login)
    return _detail(rid, req.user)


@route("GET", "/devoluciones", "auth")
def listado(req: Request):
    offset, size = page(req, 30, 200)
    user = req.user
    status = req.query.get("estado") or None
    channel = req.query.get("canal") or None
    customer = store = None
    if user.has("atencion", "direccion"):
        customer = an_id(req.query.get("cliente"), "customer", required=False)
    elif user.has("tienda", "cajero"):
        store = store_for(user, req.query.get("tienda"))
    elif "cliente" in user.roles and user.customer_id:
        customer = user.customer_id
    else:
        raise forbidden()
    online_store = store == "ONLINE"
    where = ("(? IS NULL OR h.return_status = ?) AND (? IS NULL OR h.return_channel = ?) AND (? IS NULL OR h.customer_id = ?) "
             "AND (? IS NULL OR h.store_id = ? OR (? = 1 AND h.return_channel = N'ONLINE'))")
    args = (status, status, channel, channel, customer, customer, store, store, 1 if online_store else 0)
    return {"total": db.scalar(f"SELECT COUNT(*) FROM [returns].return_header h WHERE {where}", *args),
            "devoluciones": db.query(f"""
                SELECT h.return_id, h.returned_at, h.return_channel, h.store_id, h.customer_id, h.original_order_id,
                       h.original_ticket_id, h.return_status,
                       (SELECT SUM(l.refund_amount) FROM [returns].return_line l WHERE l.return_id = h.return_id) AS importe
                FROM [returns].return_header h WHERE {where}
                ORDER BY h.returned_at DESC, h.return_id DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""", *args, offset, size)}


@route("GET", "/devoluciones/{return_id}", "auth")
def ver(req: Request):
    return _detail(an_id(req.params["return_id"], "return"), req.user)
