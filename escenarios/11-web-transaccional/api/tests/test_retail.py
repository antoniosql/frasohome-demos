"""Escenarios 1 a 5: compra online, TPV, devoluciones, inventario y catálogo."""
import uuid

from conftest import admin_sql

from fsh import cosmos, db


def available(store: str, minimum: int = 3, exclude: tuple = ()) -> list[str]:
    rows = db.query("""SELECT s.product_id FROM inventory.stock_level s JOIN catalog.product p ON p.product_id = s.product_id
                       WHERE s.store_id = ? AND s.on_hand_qty - s.reserved_qty >= ? AND p.product_status = N'Activo'
                       AND p.sale_price IS NOT NULL ORDER BY s.product_id""", store, minimum)
    return [r["product_id"] for r in rows if r["product_id"] not in exclude]


def stock(store: str, product: str) -> int:
    return db.scalar("SELECT on_hand_qty FROM inventory.stock_level WHERE store_id = ? AND product_id = ?", store, product)


def test_catalogo_publico(anon):
    r = anon.get("/catalogo/productos?categoria=Iluminación&tamano=5")
    assert r.status == 200 and r.json["total"] > 0 and len(r.json["productos"]) <= 5
    pid = r.json["productos"][0]["product_id"]
    detail = anon.get(f"/catalogo/productos/{pid}").json
    assert detail["product_id"] == pid and "stock" in detail and "opiniones" in detail
    assert anon.get("/catalogo/tiendas").json and anon.get("/catalogo/categorias").json
    ev = anon.post("/eventos", {"tipo_evento": "view_product", "page_type": "product_detail", "product_id": pid})
    assert ev.status == 200 and ev.json["session_id"].startswith("SE-")
    assert cosmos.read("eventos_web", ev.json["event_id"], ev.json["session_id"])["product_id"] == pid


def test_carrito_checkout_idempotente(as_role, people):
    c = as_role("cliente")
    p1, p2 = available("ONLINE")[:2]
    before = stock("ONLINE", p1)
    cart = c.put("/carrito", {"lineas": [{"product_id": p1, "cantidad": 2}, {"product_id": p2, "cantidad": 1}]})
    assert cart.status == 200 and cart.json["presupuesto"]["totales"]["net_total"] > 0
    assert c.get("/carrito").json["lineas"][0]["cantidad"] == 2
    body = {"direccion": "Calle Real 12", "codigo_postal": "15003", "ciudad": "A Coruña", "provincia": "A Coruña",
            "metodo_pago": "Tarjeta"}
    key = uuid.uuid4().hex
    first = c.post("/pedidos", body, idem=key)
    assert first.status == 200, first.json
    order = first.json["order_id"]
    again = c.post("/pedidos", body, idem=key)
    assert again.status == 200 and again.json["order_id"] == order and again.headers["Idempotent-Replayed"] == "true"
    assert stock("ONLINE", p1) == before - 2
    assert db.scalar("SELECT COUNT(*) FROM sales.online_order WHERE customer_id = ? AND order_id = ?", people["customer"], order) == 1
    assert c.get("/carrito").json["lineas"] == []
    # El evento de compra y la señal de identidad llegan a Cosmos por el outbox.
    assert db.scalar("SELECT COUNT(*) FROM app.outbox WHERE sent_at IS NULL") == 0
    session = first.json["resumen"]["session_id"]
    events = cosmos.query("eventos_web", "SELECT * FROM c WHERE c.order_id = @o", {"o": order}, pk=session)
    assert events and events[0]["tipo_evento"] == "purchase"
    assert c.get("/pedidos").json["pedidos"][0]["order_id"] == order
    # Cancelar el pedido pendiente devuelve el stock.
    assert c.post(f"/pedidos/{order}/cancelar").json["order_status"] == "Cancelado"
    assert stock("ONLINE", p1) == before


def test_checkout_con_cupon_y_errores_de_negocio(as_role, people):
    c = as_role("cliente")
    coupon = db.call_one("mkt.usp_coupon_issue_single", customer_id=people["customer"], coupon_type="importe_fijo", value=15,
                         valid_days=10, issue_channel="ATENCION", user_login="pytest")["coupon_code"]
    p = available("ONLINE")[0]
    bad = c.put("/carrito", {"lineas": [{"product_id": p, "cantidad": 1}], "cupon": "FSH20999999"})
    assert bad.status == 422 and bad.json["error"] == "El cupón no existe."
    body = {"lineas": [{"product_id": p, "cantidad": 1}], "cupon": coupon, "direccion": "Calle Real 12",
            "codigo_postal": "15003", "ciudad": "A Coruña", "provincia": "A Coruña", "metodo_pago": "Bizum"}
    r = c.post("/pedidos", body)
    assert r.status == 200 and r.json["resumen"]["discount_total"] >= 15
    assert db.scalar("SELECT coupon_status FROM mkt.coupon WHERE coupon_code = ?", coupon) == "canjeado"
    assert c.post("/pedidos", body).json["error"] == "El cupón ya no está disponible."
    assert c.post("/pedidos", {**body, "metodo_pago": "Cheque"}).status == 400


