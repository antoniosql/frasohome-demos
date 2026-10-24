"""FraSoHome Live · de los CSV de datos/ a las tablas de Azure SQL.

Cada método `cargar_*` lee un CSV, aplica las reglas de limpieza, registra lo que
corrige o descarta y deja las filas listas para insertar. El orden de
`PASOS` respeta las claves foráneas: lo que se carga después puede comprobar que
sus referencias existen.

Política de limpieza (la misma para todos los ficheros):
- rechazo: la fila no entra (clave inválida o duplicada, referencia obligatoria
  que no existe, cantidad cero o negativa, fecha obligatoria imposible);
- corregido: la fila entra con el valor arreglado (identificador normalizado,
  importe negativo en valor absoluto, porcentaje fuera de rango a NULL...);
- aviso: la fila entra tal cual pero hay algo que revisar (referencia opcional
  que no existe y queda a NULL, valor de categoría desconocido...).
Todo queda en quality.data_quality_issue con la fila original en JSON.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from typing import Any, Callable

import limpieza as L
from comun import CsvFile, IssueLog, read_csv

RETAIL = "retail_omnicanal/raw_csv/"
MKT = "marketing_precision/raw_csv/"
PEOPLE = "people_analytics/raw_csv/"
REL = "relaciones/"
RAG = "rag_copilot_studio/"

# Fecha de referencia para detectar fechas futuras imposibles en hechos ya ocurridos.
TODAY = date.today()


def _future(d: date | datetime | None) -> bool:
    if d is None:
        return False
    return (d.date() if isinstance(d, datetime) else d) > TODAY


class CargaSQL:
    """Acumula las filas por tabla, las incidencias y el resumen por fichero."""

    def __init__(self, columnas: Callable[[str], list[tuple[str, str, bool]]] | None = None):
        # columnas(tabla) -> metadatos de SQL; solo hace falta para las tablas literales.
        self._columnas = columnas
        self.tables: dict[str, list[dict[str, Any]]] = {}
        self.logs: list[IssueLog] = []
        self.sources: dict[str, dict[str, Any]] = {}
        # claves cargadas, para comprobar referencias
        self.customers: set[str] = set()
        self.products: set[str] = set()
        self.stores: set[str] = set()
        self.orders: dict[str, str | None] = {}           # order_id -> customer_id
        self.order_lines: dict[str, tuple[str, str | None]] = {}  # line -> (order, product)
        self.tickets: set[str] = set()
        self.ticket_lines: set[str] = set()
        self.employees: set[str] = set()
        self.campaigns: set[str] = set()
        self.dept_map: dict[str, str] = {}
        self.pos_alias: dict[str, str] = {}

    # ------------------------------------------------------------ utilidades

    def _log(self, table: str, csv: CsvFile) -> IssueLog:
        schema, name = table.split(".")
        log = IssueLog(schema, name.strip("[]"), csv.rel)
        self.logs.append(log)
        return log

    def _put(self, table: str, rows: list[dict[str, Any]]) -> None:
        self.tables.setdefault(table, []).extend(rows)

    def _source(self, csv: CsvFile, loaded: int, targets: list[str], log: IssueLog | None = None,
                note: str | None = None) -> None:
        self.sources[csv.rel] = {
            "filas_csv": len(csv.rows), "filas_cargadas": loaded, "destino": targets,
            "rechazos": log.count("rechazo") if log else 0,
            "corregidos": log.count("corregido") if log else 0,
            "avisos": log.count("aviso") if log else 0,
            **({"nota": note} if note else {}),
        }

    @staticmethod
    def _exact_dups(csv: CsvFile, log: IssueLog, key: Callable[[dict], str]) -> list[dict[str, str]]:
        seen: set[tuple] = set()
        out = []
        for r in csv.rows:
            sig = tuple(r.values())
            if sig in seen:
                log.rejected("duplicado_exacto", "Fila repetida idéntica en el CSV.", key(r), r)
                continue
            seen.add(sig)
            out.append(r)
        return out

    def _id(self, log: IssueLog, fn, value: str, row: dict, key: str, field: str,
            required: bool = False, known: set | dict | None = None, what: str = "") -> tuple[str | None, bool]:
        """Normaliza un identificador. Devuelve (valor, ok). ok=False => rechazar la fila."""
        raw = value
        val, valid = fn(raw)
        if not valid:
            if required:
                log.rejected("id_invalido", f"{field} «{raw}» no tiene un formato reconocible.", key, row)
                return None, False
            log.warn("id_invalido", f"{field} «{raw}» no tiene un formato reconocible: queda vacío.", key, row)
            return None, True
        if val is None:
            if required:
                log.rejected("id_vacio", f"{field} vacío.", key, row)
                return None, False
            return None, True
        if L.clean_text(raw) != val:
            log.fixed("id_normalizado", f"{field} «{raw}» → {val}.", key)
        if known is not None and val not in known:
            if required:
                log.rejected("referencia_inexistente", f"{field} {val} no existe{what}.", key, row)
                return None, False
            log.warn("referencia_inexistente", f"{field} {val} no existe{what}: queda vacío.", key, row)
            return None, True
        return val, True

    def _num(self, log: IssueLog, value: str, key: str, field: str, row: dict, *,
             non_negative: bool = False, lo: float | None = None, hi: float | None = None,
             integer: bool = False) -> float | int | None:
        if L.clean_text(value) is None:
            return None
        n = L.parse_number(value)
        if n is None:
            log.warn("numero_invalido", f"{field} «{value}» no es un número: queda vacío.", key, row)
            return None
        if non_negative and n < 0:
            log.fixed("negativo", f"{field} {n} negativo: se guarda en valor absoluto.", key, row)
            n = abs(n)
        if (lo is not None and n < lo) or (hi is not None and n > hi):
            log.fixed("fuera_de_rango", f"{field} {n} fuera de [{lo}, {hi}]: queda vacío.", key, row)
            return None
        if integer:
            return int(round(n))
        return n

    def _dt(self, log: IssueLog, value: str, key: str, field: str, row: dict, *,
            only_date: bool = False, allow_future: bool = False) -> datetime | date | None:
        if L.clean_text(value) is None:
            return None
        d = L.parse_datetime(value)
        if d is None:
            log.warn("fecha_invalida", f"{field} «{value}» no es una fecha válida: queda vacía.", key, row)
            return None
        if not allow_future and _future(d):
            log.fixed("fecha_futura", f"{field} {d:%Y-%m-%d} es posterior a hoy: queda vacía.", key, row)
            return None
        return d.date() if only_date else d

    def _map(self, log: IssueLog, value: str, mapping: dict, key: str, field: str, row: dict) -> str | None:
        val, known = L.mapped(value, mapping)
        if not known:
            log.warn("valor_desconocido", f"{field} «{value}» no está en la lista de valores conocidos.", key, row)
        elif val is not None and val != L.clean_text(value):
            pass  # normalizaciones de mayúsculas y sinónimos: no se registran una a una
        return val

    def _literal(self, table: str, csv: CsvFile, renames: dict[str, str] | None = None,
                 extra: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Tablas que conservan las columnas del CSV: convierte cada valor al tipo SQL."""
        if self._columnas is None:
            raise RuntimeError("Las tablas literales necesitan los metadatos de SQL.")
        meta = {name: typ for name, typ, _ in self._columnas(table)}
        rows = []
        for r in csv.rows:
            out: dict[str, Any] = dict(extra or {})
            for col, val in r.items():
                name = (renames or {}).get(col, col)
                if name not in meta:
                    continue
                out[name] = _convert(val, meta[name])
            rows.append(out)
        return rows

    # ------------------------------------------------------------ referencia y relaciones

    def cargar_departamentos(self) -> None:
        csv = read_csv(PEOPLE + "dim_departamentos_mapeo.csv")
        log = self._log("ref.department_map", csv)
        rows, seen = [], set()
        for r in csv.rows:
            raw = L.clean_text(r["departamento_raw"])
            if not raw:
                log.rejected("id_vacio", "departamento_raw vacío.", None, r)
                continue
            std = L.clean_text(r["departamento_estandar"])
            self.dept_map[L.fold(raw)] = std
            # La clave de SQL no distingue mayúsculas ni espacios finales: «COMPRAS» y «Compras »
            # son la misma fila. Se fusionan (las dos siguen sirviendo para traducir en la carga).
            key = raw.lower()
            if key in seen:
                log.fixed("duplicado_mayusculas", f"«{r['departamento_raw']}» se fusiona con la variante ya cargada.", raw, r)
                continue
            seen.add(key)
            rows.append({"department_raw": raw, "department_std": std, "hr_area": L.clean_text(r["area_rrhh"]),
                         "business_channel": L.clean_text(r["canal_negocio"]),
                         "critical_turnover_default": bool(L.parse_flag(r["area_critica_rotacion_default"]))})
        # El departamento estándar también se reconoce a sí mismo.
        for std in set(self.dept_map.values()):
            self.dept_map.setdefault(L.fold(std), std)
        self._put("ref.department_map", rows)
        self._source(csv, len(rows), ["ref.department_map"], log)

    def _dept(self, log: IssueLog, value: str, key: str, field: str, row: dict) -> str | None:
        raw = L.clean_text(value)
        if raw is None:
            return None
        std = self.dept_map.get(L.fold(raw))
        if std is None:
            log.warn("valor_desconocido", f"{field} «{raw}» no está en ref.department_map.", key, row)
            return raw
        return std

    def cargar_guardrails(self) -> None:
        csv = read_csv(MKT + "guardrails_marca_genai.csv")
        log = self._log("ref.brand_guardrail", csv)
        rows = [{"rule_id": L.generic_id(r["regla_id"]), "rule_category": L.clean_text(r["categoria_regla"]),
                 "rule_description": L.clean_text(r["descripcion_regla"]), "applies_to_channel": L.clean_text(r["aplica_a_canal"]),
                 "severity": L.clean_text(r["severidad"])} for r in csv.rows]
        self._put("ref.brand_guardrail", rows)
        self._source(csv, len(rows), ["ref.brand_guardrail"], log)

    def cargar_calendario(self) -> None:
        csv = read_csv(PEOPLE + "dim_calendario.csv")
        log = self._log("ref.calendar", csv)
        rows = []
        for r in csv.rows:
            d = L.parse_date(r["fecha"])
            if d is None:
                log.rejected("fecha_invalida", f"fecha «{r['fecha']}» no válida.", r["fecha"], r)
                continue
            rows.append({"date_key": d, "year_num": int(r["anio"]), "month_num": int(r["mes_num"]),
                         "month_name": r["mes_nombre"], "quarter_name": r["trimestre"],
                         "period_month": L.parse_date(r["periodo_mes"]), "month_end": L.parse_date(r["fin_mes"])})
        self._put("ref.calendar", rows)
        self._source(csv, len(rows), ["ref.calendar"], log)

    def cargar_alias(self) -> None:
        csv = read_csv(REL + "store_aliases.csv")
        log = self._log("xref.store_alias", csv)
        rows, seen = [], set()
        for r in csv.rows:
            alias = L.clean_text(r["alias_store_id_or_location"])
            if not alias or L.fold(alias) in seen:
                log.rejected("duplicado_clave", f"alias «{alias}» vacío o repetido.", alias, r)
                continue
            seen.add(L.fold(alias))
            rows.append({"alias": alias, "canonical_store_id": L.clean_text(r["canonical_store_id"]),
                         "source_context": L.clean_text(r["source_context"]), "confidence": L.clean_text(r["confidence"]),
                         "note": L.clean_text(r["note"])})
        self._put("xref.store_alias", rows)
        self._source(csv, len(rows), ["xref.store_alias"], log)

        csv = read_csv(REL + "product_aliases_rag_to_retail.csv")
        log = self._log("xref.product_alias", csv)
        rows = [{"source_system": r["source_system"], "source_product_id": r["source_product_id"],
                 "source_product_name": L.clean_text(r["source_product_name"]), "source_category_code": L.clean_text(r["source_category_code"]),
                 "source_category_name": L.clean_text(r["source_category_name"]), "canonical_product_id": L.clean_text(r["canonical_product_id"]),
                 "canonical_product_name": L.clean_text(r["canonical_product_name"]), "canonical_category": L.clean_text(r["canonical_category"]),
                 "canonical_subcategory": L.clean_text(r["canonical_subcategory"]), "match_method": L.clean_text(r["match_method"]),
                 "confidence": L.clean_text(r["confidence"]), "note": L.clean_text(r["note"])} for r in csv.rows]
        self._put("xref.product_alias", rows)
        self._source(csv, len(rows), ["xref.product_alias"], log)

        csv = read_csv(REL + "employee_operational_aliases.csv")
        log = self._log("xref.employee_alias", csv)
        rows = []
        for r in csv.rows:
            rows.append({"source_system": r["source_system"], "operational_employee_id": r["operational_employee_id"],
                         "canonical_employee_id": r["canonical_employee_id"],
                         "canonical_employee_location": L.clean_text(r["canonical_employee_location"]),
                         "canonical_employee_department": L.clean_text(r["canonical_employee_department"]),
                         "match_method": L.clean_text(r["match_method"]), "confidence": L.clean_text(r["confidence"]),
                         "note": L.clean_text(r["note"])})
            code, ok = L.cashier_id(r["operational_employee_id"])
            if r["source_system"].upper() == "POS" and ok and code:
                self.pos_alias.setdefault(code, r["canonical_employee_id"])
        self._put("xref.employee_alias", rows)
        self._source(csv, len(rows), ["xref.employee_alias"], log)

        csv = read_csv(REL + "employee_store_assignment.csv")
        log = self._log("xref.employee_store", csv)
        rows = [{"employee_id": r["employee_id"], "department": L.clean_text(r["department"]),
                 "location": L.clean_text(r["location"]), "canonical_store_id": L.clean_text(r["canonical_store_id"]),
                 "assignment_type": L.clean_text(r["assignment_type"]), "confidence": L.clean_text(r["confidence"])}
                for r in csv.rows]
        self._put("xref.employee_store", rows)
        self._source(csv, len(rows), ["xref.employee_store"], log)

    # ------------------------------------------------------------ retail: maestros

    def cargar_tiendas(self) -> None:
        csv = read_csv(RETAIL + "tiendas.csv")
        log = self._log("store.store", csv)
        rows = []
        for r in csv.rows:
            k = r["store_id"]
            sid, ok = self._id(log, L.store_id, r["store_id"], r, k, "store_id", required=True)
            if not ok:
                continue
            if sid in self.stores:
                log.rejected("duplicado_clave", f"store_id {sid} repetido (se conserva el primero).", sid, r)
                continue
            status = L.clean_text(r["estado"]) or "Activa"
            opened = self._dt(log, r["fecha_apertura"], sid, "fecha_apertura", r, only_date=True,
                              allow_future=(status == "Planificada"))
            lat = self._num(log, r["lat"], sid, "lat", r, lo=-90, hi=90)
            lon = self._num(log, r["lon"], sid, "lon", r, lo=-180, hi=180)
            country, _ = L.mapped(r["pais"], L.COUNTRY)
            cp = L.clean_text(r["codigo_postal"])
            if cp is None:
                log.warn("valor_vacio", "codigo_postal vacío.", sid)
            rows.append({"store_id": sid, "store_name": L.clean_text(r["nombre_tienda"]), "location_type": L.clean_text(r["tipo_ubicacion"]),
                         "channel": L.clean_text(r["canal"]), "city": L.clean_text(r["ciudad"]), "province": L.clean_text(r["provincia"]),
                         "address_line": L.clean_text(r["direccion"]), "postal_code": cp, "country_code": country,
                         "opened_at": opened, "square_meters": L.parse_int(r["metros_cuadrados"]), "phone": L.clean_text(r["telefono"]),
                         "opening_hours": L.clean_text(r["horario"]), "latitude": lat, "longitude": lon, "store_status": status,
                         "region": self._map(log, r["region"], L.REGION, sid, "region", r),
                         "manager_name": L.clean_text(r["gerente"]), "notes": L.clean_text(r["observaciones"])})
            self.stores.add(sid)
        self._put("store.store", rows)
        self._source(csv, len(rows), ["store.store"], log)

    def cargar_productos(self) -> None:
        csv = read_csv(RETAIL + "productos.csv")
        log = self._log("catalog.product", csv)
        candidates: dict[str, list[tuple[int, dict, dict]]] = defaultdict(list)
        for r in self._exact_dups(csv, log, lambda x: x["product_id"]):
            k = r["product_id"]
            pid, ok = self._id(log, L.product_id, r["product_id"], r, k, "product_id", required=True)
            if not ok:
                continue
            price = self._num(log, r["precio_venta"], pid, "precio_venta", r)
            if price is not None and price <= 0:
                log.fixed("fuera_de_rango", f"precio_venta {price} ≤ 0: queda vacío.", pid, r)
                price = None
            cost = self._num(log, r["coste_unitario"], pid, "coste_unitario", r)
            if cost is not None and cost < 0:
                log.fixed("negativo", f"coste_unitario {cost} negativo: queda vacío.", pid, r)
                cost = None
            weight = self._num(log, r["peso_kg"], pid, "peso_kg", r)
            if weight is not None and weight < 0:
                log.fixed("negativo", f"peso_kg {weight} negativo: queda vacío.", pid, r)
                weight = None
            row = {"product_id": pid, "product_name": L.clean_text(r["nombre_producto"]),
                   "category": L.title_category(r["categoria"]), "subcategory": L.clean_text(r["subcategoria"]),
                   "brand": L.clean_text(r["marca"]), "supplier": L.clean_text(r["proveedor"]),
                   "material": L.clean_text(r["material"]), "color": L.clean_text(r["color"]),
                   "sale_price": L.money(price), "unit_cost": L.money(cost),
                   "vat_pct": self._num(log, r["iva_pct"], pid, "iva_pct", r, lo=0, hi=100),
                   "weight_kg": weight, "length_cm": self._num(log, r["largo_cm"], pid, "largo_cm", r, lo=0, hi=5000),
                   "width_cm": self._num(log, r["ancho_cm"], pid, "ancho_cm", r, lo=0, hi=5000),
                   "height_cm": self._num(log, r["alto_cm"], pid, "alto_cm", r, lo=0, hi=5000),
                   "catalog_start_date": self._dt(log, r["fecha_alta_catalogo"], pid, "fecha_alta_catalogo", r, only_date=True),
                   "product_status": L.clean_text(r["estado_producto"]) or "Activo", "ean": L.clean_text(r["ean"])}
            score = (price is not None) + (cost is not None)
            candidates[pid].append((score, row, r))
        rows = []
        for pid, cands in candidates.items():
            cands.sort(key=lambda c: -c[0])
            rows.append(cands[0][1])
            for _, _, r in cands[1:]:
                log.rejected("duplicado_clave", f"product_id {pid} repetido: se conserva la fila con más datos.", pid, r)
            self.products.add(pid)
        self._put("catalog.product", rows)
        self._source(csv, len(rows), ["catalog.product"], log)

    def cargar_clientes(self) -> None:
        csv = read_csv(RETAIL + "crm.csv")
        log = self._log("crm.customer", csv)
        candidates: dict[str, list[tuple[datetime, dict, dict]]] = defaultdict(list)
        for r in self._exact_dups(csv, log, lambda x: x["customer_id"]):
            k = r["customer_id"]
            cid, ok = self._id(log, L.customer_id, r["customer_id"], r, k, "customer_id", required=True)
            if not ok:
                continue
            email = L.clean_text(r["email"])
            email = email.lower() if email else None
            valid = None
            if email:
                valid = bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)) and ".." not in email
                if not valid:
                    log.warn("email_invalido", f"email «{email}» no es válido: se conserva marcado.", cid)
            points = self._num(log, r["puntos_acumulados"], cid, "puntos_acumulados", r, integer=True)
            if points is not None and points < 0:
                log.fixed("negativo", f"puntos_acumulados {points} negativos: quedan vacíos.", cid, r)
                points = None
            cp_raw = L.clean_text(r["codigo_postal"])
            cp = None
            if cp_raw:
                m = re.search(r"\d{5}", cp_raw)
                cp = m.group(0) if m else None
                if cp is None:
                    log.warn("valor_invalido", f"codigo_postal «{cp_raw}» no tiene 5 dígitos.", cid)
            updated = self._dt(log, r["ultima_actualizacion"], cid, "ultima_actualizacion", r)
            row = {"customer_id": cid, "first_name": L.clean_text(r["nombre"]), "last_name": L.clean_text(r["apellidos"]),
                   "email": email, "email_is_valid": valid, "phone": L.clean_text(r["telefono"]),
                   "loyalty_joined_at": self._dt(log, r["fecha_alta_programa"], cid, "fecha_alta_programa", r, only_date=True),
                   "loyalty_tier": self._map(log, r["tier_fidelizacion"], L.TIER, cid, "tier_fidelizacion", r),
                   "loyalty_points": points,
                   "birth_date": self._dt(log, r["fecha_nacimiento"], cid, "fecha_nacimiento", r, only_date=True),
                   "gender": L.clean_text(r["genero"]), "city": L.clean_text(r["ciudad"]), "province": L.clean_text(r["provincia"]),
                   "postal_code": cp, "country_code": L.mapped(r["pais"], L.COUNTRY)[0],
                   "marketing_consent": L.parse_flag(r["consentimiento_marketing"]),
                   "customer_status": L.clean_text(r["estado_cliente"]) or "Activo",
                   "churned_at": self._dt(log, r["fecha_baja"], cid, "fecha_baja", r, only_date=True),
                   "acquisition_source": L.clean_text(r["origen_alta"]),
                   "preferred_channel": L.clean_text(r["canal_preferido_declarado"]), "source_updated_at": updated}
            candidates[cid].append((updated or datetime.min, row, r))
        rows = []
        for cid, cands in candidates.items():
            cands.sort(key=lambda c: c[0], reverse=True)
            rows.append(cands[0][1])
            for _, _, r in cands[1:]:
                log.rejected("duplicado_clave", f"customer_id {cid} repetido: se conserva la versión más reciente.", cid, r)
            self.customers.add(cid)
        self._put("crm.customer", rows)
        self._source(csv, len(rows), ["crm.customer"], log)

    # ------------------------------------------------------------ retail: online

    def cargar_pedidos(self) -> None:
        csv = read_csv(RETAIL + "pedidos.csv")
        log = self._log("sales.online_order", csv)
        candidates: dict[str, list[tuple[datetime, dict, dict]]] = defaultdict(list)
        for r in self._exact_dups(csv, log, lambda x: x["order_id"]):
            k = r["order_id"]
            oid, ok = self._id(log, L.order_id, r["order_id"], r, k, "order_id", required=True)
            if not ok:
                continue
            cid, _ = self._id(log, L.customer_id, r["customer_id"], r, oid, "customer_id", known=self.customers,
                              what=" en el CRM (pedido de invitado)")
            cp_raw = L.clean_text(r["codigo_postal_envio"])
            cp = None
            if cp_raw:
                fixed = cp_raw.upper().replace("O", "0")
                m = re.fullmatch(r"\d{5}", fixed)
                cp = fixed if m else None
                if cp is None:
                    log.warn("valor_invalido", f"codigo_postal_envio «{cp_raw}» no tiene 5 dígitos.", oid)
                elif cp != cp_raw:
                    log.fixed("valor_normalizado", f"codigo_postal_envio «{cp_raw}» → {cp}.", oid)
            updated = self._dt(log, r["ultima_actualizacion"], oid, "ultima_actualizacion", r)
            row = {"order_id": oid, "ordered_at": self._dt(log, r["fecha_pedido"], oid, "fecha_pedido", r),
                   "customer_id": cid, "online_user_id": L.generic_id(r["usuario_online_id"]),
                   "order_total": L.money(self._num(log, r["importe_total"], oid, "importe_total", r, non_negative=True)),
                   "currency_code": "EUR",
                   "shipping_amount": L.money(self._num(log, r["gastos_envio"], oid, "gastos_envio", r, non_negative=True)),
                   "shipping_address": L.clean_text(r["direccion_envio"]), "shipping_postal_code": cp,
                   "shipping_city": L.clean_text(r["ciudad_envio"]), "shipping_province": L.clean_text(r["provincia_envio"]),
                   "shipping_country_code": L.mapped(r["pais_envio"], L.COUNTRY)[0],
                   "payment_method": self._map(log, r["metodo_pago"], L.PAYMENT_ONLINE, oid, "metodo_pago", r),
                   "order_status": L.clean_text(r["estado_pedido"]) or "Pendiente",
                   "order_origin": self._map(log, r["origen"], L.ORDER_ORIGIN, oid, "origen", r),
                   "source_updated_at": updated}
            candidates[oid].append((updated or datetime.min, row, r))
        rows = []
        for oid, cands in candidates.items():
            cands.sort(key=lambda c: c[0], reverse=True)
            rows.append(cands[0][1])
            for _, _, r in cands[1:]:
                log.rejected("duplicado_clave", f"order_id {oid} repetido: se conserva la versión más reciente.", oid, r)
            self.orders[oid] = cands[0][1]["customer_id"]
        self._put("sales.online_order", rows)
        self._source(csv, len(rows), ["sales.online_order"], log)

    def _discount_pct(self, log, value, key, row):
        pct = self._num(log, value, key, "descuento_pct", row)
        if pct is not None and not 0 <= pct <= 100:
            log.fixed("fuera_de_rango", f"descuento_pct {pct} fuera de [0, 100]: queda vacío.", key, row)
            return None
        return pct

    def cargar_lineas_pedido(self) -> None:
        csv = read_csv(RETAIL + "lineas_pedido.csv")
        log = self._log("sales.online_order_line", csv)
        rows, seen = [], set()
        for r in self._exact_dups(csv, log, lambda x: x["order_line_id"]):
            lid = L.generic_id(r["order_line_id"])
            if not lid or lid in seen:
                log.rejected("duplicado_clave", f"order_line_id {lid} vacío o repetido.", lid, r)
                continue
            oid, ok = self._id(log, L.order_id, r["order_id"], r, lid, "order_id", required=True,
                               known=self.orders, what=" en pedidos")
            if not ok:
                continue
            qty = self._num(log, r["cantidad"], lid, "cantidad", r, integer=True)
            if qty is None or qty <= 0:
                log.rejected("cantidad_invalida", f"cantidad «{r['cantidad']}» debe ser mayor que cero.", lid, r)
                continue
            pid, _ = self._id(log, L.product_id, r["product_id"], r, lid, "product_id", known=self.products,
                              what=" en el catálogo")
            seen.add(lid)
            rows.append({"order_line_id": lid, "order_id": oid, "product_id": pid,
                         "product_description": L.clean_text(r["descripcion_producto"]),
                         "category": L.title_category(r["categoria"]), "subcategory": L.clean_text(r["subcategoria"]),
                         "quantity": qty,
                         "unit_price": L.money(self._num(log, r["precio_unitario"], lid, "precio_unitario", r, non_negative=True)),
                         "discount_pct": self._discount_pct(log, r["descuento_pct"], lid, r),
                         "discount_amount": L.money(self._num(log, r["descuento_importe"], lid, "descuento_importe", r, non_negative=True)),
                         "line_amount": L.money(self._num(log, r["importe_linea"], lid, "importe_linea", r, non_negative=True)),
                         "vat_pct": self._num(log, r["iva_pct"], lid, "iva_pct", r, lo=0, hi=100)})
            self.order_lines[lid] = (oid, pid)
        self._put("sales.online_order_line", rows)
        self._source(csv, len(rows), ["sales.online_order_line"], log)

    # ------------------------------------------------------------ retail: tienda

    def cargar_ventas_pos(self) -> None:
        csv = read_csv(RETAIL + "ventas_pos.csv")
        log = self._log("sales.pos_ticket_line", csv)
        lines, seen = [], set()
        heads: dict[str, list[dict]] = defaultdict(list)
        for r in self._exact_dups(csv, log, lambda x: x["ticket_line_id"]):
            lid = L.generic_id(r["ticket_line_id"])
            if not lid or lid in seen:
                log.rejected("duplicado_clave", f"ticket_line_id {lid} vacío o repetido.", lid, r)
                continue
            tid, ok = self._id(log, L.ticket_id, r["ticket_id"], r, lid, "ticket_id", required=True)
            if not ok:
                continue
            qty = self._num(log, r["cantidad"], lid, "cantidad", r, integer=True)
            if qty is None or qty <= 0:
                log.rejected("cantidad_invalida", f"cantidad «{r['cantidad']}» debe ser mayor que cero.", lid, r)
                continue
            pid, _ = self._id(log, L.product_id, r["product_id"], r, lid, "product_id", known=self.products,
                              what=" en el catálogo")
            seen.add(lid)
            unit = L.money(self._num(log, r["precio_unitario"], lid, "precio_unitario", r, non_negative=True))
            disc = L.money(self._num(log, r["descuento_importe"], lid, "descuento_importe", r, non_negative=True))
            amount = L.money(self._num(log, r["importe_linea"], lid, "importe_linea", r, non_negative=True))
            lines.append({"ticket_line_id": lid, "ticket_id": tid, "product_id": pid,
                          "product_description": L.clean_text(r["descripcion_producto"]),
                          "category": L.title_category(r["categoria"]), "subcategory": L.clean_text(r["subcategoria"]),
                          "quantity": qty, "unit_price": unit,
                          "discount_pct": self._discount_pct(log, r["descuento_pct"], lid, r),
                          "discount_amount": disc, "line_amount": amount, "notes": L.clean_text(r["observaciones"])})
            store, _ = self._id(log, L.store_id, r["store_id"], r, lid, "store_id", known=self.stores, what=" en tiendas")
            till, _ = self._id(log, L.till_id, r["caja_id"], r, lid, "caja_id")
            cashier, _ = self._id(log, L.cashier_id, r["cajero_id"], r, lid, "cajero_id")
            cust, _ = self._id(log, L.customer_id, r["customer_id"], r, lid, "customer_id", known=self.customers,
                               what=" en el CRM (venta sin cliente identificado)")
            heads[tid].append({"at": self._dt(log, r["fecha_hora"], lid, "fecha_hora", r), "store": store, "till": till,
                               "cashier": cashier, "customer": cust, "gross": (unit or 0) * qty, "disc": disc or 0,
                               "net": amount or 0})
        tickets = []
        for tid, hs in heads.items():
            def first(field):
                vals = Counter(h[field] for h in hs if h[field] is not None)
                return vals.most_common(1)[0][0] if vals else None
            cashier = first("cashier")
            tickets.append({"ticket_id": tid, "ticket_at": first("at"), "store_id": first("store"), "till_id": first("till"),
                            "cashier_id": cashier, "cashier_employee_id": self.pos_alias.get(cashier) if cashier else None,
                            "customer_id": first("customer"), "currency_code": "EUR", "channel": "POS",
                            "ticket_gross_amount": round(sum(h["gross"] for h in hs), 2),
                            "ticket_discount_amount": round(sum(h["disc"] for h in hs), 2),
                            "ticket_net_amount": round(sum(h["net"] for h in hs), 2)})
            self.tickets.add(tid)
        self.ticket_lines = seen
        self._put("sales.pos_ticket", tickets)
        self._put("sales.pos_ticket_line", lines)
        self._source(csv, len(lines), ["sales.pos_ticket", "sales.pos_ticket_line"], log,
                     note=f"{len(tickets)} tickets (cabecera) y {len(lines)} líneas")

    def cargar_pagos(self) -> None:
        csv = read_csv(RETAIL + "pagos_tienda.csv")
        log = self._log("sales.store_payment", csv)
        rows, seen = [], set()
        for r in self._exact_dups(csv, log, lambda x: x["payment_id"]):
            pid = L.generic_id(r["payment_id"])
            if not pid or pid in seen:
                log.rejected("duplicado_clave", f"payment_id {pid} vacío o repetido.", pid, r)
                continue
            tid, ok = self._id(log, L.ticket_id, r["ticket_id"], r, pid, "ticket_id", required=True,
                               known=self.tickets, what=" en ventas de tienda")
            if not ok:
                continue
            amount = self._num(log, r["importe_pagado"], pid, "importe_pagado", r)
            if amount is not None and amount < 0:
                log.rejected("negativo", f"importe_pagado {amount} negativo: es una devolución mal registrada.", pid, r)
                continue
            store, _ = self._id(log, L.store_id, r["store_id"], r, pid, "store_id", known=self.stores, what=" en tiendas")
            cashier, _ = self._id(log, L.cashier_id, r["cajero_id"], r, pid, "cajero_id")
            till, _ = self._id(log, L.till_id, r["caja_id"], r, pid, "caja_id")
            seen.add(pid)
            rows.append({"payment_id": pid, "ticket_id": tid, "paid_at": self._dt(log, r["fecha_pago"], pid, "fecha_pago", r),
                         "store_id": store, "till_id": till, "cashier_id": cashier,
                         "cashier_employee_id": self.pos_alias.get(cashier) if cashier else None,
                         "payment_method": self._map(log, r["metodo_pago"], L.PAYMENT_STORE, pid, "metodo_pago", r),
                         "paid_amount": L.money(amount), "currency_code": "EUR",
                         "authorization_reference": L.clean_text(r["referencia_autorizacion"]),
                         "payment_status": (L.clean_text(r["estado_pago"]) or "OK").upper(),
                         "notes": L.clean_text(r["observaciones"])})
        self._put("sales.store_payment", rows)
        self._source(csv, len(rows), ["sales.store_payment"], log)

    # ------------------------------------------------------------ retail: devoluciones

    def _return_qty(self, log, value, key, row) -> int | None:
        qty = self._num(log, value, key, "cantidad_devuelta", row, integer=True)
        if qty is None or qty <= 0:
            log.rejected("cantidad_invalida", f"cantidad_devuelta «{value}» debe ser mayor que cero.", key, row)
            return None
        if qty > 20:
            log.warn("valor_atipico", f"cantidad_devuelta {qty} es muy alta: revisar.", key, row)
        return qty

    def _refund(self, log, value, key, row) -> float | None:
        return L.money(self._num(log, value, key, "importe_reembolsado", row, non_negative=True))

    def cargar_devoluciones_online(self) -> None:
        csv = read_csv(RETAIL + "devoluciones_online.csv")
        log = self._log("returns.return_line", csv)
        headers: dict[str, dict] = {}
        lines, seen = [], set()
        line_no: Counter = Counter()
        for r in self._exact_dups(csv, log, lambda x: x["return_id"]):
            rid = L.generic_id(r["return_id"])
            if not rid:
                log.rejected("id_vacio", "return_id vacío.", None, r)
                continue
            oid, ok = self._id(log, L.order_id, r["order_id"], r, rid, "order_id", required=True,
                               known=self.orders, what=" en pedidos")
            if not ok:
                continue
            olid = L.generic_id(r["order_line_id"])
            if olid and olid not in self.order_lines:
                log.warn("referencia_inexistente", f"order_line_id {olid} no existe: queda vacío.", rid, r)
                olid = None
            pid, _ = self._id(log, L.product_id, r["product_id"], r, rid, "product_id", known=self.products,
                              what=" en el catálogo")
            if pid is None and olid:
                pid = self.order_lines[olid][1]
                if pid:
                    log.fixed("valor_deducido", f"product_id tomado de la línea de pedido {olid}.", rid)
            if (rid, pid) in seen:
                log.rejected("duplicado_clave", f"return_id {rid} con product_id {pid} repetido.", rid, r)
                continue
            qty = self._return_qty(log, r["cantidad_devuelta"], rid, r)
            if qty is None:
                continue
            seen.add((rid, pid))
            status = L.clean_text(r["estado_devolucion"])
            if status is None:
                log.fixed("valor_por_defecto", "estado_devolucion vacío: se toma Pendiente.", rid)
                status = "Pendiente"
            if rid not in headers:
                headers[rid] = {"return_id": rid, "returned_at": self._dt(log, r["fecha_devolucion"], rid, "fecha_devolucion", r),
                                "return_channel": "ONLINE", "store_id": None, "customer_id": self.orders.get(oid),
                                "original_ticket_id": None, "original_order_id": oid, "return_status": status,
                                "return_method": self._map(log, r["metodo_devolucion"], L.RETURN_METHOD_ONLINE, rid, "metodo_devolucion", r),
                                "refund_method": None, "currency_code": "EUR", "notes": L.clean_text(r["comentarios"])}
            line_no[rid] += 1
            lines.append({"return_line_id": f"{rid}-{line_no[rid]}", "return_id": rid, "product_id": pid,
                          "original_ticket_line_id": None, "original_order_line_id": olid, "returned_quantity": qty,
                          "refund_amount": self._refund(log, r["importe_reembolsado"], rid, r),
                          "return_reason": L.clean_text(r["motivo_devolucion"]), "original_sales_channel": "ONLINE"})
        self._put("returns.return_header", list(headers.values()))
        self._put("returns.return_line", lines)
        self._source(csv, len(lines), ["returns.return_header", "returns.return_line"], log,
                     note=f"{len(headers)} devoluciones (cabecera) y {len(lines)} líneas")

    def cargar_devoluciones_tienda(self) -> None:
        csv = read_csv(RETAIL + "devoluciones_tienda.csv")
        log = self._log("returns.return_line", csv)
        headers: dict[str, dict] = {}
        lines, seen = [], set()
        line_no: Counter = Counter()
        for r in self._exact_dups(csv, log, lambda x: x["return_id"]):
            rid = L.generic_id(r["return_id"])
            if not rid:
                log.rejected("id_vacio", "return_id vacío.", None, r)
                continue
            pid, _ = self._id(log, L.product_id, r["product_id"], r, rid, "product_id", known=self.products,
                              what=" en el catálogo")
            if (rid, pid) in seen:
                log.rejected("duplicado_clave", f"return_id {rid} con product_id {pid} repetido.", rid, r)
                continue
            qty = self._return_qty(log, r["cantidad_devuelta"], rid, r)
            if qty is None:
                continue
            seen.add((rid, pid))
            if rid not in headers:
                store, _ = self._id(log, L.store_id, r["store_id"], r, rid, "store_id", known=self.stores, what=" en tiendas")
                tid, _ = self._id(log, L.ticket_id, r["ticket_id_original"], r, rid, "ticket_id_original",
                                  known=self.tickets, what=" en ventas de tienda")
                oid, _ = self._id(log, L.order_id, r["order_id_original"], r, rid, "order_id_original",
                                  known=self.orders, what=" en pedidos")
                cust, _ = self._id(log, L.customer_id, r["customer_id"], r, rid, "customer_id", known=self.customers,
                                   what=" en el CRM")
                headers[rid] = {"return_id": rid, "returned_at": self._dt(log, r["fecha_devolucion"], rid, "fecha_devolucion", r),
                                "return_channel": "TIENDA", "store_id": store, "customer_id": cust,
                                "original_ticket_id": tid, "original_order_id": oid,
                                "return_status": L.clean_text(r["estado_devolucion"]) or "Pendiente",
                                "return_method": None,
                                "refund_method": self._map(log, r["metodo_reembolso"], L.REFUND_METHOD, rid, "metodo_reembolso", r),
                                "currency_code": "EUR", "notes": L.clean_text(r["comentarios"])}
            tl = L.generic_id(r["ticket_line_id_original"])
            if tl and tl not in self.ticket_lines:
                log.warn("referencia_inexistente", f"ticket_line_id_original {tl} no existe: queda vacío.", rid, r)
                tl = None
            line_no[rid] += 1
            channel = (L.clean_text(r["canal_origen_venta"]) or "POS").upper()
            lines.append({"return_line_id": f"{rid}-{line_no[rid]}", "return_id": rid, "product_id": pid,
                          "original_ticket_line_id": tl, "original_order_line_id": None, "returned_quantity": qty,
                          "refund_amount": self._refund(log, r["importe_reembolsado"], rid, r),
                          "return_reason": L.clean_text(r["motivo_devolucion"]), "original_sales_channel": channel})
        self._put("returns.return_header", list(headers.values()))
        self._put("returns.return_line", lines)
        self._source(csv, len(lines), ["returns.return_header", "returns.return_line"], log,
                     note=f"{len(headers)} devoluciones (cabecera) y {len(lines)} líneas")

    # ------------------------------------------------------------ retail: stock

    def cargar_stock(self) -> None:
        csv = read_csv(RETAIL + "stock_diario.csv")
        log = self._log("inventory.stock_snapshot", csv)
        rows, seen = [], set()
        latest: dict[tuple[str, str], dict] = {}
        for r in self._exact_dups(csv, log, lambda x: f"{x['fecha']}|{x['store_id']}|{x['product_id']}"):
            k = f"{r['fecha']}|{r['store_id']}|{r['product_id']}"
            d = self._dt(log, r["fecha"], k, "fecha", r, only_date=True)
            if d is None:
                log.rejected("fecha_invalida", "Foto de stock sin fecha válida.", k, r)
                continue
            store, ok = self._id(log, L.store_id, r["store_id"], r, k, "store_id", required=True, known=self.stores,
                                 what=" en tiendas")
            if not ok:
                continue
            pid, ok = self._id(log, L.product_id, r["product_id"], r, k, "product_id", required=True,
                               known=self.products, what=" en el catálogo")
            if not ok:
                continue
            key = (d, store, pid)
            if key in seen:
                log.rejected("duplicado_clave", f"Foto repetida para {store}/{pid} el {d}.", k, r)
                continue
            seen.add(key)
            closing = self._num(log, r["stock_cierre"], k, "stock_cierre", r)
            if closing is not None and closing < 0:
                log.fixed("negativo", f"stock_cierre {closing} negativo: se pone a 0.", k, r)
                closing = 0
            row = {"snapshot_date": d, "store_id": store, "product_id": pid, "closing_stock_qty": closing,
                   "reserved_stock_qty": self._num(log, r["stock_reservado"], k, "stock_reservado", r, non_negative=True),
                   "in_transit_stock_qty": self._num(log, r["stock_en_transito"], k, "stock_en_transito", r, non_negative=True),
                   "minimum_stock_qty": self._num(log, r["stock_minimo"], k, "stock_minimo", r, non_negative=True),
                   "source_system": L.clean_text(r["fuente"]), "notes": L.clean_text(r["comentarios"])}
            rows.append(row)
            prev = latest.get((store, pid))
            if prev is None or prev["snapshot_date"] < d:
                latest[(store, pid)] = row
        levels = [{"store_id": s, "product_id": p, "on_hand_qty": int(round(r["closing_stock_qty"] or 0)),
                   "reserved_qty": int(round(r["reserved_stock_qty"] or 0)),
                   "in_transit_qty": int(round(r["in_transit_stock_qty"] or 0)),
                   "minimum_qty": int(round(r["minimum_stock_qty"] or 0))} for (s, p), r in latest.items()]
        self._put("inventory.stock_snapshot", rows)
        self._put("inventory.stock_level", levels)
        self._source(csv, len(rows), ["inventory.stock_snapshot", "inventory.stock_level"], log,
                     note=f"stock vivo inicial: última foto de {len(levels)} pares tienda-producto")

    # ------------------------------------------------------------ personas

    def cargar_empleados(self) -> None:
        csv = read_csv(PEOPLE + "raw_hris_empleados.csv")
        log = self._log("hr.employee", csv)
        rows, managers = [], {}
        for r in csv.rows:
            k = r["source_row_id"]
            eid, ok = self._id(log, L.employee_id, r["employee_code_raw"], r, k, "employee_code_raw", required=True)
            if not ok:
                continue
            if eid in self.employees:
                log.rejected("duplicado_clave", f"{eid} repetido en el HRIS: se conserva el primer registro.", eid, r)
                continue
            hired = L.parse_date(r["fecha_alta_txt"])
            if hired is None:
                log.rejected("fecha_invalida", f"fecha_alta «{r['fecha_alta_txt']}» no es válida.", eid, r)
                continue
            birth = self._dt(log, r["fecha_nacimiento_txt"], eid, "fecha_nacimiento", r, only_date=True)
            left = self._dt(log, r["fecha_salida_txt"], eid, "fecha_salida", r, only_date=True)
            if left is not None and left < hired:
                log.fixed("fechas_incoherentes", f"fecha_salida {left} anterior a fecha_alta {hired}: queda vacía.", eid, r)
                left = None
            status = self._map(log, r["estado_raw"], L.STATUS_HR, eid, "estado", r) or "Activo"
            if status == "Baja" and left is None:
                log.warn("dato_incompleto", "Empleado de baja sin fecha de salida.", eid)
            mgr, _ = self._id(log, L.employee_id, r["manager_code_raw"], r, eid, "manager_code_raw")
            if mgr == eid:
                log.fixed("referencia_circular", "El empleado figura como su propio responsable: queda vacío.", eid)
                mgr = None
            managers[eid] = (mgr, r)
            rows.append({"employee_id": eid, "full_name": L.clean_text(r["nombre_apellidos_raw"]),
                         "gender": self._map(log, r["genero_raw"], L.GENDER_HR, eid, "genero", r),
                         "birth_date": birth, "hired_at": hired, "left_at": left, "employee_status": status,
                         "exit_type": self._map(log, r["tipo_salida_raw"], L.EXIT_TYPE, eid, "tipo_salida", r),
                         "exit_reason": None,
                         "department": self._dept(log, r["departamento_raw"], eid, "departamento", r),
                         "location": L.clean_text(r["ubicacion_raw"]), "role_name": L.clean_text(r["rol_raw"]),
                         "level_name": self._map(log, r["nivel_raw"], L.LEVEL, eid, "nivel", r),
                         "contract_type": self._map(log, r["tipo_contrato_raw"], L.CONTRACT, eid, "tipo_contrato", r),
                         "work_schedule": self._map(log, r["jornada_raw"], L.SCHEDULE, eid, "jornada", r),
                         "manager_id": None,
                         "remote_days_week": self._num(log, r["teletrabajo_dias_semana_raw"], eid, "teletrabajo_dias_semana", r, lo=0, hi=5, integer=True),
                         "commute_km": self._num(log, r["distancia_casa_trabajo_km_raw"], eid, "distancia_casa_trabajo_km", r, non_negative=True),
                         "source_row_id": k})
            self.employees.add(eid)
        # Responsables: solo si existen (se aplican con un UPDATE tras insertar).
        updates = []
        for eid, (mgr, r) in managers.items():
            if mgr is None:
                continue
            if mgr not in self.employees:
                log.warn("referencia_inexistente", f"manager {mgr} no existe en el HRIS: queda vacío.", eid, r)
                continue
            updates.append({"employee_id": eid, "manager_id": mgr})
        self._put("hr.employee", rows)
        self.tables["hr.employee#manager"] = updates
        self._source(csv, len(rows), ["hr.employee"], log)

    def _employee(self, log, value, key, row, field="employee_code_raw", required=True):
        return self._id(log, L.employee_id, value, row, key, field, required=required, known=self.employees,
                        what=" en hr.employee")

    def cargar_movimientos(self) -> None:
        csv = read_csv(PEOPLE + "raw_movimientos_personal.csv")
        log = self._log("hr.employee_movement", csv)
        rows = []
        for r in csv.rows:
            k = r["movimiento_id"]
            eid, ok = self._employee(log, r["employee_code_raw"], k, r)
            if not ok:
                continue
            rows.append({"movement_id": k, "employee_id": eid,
                         "moved_at": self._dt(log, r["fecha_movimiento_txt"], k, "fecha_movimiento", r, only_date=True),
                         "movement_type": self._map(log, r["tipo_movimiento_raw"], L.MOVEMENT_TYPE, k, "tipo_movimiento", r) or "Sin tipo",
                         "department_from": self._dept(log, r["departamento_origen_raw"], k, "departamento_origen", r),
                         "department_to": self._dept(log, r["departamento_destino_raw"], k, "departamento_destino", r),
                         "level_from": self._map(log, r["nivel_origen_raw"], L.LEVEL, k, "nivel_origen", r),
                         "level_to": self._map(log, r["nivel_destino_raw"], L.LEVEL, k, "nivel_destino", r),
                         "reason": L.clean_text(r["motivo_movimiento_raw"]), "hr_comment": L.clean_text(r["comentario_rrhh"]),
                         "loaded_by": L.clean_text(r["usuario_carga"]),
                         "loaded_at": L.parse_date(r["fecha_carga_txt"])})
        self._put("hr.employee_movement", rows)
        self._source(csv, len(rows), ["hr.employee_movement"], log)

    def cargar_ausencias(self) -> None:
        csv = read_csv(PEOPLE + "raw_absentismo.csv")
        log = self._log("hr.absence", csv)
        rows = []
        for r in csv.rows:
            k = r["ausencia_id"]
            eid, ok = self._employee(log, r["employee_code_raw"], k, r)
            if not ok:
                continue
            start = self._dt(log, r["fecha_inicio_txt"], k, "fecha_inicio", r, only_date=True, allow_future=True)
            end = self._dt(log, r["fecha_fin_txt"], k, "fecha_fin", r, only_date=True, allow_future=True)
            if start and end and end < start:
                log.fixed("fechas_incoherentes", f"fecha_fin {end} anterior a fecha_inicio {start}: se intercambian.", k, r)
                start, end = end, start
            rows.append({"absence_id": k, "employee_id": eid, "start_date": start, "end_date": end,
                         "absence_type": L.clean_text(r["tipo_ausencia_raw"]) or "Sin tipo",
                         "working_days": self._num(log, r["dias_laborables_raw"], k, "dias_laborables", r, non_negative=True, integer=True),
                         "justified": self._map(log, r["justificada_raw"], L.JUSTIFIED, k, "justificada", r),
                         "notes": L.clean_text(r["observaciones_raw"])})
        self._put("hr.absence", rows)
        self._source(csv, len(rows), ["hr.absence"], log)

    def cargar_horas_extra(self) -> None:
        csv = read_csv(PEOPLE + "raw_horas_extra.csv")
        log = self._log("hr.overtime", csv)
        rows = []
        for r in csv.rows:
            k = r["horas_extra_id"]
            eid, ok = self._employee(log, r["employee_code_raw"], k, r)
            if not ok:
                continue
            month = L.parse_month(r["periodo_mes_txt"])
            if month is None:
                log.rejected("fecha_invalida", f"periodo_mes «{r['periodo_mes_txt']}» no válido.", k, r)
                continue
            approver, _ = self._employee(log, r["aprobador_raw"], k, r, field="aprobador", required=False)
            rows.append({"overtime_id": k, "employee_id": eid, "period_month": month,
                         "department_reported": self._dept(log, r["departamento_reportado_raw"], k, "departamento_reportado", r),
                         "hours": self._num(log, r["horas_extra_raw"], k, "horas_extra", r, non_negative=True),
                         "reason": L.clean_text(r["motivo_raw"]),
                         "approval_status": self._map(log, r["estado_aprobacion_raw"], L.APPROVAL, k, "estado_aprobacion", r) or "Pendiente",
                         "approver_id": approver})
        self._put("hr.overtime", rows)
        self._source(csv, len(rows), ["hr.overtime"], log)

    def cargar_formacion(self) -> None:
        csv = read_csv(PEOPLE + "raw_formacion.csv")
        log = self._log("hr.training", csv)
        rows = []
        for r in csv.rows:
            k = r["formacion_id"]
            eid, ok = self._employee(log, r["employee_code_raw"], k, r)
            if not ok:
                continue
            start = self._dt(log, r["fecha_inicio_txt"], k, "fecha_inicio", r, only_date=True, allow_future=True)
            end = self._dt(log, r["fecha_fin_txt"], k, "fecha_fin", r, only_date=True, allow_future=True)
            if start and end and end < start:
                log.fixed("fechas_incoherentes", f"fecha_fin {end} anterior a fecha_inicio {start}: se intercambian.", k, r)
                start, end = end, start
            rows.append({"training_id": k, "employee_id": eid, "course_id": L.generic_id(r["curso_id"]),
                         "course_name": L.clean_text(r["curso_nombre"]), "category": L.clean_text(r["categoria_formacion_raw"]),
                         "start_date": start, "end_date": end,
                         "planned_hours": self._num(log, r["horas_planificadas_raw"], k, "horas_planificadas", r, non_negative=True),
                         "completed_hours": self._num(log, r["horas_realizadas_raw"], k, "horas_realizadas", r, non_negative=True),
                         "training_status": self._map(log, r["estado_curso_raw"], L.TRAINING_STATUS, k, "estado_curso", r) or "Inscrito",
                         "cost_eur": L.money(self._num(log, r["coste_eur_raw"], k, "coste_eur", r, non_negative=True)),
                         "provider": L.clean_text(r["proveedor_raw"])})
        self._put("hr.training", rows)
        self._source(csv, len(rows), ["hr.training"], log)

    def cargar_evaluaciones(self) -> None:
        csv = read_csv(PEOPLE + "raw_evaluaciones_desempeno.csv")
        log = self._log("hr.performance_review", csv)
        rows = []
        for r in csv.rows:
            k = r["evaluacion_id"]
            eid, ok = self._employee(log, r["employee_code_raw"], k, r)
            if not ok:
                continue
            reviewer, _ = self._employee(log, r["evaluador_code_raw"], k, r, field="evaluador", required=False)
            rows.append({"review_id": k, "employee_id": eid, "review_cycle": L.clean_text(r["ciclo_evaluacion"]),
                         "reviewed_at": self._dt(log, r["fecha_evaluacion_txt"], k, "fecha_evaluacion", r, only_date=True),
                         "overall_score": self._num(log, r["evaluacion_global_raw"], k, "evaluacion_global", r, lo=1, hi=5),
                         "objectives_pct": self._num(log, r["cumplimiento_objetivos_pct_raw"], k, "cumplimiento_objetivos_pct", r, lo=0, hi=300),
                         "competencies_score": self._num(log, r["competencias_1_5_raw"], k, "competencias_1_5", r, lo=1, hi=5),
                         "potential": L.clean_text(r["potencial_raw"]), "reviewer_id": reviewer,
                         "manager_comment": L.clean_text(r["comentario_manager_raw"]), "source_system": L.clean_text(r["fuente"])})
        self._put("hr.performance_review", rows)
        self._source(csv, len(rows), ["hr.performance_review"], log)

    def cargar_salarios(self) -> None:
        csv = read_csv(PEOPLE + "raw_salarios_beneficios.csv")
        log = self._log("hr.compensation", csv)
        rows = []
        for r in csv.rows:
            k = r["nomina_id"]
            eid, ok = self._employee(log, r["employee_code_raw"], k, r)
            if not ok:
                continue
            month = L.parse_month(r["periodo_nomina_txt"])
            if month is None:
                log.rejected("fecha_invalida", f"periodo_nomina «{r['periodo_nomina_txt']}» no válido.", k, r)
                continue
            rows.append({"payroll_id": k, "employee_id": eid, "period_month": month,
                         "base_salary_eur": L.money(self._num(log, r["salario_base_anual_raw"], k, "salario_base_anual", r, non_negative=True)),
                         "variable_salary_eur": L.money(self._num(log, r["salario_variable_anual_raw"], k, "salario_variable_anual", r, non_negative=True)),
                         "increase_pct": self._num(log, r["incremento_aplicado_pct_raw"], k, "incremento_aplicado_pct", r, lo=-50, hi=100),
                         "currency_code": "EUR", "source_system": L.clean_text(r["fuente_nomina_raw"]),
                         "loaded_at": L.parse_date(r["fecha_carga_txt"])})
        self._put("hr.compensation", rows)
        self._source(csv, len(rows), ["hr.compensation"], log)

    def cargar_semillas_personas(self) -> None:
        for rel, table in [(PEOPLE + "frasohome_people_analytics.csv", "hr.people_analytics_seed"),
                           (PEOPLE + "frasohome_rotacion_mensual.csv", "hr.turnover_monthly_seed"),
                           (PEOPLE + "frasohome_muestra_prompt_chatgpt.csv", "lab.prompt_sample")]:
            csv = read_csv(rel)
            rows = self._literal(table, csv)
            self._put(table, rows)
            self._source(csv, len(rows), [table], note="se guarda tal cual: no se puede recalcular")

    # ------------------------------------------------------------ marketing

    def cargar_campanas(self) -> None:
        csv = read_csv(MKT + "campanas_marketing.csv")
        log = self._log("mkt.campaign", csv)
        rows = []
        for r in csv.rows:
            cid = L.generic_id(r["campaign_id"])
            store, _ = self._id(log, L.store_id, r["store_id_objetivo"], r, cid, "store_id_objetivo", known=self.stores, what=" en tiendas")
            rows.append({"campaign_id": cid, "campaign_name": L.clean_text(r["nombre_campana"]), "objective": L.clean_text(r["objetivo"]),
                         "channel": (L.clean_text(r["canal"]) or "").upper(),
                         "starts_at": L.parse_datetime(r["fecha_inicio"]), "ends_at": L.parse_datetime(r["fecha_fin"]),
                         "target_segment": L.clean_text(r["segmento_objetivo"]), "target_category": L.clean_text(r["categoria_objetivo"]),
                         "target_subcategory": L.clean_text(r["subcategoria_objetivo"]), "target_store_id": store,
                         "offer_type": L.clean_text(r["tipo_oferta"]), "discount_pct": L.parse_number(r["descuento_pct"]) or 0,
                         "budget_eur": L.parse_number(r["presupuesto_plan_eur"]), "control_group_pct": L.parse_number(r["grupo_control_pct"]) or 0,
                         "primary_kpi": L.clean_text(r["kpi_primario"]), "campaign_status": L.clean_text(r["estado"]) or "borrador",
                         "copy_axis": L.clean_text(r["copy_eje"]), "created_by": "carga_inicial"})
            self.campaigns.add(cid)
        self._put("mkt.campaign", rows)
        self._source(csv, len(rows), ["mkt.campaign"], log,
                     note="solo la definición: los recuentos y resultados los recalcula la exportación")

    def cargar_cupones(self) -> None:
        csv = read_csv(MKT + "cupones_clientes.csv")
        log = self._log("mkt.coupon", csv)
        rows = []
        for r in csv.rows:
            k = L.generic_id(r["coupon_instance_id"])
            cust, ok = self._id(log, L.customer_id, r["customer_id"], r, k, "customer_id", required=True,
                                known=self.customers, what=" en el CRM")
            if not ok:
                continue
            camp = L.generic_id(r["campaign_id"])
            if camp and camp not in self.campaigns:
                log.warn("referencia_inexistente", f"campaign_id {camp} no existe: queda vacío.", k, r)
                camp = None
            rows.append({"coupon_instance_id": k, "coupon_code": L.generic_id(r["coupon_code"]), "campaign_id": camp,
                         "customer_id": cust, "issued_at": L.parse_datetime(r["fecha_emision"]),
                         "valid_from": L.parse_datetime(r["fecha_inicio_validez"]), "valid_to": L.parse_datetime(r["fecha_fin_validez"]),
                         "coupon_type": L.clean_text(r["tipo_cupon"]), "discount_pct": L.parse_number(r["descuento_pct"]),
                         "discount_eur": L.parse_number(r["descuento_importe_eur"]), "min_spend_eur": L.parse_number(r["gasto_minimo_eur"]) or 0,
                         "restricted_category": L.clean_text(r["categoria_restringida"]),
                         "restricted_store_id": L.store_id(r["store_id_restringido"])[0],
                         "issue_channel": L.clean_text(r["canal_emision"]), "coupon_status": L.clean_text(r["estado_cupon"]) or "emitido",
                         "redeemed_at": L.parse_datetime(r["fecha_canje"]), "order_id": L.order_id(r["order_id"])[0],
                         "ticket_id": L.ticket_id(r["ticket_id"])[0], "basket_eur": L.parse_number(r["importe_cesta_eur"]),
                         "discount_applied_eur": L.parse_number(r["descuento_aplicado_eur"]),
                         "margin_after_discount_eur": L.parse_number(r["margen_post_descuento_eur"])})
        self._put("mkt.coupon", rows)
        self._source(csv, len(rows), ["mkt.coupon"], log)

    def cargar_contactos(self) -> None:
        csv = read_csv(MKT + "contactos_campana.csv")
        log = self._log("mkt.campaign_contact", csv)
        rows = []
        for r in csv.rows:
            k = L.generic_id(r["contact_id"])
            camp = L.generic_id(r["campaign_id"])
            if camp not in self.campaigns:
                log.rejected("referencia_inexistente", f"campaign_id {camp} no existe.", k, r)
                continue
            cust, ok = self._id(log, L.customer_id, r["customer_id"], r, k, "customer_id", required=True,
                                known=self.customers, what=" en el CRM")
            if not ok:
                continue
            rec1, _ = self._id(log, L.product_id, r["product_id_recomendado_1"], r, k, "product_id_recomendado_1",
                               known=self.products, what=" en el catálogo")
            rec2, _ = self._id(log, L.product_id, r["product_id_recomendado_2"], r, k, "product_id_recomendado_2",
                               known=self.products, what=" en el catálogo")
            rows.append({"contact_id": k, "campaign_id": camp, "customer_id": cust,
                         "contacted_at": L.parse_datetime(r["fecha_contacto"]), "contact_channel": L.clean_text(r["canal_contacto"]),
                         "experiment_group": L.clean_text(r["grupo_experimental"]), "is_control": bool(L.parse_flag(r["grupo_control_flag"])),
                         "assigned_segment": L.clean_text(r["segmento_asignado"]), "offer_code": L.generic_id(r["offer_code"]),
                         "coupon_instance_id": L.generic_id(r["coupon_instance_id"]), "delivery_status": L.clean_text(r["estado_entrega"]),
                         "contact_cost_eur": L.parse_number(r["coste_contacto_eur"]) or 0,
                         "contact_priority": L.clean_text(r["prioridad_contacto"]),
                         "personalized_store_id": L.store_id(r["store_id_personalizado"])[0],
                         "recommended_product_1": rec1, "recommended_product_2": rec2, "app_user_id": L.generic_id(r["app_user_id"]),
                         "conversion_30d": bool(L.parse_flag(r["conversion_30d_flag"])),
                         "conversion_order_id": L.order_id(r["order_id_conversion_30d"])[0],
                         "conversion_ticket_id": L.ticket_id(r["ticket_id_conversion_30d"])[0],
                         "revenue_30d_eur": L.parse_number(r["revenue_30d_eur"]) or 0,
                         "margin_30d_eur": L.parse_number(r["margen_30d_eur"]) or 0,
                         "converted_at": L.parse_datetime(r["fecha_conversion_30d"])})
        self._put("mkt.campaign_contact", rows)
        self._source(csv, len(rows), ["mkt.campaign_contact"], log)

    def cargar_promociones(self) -> None:
        csv = read_csv(MKT + "promociones_calendario.csv")
        log = self._log("mkt.promotion", csv)
        rows = []
        for r in csv.rows:
            k = L.generic_id(r["promo_id"])
            camp = L.generic_id(r["campana_id_relacionada"])
            if camp and camp not in self.campaigns:
                log.warn("referencia_inexistente", f"campana_id_relacionada {camp} no existe: queda vacía.", k, r)
                camp = None
            store, _ = self._id(log, L.store_id, r["store_id"], r, k, "store_id", known=self.stores, what=" en tiendas")
            rows.append({"promo_id": k, "promo_name": L.clean_text(r["nombre_promocion"]),
                         "starts_at": L.parse_datetime(r["fecha_inicio"]), "ends_at": L.parse_datetime(r["fecha_fin"]),
                         "scope_type": L.clean_text(r["ambito"]), "scope_id": L.clean_text(r["scope_id"]),
                         "promo_type": L.clean_text(r["tipo_promocion"]), "discount_pct": L.parse_number(r["descuento_pct"]),
                         "discount_eur": L.parse_number(r["descuento_importe_eur"]), "channel": L.clean_text(r["canal"]),
                         "target_segment": L.clean_text(r["segmento_objetivo"]), "store_id": store,
                         "combinable": bool(L.parse_flag(r["combinable"])), "basket_threshold_eur": L.parse_number(r["umbral_cesta_eur"]) or 0,
                         "min_margin_pct": L.parse_number(r["objetivo_margen_min_pct"]), "related_campaign_id": camp})
        self._put("mkt.promotion", rows)
        self._source(csv, len(rows), ["mkt.promotion"], log)

    def cargar_afinidad(self) -> None:
        csv = read_csv(MKT + "afinidad_tienda_cliente.csv")
        log = self._log("mkt.customer_store_affinity", csv)
        rows = []
        for r in csv.rows:
            k = r["customer_id"]
            cust, ok = self._id(log, L.customer_id, r["customer_id"], r, k, "customer_id", required=True,
                                known=self.customers, what=" en el CRM")
            if not ok:
                continue
            pref, _ = self._id(log, L.store_id, r["store_id_preferida"], r, cust, "store_id_preferida", known=self.stores, what=" en tiendas")
            near, _ = self._id(log, L.store_id, r["store_id_mas_cercana"], r, cust, "store_id_mas_cercana", known=self.stores, what=" en tiendas")
            rows.append({"customer_id": cust, "preferred_store_id": pref, "nearest_store_id": near,
                         "nearest_store_km": L.parse_number(r["distancia_km_store_mas_cercana"]),
                         "store_visits_12m": L.parse_int(r["frecuencia_visita_tienda_12m"]),
                         "store_spend_12m_eur": L.parse_number(r["gasto_tienda_12m_eur"]),
                         "online_spend_12m_eur": L.parse_number(r["gasto_online_12m_eur"]),
                         "click_collect_propensity": L.parse_number(r["click_collect_propension"]),
                         "visit_probability_30d": L.parse_number(r["probabilidad_visita_30d"]),
                         "local_cluster": L.clean_text(r["cluster_local"]), "locally_capturable": L.parse_flag(r["es_capturable_localmente"]),
                         "home_city": L.clean_text(r["ciudad_residencia"]), "home_province": L.clean_text(r["provincia_residencia"])})
        self._put("mkt.customer_store_affinity", rows)
        self._source(csv, len(rows), ["mkt.customer_store_affinity"], log,
                     note="semilla; la recalcula un procedimiento a partir de compras y tiendas")

    def cargar_costes(self) -> None:
        csv = read_csv(MKT + "costes_operativos_transaccion.csv")
        log = self._log("fin.transaction_cost", csv)
        rows = []
        for r in csv.rows:
            k = L.generic_id(r["transaction_cost_id"])
            store, _ = self._id(log, L.store_id, r["store_id"], r, k, "store_id", known=self.stores, what=" en tiendas")
            cust, _ = self._id(log, L.customer_id, r["customer_id"], r, k, "customer_id")
            n = lambda c: L.parse_number(r[c])  # noqa: E731
            rows.append({"transaction_cost_id": k, "document_type": L.clean_text(r["tipo_documento"]),
                         "order_id": L.order_id(r["order_id"])[0], "ticket_id": L.ticket_id(r["ticket_id"])[0],
                         "customer_id": cust, "transaction_at": L.parse_datetime(r["fecha_transaccion"]),
                         "channel": L.clean_text(r["canal"]), "store_id": store, "main_category": L.title_category(r["categoria_principal"]),
                         "gross_revenue_eur": n("ingreso_bruto_eur"), "discount_eur": n("descuento_total_eur"),
                         "product_cost_eur": n("coste_producto_eur"), "logistics_cost_eur": n("coste_logistico_eur"),
                         "packaging_cost_eur": n("coste_packaging_eur"), "last_mile_cost_eur": n("coste_ultima_milla_eur"),
                         "payment_cost_eur": n("coste_pago_eur"), "service_cost_eur": n("coste_servicio_eur"),
                         "expected_return_cost_eur": n("coste_devolucion_esperado_eur"), "cac_eur": n("cac_asignado_eur"),
                         "attributed_campaign_id": L.generic_id(r["campaign_id_atribuida"]),
                         "net_contribution_eur": n("margen_contribucion_neto_eur")})
        self._put("fin.transaction_cost", rows)
        self._source(csv, len(rows), ["fin.transaction_cost"], log)

    # ------------------------------------------------------------ rag, laboratorio y metadatos

    def cargar_rag(self) -> None:
        for rel, table in [("structured_csv/FS_Clientes.csv", "rag.customer"), ("structured_csv/FS_Productos.csv", "rag.product"),
                           ("structured_csv/FS_Tiendas.csv", "rag.store"), ("structured_csv/FS_StockDiario.csv", "rag.stock_daily"),
                           ("structured_csv/FS_VentasResumenDiario.csv", "rag.sales_daily"),
                           ("structured_csv/FS_DevolucionesFact.csv", "rag.return_fact"),
                           ("structured_csv/FS_Alertas_Stockout.csv", "rag.stockout_alert")]:
            csv = read_csv(RAG + rel)
            rows = self._literal(table, csv)
            self._put(table, rows)
            self._source(csv, len(rows), [table], note="semilla del universo de Copilot Studio")

    def cargar_laboratorio(self) -> None:
        csv = read_csv(MKT + "identidades_cliente_ground_truth.csv")
        rows = self._literal("lab.identity_ground_truth", csv)
        self._put("lab.identity_ground_truth", rows)
        self._source(csv, len(rows), ["lab.identity_ground_truth"])
        for name, test_set in [("FS_TestSet_Documental.csv", "Documental"), ("FS_TestSet_Metrico_Mixto.csv", "Metrico_Mixto")]:
            csv = read_csv(RAG + "test_sets/" + name)
            rows = [{"test_set": test_set, "row_num": i, "question": r["Question"], "expected_response": r["Expected response"]}
                    for i, r in enumerate(csv.rows, start=1)]
            self._put("lab.rag_test_case", rows)
            self._source(csv, len(rows), ["lab.rag_test_case"])

    def cargar_metadatos(self) -> None:
        files = [(MKT + "catalogo_datasets_marketing_precision.csv", "Catálogo de datasets de marketing de precisión"),
                 (MKT + "diccionario_columnas_marketing_precision.csv", "Diccionario de columnas de marketing de precisión"),
                 (MKT + "mapeo_casos_marketing_precision.csv", "Casos de uso de marketing de precisión y sus datasets"),
                 (REL + "marketing_precision_operational_links.csv", "Enlaces entre marketing de precisión y retail"),
                 (PEOPLE + "diccionario_fuentes_brutas.csv", "Diccionario de las fuentes brutas de RR. HH."),
                 (PEOPLE + "frasohome_diccionario_datos.csv", "Diccionario de datos de people analytics"),
                 (PEOPLE + "plantilla_backlog_indicadores.csv", "Plantilla de backlog de indicadores de RR. HH.")]
        for rel, desc in files:
            csv = read_csv(rel)
            self._put("meta.reference_file", [{"file_path": csv.rel, "column_list": ",".join(csv.header),
                                               "has_bom": csv.has_bom, "description": desc}])
            self._put("meta.reference_row", [{"file_path": csv.rel, "row_num": i,
                                              "row_json": json.dumps(r, ensure_ascii=False)}
                                             for i, r in enumerate(csv.rows, start=1)])
            self._source(csv, len(csv.rows), ["meta.reference_row"], note="fila a fila en JSON")

    # ------------------------------------------------------------ orden de carga

    PASOS = ["cargar_departamentos", "cargar_guardrails", "cargar_calendario", "cargar_alias",
             "cargar_tiendas", "cargar_productos", "cargar_clientes",
             "cargar_pedidos", "cargar_lineas_pedido", "cargar_ventas_pos", "cargar_pagos",
             "cargar_devoluciones_online", "cargar_devoluciones_tienda", "cargar_stock",
             "cargar_empleados", "cargar_movimientos", "cargar_ausencias", "cargar_horas_extra",
             "cargar_formacion", "cargar_evaluaciones", "cargar_salarios", "cargar_semillas_personas",
             "cargar_campanas", "cargar_cupones", "cargar_contactos", "cargar_promociones",
             "cargar_afinidad", "cargar_costes", "cargar_rag", "cargar_laboratorio", "cargar_metadatos"]

    def ejecutar(self) -> None:
        for paso in self.PASOS:
            getattr(self, paso)()

    def issues(self) -> list[dict[str, Any]]:
        return [i.as_row() for log in self.logs for i in log.issues]


# ---------------------------------------------------------------- conversión literal

def _convert(value: str, sql_type: str) -> Any:
    v = L.clean_text(value)
    if v is None:
        return None
    t = sql_type.lower()
    if t.startswith(("int", "smallint", "tinyint", "bigint")):
        return L.parse_int(v)
    if t.startswith(("decimal", "numeric", "float", "real")):
        return L.parse_number(v)
    if t == "bit":
        return L.parse_flag(v)
    if t == "date":
        return L.parse_date(v)
    if t.startswith("datetime"):
        return L.parse_datetime(v)
    return v
