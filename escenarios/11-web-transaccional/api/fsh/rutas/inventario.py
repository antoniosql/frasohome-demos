"""Escenario 4 · inventario y reposición: stock vivo, ajustes, tránsito, cierre diario y alertas."""
from __future__ import annotations

from .. import db
from ..auth import store_for
from ..util import a_date, an_id, field, like, number, page
from ..web import Request, route

ROLES = {"tienda"}


@route("GET", "/inventario/stock", ROLES)
def stock(req: Request):
    store = store_for(req.user, req.query.get("tienda"))
    offset, size = page(req, 50, 200)
    q = like(req.query.get("q"))
    low = 1 if req.query.get("bajo_minimo") in ("1", "true") else 0
    cat = req.query.get("categoria") or None
    where = ("s.store_id = ? AND (? IS NULL OR p.product_name LIKE ? OR p.product_id = ?) AND (? IS NULL OR p.category = ?) "
             "AND (? = 0 OR s.on_hand_qty - s.reserved_qty <= s.minimum_qty)")
    args = (store, q, q, (req.query.get("q") or "").strip().upper(), cat, cat, low)
    return {"tienda": store,
            "total": db.scalar(f"SELECT COUNT(*) FROM inventory.stock_level s JOIN catalog.product p ON p.product_id = s.product_id WHERE {where}", *args),
            "stock": db.query(f"""
                SELECT s.product_id, p.product_name, p.category, s.on_hand_qty, s.reserved_qty, s.in_transit_qty,
                       s.on_hand_qty - s.reserved_qty AS disponible, s.minimum_qty, s.updated_at
                FROM inventory.stock_level s JOIN catalog.product p ON p.product_id = s.product_id
                WHERE {where} ORDER BY p.product_name OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""", *args, offset, size)}


def _target(req: Request) -> tuple[str, str, dict]:
    data = req.json()
    return store_for(req.user, data.get("tienda")), an_id(data.get("product_id"), "product"), data


def _level(store: str, product: str) -> dict:
    return db.one("""SELECT store_id, product_id, on_hand_qty, reserved_qty, in_transit_qty, minimum_qty,
                            on_hand_qty - reserved_qty AS disponible
                     FROM inventory.stock_level WHERE store_id = ? AND product_id = ?""", store, product) or {}


@route("POST", "/inventario/ajustes", ROLES)
def ajuste(req: Request):
    store, product, data = _target(req)
    db.call("inventory.usp_stock_adjust", store_id=store, product_id=product,
            delta=number(data.get("delta"), "delta", lo=-500, hi=500, integer=True),
            reason=field(data, "motivo", max_len=300), user_login=req.user.login)
    return _level(store, product)


@route("POST", "/inventario/reposiciones", ROLES)
def reposicion(req: Request):
    store, product, data = _target(req)
    db.call("inventory.usp_stock_replenish", store_id=store, product_id=product,
            quantity=number(data.get("cantidad"), "cantidad", lo=1, hi=500, integer=True), user_login=req.user.login)
    return _level(store, product)


@route("POST", "/inventario/recepciones", ROLES)
def recepcion(req: Request):
    store, product, data = _target(req)
    db.call("inventory.usp_stock_receive", store_id=store, product_id=product,
            quantity=number(data.get("cantidad"), "cantidad", lo=1, hi=500, integer=True), user_login=req.user.login)
    return _level(store, product)


@route("POST", "/inventario/minimos", ROLES)
def minimo(req: Request):
    store, product, data = _target(req)
    db.call("inventory.usp_stock_set_minimum", store_id=store, product_id=product,
            minimum=number(data.get("minimo"), "minimo", lo=0, hi=500, integer=True), user_login=req.user.login)
    return _level(store, product)


@route("POST", "/inventario/cierre", {"admin"})
def cierre(req: Request):
    """Cierre diario: fotografía el stock vivo de todas las tiendas en el histórico."""
    data = req.json()
    return db.call_one("inventory.usp_stock_close_day", snapshot_date=a_date(data.get("fecha"), "fecha", required=False),
                       user_login=req.user.login)


@route("GET", "/inventario/alertas", ROLES)
def alertas(req: Request):
    """Productos con disponible por debajo del mínimo y unidades vendidas en los últimos 7 días."""
    store = store_for(req.user, req.query.get("tienda"))
    return db.query("""
        SELECT s.product_id, p.product_name, p.category, s.on_hand_qty - s.reserved_qty AS disponible, s.minimum_qty,
               s.in_transit_qty,
               ISNULL((SELECT SUM(l.quantity) FROM sales.pos_ticket_line l JOIN sales.pos_ticket t ON t.ticket_id = l.ticket_id
                       WHERE t.store_id = s.store_id AND l.product_id = s.product_id
                         AND t.ticket_at >= DATEADD(DAY, -7, SYSUTCDATETIME())), 0)
             + ISNULL((SELECT SUM(l.quantity) FROM sales.online_order_line l JOIN sales.online_order o ON o.order_id = l.order_id
                       WHERE s.store_id = N'ONLINE' AND l.product_id = s.product_id AND o.order_status <> N'Cancelado'
                         AND o.ordered_at >= DATEADD(DAY, -7, SYSUTCDATETIME())), 0) AS vendidas_7d,
               CASE WHEN s.on_hand_qty - s.reserved_qty <= 0 THEN N'Alta' ELSE N'Media' END AS prioridad
        FROM inventory.stock_level s JOIN catalog.product p ON p.product_id = s.product_id
        WHERE s.store_id = ? AND p.product_status = N'Activo' AND s.on_hand_qty - s.reserved_qty <= s.minimum_qty
        ORDER BY CASE WHEN s.on_hand_qty - s.reserved_qty <= 0 THEN 0 ELSE 1 END, p.product_name""", store)


@route("GET", "/inventario/movimientos", ROLES)
def movimientos(req: Request):
    store = store_for(req.user, req.query.get("tienda"))
    product = an_id(req.query.get("product_id"), "product", required=False)
    offset, size = page(req, 50, 200)
    return db.query("""SELECT movement_id, moved_at, product_id, movement_type, on_hand_delta, reserved_delta, in_transit_delta,
                              document_type, document_id, user_login, notes
                       FROM inventory.stock_movement WHERE store_id = ? AND (? IS NULL OR product_id = ?)
                       ORDER BY movement_id DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""", store, product, product, offset, size)
