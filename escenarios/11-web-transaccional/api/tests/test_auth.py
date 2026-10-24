"""Sesión, contraseñas, bloqueo, CSRF, roles y ámbitos."""
from conftest import PASSWORD, Client, _drop_user, admin_sql
from fsh import db, usuarios


def test_salud_publica(anon):
    r = anon.get("/salud")
    assert r.status == 200 and r.json["sql"]["ok"] and r.json["cosmos"]["ok"]


def test_login_cookie_y_me(people):
    c = Client()
    r = c.post("/auth/login", {"login": "t.cliente", "password": PASSWORD})
    assert r.status == 200
    cookie = r.cookies[0]
    assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=Strict" in cookie
    assert "Domain=frasohome.dataging.com" in cookie          # hallazgo de la fase 0
    me = c.get("/auth/me").json["usuario"]
    assert me["roles"] == ["cliente"] and me["ambitos"]["customer"] == [people["customer"]]
    assert db.scalar("SELECT COUNT(*) FROM app.user_session s JOIN app.app_user u ON u.user_id = s.user_id "
                     "WHERE u.login = 't.cliente'") >= 1


def test_mensaje_generico_y_bloqueo(people):
    login = "t.bloqueo"
    _drop_user(login)
    usuarios.create(login, "Bloqueo", ["cliente"], {"customer": [people["customer"]]}, password=PASSWORD, must_change=False)
    try:
        c = Client()
        unknown = c.post("/auth/login", {"login": "no.existe", "password": "x" * 12})
        for _ in range(5):
            bad = c.post("/auth/login", {"login": login, "password": "incorrecta-123"})
            assert bad.status == 401
        assert bad.json["error"] == unknown.json["error"] == "Usuario o contraseña incorrectos."
        # Bloqueado: ni con la contraseña buena.
        assert c.post("/auth/login", {"login": login, "password": PASSWORD}).status == 401
        admin_sql("UPDATE app.app_user SET locked_until = DATEADD(SECOND, -1, SYSUTCDATETIME()) WHERE login = ?", login)
        assert c.post("/auth/login", {"login": login, "password": PASSWORD}).status == 200
    finally:
        _drop_user(login)


def test_cambio_obligatorio_de_contrasena(people):
    login = "t.nuevo"
    _drop_user(login)
    temp = usuarios.create(login, "Nuevo", ["marketing"], {})["contrasena_temporal"]
    try:
        c = Client()
        assert c.post("/auth/login", {"login": login, "password": temp}).json["usuario"]["debe_cambiar_contrasena"]
        assert c.get("/campanas").json["codigo"] == "cambiar_contrasena"
        weak = c.post("/auth/password", {"actual": temp, "nueva": "corta"})
        assert weak.status == 422
        ok = c.post("/auth/password", {"actual": temp, "nueva": "Una-Clave-Nueva-2026"})
        assert ok.status == 200 and ok.cookies
        assert c.get("/campanas").status == 200
        assert Client().post("/auth/login", {"login": login, "password": temp}).status == 401
    finally:
        _drop_user(login)


def test_logout_invalida_la_sesion(people):
    c = Client()
    c.login("t.marketing")
    token = c.cookie
    assert c.post("/auth/logout").status == 200
    other = Client()
    other.cookie = token
    assert other.get("/campanas").status == 401


def test_sesion_caducada(people):
    c = Client()
    c.login("t.atencion")
    admin_sql("UPDATE s SET expires_at = DATEADD(SECOND, -1, SYSUTCDATETIME()) FROM app.user_session s "
              "JOIN app.app_user u ON u.user_id = s.user_id WHERE u.login = 't.atencion'")
    assert c.get("/clientes").status == 401


def test_csrf_obligatorio_en_escrituras(as_role):
    c = as_role("cliente")
    r = c.request("PUT", "/carrito", {"lineas": []}, csrf=False)
    assert r.status == 403 and r.json["codigo"] == "csrf"


def test_rol_y_ambito(as_role, people):
    cliente = as_role("cliente")
    assert cliente.get("/clientes").status == 403                  # CRM solo atención y marketing
    other = db.scalar("SELECT TOP 1 order_id FROM sales.online_order WHERE customer_id <> ? ORDER BY order_id", people["customer"])
    assert cliente.get(f"/pedidos/{other}").status == 404          # pedido ajeno: no existe para él
    cajero = as_role("cajero")
    assert cajero.get("/tpv/caja?tienda=S002").status == 403       # otra tienda
    manager = as_role("manager")
    assert manager.get(f"/rrhh/empleados/{people['outsider']}").status == 403
    assert manager.get(f"/rrhh/empleados/{people['report']}").status == 200
    assert "compensacion" not in manager.get(f"/rrhh/empleados/{people['report']}").json


def test_ruta_inexistente_y_metodo(anon):
    assert anon.get("/no/existe").status == 404
    assert anon.request("DELETE", "/salud").status == 405
