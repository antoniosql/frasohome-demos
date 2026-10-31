"""Escenario 2 · venta en tienda (TPV): caja, ticket con cobro mixto y cliente por tarjeta."""
from __future__ import annotations

from datetime import date

from .. import cosmos, db
from ..auth import User, store_for
from ..util import a_date, an_id, field, like, lines, number
from ..web import HttpError, Request, bad_request, forbidden, not_found, route
from .pedidos import quote

STORE_PAYMENTS = ["Tarjeta", "Efectivo", "Bizum", "Tarjeta regalo", "Vale", "Cupón", "Financiación"]


def _cashier(user: User) -> str:
    emp = user.employee_id
    if not emp:
        raise forbidden("Tu usuario de caja no está asociado a un empleado.")
    return emp


@route("GET", "/tpv/caja", {"cajero", "tienda"})
def caja(req: Request):
    store = store_for(req.user, req.query.get("tienda"))
    return db.query("""SELECT ts.till_session_id, ts.till_id, ts.cashier_id, e.full_name AS cajero, ts.opened_at, ts.opening_cash,
                              (SELECT COUNT(*) FROM sales.pos_ticket t WHERE t.till_session_id = ts.till_session_id) AS tickets,
                              (SELECT ISNULL(SUM(t.ticket_net_amount), 0) FROM sales.pos_ticket t
                                WHERE t.till_session_id = ts.till_session_id) AS ventas
                       FROM store.till_session ts LEFT JOIN hr.employee e ON e.employee_id = ts.cashier_id
                       WHERE ts.store_id = ? AND ts.session_status = N'Abierta' ORDER BY ts.till_id""", store)


@route("POST", "/tpv/caja/abrir", {"cajero"})
def abrir(req: Request):
    data = req.json()
    store = store_for(req.user, data.get("tienda"))
    till = an_id(data.get("caja"), "till", "caja")
    row = db.call_one("store.usp_till_open", store_id=store, till_id=till, cashier_id=_cashier(req.user),
                      opening_cash=number(data.get("efectivo_inicial", 0), "efectivo_inicial", lo=0, hi=5000))
    return {"till_session_id": row["till_session_id"], "tienda": store, "caja": till}


@route("POST", "/tpv/caja/cerrar", {"cajero"})
def cerrar(req: Request):
    data = req.json()
    store = store_for(req.user, data.get("tienda"))
    till = an_id(data.get("caja"), "till", "caja")
    session = db.scalar("SELECT till_session_id FROM store.till_session WHERE store_id = ? AND till_id = ? "
                        "AND session_status = N'Abierta'", store, till)
    if session is None:
        raise HttpError(422, "Esa caja no está abierta.", "estado")
    return db.call_one("store.usp_till_close", till_session_id=session,
                       counted_cash=number(data.get("efectivo_contado"), "efectivo_contado", lo=0, hi=100_000))


@route("POST", "/tpv/presupuesto", {"cajero"})
def presupuesto(req: Request):
    data = req.json()
    store = store_for(req.user, data.get("tienda"))
    return quote(store, an_id(data.get("customer_id"), "customer", required=False), lines(data),
                 field(data, "cupon", required=False, max_len=30))


@route("POST", "/tpv/tickets", {"cajero"}, idempotent=True)
def ticket(req: Request):
    data = req.json()
    store = store_for(req.user, data.get("tienda"))
    pays = data.get("pagos")
    if not isinstance(pays, list) or not pays or len(pays) > 5:
        raise bad_request("«pagos» debe ser una lista de 1 a 5 cobros.")
    payments = []
    for i, p in enumerate(pays, start=1):
        if not isinstance(p, dict):
            raise bad_request(f"El cobro {i} no es un objeto.")
        method = p.get("metodo")
        if method not in STORE_PAYMENTS:
            raise bad_request(f"Método de cobro {i} no válido: {', '.join(STORE_PAYMENTS)}.")
        payments.append({"payment_method": method, "amount": number(p.get("importe"), f"pagos[{i}].importe", lo=0.01, hi=50_000),
                         "reference": field(p, "referencia", required=False, max_len=100)})
    row = db.call_one("sales.usp_pos_ticket", store_id=store, till_id=an_id(data.get("caja"), "till", "caja"),
                      cashier_id=_cashier(req.user), customer_id=an_id(data.get("customer_id"), "customer", required=False),
                      lines_json=lines(data), payments_json=payments,
                      coupon_code=field(data, "cupon", required=False, max_len=30), user_login=req.user.login)
    return _ticket(row["ticket_id"], req.user) | {"resumen": row}


