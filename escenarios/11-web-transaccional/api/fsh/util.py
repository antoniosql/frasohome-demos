"""FraSoHome Live · utilidades de validación de las rutas."""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Iterable

from .web import HttpError, Request, bad_request

ID_PATTERNS = {
    "customer": r"C\d{4}", "product": r"P\d{4}", "store": r"S\d{3}|ONLINE", "order": r"O-\d{9}",
    "order_line": r"OL-\d{7}", "ticket": r"T-\d{6}", "ticket_line": r"TL-\d{6}", "employee": r"FSH\d{4}",
    "campaign": r"CAM-\d{4}-\d{3}", "promo": r"PROMO-\d{4}", "return": r"R[OT]-\d{4}-\d{5}",
    "till": r"CAJ\d{2}", "coupon_code": r"FSH\d{8}",
}


def field(data: dict[str, Any], name: str, *, required: bool = True, max_len: int = 500, default: Any = None) -> Any:
    value = data.get(name, default)
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            value = None
        elif len(value) > max_len:
            raise bad_request(f"«{name}» es demasiado largo (máximo {max_len} caracteres).")
    if value is None and required:
        raise bad_request(f"Falta «{name}».")
    return value


def an_id(value: Any, kind: str, name: str | None = None, required: bool = True) -> str | None:
    if value in (None, ""):
        if required:
            raise bad_request(f"Falta «{name or kind}».")
        return None
    text = str(value).strip().upper()
    if not re.fullmatch(ID_PATTERNS[kind], text):
        raise bad_request(f"«{name or kind}» no tiene un formato válido.")
    return text


def number(value: Any, name: str, *, lo: float | None = None, hi: float | None = None, required: bool = True,
           integer: bool = False) -> Any:
    if value in (None, ""):
        if required:
            raise bad_request(f"Falta «{name}».")
        return None
    try:
        n = int(value) if integer else float(value)
        if integer and float(value) != int(value):
            raise ValueError
    except (TypeError, ValueError):
        raise bad_request(f"«{name}» debe ser {'un entero' if integer else 'un número'}.") from None
    if (lo is not None and n < lo) or (hi is not None and n > hi):
        raise bad_request(f"«{name}» debe estar entre {lo} y {hi}.")
    return n


def a_date(value: Any, name: str, required: bool = True) -> date | None:
    if value in (None, ""):
        if required:
            raise bad_request(f"Falta «{name}».")
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        raise bad_request(f"«{name}» debe ser una fecha AAAA-MM-DD.") from None


def a_datetime(value: Any, name: str, required: bool = True) -> datetime | None:
    if value in (None, ""):
        if required:
            raise bad_request(f"Falta «{name}».")
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", ""))
    except ValueError:
        raise bad_request(f"«{name}» debe ser una fecha y hora ISO.") from None


def one_of(value: Any, options: Iterable[str], name: str, required: bool = True) -> str | None:
    if value in (None, ""):
        if required:
            raise bad_request(f"Falta «{name}».")
        return None
    opts = list(options)
    if value not in opts:
        raise bad_request(f"«{name}» debe ser uno de: {', '.join(opts)}.")
    return value


def flag(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "si", "sí", "yes"}


def lines(data: dict[str, Any], name: str = "lineas", max_lines: int = 30) -> list[dict[str, Any]]:
    raw = data.get(name)
    if not isinstance(raw, list) or not raw:
        raise bad_request(f"«{name}» debe ser una lista con al menos una línea.")
    if len(raw) > max_lines:
        raise bad_request(f"Como mucho {max_lines} líneas.")
    out = []
    for i, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise bad_request(f"La línea {i} no es un objeto.")
        out.append({"product_id": an_id(item.get("product_id"), "product", f"lineas[{i}].product_id"),
                    "quantity": number(item.get("cantidad", item.get("quantity")), f"lineas[{i}].cantidad",
                                       lo=1, hi=20, integer=True)})
    return out


def page(req: Request, default_size: int = 50, max_size: int = 200) -> tuple[int, int]:
    """(desplazamiento, tamaño) a partir de ?pagina=1&tamano=50."""
    size = req.int_arg("tamano", default_size, 1, max_size)
    number_ = req.int_arg("pagina", 1, 1, 100_000)
    return (number_ - 1) * size, size


def like(text: str | None) -> str | None:
    if not text:
        return None
    text = text.strip()[:60]
    return "%" + text.replace("[", "[[]").replace("%", "[%]").replace("_", "[_]") + "%"


def require_any(user, *roles: str) -> None:
    if not user.has(*roles):
        raise HttpError(403, "Tu rol no permite esta operación.", "prohibido")
