"""Escenario 14 · paneles operativos de dirección (solo lectura): ventas, ficha 360 de cliente y de
empleado, rotación mensual y comentarios de clima y salida."""
from __future__ import annotations

from datetime import date, timedelta

from .. import cosmos, db
from ..util import a_date, an_id
from ..web import Request, bad_request, route
from .clientes import ficha as ficha_cliente
from .rrhh import ficha as ficha_empleado

ROLES = {"direccion"}


@route("GET", "/paneles/ventas", ROLES)
def ventas(req: Request):
    until = a_date(req.query.get("hasta"), "hasta", required=False) or date.today()
    since = a_date(req.query.get("desde"), "desde", required=False) or until - timedelta(days=30)
    if (until - since).days > 800:
        raise bad_request("Como mucho 800 días.")
    days = db.query("""
        WITH online AS (
            SELECT CAST(ordered_at AS DATE) AS dia, COUNT(*) AS documentos, SUM(order_total - ISNULL(shipping_amount, 0)) AS ventas
            FROM sales.online_order WHERE order_status <> N'Cancelado' AND ordered_at >= ? AND ordered_at < DATEADD(DAY, 1, ?)
            GROUP BY CAST(ordered_at AS DATE)),
        tienda AS (
            SELECT CAST(ticket_at AS DATE) AS dia, COUNT(*) AS documentos, SUM(ticket_net_amount) AS ventas
            FROM sales.pos_ticket WHERE ticket_at >= ? AND ticket_at < DATEADD(DAY, 1, ?) GROUP BY CAST(ticket_at AS DATE)),
        devol AS (
            SELECT CAST(h.returned_at AS DATE) AS dia, SUM(l.refund_amount) AS importe
            FROM [returns].return_header h JOIN [returns].return_line l ON l.return_id = h.return_id
            WHERE h.return_status IN (N'Aceptada', N'Reembolsada') AND h.returned_at >= ? AND h.returned_at < DATEADD(DAY, 1, ?)
            GROUP BY CAST(h.returned_at AS DATE)),
        dias AS (SELECT dia FROM online UNION SELECT dia FROM tienda UNION SELECT dia FROM devol)
        SELECT d.dia, ISNULL(o.ventas, 0) AS online, ISNULL(o.documentos, 0) AS pedidos, ISNULL(t.ventas, 0) AS tienda,
               ISNULL(t.documentos, 0) AS tickets, ISNULL(r.importe, 0) AS devoluciones,
               ISNULL(o.ventas, 0) + ISNULL(t.ventas, 0) - ISNULL(r.importe, 0) AS neto
        FROM dias d LEFT JOIN online o ON o.dia = d.dia LEFT JOIN tienda t ON t.dia = d.dia LEFT JOIN devol r ON r.dia = d.dia
        ORDER BY d.dia""", since, until, since, until, since, until)
    total = {k: round(sum(float(d[k]) for d in days), 2) for k in ("online", "tienda", "devoluciones", "neto")}
    top = db.query("""
        SELECT TOP 10 p.product_id, p.product_name, p.category, SUM(x.qty) AS unidades, SUM(x.amount) AS ventas
        FROM (SELECT l.product_id, l.quantity AS qty, l.line_amount AS amount FROM sales.online_order_line l
              JOIN sales.online_order o ON o.order_id = l.order_id
              WHERE o.order_status <> N'Cancelado' AND o.ordered_at >= ? AND o.ordered_at < DATEADD(DAY, 1, ?)
              UNION ALL
              SELECT l.product_id, l.quantity, l.line_amount FROM sales.pos_ticket_line l
              JOIN sales.pos_ticket t ON t.ticket_id = l.ticket_id WHERE t.ticket_at >= ? AND t.ticket_at < DATEADD(DAY, 1, ?)) x
        JOIN catalog.product p ON p.product_id = x.product_id
        GROUP BY p.product_id, p.product_name, p.category ORDER BY ventas DESC""", since, until, since, until)
    by_store = db.query("""SELECT t.store_id, s.store_name, COUNT(*) AS tickets, SUM(t.ticket_net_amount) AS ventas
                           FROM sales.pos_ticket t JOIN store.store s ON s.store_id = t.store_id
                           WHERE t.ticket_at >= ? AND t.ticket_at < DATEADD(DAY, 1, ?)
                           GROUP BY t.store_id, s.store_name ORDER BY ventas DESC""", since, until)
    return {"desde": since, "hasta": until, "totales": total, "dias": days, "top_productos": top, "tiendas": by_store}