def _ticket(ticket_id: str, user: User) -> dict:
    t = db.one("""SELECT t.ticket_id, t.ticket_at, t.store_id, t.till_id, t.cashier_id, t.cashier_employee_id, t.customer_id,
                         t.ticket_gross_amount, t.ticket_discount_amount, t.ticket_net_amount, t.coupon_instance_id
                  FROM sales.pos_ticket t WHERE t.ticket_id = ?""", ticket_id)
    if t is None or not (user.has("atencion", "direccion") or t["store_id"] in user.stores):
        raise not_found("El ticket no existe en tu tienda.")
    t["lineas"] = db.query("""SELECT ticket_line_id, product_id, product_description, quantity, unit_price, discount_amount,
                                     line_amount, promo_id,
                                     quantity - [returns].fn_returned_qty(NULL, ticket_line_id) AS devolvible
                              FROM sales.pos_ticket_line WHERE ticket_id = ? ORDER BY ticket_line_id""", ticket_id)
    t["pagos"] = db.query("""SELECT payment_id, payment_method, paid_amount, authorization_reference, payment_status
                             FROM sales.store_payment WHERE ticket_id = ? ORDER BY payment_id""", ticket_id)
    return t


@route("GET", "/tpv/tickets", {"cajero", "tienda"})
def tickets(req: Request):
    store = store_for(req.user, req.query.get("tienda"))
    day = a_date(req.query.get("fecha"), "fecha", required=False) or date.today()
    return db.query("""SELECT ticket_id, ticket_at, till_id, cashier_id, customer_id, ticket_net_amount,
                              (SELECT COUNT(*) FROM sales.pos_ticket_line l WHERE l.ticket_id = t.ticket_id) AS lineas
                       FROM sales.pos_ticket t WHERE store_id = ? AND CAST(ticket_at AS DATE) = ?
                       ORDER BY ticket_at DESC""", store, day)


@route("GET", "/tpv/tickets/{ticket_id}", {"cajero", "tienda", "atencion"})
def ver_ticket(req: Request):
    return _ticket(an_id(req.params["ticket_id"], "ticket"), req.user)


@route("GET", "/tpv/pedidos/{order_id}", {"cajero", "atencion"})
def pedido_online(req: Request):
    """Pedido online, para devolver en tienda una compra online: líneas y unidades que quedan por devolver."""
    oid = an_id(req.params["order_id"], "order")
    order = db.one("""SELECT order_id, ordered_at, customer_id, order_status, order_total
                      FROM sales.online_order WHERE order_id = ?""", oid)
    if order is None:
        raise not_found("El pedido no existe.")
    order["lineas"] = db.query("""SELECT l.order_line_id, l.product_id, l.product_description, l.quantity, l.unit_price, l.line_amount,
                                         l.quantity - [returns].fn_returned_qty(l.order_line_id, NULL) AS devolvible
                                  FROM sales.online_order_line l WHERE l.order_id = ? ORDER BY l.order_line_id""", oid)
    return order


@route("GET", "/tpv/clientes", {"cajero", "atencion"})
def buscar_cliente(req: Request):
    """Cliente por tarjeta de fidelización (señales de Cosmos), id, email o teléfono."""
    card = (req.query.get("tarjeta") or "").strip().upper()
    if card:
        hits = cosmos.query("senales_identidad", "SELECT VALUE c.customer_id_candidato FROM c "
                            "WHERE c.tarjeta_fidelizacion_id = @t", {"t": card}, max_items=50)
        ids = sorted({h for h in hits if h})[:5]
        if not ids:
            return []
        marks = ",".join("?" * len(ids))
        return db.query(f"""SELECT customer_id, first_name, last_name, loyalty_tier, loyalty_points, customer_status
                            FROM crm.customer WHERE customer_id IN ({marks})""", *ids)
    q = (req.query.get("q") or "").strip()
    if len(q) < 3:
        raise bad_request("Escribe al menos 3 caracteres o pasa «tarjeta».")
    pattern = like(q)
    digits = "".join(ch for ch in q if ch.isdigit())
    return db.query("""SELECT TOP 10 customer_id, first_name, last_name, email, loyalty_tier, loyalty_points, customer_status
                       FROM crm.customer
                       WHERE customer_id = ? OR email LIKE ? OR (LEN(?) >= 6 AND REPLACE(REPLACE(phone, N' ', N''), N'-', N'') LIKE N'%' + ? + N'%')
                          OR (first_name + N' ' + last_name) LIKE ?
                       ORDER BY customer_id""", q.upper(), pattern, digits, digits, pattern)
