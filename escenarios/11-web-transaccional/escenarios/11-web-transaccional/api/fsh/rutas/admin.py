"""Escenarios 5 y 15 · catálogo y tiendas, y administración de datos: usuarios y roles,
rechazos de la carga, metadatos, outbox y auditoría."""
from __future__ import annotations

from .. import cosmos, db, usuarios
from ..util import a_date, an_id, field, flag, number, one_of, page
from ..web import Request, not_found, route

ADMIN = {"admin"}
PRODUCT_FIELDS = """product_id, product_name, category, subcategory, brand, supplier, material, color, sale_price, unit_cost,
                    vat_pct, weight_kg, length_cm, width_cm, height_cm, catalog_start_date, product_status, ean, updated_at"""


# ------------------------------------------------------------------ catálogo y tiendas

@route("GET", "/admin/productos", ADMIN)
def productos(req: Request):
    offset, size = page(req, 50, 200)
    status = req.query.get("estado") or None
    return db.query(f"""SELECT {PRODUCT_FIELDS} FROM catalog.product WHERE (? IS NULL OR product_status = ?)
                        ORDER BY product_id OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""", status, status, offset, size)


def _product(data: dict, product_id: str | None, login: str) -> dict:
    row = db.call_one(
        "catalog.usp_product_upsert", product_id=product_id, product_name=field(data, "nombre", max_len=255),
        category=one_of(data.get("categoria"), ["Muebles", "Decoración", "Iluminación", "Textil hogar"], "categoria"),
        subcategory=field(data, "subcategoria", required=False, max_len=100), brand=field(data, "marca", required=False, max_len=100),
        supplier=field(data, "proveedor", required=False, max_len=100), material=field(data, "material", required=False, max_len=100),
        color=field(data, "color", required=False, max_len=100), sale_price=number(data.get("precio"), "precio", lo=0.01, hi=100_000),
        unit_cost=number(data.get("coste"), "coste", lo=0, hi=100_000, required=False),
        vat_pct=number(data.get("iva", 21), "iva", lo=0, hi=21), weight_kg=number(data.get("peso_kg"), "peso_kg", lo=0, hi=2000, required=False),
        length_cm=number(data.get("largo_cm"), "largo_cm", lo=0, hi=1000, required=False),
        width_cm=number(data.get("ancho_cm"), "ancho_cm", lo=0, hi=1000, required=False),
        height_cm=number(data.get("alto_cm"), "alto_cm", lo=0, hi=1000, required=False),
        product_status=one_of(data.get("estado", "Activo"), ["Activo", "Descatalogado"], "estado"),
        ean=field(data, "ean", required=False, max_len=13), user_login=login)
    return db.one(f"SELECT {PRODUCT_FIELDS} FROM catalog.product WHERE product_id = ?", row["product_id"])


@route("POST", "/admin/productos", ADMIN)
def alta_producto(req: Request):
    return _product(req.json(), None, req.user.login)


@route("PUT", "/admin/productos/{product_id}", ADMIN)
def editar_producto(req: Request):
    return _product(req.json(), an_id(req.params["product_id"], "product"), req.user.login)


@route("PUT", "/admin/tiendas/{store_id}", ADMIN)
def editar_tienda(req: Request):
    sid = an_id(req.params["store_id"], "store")
    d = req.json()
    db.call("store.usp_store_update", store_id=sid, store_name=field(d, "nombre", max_len=150),
            opening_hours=field(d, "horario", required=False, max_len=100), phone=field(d, "telefono", required=False, max_len=50),
            manager_name=field(d, "gerente", required=False, max_len=150),
            store_status=one_of(d.get("estado"), ["Activa", "Planificada", "Cerrada"], "estado"),
            opened_at=a_date(d.get("apertura"), "apertura", required=False), user_login=req.user.login)
    return db.one("SELECT * FROM store.store WHERE store_id = ?", sid)


@route("GET", "/admin/alias-productos", ADMIN | {"profesor"})
def alias_productos(req: Request):
    return db.query("""SELECT a.source_system, a.source_product_id, a.source_product_name, a.canonical_product_id,
                              p.product_name AS canonical_product_name, a.match_method, a.confidence, a.note
                       FROM xref.product_alias a LEFT JOIN catalog.product p ON p.product_id = a.canonical_product_id
                       ORDER BY a.source_product_id""")


# ------------------------------------------------------------------ usuarios

@route("GET", "/admin/usuarios", ADMIN)
def usuarios_lista(req: Request):
    return usuarios.listing()


@route("POST", "/admin/usuarios", ADMIN)
def usuario_alta(req: Request):
    d = req.json()
    roles = d.get("roles") or []
    scopes = d.get("ambitos") or {}
    if not isinstance(roles, list) or not isinstance(scopes, dict):
        from ..web import bad_request
        raise bad_request("«roles» es una lista y «ambitos» un objeto {customer|employee|store: [...]}.")
    return usuarios.create(field(d, "login", max_len=50), field(d, "nombre", max_len=200), roles,
                           {k: v if isinstance(v, list) else [v] for k, v in scopes.items()}, actor=req.user.login)