@route("GET", "/paneles/cliente/{customer_id}", ROLES)
def cliente(req: Request):
    cid = an_id(req.params["customer_id"], "customer")
    c = ficha_cliente(cid)
    c["pedidos"] = db.query("""SELECT TOP 10 order_id, ordered_at, order_total, order_status FROM sales.online_order
                               WHERE customer_id = ? ORDER BY ordered_at DESC""", cid)
    c["tickets"] = db.query("""SELECT TOP 10 ticket_id, ticket_at, store_id, ticket_net_amount FROM sales.pos_ticket
                               WHERE customer_id = ? ORDER BY ticket_at DESC""", cid)
    c["devoluciones"] = db.query("""SELECT TOP 10 return_id, returned_at, return_channel, return_status FROM [returns].return_header
                                    WHERE customer_id = ? ORDER BY returned_at DESC""", cid)
    c["campanas"] = db.query("""SELECT cc.campaign_id, m.campaign_name, cc.experiment_group, cc.delivery_status, cc.conversion_30d,
                                       cc.revenue_30d_eur FROM mkt.campaign_contact cc JOIN mkt.campaign m ON m.campaign_id = cc.campaign_id
                                WHERE cc.customer_id = ? ORDER BY cc.contacted_at DESC""", cid)
    c["opiniones"] = cosmos.query("feedback", "SELECT c.feedback_id, c.fecha_feedback, c.tipo_feedback, c.rating_1_5, c.nps_0_10, "
                                  "c.sentimiento, c.tema_principal FROM c ORDER BY c.fecha_feedback DESC", pk=cid, max_items=20)
    c["casos"] = cosmos.query("atencion_cliente", "SELECT c.service_ticket_id, c.fecha_apertura, c.tipo_caso, c.prioridad, "
                              "c.estado_resolucion, c.csat_1_5 FROM c ORDER BY c.fecha_apertura DESC", pk=cid, max_items=20)
    c["senales_identidad"] = (cosmos.query("senales_identidad", "SELECT VALUE COUNT(1) FROM c", pk=cid) or [0])[0]
    return c


@route("GET", "/paneles/empleado/{employee_id}", ROLES)
def empleado(req: Request):
    eid = an_id(req.params["employee_id"], "employee")
    e = ficha_empleado(eid, req.user, full=True)
    e["people_analytics"] = db.one("""SELECT probabilidad_abandono, riesgo_abandono, alto_riesgo_flag, talento_clave_flag,
                                             prioridad_retencion, satisfaccion_1_10, engagement_1_10, enps
                                      FROM hr.people_analytics_seed WHERE employee_id = ?""", eid)
    answers = cosmos.query("encuesta_clima", "SELECT c.oleada, c.dimension, c.score, c.comentario_abierto FROM c", pk=eid,
                           max_items=500)
    by_dim: dict[str, list[float]] = {}
    for a in answers:
        if a.get("score") is not None:
            by_dim.setdefault(a["dimension"], []).append(float(a["score"]))
    e["clima"] = {d: round(sum(v) / len(v), 2) for d, v in sorted(by_dim.items())}
    e["comentarios_clima"] = [a["comentario_abierto"] for a in answers if a.get("comentario_abierto")]
    e["entrevista_salida"] = cosmos.query("entrevistas_salida", "SELECT * FROM c", pk=eid, max_items=5)
    return e


