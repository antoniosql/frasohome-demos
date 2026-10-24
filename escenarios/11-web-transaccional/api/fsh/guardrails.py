"""FraSoHome Live · comprobación de creatividades contra las reglas de marca (ref.brand_guardrail).

Reglas explícitas y explicables en clase: listas de expresiones por regla. No sustituyen
una revisión humana; sirven para que el editor de creatividades avise y bloquee lo obvio.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from . import db


def _fold(text: str) -> str:
    s = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


AGGRESSIVE = ["!!!", "¡¡", "ultima oportunidad", "brutal", "locura", "no te lo puedes perder", "increible pero cierto",
              "aprovecha ya", "ahora o nunca"]
STOCK_PROMISES = ["stock garantizado", "siempre disponible", "nunca se agota", "disponibilidad garantizada",
                  "lo tenemos seguro", "sin roturas de stock"]
PRICE_CLAIMS = ["el mas barato", "los mas baratos", "mas barato que nadie", "mejor precio garantizado", "precio mas bajo",
                "precios imbatibles", "imbatible"]
SENSITIVE = ["embaraz", "divorci", "enfermedad", "tu salud", "religion", "orientacion sexual", "deudas", "tu edad",
             "sabemos que", "hemos visto que estas", "tu pareja te"]
URGENCY = ["solo hoy", "corre", "se agota", "ultimas unidades", "quedan pocas", "date prisa", "termina en horas"]
CONDITIONS = ["condiciones", "valido hasta", "válido hasta", "hasta el", "consulta", "minimo", "mínimo", "bases",
              "compra minima", "no acumulable", "aplica a"]
TECH_CLAIMS = ["ignifug", "garantia de por vida", "irrompible", "100% organico", "100 % organico", "a prueba de todo",
               "resistente al fuego"]
CTAS = ["reservar ahora", "activar oferta", "explorar coleccion", "descubrir", "ver seleccion", "comprar hoy", "compra ya",
        "comprar ahora", "ver ofertas", "visitanos", "reserva ya"]


def _rules() -> dict[str, dict[str, Any]]:
    return {r["rule_id"]: r for r in db.query(
        "SELECT rule_id, rule_category, rule_description, applies_to_channel, severity FROM ref.brand_guardrail")}


def check(creative: dict[str, Any], campaign: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Devuelve las infracciones: [{regla_id, severidad, descripcion, detalle}]."""
    rules = _rules()
    channel = (creative.get("canal") or "").lower()
    texts = " · ".join(str(creative.get(k) or "") for k in ("asunto", "copy_corto", "copy_largo", "prueba_social", "cta"))
    t = _fold(texts)
    found: list[dict[str, Any]] = []

    def hit(rule_id: str, detail: str, severity: str | None = None) -> None:
        rule = rules.get(rule_id, {})
        applies = (rule.get("applies_to_channel") or "all").lower()
        if applies != "all" and channel and channel not in [a.strip() for a in applies.split(",")]:
            return
        found.append({"regla_id": rule_id, "severidad": severity or rule.get("severity", "media"),
                      "descripcion": rule.get("rule_description", ""), "detalle": detail})

    def any_of(words: list[str]) -> list[str]:
        return [w for w in words if _fold(w) in t]

    if (w := any_of(AGGRESSIVE)) or re.search(r"\b[A-ZÁÉÍÓÚÑ]{4,}\b(\s+\b[A-ZÁÉÍÓÚÑ]{4,}\b){2,}", texts):
        hit("GR-001", "Lenguaje agresivo o en mayúsculas: " + (", ".join(w) if w else "varias palabras seguidas en mayúsculas"))
    if w := any_of(STOCK_PROMISES):
        hit("GR-002", "Promesa de stock: " + ", ".join(w))
    if w := any_of(PRICE_CLAIMS):
        hit("GR-003", "Claim absoluto de precio: " + ", ".join(w))
    if w := any_of(SENSITIVE):
        hit("GR-004", "Referencia a atributos personales: " + ", ".join(w))
        hit("GR-007", "Personalización por rasgos sensibles: " + ", ".join(w))
    if w := any_of(URGENCY):
        post_return = (creative.get("microsegmento") or (campaign or {}).get("target_segment")) == "POST_DEVOLUCION"
        hit("GR-005", "Urgencia" + (" en post-devolución" if post_return else "") + ": " + ", ".join(w),
            severity="alta" if post_return else None)
    offer = (campaign or {}).get("offer_type")
    if (re.search(r"\d+\s*(%|€)", texts) or offer in ("descuento_pct", "cupon_importe")) and not any_of(CONDITIONS):
        if re.search(r"\d+\s*(%|€)", texts):
            hit("GR-006", "Menciona un descuento sin condiciones legibles (validez, mínimo, aplicación).")
    if w := any_of(TECH_CLAIMS):
        hit("GR-009", "Propiedad técnica no respaldada por el catálogo: " + ", ".join(w))
    if channel in ("sms", "push") and "tienda" in t and (campaign or {}).get("target_segment") != "LOCAL_STORE":
        hit("GR-011", "Menciona la tienda en una campaña que no es local.")
    ctas = [c for c in CTAS if _fold(c) in _fold(" ".join(str(creative.get(k) or "") for k in ("copy_corto", "copy_largo")))]
    if creative.get("cta"):
        ctas = sorted(set(ctas) | {_fold(str(creative["cta"]))})
    if len(ctas) > 1:
        hit("GR-012", "Más de una llamada a la acción: " + ", ".join(ctas))
    if channel == "sms" and len(str(creative.get("copy_corto") or "")) > 160:
        found.append({"regla_id": "FORMATO", "severidad": "alta", "descripcion": "Un SMS admite 160 caracteres.",
                      "detalle": f"copy_corto tiene {len(str(creative.get('copy_corto')))} caracteres."})
    return found
