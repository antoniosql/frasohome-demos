"""FraSoHome Live · capa HTTP mínima sin dependencias.

Independiente de azure.functions para poder probar la API con pytest sin el host
de Functions: function_app.py traduce func.HttpRequest a `Request` y `Response`
a func.HttpResponse.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable
from urllib.parse import parse_qs


class HttpError(Exception):
    """Error que se devuelve al cliente tal cual: {"error": mensaje}."""

    def __init__(self, status: int, message: str, code: str | None = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.code = code


def bad_request(message: str) -> HttpError:
    return HttpError(400, message, "peticion_invalida")


def not_found(message: str = "No existe.") -> HttpError:
    return HttpError(404, message, "no_encontrado")


def forbidden(message: str = "No tienes permiso para esto.") -> HttpError:
    return HttpError(403, message, "prohibido")


@dataclass
class Request:
    method: str
    path: str                                   # sin prefijo /api, empieza por /
    headers: dict[str, str]                     # claves en minúsculas
    query: dict[str, str]
    body: bytes = b""
    params: dict[str, str] = field(default_factory=dict)   # de la ruta
    user: Any = None                                        # fsh.auth.User

    @classmethod
    def build(cls, method: str, url_path: str, headers: dict[str, str], body: bytes = b"",
              query_string: str = "") -> "Request":
        path = "/" + url_path.strip("/")
        if path.startswith("/api/") or path == "/api":
            path = path[4:] or "/"
        q = {k: v[-1] for k, v in parse_qs(query_string, keep_blank_values=True).items()}
        return cls(method.upper(), path, {k.lower(): v for k, v in headers.items()}, q, body or b"")

    def json(self) -> dict[str, Any]:
        if not self.body:
            return {}
        try:
            data = json.loads(self.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise bad_request("El cuerpo no es JSON válido.") from None
        if not isinstance(data, dict):
            raise bad_request("El cuerpo debe ser un objeto JSON.")
        return data

    def cookie(self, name: str) -> str | None:
        raw = self.headers.get("cookie", "")
        for part in raw.split(";"):
            k, _, v = part.strip().partition("=")
            if k == name:
                return v
        return None

    def public_host(self) -> str | None:
        """Host público de la petición. SWA lo pasa en X-Forwarded-Host: hace falta para
        poner Domain explícito en la cookie (sin él, SWA descarta la cabecera Set-Cookie)."""
        host = self.headers.get("x-forwarded-host") or self.headers.get("host") or ""
        host = host.split(",")[0].strip().split(":")[0]
        return host or None

    def int_arg(self, name: str, default: int, lo: int = 1, hi: int = 10_000) -> int:
        raw = self.query.get(name)
        if raw in (None, ""):
            return default
        try:
            v = int(raw)
        except ValueError:
            raise bad_request(f"«{name}» debe ser un número entero.") from None
        return max(lo, min(hi, v))


@dataclass
class Response:
    status: int = 200
    body: Any = None
    headers: dict[str, str] = field(default_factory=dict)
    cookies: list[str] = field(default_factory=list)

    def encoded(self) -> bytes:
        if self.body is None:
            return b""
        return json.dumps(self.body, ensure_ascii=False, default=json_default).encode("utf-8")


def json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    raise TypeError(f"No serializable: {type(value)}")


def ok(body: Any = None, status: int = 200) -> Response:
    return Response(status=status, body=body if body is not None else {"ok": True})


# ------------------------------------------------------------------ enrutador

Handler = Callable[[Request], Response | dict | list | None]


@dataclass
class Route:
    method: str
    pattern: re.Pattern
    template: str
    handler: Handler
    roles: frozenset[str] | None      # None = pública
    idempotent: bool
    allow_pending_password: bool


class Router:
    def __init__(self) -> None:
        self.routes: list[Route] = []

    def add(self, method: str, template: str, handler: Handler, roles: set[str] | None,
            idempotent: bool = False, allow_pending_password: bool = False) -> None:
        regex = "^" + re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", template.rstrip("/") or "/") + "$"
        self.routes.append(Route(method.upper(), re.compile(regex), template, handler,
                                 frozenset(roles) if roles is not None else None, idempotent,
                                 allow_pending_password))

    def match(self, method: str, path: str) -> tuple[Route | None, dict[str, str], bool]:
        """(ruta, parámetros, la ruta existe con otro método)."""
        path = path.rstrip("/") or "/"
        other = False
        for r in self.routes:
            m = r.pattern.match(path)
            if m:
                if r.method == method:
                    return r, m.groupdict(), False
                other = True
        return None, {}, other


router = Router()
PUBLIC = None


def route(method: str, template: str, roles: set[str] | None | str = "auth", *, idempotent: bool = False,
          allow_pending_password: bool = False):
    """Registra un endpoint.
    roles: None (pública), "auth" (cualquier usuario con sesión) o un conjunto de roles."""
    def deco(fn: Handler) -> Handler:
        rs: set[str] | None
        if roles == "auth":
            rs = set()
        else:
            rs = roles  # type: ignore[assignment]
        router.add(method, template, fn, rs, idempotent, allow_pending_password)
        return fn
    return deco
