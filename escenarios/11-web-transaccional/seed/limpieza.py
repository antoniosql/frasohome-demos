"""FraSoHome Live · reglas de limpieza de la carga inicial.

Son las reglas del notebook 3 del escenario 02 (fechas en formatos mixtos y con
meses en español, importes con €, coma o punto, identificadores con espacios o
en minúsculas) ampliadas a los dominios de marketing y personas, y escritas sin
pandas para que la carga dependa solo del driver de SQL.

Cada función devuelve el valor limpio o None si no puede interpretarlo; quien
llama decide si eso es un rechazo, una corrección o un aviso.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime

NULL_TOKENS = {"", "na", "n/a", "null", "none", "nan", "?", "??", "???", "-", "sin dato", "desconocido"}

SPANISH_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
    "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


def clean_text(value: str | None) -> str | None:
    """Recorta, colapsa espacios y convierte los marcadores de nulo en None."""
    if value is None:
        return None
    s = re.sub(r"\s+", " ", str(value)).strip()
    if s.lower() in NULL_TOKENS:
        return None
    return s


def fold(value: str) -> str:
    """Minúsculas sin tildes, para comparar categorías escritas de varias formas."""
    s = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(c for c in s if not unicodedata.combining(c))


# ---------------------------------------------------------------- fechas

_DATE_PATTERNS = [
    # (regex, orden de campos) — se prueban en este orden
    (re.compile(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?$"), "ymd"),
    (re.compile(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?$"), "dmy"),
    (re.compile(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{2})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?$"), "dmy2"),
]
_SPANISH_TEXT = re.compile(
    r"^(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+de\s+(\d{4})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?$", re.IGNORECASE)


def parse_datetime(value: str | None) -> datetime | None:
    """ISO, DD/MM/AAAA, DD-MM-AA y «14 de septiembre de 2025 08:25», con o sin hora.
    Día primero, como en España. Devuelve None si la fecha no existe (31/02)."""
    s = clean_text(value)
    if s is None:
        return None
    m = _SPANISH_TEXT.match(s)
    if m:
        month = SPANISH_MONTHS.get(fold(m.group(2)))
        if not month:
            return None
        parts = (int(m.group(3)), month, int(m.group(1)), m.group(4), m.group(5), m.group(6))
    else:
        parts = None
        for rx, order in _DATE_PATTERNS:
            m = rx.match(s)
            if not m:
                continue
            a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if order == "ymd":
                y, mo, d = a, b, c
            elif order == "dmy":
                d, mo, y = a, b, c
            else:
                # Año con dos cifras: «65» es 1965, no 2065 (nadie nace ni se contrata en el futuro).
                d, mo = a, b
                y = 2000 + c if 2000 + c <= date.today().year else 1900 + c
            parts = (y, mo, d, m.group(4), m.group(5), m.group(6))
            break
        if parts is None:
            return None
    y, mo, d, hh, mi, ss = parts
    try:
        return datetime(y, mo, d, int(hh or 0), int(mi or 0), int(ss or 0))
    except ValueError:
        return None


def parse_date(value: str | None) -> date | None:
    dt = parse_datetime(value)
    return dt.date() if dt else None


def parse_month(value: str | None) -> str | None:
    """«2025-04», «2025/04», «04/2025» → «2025-04»."""
    s = clean_text(value)
    if s is None:
        return None
    m = re.fullmatch(r"(\d{4})[-/](\d{1,2})", s)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
    else:
        m = re.fullmatch(r"(\d{1,2})[-/](\d{4})", s)
        if not m:
            return None
        mo, y = int(m.group(1)), int(m.group(2))
    if not 1 <= mo <= 12:
        return None
    return f"{y:04d}-{mo:02d}"


# ---------------------------------------------------------------- números

def parse_number(value: str | None) -> float | None:
    """«€1.136,08», «1,136.08», «12.5 EUR», «40 €», «92,4%» → float.
    Con punto y coma a la vez, el último separador es el decimal; con solo coma,
    la coma es decimal. «100,0,0» no se puede interpretar: None."""
    s = clean_text(value)
    if s is None:
        return None
    s = re.sub(r"(?i)(eur|euro|€|%|\s)", "", s)
    s = re.sub(r"[^0-9,.\-]", "", s)
    if not s or s in {"-", ".", ","}:
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif s.count(",") == 1:
        s = s.replace(",", ".")
    elif s.count(",") > 1:
        return None
    if s.count(".") > 1 or s.count("-") > 1 or ("-" in s and not s.startswith("-")):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_int(value: str | None) -> int | None:
    f = parse_number(value)
    if f is None:
        return None
    return int(round(f))


def money(value: float | None) -> float | None:
    return None if value is None else round(value, 2)


def parse_flag(value: str | None) -> bool | None:
    """1/0, sí/no, S/N, yes/no, true/false."""
    s = clean_text(value)
    if s is None:
        return None
    f = fold(s)
    if f in {"1", "1.0", "si", "s", "yes", "y", "true", "verdadero"}:
        return True
    if f in {"0", "0.0", "no", "n", "false", "falso"}:
        return False
    return None


# ---------------------------------------------------------------- identificadores

def _upper_id(value: str | None) -> str | None:
    s = clean_text(value)
    if s is None:
        return None
    s = s.replace("✓", "").replace(" ", "").upper()
    return s or None


def customer_id(value: str | None) -> tuple[str | None, bool]:
    """(C####, válido). «c0077», « C0012», «C-0010», «CL0002» (prefijo de la tarjeta de
    fidelización) → C####. GUEST, CX123, NULL → (None, False)."""
    s = _upper_id(value)
    if s is None:
        return None, True
    s = s.replace("-", "")
    m = re.fullmatch(r"CL?(\d{1,4})", s)
    if not m:
        return None, False
    return f"C{int(m.group(1)):04d}", True


