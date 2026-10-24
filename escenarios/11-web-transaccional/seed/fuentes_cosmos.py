"""FraSoHome Live · de los CSV de datos/ a los documentos de Cosmos DB.

Un documento por fila del CSV, plano en todo lo que se analiza (regla de diseño
para el mirroring futuro) y con los nombres de columna del CSV, sin los sufijos
_raw y _txt cuando el valor ya está limpio. Cada documento lleva:
  id   el identificador de la fila (WEB-…, EV-…, FB-…)
  pk   la clave de partición del contenedor (sesión, campaña, cliente o empleado)
  origen = "carga_inicial"

Las referencias a SQL (clientes, productos, tiendas, campañas, empleados) se
comprueban contra lo que ya cargó load_sql.py y siguen la misma política:
rechazo, corregido o aviso, con la fila original en quality.data_quality_issue.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Callable

import limpieza as L
from comun import CsvFile, IssueLog, read_csv

MKT = "marketing_precision/raw_csv/"
PEOPLE = "people_analytics/raw_csv/"
TODAY = date.today()


def iso(d: datetime | date | None) -> str | None:
    if d is None:
        return None
    if isinstance(d, datetime):
        return d.strftime("%Y-%m-%dT%H:%M:%S")
    return d.isoformat()


@dataclass
class Referencias:
    """Claves de SQL contra las que se validan los documentos."""
    customers: set[str] = field(default_factory=set)
    products: set[str] = field(default_factory=set)
    stores: set[str] = field(default_factory=set)
    campaigns: set[str] = field(default_factory=set)
    contacts: set[str] = field(default_factory=set)
    employees: set[str] = field(default_factory=set)
    dept_map: dict[str, str] = field(default_factory=dict)


@dataclass
class Contenedor:
    name: str
    csv: CsvFile
    docs: list[dict[str, Any]]
    log: IssueLog


class CargaCosmos:
    def __init__(self, refs: Referencias):
        self.refs = refs
        self.containers: list[Contenedor] = []

    # ------------------------------------------------------------ utilidades

    def _start(self, name: str, rel: str) -> tuple[CsvFile, IssueLog, list[dict[str, Any]]]:
        csv = read_csv(rel)
        log = IssueLog("cosmos", name, csv.rel)
        docs: list[dict[str, Any]] = []
        self.containers.append(Contenedor(name, csv, docs, log))
        return csv, log, docs

    @staticmethod
    def _ref(log: IssueLog, fn: Callable, value: str, known: set[str] | None, key: str, field: str,
             row: dict) -> str | None:
        """Referencia opcional: normaliza; si no existe, queda a None con aviso."""
        val, valid = fn(value)
        if not valid:
            log.warn("id_invalido", f"{field} «{value}» no tiene un formato reconocible: queda vacío.", key, row)
            return None
        if val is not None and L.clean_text(value) != val:
            log.fixed("id_normalizado", f"{field} «{value}» → {val}.", key)
        if val is not None and known is not None and val not in known:
            log.warn("referencia_inexistente", f"{field} {val} no existe: queda vacío.", key, row)
            return None
        return val

    @staticmethod
    def _dt(log: IssueLog, value: str, key: str, field: str, row: dict, allow_future: bool = False) -> str | None:
        if L.clean_text(value) is None:
            return None
        d = L.parse_datetime(value)
        if d is None:
            log.warn("fecha_invalida", f"{field} «{value}» no es una fecha válida: queda vacía.", key, row)
            return None
        if not allow_future and d.date() > TODAY:
            log.fixed("fecha_futura", f"{field} {d:%Y-%m-%d} es posterior a hoy: queda vacía.", key, row)
            return None
        return iso(d)

    @staticmethod
    def _num(log: IssueLog, value: str, key: str, field: str, row: dict, lo: float | None = None,
             hi: float | None = None) -> float | None:
        if L.clean_text(value) is None:
            return None
        n = L.parse_number(value)
        if n is None:
            log.warn("numero_invalido", f"{field} «{value}» no es un número: queda vacío.", key, row)
            return None
        if (lo is not None and n < lo) or (hi is not None and n > hi):
            log.fixed("fuera_de_rango", f"{field} {n} fuera de [{lo}, {hi}]: queda vacío.", key, row)
            return None
        return n

    @staticmethod
    def _int(value: str) -> int | None:
        return L.parse_int(value)

    @staticmethod
    def _flag(value: str) -> bool | None:
        return L.parse_flag(value)

    def _employee(self, log: IssueLog, value: str, key: str, row: dict) -> str | None:
        """Empleado obligatorio (es la clave de partición): si no existe, rechazo."""
        eid, valid = L.employee_id(value)
        if not valid or eid is None:
            log.rejected("id_invalido", f"employee_code «{value}» no tiene un formato reconocible.", key, row)
            return None
        if eid not in self.refs.employees:
            log.rejected("referencia_inexistente", f"empleado {eid} no existe en hr.employee.", key, row)
            return None
        if L.clean_text(value) != eid:
            log.fixed("id_normalizado", f"employee_code «{value}» → {eid}.", key)
        return eid

    def _unique(self, log: IssueLog, seen: set[str], doc_id: str | None, row: dict) -> bool:
        if not doc_id:
            log.rejected("id_vacio", "Fila sin identificador.", None, row)
            return False
        if doc_id in seen:
            log.rejected("duplicado_clave", f"{doc_id} repetido.", doc_id, row)
            return False
        seen.add(doc_id)
        return True

    # ------------------------------------------------------------ marketing

    def eventos_web(self) -> None:
        csv, log, docs = self._start("eventos_web", MKT + "eventos_web_app.csv")
        seen: set[str] = set()
        R = self.refs
        for r in csv.rows:
            k = L.generic_id(r["event_id"])
            if not self._unique(log, seen, k, r):
                continue
            session = L.generic_id(r["session_id"])
            if not session:
                log.rejected("id_vacio", "session_id vacío (es la clave de partición).", k, r)
                continue
            docs.append({
                "id": k, "pk": session, "event_id": k, "fecha_hora_evento": self._dt(log, r["fecha_hora_evento"], k, "fecha_hora_evento", r),
                "session_id": session, "customer_id": self._ref(log, L.customer_id, r["customer_id"], R.customers, k, "customer_id", r),
                "cookie_id": L.generic_id(r["cookie_id"]), "device_id": L.generic_id(r["device_id"]),
                "usuario_online_id": L.generic_id(r["usuario_online_id"]), "canal_adquisicion": L.clean_text(r["canal_adquisicion"]),
                "utm_source": L.clean_text(r["utm_source"]), "utm_medium": L.clean_text(r["utm_medium"]),
                "utm_campaign": L.generic_id(r["utm_campaign"]), "tipo_evento": L.clean_text(r["tipo_evento"]),
                "page_type": L.clean_text(r["page_type"]),
                "product_id": self._ref(log, L.product_id, r["product_id"], R.products, k, "product_id", r),
                "categoria": L.title_category(r["categoria"]), "subcategoria": L.clean_text(r["subcategoria"]),
                "search_term": L.clean_text(r["search_term"]),
                "store_id_interes": self._ref(log, L.store_id, r["store_id_interes"], R.stores, k, "store_id_interes", r),
                "valor_evento_eur": L.parse_number(r["valor_evento_eur"]),
                "order_id": L.order_id(r["order_id"])[0], "consent_analytics": self._flag(r["consent_analytics"]),
                "logged_in_flag": self._flag(r["logged_in_flag"]), "origen": "carga_inicial"})

    def eventos_campana(self) -> None:
        csv, log, docs = self._start("eventos_campana", MKT + "eventos_campana.csv")
        seen: set[str] = set()
        R = self.refs
        for r in csv.rows:
            k = L.generic_id(r["event_id"])
            if not self._unique(log, seen, k, r):
                continue
            camp = L.generic_id(r["campaign_id"])
            if camp not in R.campaigns:
                log.rejected("referencia_inexistente", f"campaign_id {camp} no existe en mkt.campaign.", k, r)
                continue
            contact = L.generic_id(r["contact_id"])
            if contact and contact not in R.contacts:
                log.warn("referencia_inexistente", f"contact_id {contact} no existe: queda vacío.", k, r)
                contact = None
            docs.append({
                "id": k, "pk": camp, "event_id": k, "contact_id": contact, "campaign_id": camp,
                "customer_id": self._ref(log, L.customer_id, r["customer_id"], R.customers, k, "customer_id", r),
                "fecha_evento": self._dt(log, r["fecha_evento"], k, "fecha_evento", r),
                "tipo_evento": L.clean_text(r["tipo_evento"]), "order_id": L.order_id(r["order_id"])[0],
                "ticket_id": L.ticket_id(r["ticket_id"])[0],
                "store_id": self._ref(log, L.store_id, r["store_id"], R.stores, k, "store_id", r),
                "revenue_atribuido_eur": L.parse_number(r["revenue_atribuido_eur"]),
                "margen_atribuido_eur": L.parse_number(r["margen_atribuido_eur"]),
                "device_type": L.clean_text(r["device_type"]), "origen_evento": L.clean_text(r["origen_evento"]),
                "origen": "carga_inicial"})

    def senales_identidad(self) -> None:
        csv, log, docs = self._start("senales_identidad", MKT + "identidades_cliente.csv")
        seen: set[str] = set()
        R = self.refs
        for r in csv.rows:
            k = L.generic_id(r["identity_signal_id"])
            if not self._unique(log, seen, k, r):
                continue
            # customer_id_raw se conserva tal cual: es la señal que la consola de identidad resuelve.
            cand, valid = L.customer_id(r["customer_id_raw"])
            if not valid or cand not in R.customers:
                cand = None
            docs.append({
                "id": k, "pk": cand or "SIN_CLIENTE", "identity_signal_id": k,
                "fecha_evento": self._dt(log, r["fecha_evento"], k, "fecha_evento", r),
                "fuente_sistema": L.clean_text(r["fuente_sistema"]), "tipo_senal": L.clean_text(r["tipo_senal"]),
                "customer_id_raw": r["customer_id_raw"] if L.clean_text(r["customer_id_raw"]) else None,
                "customer_id_candidato": cand,
                "email_hash": L.clean_text(r["email_hash"]), "telefono_hash": L.clean_text(r["telefono_hash"]),
                "tarjeta_fidelizacion_id": L.generic_id(r["tarjeta_fidelizacion_id"]),
                "cookie_id": L.generic_id(r["cookie_id"]), "device_id": L.generic_id(r["device_id"]),
                "app_user_id": L.generic_id(r["app_user_id"]), "usuario_online_id": L.generic_id(r["usuario_online_id"]),
                "order_id": L.order_id(r["order_id"])[0], "ticket_id": L.ticket_id(r["ticket_id"])[0],
                "store_id": self._ref(log, L.store_id, r["store_id"], R.stores, k, "store_id", r),
                "consentimiento_snapshot": self._flag(r["consentimiento_snapshot"]),
                "confianza_origen": L.parse_number(r["confianza_origen"]), "origen": "carga_inicial"})

    def feedback(self) -> None:
        csv, log, docs = self._start("feedback", MKT + "feedback_clientes.csv")
        seen: set[str] = set()
        R = self.refs
        for r in csv.rows:
            k = L.generic_id(r["feedback_id"])
            if not self._unique(log, seen, k, r):
                continue
            cust, valid = L.customer_id(r["customer_id"])
            if not valid or cust not in R.customers:
                log.rejected("referencia_inexistente", f"customer_id «{r['customer_id']}» no existe en el CRM.", k, r)
                continue
            docs.append({
                "id": k, "pk": cust, "feedback_id": k, "fecha_feedback": self._dt(log, r["fecha_feedback"], k, "fecha_feedback", r),
                "customer_id": cust, "order_id": self._ref(log, L.order_id, r["order_id"], None, k, "order_id", r),
                "product_id": self._ref(log, L.product_id, r["product_id"], R.products, k, "product_id", r),
                "store_id": self._ref(log, L.store_id, r["store_id"], R.stores, k, "store_id", r),
                "canal_feedback": L.clean_text(r["canal_feedback"]), "tipo_feedback": L.clean_text(r["tipo_feedback"]),
                "rating_1_5": self._num(log, r["rating_1_5"], k, "rating_1_5", r, 1, 5),
                "nps_0_10": self._num(log, r["nps_0_10"], k, "nps_0_10", r, 0, 10),
                "sentimiento": L.clean_text(r["sentimiento"]), "tema_principal": L.clean_text(r["tema_principal"]),
                "texto_feedback": L.clean_text(r["texto_feedback"]), "publicado_flag": self._flag(r["publicado_flag"]),
                "respondido_flag": self._flag(r["respondido_flag"]), "origen": "carga_inicial"})

    def atencion_cliente(self) -> None:
        csv, log, docs = self._start("atencion_cliente", MKT + "tickets_atencion_cliente.csv")
        seen: set[str] = set()
        R = self.refs
        for r in csv.rows:
            k = L.generic_id(r["service_ticket_id"])
            if not self._unique(log, seen, k, r):
                continue
            cust, valid = L.customer_id(r["customer_id"])
            if not valid or cust not in R.customers:
                log.rejected("referencia_inexistente", f"customer_id «{r['customer_id']}» no existe en el CRM.", k, r)
                continue
            opened = self._dt(log, r["fecha_apertura"], k, "fecha_apertura", r)
            closed = self._dt(log, r["fecha_cierre"], k, "fecha_cierre", r)
            if opened and closed and closed < opened:
                log.fixed("fechas_incoherentes", "fecha_cierre anterior a fecha_apertura: queda vacía.", k, r)
                closed = None
            # La conversación es lo único anidado: no se analiza campo a campo.
            conversacion = []
            if L.clean_text(r["texto_cliente"]):
                conversacion.append({"autor": "cliente", "fecha": opened, "texto": L.clean_text(r["texto_cliente"])})
            if L.clean_text(r["texto_resolucion"]):
                conversacion.append({"autor": "agente", "agente_id": L.generic_id(r["agente_id"]), "fecha": closed,
                                     "texto": L.clean_text(r["texto_resolucion"])})
            docs.append({
                "id": k, "pk": cust, "service_ticket_id": k, "fecha_apertura": opened, "fecha_cierre": closed,
                "customer_id": cust, "order_id": self._ref(log, L.order_id, r["order_id"], None, k, "order_id", r),
                "ticket_id": self._ref(log, L.ticket_id, r["ticket_id"], None, k, "ticket_id", r),
                "store_id": self._ref(log, L.store_id, r["store_id"], R.stores, k, "store_id", r),
                "canal_soporte": L.clean_text(r["canal_soporte"]), "tipo_caso": L.clean_text(r["tipo_caso"]),
                "subtipo_caso": L.clean_text(r["subtipo_caso"]), "motivo_contacto": L.clean_text(r["motivo_contacto"]),
                "prioridad": L.clean_text(r["prioridad"]), "sentimiento_inicial": L.clean_text(r["sentimiento_inicial"]),
                "estado_resolucion": L.clean_text(r["estado_resolucion"]),
                "sla_horas": L.parse_number(r["sla_horas"]), "csat_1_5": self._num(log, r["csat_1_5"], k, "csat_1_5", r, 1, 5),
                "agente_id": L.generic_id(r["agente_id"]),
                "importe_compensacion_eur": L.parse_number(r["importe_compensacion_eur"]),
                "conversacion": conversacion, "origen": "carga_inicial"})

    def creatividades(self) -> None:
        csv, log, docs = self._start("creatividades", MKT + "creatividades_segmento.csv")
        seen: set[str] = set()
        for r in csv.rows:
            k = L.generic_id(r["creative_id"])
            if not self._unique(log, seen, k, r):
                continue
            camp = L.generic_id(r["campaign_id"])
            if camp not in self.refs.campaigns:
                log.rejected("referencia_inexistente", f"campaign_id {camp} no existe en mkt.campaign.", k, r)
                continue
            docs.append({
                "id": k, "pk": camp, "creative_id": k, "campaign_id": camp,
                "microsegmento": L.clean_text(r["microsegmento"]), "canal": L.clean_text(r["canal"]),
                "categoria_objetivo": L.clean_text(r["categoria_objetivo"]), "tono": L.clean_text(r["tono"]),
                "beneficio_principal": L.clean_text(r["beneficio_principal"]), "cta": L.clean_text(r["cta"]),
                "asunto": L.clean_text(r["asunto"]), "copy_corto": L.clean_text(r["copy_corto"]),
                "copy_largo": L.clean_text(r["copy_largo"]), "prueba_social": L.clean_text(r["prueba_social"]),
                "prompt_base": L.clean_text(r["prompt_base"]), "guardrail_legal": L.clean_text(r["guardrail_legal"]),
                # Métricas históricas: no se pueden recalcular (los eventos no llevan la creatividad).
                "open_rate": L.parse_number(r["open_rate"]), "ctr": L.parse_number(r["ctr"]), "cvr": L.parse_number(r["cvr"]),
                "revenue_por_1000_envios_eur": L.parse_number(r["revenue_por_1000_envios_eur"]),
                "winning_variant_flag": self._flag(r["winning_variant_flag"]), "origen": "carga_inicial"})

    # ------------------------------------------------------------ personas

    def encuesta_clima(self) -> None:
        csv, log, docs = self._start("encuesta_clima", PEOPLE + "raw_encuesta_clima_respuestas.csv")
        seen: set[str] = set()
        for r in csv.rows:
            k = L.generic_id(r["respuesta_id"])
            if not self._unique(log, seen, k, r):
                continue
            eid = self._employee(log, r["employee_code_raw"], k, r)
            if eid is None:
                continue
            wave, known = L.mapped(r["oleada_raw"], L.SURVEY_WAVE)
            if not known:
                log.warn("valor_desconocido", f"oleada «{r['oleada_raw']}» no está en la lista.", k, r)
            docs.append({
                "id": k, "pk": eid, "respuesta_id": k, "employee_id": eid,
                "fecha_encuesta": (self._dt(log, r["fecha_encuesta_txt"], k, "fecha_encuesta", r) or "")[:10] or None,
                "oleada": wave, "dimension": L.clean_text(r["dimension_raw"]), "question_code": L.generic_id(r["question_code"]),
                "pregunta_texto": L.clean_text(r["pregunta_texto"]),
                "score": self._num(log, r["score_raw"], k, "score", r, 0, 10),
                "comentario_abierto": L.clean_text(r["comentario_abierto_raw"]),
                "canal_respuesta": L.clean_text(r["canal_respuesta"]), "fuente": L.clean_text(r["fuente"]),
                "origen": "carga_inicial"})

    def entrevistas_salida(self) -> None:
        csv, log, docs = self._start("entrevistas_salida", PEOPLE + "raw_exit_interviews.csv")
        seen: set[str] = set()
        for r in csv.rows:
            k = L.generic_id(r["exit_interview_id"])
            if not self._unique(log, seen, k, r):
                continue
            eid = self._employee(log, r["employee_code_raw"], k, r)
            if eid is None:
                continue
            exit_type, known = L.mapped(r["tipo_salida_raw"], L.EXIT_TYPE)
            if not known:
                log.warn("valor_desconocido", f"tipo_salida «{r['tipo_salida_raw']}» no está en la lista.", k, r)
            docs.append({
                "id": k, "pk": eid, "exit_interview_id": k, "employee_id": eid,
                "fecha_salida": (self._dt(log, r["fecha_salida_txt"], k, "fecha_salida", r) or "")[:10] or None,
                "fecha_entrevista": (self._dt(log, r["fecha_entrevista_txt"], k, "fecha_entrevista", r) or "")[:10] or None,
                "tipo_salida": exit_type, "motivo_salida_rrhh": L.clean_text(r["motivo_salida_rrhh_raw"]),
                "comentario_salida": L.clean_text(r["comentario_salida_raw"]),
                "recomendaria_empresa_1_10": self._num(log, r["recomendaria_empresa_1_10_raw"], k, "recomendaria_empresa_1_10", r, 0, 10),
                "canal_entrevista": L.clean_text(r["canal_entrevista_raw"]), "entrevistador": L.clean_text(r["entrevistador_raw"]),
                "origen": "carga_inicial"})

    PASOS = ["eventos_web", "eventos_campana", "senales_identidad", "feedback", "atencion_cliente",
             "creatividades", "encuesta_clima", "entrevistas_salida"]

    def ejecutar(self, solo: list[str] | None = None) -> None:
        for paso in self.PASOS:
            if solo and paso not in solo:
                continue
            getattr(self, paso)()