def test_tpv_ticket_mixto_devolucion_y_cierre(as_role, people):
    c = as_role("cajero")
    admin_sql("UPDATE store.till_session SET session_status = N'Cerrada' WHERE store_id = N'S001' AND till_id = N'CAJ08'")
    assert c.post("/tpv/caja/abrir", {"caja": "CAJ08", "efectivo_inicial": 150}).status == 200
    p = available("S001")[0]
    before = stock("S001", p)
    quote = c.post("/tpv/presupuesto", {"lineas": [{"product_id": p, "cantidad": 2}], "customer_id": people["customer2"]}).json
    total = quote["totales"]["net_total"]
    wrong = c.post("/tpv/tickets", {"caja": "CAJ08", "lineas": [{"product_id": p, "cantidad": 2}],
                                    "pagos": [{"metodo": "Efectivo", "importe": total - 1}]})
    assert wrong.status == 422 and "no cuadran" in wrong.json["error"]
    cash = round(total / 2, 2)
    t = c.post("/tpv/tickets", {"caja": "CAJ08", "customer_id": people["customer2"], "lineas": [{"product_id": p, "cantidad": 2}],
                                "pagos": [{"metodo": "Efectivo", "importe": cash}, {"metodo": "Tarjeta", "importe": round(total - cash, 2)}]})
    assert t.status == 200, t.json
    assert len(t.json["pagos"]) == 2 and t.json["cashier_employee_id"] == people["cashier"]
    assert t.json["cashier_id"].startswith("EMP")
    assert stock("S001", p) == before - 2
    line = t.json["lineas"][0]["ticket_line_id"]
    ret = c.post("/devoluciones/tienda", {"ticket_line_id": line, "cantidad": 1, "motivo": "Cambio de opinión",
                                          "metodo_reembolso": "Efectivo"})
    assert ret.status == 200 and ret.json["return_status"] == "Aceptada"
    assert stock("S001", p) == before - 1
    again = c.post("/devoluciones/tienda", {"ticket_line_id": line, "cantidad": 2, "motivo": "x", "metodo_reembolso": "Efectivo"})
    assert again.status == 422
    close = c.post("/tpv/caja/cerrar", {"caja": "CAJ08", "efectivo_contado": 150 + cash})
    assert close.status == 200 and float(close.json["expected_cash"]) == 150 + cash
    card = db.query("SELECT TOP 1 c.customer_id FROM crm.customer c WHERE c.customer_id = ?", people["customer2"])
    assert c.get(f"/tpv/clientes?q={people['customer2']}").json[0]["customer_id"] == card[0]["customer_id"]


def test_devolucion_online_y_resolucion(as_role, people):
    c = as_role("cliente")
    p = available("ONLINE")[0]
    order = c.post("/pedidos", {"lineas": [{"product_id": p, "cantidad": 2}], "direccion": "Calle Real 12", "codigo_postal": "15003",
                                "ciudad": "A Coruña", "provincia": "A Coruña", "metodo_pago": "Tarjeta"}).json
    almacen = as_role("almacen")
    for status in ("En preparación", "Entregado"):
        assert almacen.post(f"/pedidos/{order['order_id']}/estado", {"estado": status}).status == 200
    line = order["lineas"][0]["order_line_id"]
    ret = c.post("/devoluciones/online", {"order_id": order["order_id"], "order_line_id": line, "cantidad": 1,
                                          "motivo": "Defectuoso", "metodo": "Envío"})
    assert ret.status == 200 and ret.json["return_status"] == "Pendiente"
    before = stock("ONLINE", p)
    at = as_role("atencion")
    assert at.post(f"/devoluciones/{ret.json['return_id']}/estado", {"estado": "Aceptada"}).json["return_status"] == "Aceptada"
    assert stock("ONLINE", p) == before + 1
    assert at.post(f"/devoluciones/{ret.json['return_id']}/estado", {"estado": "Reembolsada"}).status == 200
    assert c.get(f"/pedidos/{order['order_id']}").json["order_status"] == "Devuelto Parcial"
    assert c.get("/devoluciones").json["total"] >= 1


def test_inventario(as_role):
    t = as_role("tienda")
    p = available("ONLINE", 10)[0]
    lvl = t.post("/inventario/ajustes", {"product_id": p, "delta": -1, "motivo": "Rotura en exposición"})
    assert lvl.status == 200
    before = lvl.json["on_hand_qty"]
    assert t.post("/inventario/reposiciones", {"product_id": p, "cantidad": 3}).json["in_transit_qty"] >= 3
    assert t.post("/inventario/recepciones", {"product_id": p, "cantidad": 3}).json["on_hand_qty"] == before + 3
    assert t.post("/inventario/minimos", {"product_id": p, "minimo": 999}).status == 400
    assert t.post("/inventario/minimos", {"product_id": p, "minimo": 500}).json["minimum_qty"] == 500
    assert any(a["product_id"] == p for a in t.get("/inventario/alertas").json)
    assert t.get("/inventario/movimientos").json[0]["product_id"] == p
    assert t.post("/inventario/ajustes", {"tienda": "S002", "product_id": p, "delta": 1, "motivo": "x"}).status == 403
    assert t.post("/inventario/cierre").status == 403
    assert as_role("admin").post("/inventario/cierre").json["rows_written"] > 0


def test_catalogo_y_tiendas_admin(as_role):
    a = as_role("admin")
    p = a.post("/admin/productos", {"nombre": "Lámpara de prueba", "categoria": "Iluminación", "precio": 59.9, "coste": 21})
    assert p.status == 200 and p.json["product_id"].startswith("P")
    assert a.put(f"/admin/productos/{p.json['product_id']}", {"nombre": "Lámpara de prueba", "categoria": "Iluminación",
                                                              "precio": 10, "coste": 21}).status == 422
    assert a.put("/admin/tiendas/S006", {"nombre": "FraSoHome Málaga Centro", "estado": "Planificada"}).status == 200
    assert a.get("/admin/alias-productos").json