def product_id(value: str | None) -> tuple[str | None, bool]:
    """(P####, válido). «p1005», «P-1005», «SKU-1019», «PX1004», «P10O5» (letra O) → P####.
    «P101Z» o «p10X1» no se pueden resolver."""
    s = _upper_id(value)
    if s is None:
        return None, True
    s = s.replace("-", "")
    s = re.sub(r"^(SKU|PX)", "P", s)
    if s.startswith("P"):
        s = "P" + s[1:].replace("O", "0")
    m = re.fullmatch(r"P(\d{4})", s)
    if not m:
        return None, False
    return s, True


def store_id(value: str | None) -> tuple[str | None, bool]:
    """(S### u ONLINE, válido). «s1», «S01», «S003 » → S001…"""
    s = _upper_id(value)
    if s is None:
        return None, True
    if s == "ONLINE":
        return s, True
    m = re.fullmatch(r"S(\d{1,3})", s)
    if not m:
        return None, False
    return f"S{int(m.group(1)):03d}", True


def ticket_id(value: str | None) -> tuple[str | None, bool]:
    """(T-######, válido). «500031», «T500540», « T-500069» → T-######."""
    s = _upper_id(value)
    if s is None:
        return None, True
    m = re.fullmatch(r"T?-?(\d{6})", s)
    if not m:
        return None, False
    return f"T-{m.group(1)}", True


def order_id(value: str | None) -> tuple[str | None, bool]:
    s = _upper_id(value)
    if s is None:
        return None, True
    m = re.fullmatch(r"O-?(\d{9})", s)
    if not m:
        return None, False
    return f"O-{m.group(1)}", True


def cashier_id(value: str | None) -> tuple[str | None, bool]:
    """(EMP###, válido). «EMP049✓», «EM070» → EMP###. «EMP00?» no es válido."""
    s = _upper_id(value)
    if s is None:
        return None, True
    m = re.fullmatch(r"EMP?(\d{3})", s)
    if not m:
        return None, False
    return f"EMP{m.group(1)}", True


def till_id(value: str | None) -> tuple[str | None, bool]:
    """(CAJ##, válido). «CJ02» → CAJ02. «CAJXX» no es válido."""
    s = _upper_id(value)
    if s is None:
        return None, True
    m = re.fullmatch(r"CA?J(\d{2})", s)
    if not m:
        return None, False
    return f"CAJ{m.group(1)}", True


def employee_id(value: str | None) -> tuple[str | None, bool]:
    """(FSH####, válido). «fsh0001», « FSH0001 », «FSH-0001» → FSH0001."""
    s = _upper_id(value)
    if s is None:
        return None, True
    s = s.replace("-", "")
    m = re.fullmatch(r"FSH(\d{4})", s)
    if not m:
        return None, False
    return s, True


def generic_id(value: str | None) -> str | None:
    """Identificadores sin formato fijo (cupones, campañas, sesiones): recorte y mayúsculas."""
    return _upper_id(value)


# ---------------------------------------------------------------- categorías

def mapped(value: str | None, mapping: dict[str, str], keep_unknown: bool = True) -> tuple[str | None, bool]:
    """Normaliza con un diccionario cuyas claves están plegadas (fold). (valor, conocido)."""
    s = clean_text(value)
    if s is None:
        return None, True
    hit = mapping.get(fold(s))
    if hit is not None:
        return hit, True
    return (s if keep_unknown else None), False


def title_category(value: str | None) -> str | None:
    """«decoración» → «Decoración», «textil hogar» → «Textil hogar» (como el catálogo)."""
    s = clean_text(value)
    if s is None:
        return None
    return s[:1].upper() + s[1:].lower()


TIER = {"bronce": "Bronce", "bronze": "Bronce", "plata": "Plata", "silver": "Plata", "oro": "Oro",
        "gold": "Oro", "platino": "Platino", "platinum": "Platino", "vip": "VIP"}