@route("GET", "/paneles/rotacion", ROLES)
def rotacion(req: Request):
    """Rotación mensual por departamento: la foto histórica y, para los meses posteriores, el cálculo
    sobre hr.employee (altas, bajas voluntarias e involuntarias, plantilla al inicio y al final)."""
    seed = db.query("""SELECT periodo_mes, departamento, headcount_inicio_mes, altas_mes, bajas_voluntarias_mes,
                              bajas_no_voluntarias_mes, bajas_totales_mes, headcount_fin_mes, tasa_rotacion_voluntaria_pct,
                              tasa_rotacion_total_pct, N'historico' AS fuente
                       FROM hr.turnover_monthly_seed ORDER BY periodo_mes, departamento""")
    last = max((r["periodo_mes"] for r in seed), default=None)
    live = db.query("""
        WITH meses AS (
            SELECT DATEFROMPARTS(YEAR(DATEADD(MONTH, 1, ?)), MONTH(DATEADD(MONTH, 1, ?)), 1) AS mes
            UNION ALL SELECT DATEADD(MONTH, 1, mes) FROM meses WHERE DATEADD(MONTH, 1, mes) <= SYSUTCDATETIME()),
        deps AS (SELECT DISTINCT department FROM hr.employee WHERE department IS NOT NULL)
        SELECT m.mes AS periodo_mes, d.department AS departamento,
               (SELECT COUNT(*) FROM hr.employee e WHERE e.department = d.department AND e.hired_at < m.mes
                  AND (e.left_at IS NULL OR e.left_at >= m.mes)) AS headcount_inicio_mes,
               (SELECT COUNT(*) FROM hr.employee e WHERE e.department = d.department AND e.hired_at >= m.mes
                  AND e.hired_at < DATEADD(MONTH, 1, m.mes)) AS altas_mes,
               (SELECT COUNT(*) FROM hr.employee e WHERE e.department = d.department AND e.exit_type = N'Voluntaria'
                  AND e.left_at >= m.mes AND e.left_at < DATEADD(MONTH, 1, m.mes)) AS bajas_voluntarias_mes,
               (SELECT COUNT(*) FROM hr.employee e WHERE e.department = d.department AND ISNULL(e.exit_type, N'') <> N'Voluntaria'
                  AND e.left_at >= m.mes AND e.left_at < DATEADD(MONTH, 1, m.mes)) AS bajas_no_voluntarias_mes
        FROM meses m CROSS JOIN deps d
        OPTION (MAXRECURSION 120)""", last, last) if last else []
    for r in live:
        r["bajas_totales_mes"] = r["bajas_voluntarias_mes"] + r["bajas_no_voluntarias_mes"]
        r["headcount_fin_mes"] = r["headcount_inicio_mes"] + r["altas_mes"] - r["bajas_totales_mes"]
        base = r["headcount_inicio_mes"] or None
        r["tasa_rotacion_voluntaria_pct"] = round(100 * r["bajas_voluntarias_mes"] / base, 2) if base else None
        r["tasa_rotacion_total_pct"] = round(100 * r["bajas_totales_mes"] / base, 2) if base else None
        r["fuente"] = "calculado"
    return {"meses": seed + live, "ultimo_mes_historico": last}


@route("GET", "/paneles/comentarios", ROLES)
def comentarios(req: Request):
    kind = req.query.get("tipo", "clima")
    dep = req.query.get("departamento") or None
    if kind == "salida":
        docs = cosmos.query("entrevistas_salida", "SELECT c.employee_id, c.fecha_salida, c.tipo_salida, c.motivo_salida_rrhh, "
                            "c.comentario_salida, c.recomendaria_empresa_1_10 FROM c WHERE IS_STRING(c.comentario_salida)",
                            max_items=2000)
    else:
        docs = cosmos.query("encuesta_clima", "SELECT c.employee_id, c.oleada, c.fecha_encuesta, c.comentario_abierto FROM c "
                            "WHERE IS_STRING(c.comentario_abierto)", max_items=5000)
    staff = {r["employee_id"]: r for r in db.query("SELECT employee_id, department, location, role_name FROM hr.employee")}
    out = []
    for d in docs:
        e = staff.get(d["employee_id"], {})
        if dep and e.get("department") != dep:
            continue
        out.append({**d, "departamento": e.get("department"), "ubicacion": e.get("location"), "rol": e.get("role_name")})
    out.sort(key=lambda r: r.get("fecha_salida") or r.get("fecha_encuesta") or "", reverse=True)
    return out[:req.int_arg("tamano", 200, 1, 5000)]
