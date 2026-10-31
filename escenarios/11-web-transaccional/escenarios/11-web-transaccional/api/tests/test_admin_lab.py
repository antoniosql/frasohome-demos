"""Escenarios 15 y 16: administración de datos y usuarios, laboratorio docente, y tools/users.py."""
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

from conftest import PASSWORD, Client, _drop_user
from fsh import db

USERS_PY = Path(__file__).resolve().parents[2] / "tools" / "users.py"


def test_usuarios_desde_administracion(as_role):
    admin = as_role("admin")
    login = f"t.alta.{uuid.uuid4().hex[:6]}"
    try:
        _alta_desde_admin(admin, login)
    finally:
        _delete(login)
    assert as_role("marketing").get("/admin/usuarios").status == 403


def _alta_desde_admin(admin, login):
    r = admin.post("/admin/usuarios", {"login": login, "nombre": "Alta desde admin", "roles": ["cajero"],
                                       "ambitos": {"store": "S002"}})
    assert r.status == 200, r.json
    temp = r.json["contrasena_temporal"]
    assert len(temp) >= 16
    # Primer acceso: solo puede cambiar la contraseña.
    u = Client()
    assert u.login(login, temp).json["usuario"]["debe_cambiar_contrasena"] is True
    assert u.get("/tpv/caja").status == 403
    assert u.post("/auth/password", {"actual": temp, "nueva": PASSWORD + "!x"}).status == 200
    assert u.get("/tpv/caja").status in (200, 404)
    assert admin.post(f"/admin/usuarios/{login}/roles", {"rol": "tienda", "conceder": True}).status == 200
    assert admin.post(f"/admin/usuarios/{login}/ambitos", {"tipo": "store", "valor": "S999", "conceder": True}).status in (400, 422)
    listed = {x["login"]: x for x in admin.get("/admin/usuarios").json}
    assert set(listed[login]["roles"]) >= {"cajero", "tienda"}
    assert admin.post(f"/admin/usuarios/{login}/activo", {"activo": False}).status == 200
    assert u.get("/auth/me").status == 401                 # desactivar cierra sus sesiones
    reset = admin.post(f"/admin/usuarios/{login}/reset").json
    assert reset["contrasena_temporal"] != temp


def test_calidad_metadatos_outbox_y_catalogo(as_role):
    admin = as_role("admin")
    summary = admin.get("/admin/calidad/resumen").json
    assert summary
    rows = admin.get("/admin/calidad?gravedad=rechazo&tamano=20").json
    assert rows["total"] > 0 and all(r["issue_severity"] == "rechazo" for r in rows["incidencias"])
    files = admin.get("/admin/metadatos").json
    assert len(files) == 7
    first = files[0]["file_path"]
    assert admin.get(f"/admin/metadatos/filas?fichero={first}").status == 200
    assert isinstance(admin.get("/admin/outbox").json, (list, dict))
    assert admin.post("/admin/outbox/reintentar").status == 200
    assert admin.get("/admin/auditoria").status == 200
    assert admin.get("/admin/alias-productos").json
    # Catálogo: alta, cambio de precio y tienda.
    p = admin.post("/admin/productos", {"nombre": "Lámpara prueba", "categoria": "Iluminación", "subcategoria": "Lámparas mesa",
                                        "precio": 49.9, "coste": 21.5, "iva": 21})
    assert p.status == 200, p.json
    pid = p.json["product_id"]
    upd = admin.put(f"/admin/productos/{pid}", {"nombre": "Lámpara prueba", "categoria": "Iluminación", "precio": 44.9,
                                                 "coste": 21.5, "estado": "Descatalogado"})
    assert upd.status == 200 and upd.json["product_status"] == "Descatalogado"
    assert admin.get("/admin/productos?estado=Descatalogado").status == 200
    store = admin.put("/admin/tiendas/S006", {"estado": "Planificada", "nombre": "FraSoHome Málaga Centro"})
    assert store.status in (200, 400), store.json


def test_laboratorio(as_role):
    prof = as_role("profesor")
    ev = prof.get("/lab/identidad/evaluacion")
    assert ev.status == 200 and ev.json
    cases = prof.get("/lab/rag/casos?juego=Documental").json
    assert len(cases) >= 10
    new = prof.post("/lab/rag/casos", {"juego": "Documental", "pregunta": "¿Prueba?", "respuesta": "Sí"})
    assert new.status == 200, new.json
    row = new.json["row_num"]
    assert prof.put(f"/lab/rag/casos/Documental/{row}", {"pregunta": "¿Prueba editada?", "respuesta": "Sí"}).status == 200
    assert prof.delete(f"/lab/rag/casos/Documental/{row}").status == 200
    assert prof.get("/lab/prompts").json and prof.get("/lab/backlog").json
    for table in ("clientes", "productos", "tiendas", "stock", "devoluciones"):
        r = prof.get(f"/lab/rag/tablas/{table}")
        assert r.status in (200, 404), table
    assert prof.get("/lab/rag/tablas/nada").status in (400, 404)
    assert as_role("marketing").get("/lab/identidad/evaluacion").status == 403


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(USERS_PY), *args], capture_output=True, text=True,
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=120)


def _delete(login: str) -> None:
    _drop_user(login)


def test_users_py():
    login = f"t.cli.{uuid.uuid4().hex[:6]}"
    try:
        _cli(login)
    finally:
        _delete(login)


def _cli(login):
    r = _run("add", "--login", login, "--nombre", "Prueba CLI", "--rol", "cajero", "--tienda", "S001")
    assert r.returncode == 0, r.stderr
    temp = re.search(r"Contraseña temporal[^:]*: (\S+)", r.stdout)
    assert temp, r.stdout
    assert Client().login(login, temp.group(1)).json["usuario"]["debe_cambiar_contrasena"] is True
    assert login in _run("list").stdout
    assert _run("add-role", "--login", login, "--rol", "tienda").returncode == 0
    assert _run("disable", "--login", login).returncode == 0
    assert db.scalar("SELECT is_active FROM app.app_user WHERE login = ?", login) is False or \
        db.scalar("SELECT is_active FROM app.app_user WHERE login = ?", login) == 0
    assert _run("enable", "--login", login).returncode == 0
    reset = _run("reset", "--login", login)
    assert reset.returncode == 0 and "contraseña temporal" in reset.stdout.lower()
    bad = _run("add", "--login", login, "--nombre", "Otra vez", "--rol", "cajero")
    assert bad.returncode != 0
    wrong = _run("add", "--login", "t.x" + uuid.uuid4().hex[:4], "--nombre", "X", "--rol", "superusuario")
    assert wrong.returncode != 0