COUNTRY = {"es": "ES", "espana": "ES", "spain": "ES"}
PAYMENT_ONLINE = {"tarjeta": "Tarjeta", "tarjeta credito": "Tarjeta", "applepay": "ApplePay", "bizum": "Bizum",
                  "transferencia": "Transferencia", "contrareembolso": "ContraReembolso", "paypal": "PayPal",
                  "desconocido": None}
PAYMENT_STORE = {
    "visa/mastercard": "Tarjeta", "tarjeta credito": "Tarjeta", "credit card": "Tarjeta", "cc": "Tarjeta",
    "tarjeta (credito)": "Tarjeta", "tarjeta": "Tarjeta", "card": "Tarjeta", "debit card": "Tarjeta",
    "tarjeta (debito)": "Tarjeta", "tarjeta debito": "Tarjeta", "dc": "Tarjeta", "debito": "Tarjeta",
    "efectivo": "Efectivo", "cash": "Efectivo", "contado": "Efectivo",
    "tarjeta regalo": "Tarjeta regalo", "tarjeta_regalo": "Tarjeta regalo", "giftcard": "Tarjeta regalo",
    "gift card": "Tarjeta regalo",
    "vale": "Vale", "vale devolucion": "Vale", "voucher": "Vale", "cupon": "Cupón",
    "bizum": "Bizum", "financiacion": "Financiación", "financing": "Financiación", "aplazado": "Financiación",
}
RETURN_METHOD_ONLINE = {"tienda": "Tienda", "punto pack": "Punto Pack", "envio": "Envío"}
REFUND_METHOD = {"transferencia": "Transferencia", "tarjeta regalo": "Tarjeta regalo", "vale": "Vale",
                 "tarjeta": "Tarjeta", "tarjetaa": "Tarjeta", "efectivo": "Efectivo", "cupon": "Cupón"}
ORDER_ORIGIN = {"web": "web", "app": "app", "marketplace": "marketplace"}
REGION = {"levante": "Levante", "centro": "Centro", "central": "Centro", "cataluna": "Cataluña",
          "andalucia": "Andalucía", "norte": "Norte"}

GENDER_HR = {"f": "F", "mujer": "F", "m": "M", "hombre": "M", "no declarado": "No declarado"}
STATUS_HR = {"activo": "Activo", "activo/a": "Activo", "baja": "Baja", "baja definitiva": "Baja"}
EXIT_TYPE = {"voluntaria": "Voluntaria", "baja voluntaria": "Voluntaria", "baja vol.": "Voluntaria",
             "renuncia": "Voluntaria", "dimision": "Voluntaria",
             "involuntaria/fin contrato": "Involuntaria/fin contrato", "no voluntaria": "Involuntaria/fin contrato",
             "despido/fin contrato": "Involuntaria/fin contrato", "fin contrato": "Involuntaria/fin contrato",
             "baja inv.": "Involuntaria/fin contrato"}
LEVEL = {"junior": "Junior", "jr": "Junior", "n1": "Junior", "semi senior": "Semi Senior",
         "semi-senior": "Semi Senior", "ssr": "Semi Senior", "n2": "Semi Senior", "senior": "Senior",
         "sr": "Senior", "n3": "Senior", "manager": "Manager", "n4": "Manager", "responsable": "Manager"}
CONTRACT = {"indefinido": "Indefinido", "contrato indefinido": "Indefinido", "fijo": "Indefinido",
            "temporal": "Temporal", "eventual": "Temporal", "duracion determinada": "Temporal",
            "fijo discontinuo": "Fijo discontinuo"}
SCHEDULE = {"completa": "Completa", "jornada completa": "Completa", "full time": "Completa",
            "parcial": "Parcial", "media jornada": "Parcial", "part time": "Parcial"}
JUSTIFIED = {"si": "Sí", "no": "No", "pendiente": "Pendiente"}
APPROVAL = {"aprobada": "Aprobada", "pendiente": "Pendiente", "rechazada": "Rechazada"}
TRAINING_STATUS = {"completado": "Completado", "finalizado": "Completado", "en curso": "En curso",
                   "no completado": "No completado", "inscrito": "Inscrito"}
MOVEMENT_TYPE = {"alta": "Alta", "incorporacion": "Alta", "baja": "Baja", "baja voluntaria": "Baja",
                 "voluntaria": "Baja", "baja no voluntaria": "Baja", "involuntaria/fin contrato": "Baja",
                 "promocion": "Promoción", "cambio nivel": "Promoción",
                 "revision salarial": "Revisión salarial", "ajuste salario": "Revisión salarial",
                 "movilidad interna": "Movilidad interna", "cambio departamento": "Movilidad interna",
                 "transferencia": "Movilidad interna"}
SURVEY_WAVE = {"pulse_q1_2026": "Pulso 2026 Q1", "pulso 2026 q1": "Pulso 2026 Q1",
               "clima anual 2026": "Clima anual 2026"}
