"""Escenario 1 (parte pública) · catálogo, tiendas, promociones y eventos de navegación."""
from __future__ import annotations

from datetime import datetime, timezone

from .. import cosmos, db
from ..util import an_id, field, like, one_of, page
from ..web import PUBLIC, Request, not_found, route

ORDERS = {"nombre": "p.product_name", "precio": "p.sale_price", "precio_desc": "p.sale_price DESC",
          "novedad": "p.catalog_start_date DESC"}
WEB_EVENTS = ["page_view", "category_view", "view_product", "search", "add_to_wishlist", "add_to_cart",
              "begin_checkout", "store_locator", "stock_check_store"]
PAGE_TYPES = ["home", "category_listing", "product_detail", "search_results", "cart", "checkout", "store_locator"]


@route("GET", "/catalogo/productos", PUBLIC)
def productos(req: Request):
    offset, size = page(req, 24, 100)
    order = ORDERS.get(req.query.get("orden", "nombre"), "p.product_name")
    q = like(req.query.get("q"))
    cat = req.query.get("categoria") or None
    sub = req.query.get("subcategoria") or None
    where = ("p.product_status = N'Activo' AND p.sale_price IS NOT NULL AND (? IS NULL OR p.product_name LIKE ? "
             "OR p.brand LIKE ? OR p.product_id = ?) AND (? IS NULL OR p.category = ?) AND (? IS NULL OR p.subcategory = ?)")
    args = (q, q, q, (req.query.get("q") or "").strip().upper(), cat, cat, sub, sub)
    total = db.scalar(f"SELECT COUNT(*) FROM catalog.product p WHERE {where}", *args)
    rows = db.query(f"""
        SELECT p.product_id, p.product_name, p.category, p.subcategory, p.brand, p.material, p.color, p.sale_price,
               ISNULL(s.on_hand_qty - s.reserved_qty, 0) AS disponible_online,
               (SELECT MAX(pr.discount_pct) FROM mkt.promotion pr
                 WHERE pr.promo_type = N'descuento_pct' AND SYSUTCDATETIME() BETWEEN pr.starts_at AND pr.ends_at
                   AND pr.scope_type = N'categoria' AND pr.scope_id = p.category) AS promo_pct
        FROM catalog.product p
        LEFT JOIN inventory.stock_level s ON s.store_id = N'ONLINE' AND s.product_id = p.product_id
        WHERE {where}
        ORDER BY {order}, p.product_id OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""", *args, offset, size)
    return {"total": total, "productos": rows}


@route("GET", "/catalogo/productos/{product_id}", PUBLIC)
def producto(req: Request):
    pid = an_id(req.params["product_id"], "product")
    row = db.one("""SELECT product_id, product_name, category, subcategory, brand, material, color, sale_price, vat_pct,
                           weight_kg, length_cm, width_cm, height_cm, product_status, ean
                    FROM catalog.product WHERE product_id = ?""", pid)
    if row is None:
        raise not_found("El producto no existe.")
    row["stock"] = db.query("""SELECT s.store_id, st.store_name, s.on_hand_qty - s.reserved_qty AS disponible
                               FROM inventory.stock_level s JOIN store.store st ON st.store_id = s.store_id
                               WHERE s.product_id = ? AND st.store_status = N'Activa' ORDER BY s.store_id""", pid)
    row["promociones"] = db.query("""SELECT promo_id, promo_name, promo_type, discount_pct, discount_eur, ends_at, store_id
                                     FROM mkt.promotion WHERE SYSUTCDATETIME() BETWEEN starts_at AND ends_at
                                       AND ((scope_type = N'categoria' AND scope_id = ?)
                                         OR (scope_type = N'categoria_tienda' AND scope_id LIKE ? + N'|%'))
                                     ORDER BY discount_pct DESC""", row["category"], row["category"])
    reviews = cosmos.query("feedback", "SELECT c.feedback_id, c.fecha_feedback, c.rating_1_5, c.texto_feedback, "
                           "c.respuesta_marca FROM c WHERE c.product_id = @p AND c.publicado_flag = true "
                           "ORDER BY c.fecha_feedback DESC", {"p": pid}, max_items=20)
    ratings = [r["rating_1_5"] for r in reviews if r.get("rating_1_5")]
    row["opiniones"] = {"media": round(sum(ratings) / len(ratings), 2) if ratings else None, "total": len(reviews),
                        "ultimas": reviews[:10]}
    return row


@route("GET", "/catalogo/categorias", PUBLIC)
def categorias(req: Request):
    return db.query("""SELECT category AS categoria, subcategory AS subcategoria, COUNT(*) AS productos
                       FROM catalog.product WHERE product_status = N'Activo' AND sale_price IS NOT NULL
                       GROUP BY category, subcategory ORDER BY category, subcategory""")


@route("GET", "/catalogo/tiendas", PUBLIC)
def tiendas(req: Request):
    return db.query("""SELECT store_id, store_name, city, province, address_line, postal_code, phone, opening_hours,
                              latitude, longitude, store_status, region
                       FROM store.store WHERE channel = N'FISICO' AND store_status IN (N'Activa', N'Planificada')
                       ORDER BY store_id""")


@route("GET", "/catalogo/promociones", PUBLIC)
def promociones(req: Request):
    return db.query("""SELECT promo_id, promo_name, starts_at, ends_at, scope_type, scope_id, promo_type, discount_pct,
                              discount_eur, channel, store_id, combinable, basket_threshold_eur
                       FROM mkt.promotion WHERE SYSUTCDATETIME() BETWEEN starts_at AND ends_at ORDER BY ends_at""")


@route("POST", "/eventos", PUBLIC)
def evento(req: Request):
    """Evento de navegación de la tienda online. Va directo a Cosmos (sin outbox): es efímero."""
    data = req.json()
    tipo = one_of(field(data, "tipo_evento"), WEB_EVENTS, "tipo_evento")
    session = field(data, "session_id", required=False, max_len=20)
    if session is None or not session.startswith("SE-"):
        session = cosmos.next_ids("web_session")[0]
    event_id = cosmos.next_ids("web_event")[0]
    customer = req.user.customer_id if req.user and "cliente" in req.user.roles else None
    product = an_id(data.get("product_id"), "product", required=False)
    store = an_id(data.get("store_id_interes"), "store", required=False)
    doc = {"id": event_id, "pk": session, "event_id": event_id,
           "fecha_hora_evento": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"), "session_id": session,
           "customer_id": customer, "cookie_id": None, "device_id": None, "usuario_online_id": None,
           "canal_adquisicion": one_of(data.get("canal_adquisicion", "direct"), ["direct", "crm", "paid_search", "paid_social"],
                                       "canal_adquisicion"),
           "utm_source": field(data, "utm_source", required=False, max_len=40) or "direct",
           "utm_medium": field(data, "utm_medium", required=False, max_len=40) or "(none)",
           "utm_campaign": field(data, "utm_campaign", required=False, max_len=30),
           "tipo_evento": tipo, "page_type": one_of(data.get("page_type", "home"), PAGE_TYPES, "page_type"),
           "product_id": product, "categoria": field(data, "categoria", required=False, max_len=100),
           "subcategoria": field(data, "subcategoria", required=False, max_len=100),
           "search_term": field(data, "search_term", required=False, max_len=100), "store_id_interes": store,
           "valor_evento_eur": 0.0, "order_id": None, "consent_analytics": bool(data.get("consent_analytics", False)),
           "logged_in_flag": customer is not None, "origen": "web"}
    cosmos.upsert_direct("eventos_web", doc)
    return {"session_id": session, "event_id": event_id}