@route("POST", "/admin/usuarios/{login}/reset", ADMIN)
def usuario_reset(req: Request):
    return usuarios.reset_password(req.params["login"], actor=req.user.login)


@route("POST", "/admin/usuarios/{login}/activo", ADMIN)
def usuario_activo(req: Request):
    usuarios.set_active(req.params["login"], flag(req.json().get("activo")), actor=req.user.login)
    return {"ok": True}


@route("POST", "/admin/usuarios/{login}/roles", ADMIN)
def usuario_rol(req: Request):
    d = req.json()
    usuarios.set_role(req.params["login"], field(d, "rol", max_len=30), flag(d.get("conceder"), True), actor=req.user.login)
    return {"ok": True}


@route("POST", "/admin/usuarios/{login}/ambitos", ADMIN)
def usuario_ambito(req: Request):
    d = req.json()
    usuarios.set_scope(req.params["login"], field(d, "tipo", max_len=20), field(d, "valor", max_len=50),
                       flag(d.get("conceder"), True), actor=req.user.login)
    return {"ok": True}


# ------------------------------------------------------------------ calidad, metadatos, outbox, auditoría

@route("GET", "/admin/calidad/resumen", ADMIN | {"profesor"})
def calidad_resumen(req: Request):
    return db.query("""SELECT source_schema, source_table, source_file, issue_severity, issue_type, COUNT(*) AS filas
                       FROM quality.data_quality_issue GROUP BY source_schema, source_table, source_file, issue_severity, issue_type
                       ORDER BY source_file, issue_severity, filas DESC""")


@route("GET", "/admin/calidad", ADMIN | {"profesor"})
def calidad(req: Request):
    offset, size = page(req, 50, 500)
    table = req.query.get("tabla") or None
    sev = req.query.get("gravedad") or None
    kind = req.query.get("tipo") or None
    where = "(? IS NULL OR source_table = ?) AND (? IS NULL OR issue_severity = ?) AND (? IS NULL OR issue_type = ?)"
    args = (table, table, sev, sev, kind, kind)
    return {"total": db.scalar(f"SELECT COUNT(*) FROM quality.data_quality_issue WHERE {where}", *args),
            "incidencias": db.query(f"""SELECT issue_id, source_schema, source_table, source_file, source_key, issue_type,
                                              issue_severity, issue_description, source_row, detected_at
                                       FROM quality.data_quality_issue WHERE {where}
                                       ORDER BY issue_id OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""", *args, offset, size)}


@route("GET", "/admin/metadatos", ADMIN | {"profesor"})
def metadatos(req: Request):
    return db.query("""SELECT f.file_path, f.description, f.column_list, f.has_bom,
                              (SELECT COUNT(*) FROM meta.reference_row r WHERE r.file_path = f.file_path) AS filas
                       FROM meta.reference_file f ORDER BY f.file_path""")


@route("GET", "/admin/metadatos/filas", ADMIN | {"profesor"})
def metadatos_filas(req: Request):
    path = field(req.query, "fichero", max_len=260)
    if not db.scalar("SELECT 1 FROM meta.reference_file WHERE file_path = ?", path):
        raise not_found("Ese fichero de metadatos no existe.")
    import json
    rows = db.query("SELECT row_num, row_json FROM meta.reference_row WHERE file_path = ? ORDER BY row_num", path)
    return [{"fila": r["row_num"], **json.loads(r["row_json"])} for r in rows]


@route("GET", "/admin/outbox", ADMIN)
def outbox(req: Request):
    return {"pendientes": db.scalar("SELECT COUNT(*) FROM app.outbox WHERE sent_at IS NULL"),
            "fallidos": db.query("""SELECT TOP 50 outbox_id, container_name, operation, created_at, attempts, last_error
                                    FROM app.outbox WHERE sent_at IS NULL AND attempts > 0 ORDER BY outbox_id""")}


@route("POST", "/admin/outbox/reintentar", ADMIN)
def outbox_retry(req: Request):
    reset = db.call_one("app.usp_outbox_retry", user_login=req.user.login)
    sent = cosmos.flush(limit=500)
    return {"reiniciados": reset.get("rows_reset", 0), **sent}


@route("GET", "/admin/auditoria", ADMIN)
def auditoria(req: Request):
    offset, size = page(req, 50, 500)
    who = req.query.get("usuario") or None
    return db.query("""SELECT audit_id, logged_at, user_login, action_name, entity_name, entity_id, detail
                       FROM app.audit_log WHERE (? IS NULL OR user_login = ?)
                       ORDER BY audit_id DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""", who, who, offset, size)
