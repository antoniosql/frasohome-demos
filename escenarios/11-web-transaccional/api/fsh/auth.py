"""FraSoHome Live · usuarios, contraseñas y sesiones propios.

- Contraseñas con hashlib.scrypt (biblioteca estándar) y sal por usuario.
- Sesión: token aleatorio de 32 bytes en la cookie fsh_session (HttpOnly, Secure,
  SameSite=Strict, 8 horas). En la base solo se guarda su SHA-256.
- Bloqueo de 15 minutos tras 5 fallos (app.usp_login_failed) y mensaje genérico.
- Cada usuario tiene roles y ámbitos (cliente, empleado o tienda a los que se ata).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import string
from dataclasses import dataclass, field
from typing import Any

from . import db
from .web import HttpError, Request, Response, forbidden

COOKIE = "fsh_session"
SESSION_HOURS = int(os.environ.get("FSH_SESSION_HOURS", "8"))
SCRYPT_N, SCRYPT_R, SCRYPT_P, KEY_LEN = 2 ** 14, 8, 1, 64
ROLES = {"cliente", "cajero", "tienda", "atencion", "marketing", "rrhh", "manager", "empleado", "direccion",
         "profesor", "admin"}
GENERIC_LOGIN_ERROR = "Usuario o contraseña incorrectos."
_DUMMY_SALT = b"\x00" * 16


# ------------------------------------------------------------------ contraseñas

def hash_password(password: str, salt: bytes | None = None, n: int = SCRYPT_N, r: int = SCRYPT_R,
                  p: int = SCRYPT_P) -> tuple[bytes, bytes]:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=KEY_LEN, maxmem=64 * 1024 * 1024)
    return digest, salt


def verify_password(password: str, digest: bytes, salt: bytes, n: int, r: int, p: int) -> bool:
    candidate, _ = hash_password(password, salt, n, r, p)
    return hmac.compare_digest(candidate, bytes(digest))


def generate_password(length: int = 16) -> str:
    """Contraseña aleatoria sin caracteres ambiguos (sin 0/O, 1/l/I)."""
    alphabet = "".join(c for c in string.ascii_letters + string.digits if c not in "0O1lI") + "-_.!"
    while True:
        pw = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in pw) and any(c.isupper() for c in pw) and any(c.isdigit() for c in pw)):
            return pw


def check_policy(password: str, login: str) -> None:
    if len(password) < 12:
        raise HttpError(422, "La contraseña debe tener al menos 12 caracteres.", "politica")
    if login.lower() in password.lower():
        raise HttpError(422, "La contraseña no puede contener el usuario.", "politica")
    classes = sum([any(c.islower() for c in password), any(c.isupper() for c in password),
                   any(c.isdigit() for c in password), any(not c.isalnum() for c in password)])
    if classes < 3:
        raise HttpError(422, "Usa al menos tres tipos de carácter: minúsculas, mayúsculas, números o símbolos.", "politica")


def token_hash(token: str) -> bytes:
    return hashlib.sha256(token.encode("ascii")).digest()


# ------------------------------------------------------------------ usuario de la petición

@dataclass
class User:
    user_id: int
    login: str
    display_name: str
    roles: set[str]
    scopes: dict[str, set[str]] = field(default_factory=dict)
    must_change_password: bool = False

    def has(self, *roles: str) -> bool:
        return bool(self.roles.intersection(roles)) or "admin" in self.roles

    def scope(self, kind: str) -> set[str]:
        return self.scopes.get(kind, set())

    def single(self, kind: str) -> str | None:
        values = sorted(self.scope(kind))
        return values[0] if values else None

    @property
    def customer_id(self) -> str | None:
        return self.single("customer")

    @property
    def employee_id(self) -> str | None:
        return self.single("employee")

    @property
    def stores(self) -> set[str]:
        return self.scope("store")

    def public(self) -> dict[str, Any]:
        return {"login": self.login, "nombre": self.display_name, "roles": sorted(self.roles),
                "ambitos": {k: sorted(v) for k, v in self.scopes.items()},
                "debe_cambiar_contrasena": self.must_change_password}


def require(user: User, *roles: str) -> None:
    if not user.has(*roles):
        raise forbidden()


def require_store(user: User, store_id: str) -> None:
    """El usuario puede operar esa tienda: admin, o la tiene en su ámbito."""
    if "admin" in user.roles:
        return
    if store_id not in user.stores:
        raise forbidden("Esa tienda no está en tu ámbito.")


def store_for(user: User, requested: str | None) -> str:
    """Tienda con la que opera el usuario: la pedida (si puede) o la única de su ámbito."""
    if requested:
        require_store(user, requested)
        return requested
    stores = sorted(user.stores)
    if len(stores) == 1:
        return stores[0]
    if "admin" in user.roles:
        raise HttpError(400, "Indica la tienda.", "peticion_invalida")
    raise forbidden("No tienes una tienda asignada.")


def _session_row(token: str) -> dict[str, Any] | None:
    return db.one(
        """SELECT u.user_id, u.login, u.display_name, u.must_change_password,
                  (SELECT r.role_name AS r FROM app.user_role r WHERE r.user_id = u.user_id FOR JSON PATH) AS roles,
                  (SELECT sc.scope_type AS t, sc.scope_value AS v FROM app.user_scope sc WHERE sc.user_id = u.user_id
                   FOR JSON PATH) AS scopes
           FROM app.user_session s
           JOIN app.app_user u ON u.user_id = s.user_id
           WHERE s.session_hash = ? AND s.expires_at > SYSUTCDATETIME() AND u.is_active = 1""",
        token_hash(token))


def _user_from_row(row: dict[str, Any]) -> User:
    roles = {r["r"] for r in json.loads(row["roles"] or "[]")}
    scopes: dict[str, set[str]] = {}
    for s in json.loads(row["scopes"] or "[]"):
        scopes.setdefault(s["t"], set()).add(s["v"])
    return User(int(row["user_id"]), row["login"], row["display_name"], roles, scopes, bool(row["must_change_password"]))


def current_user(req: Request) -> User | None:
    token = req.cookie(COOKIE)
    if not token or len(token) > 100:
        return None
    try:
        token.encode("ascii")
    except UnicodeEncodeError:
        return None
    row = _session_row(token)
    return _user_from_row(row) if row else None


# ------------------------------------------------------------------ cookies

def session_cookie(req: Request, token: str, max_age: int) -> str:
    parts = [f"{COOKIE}={token}", "Path=/", f"Max-Age={max_age}", "HttpOnly", "Secure", "SameSite=Strict"]
    host = req.public_host()
    # SWA descarta Set-Cookie si el worker deja «domain=» vacío: se pone el dominio explícito.
    if host and "." in host and not host.replace(".", "").isdigit():
        parts.insert(2, f"Domain={host}")
    return "; ".join(parts)


def new_session(req: Request, login: str) -> str:
    token = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("ascii")
    db.call("app.usp_login_succeeded", login=login, session_hash=token_hash(token), hours=SESSION_HOURS,
            user_agent=(req.headers.get("user-agent") or "")[:300])
    return token


# ------------------------------------------------------------------ casos de uso

def login(req: Request) -> Response:
    data = req.json()
    login_name = str(data.get("login") or "").strip().lower()
    password = str(data.get("password") or "")
    if not login_name or not password or len(login_name) > 100 or len(password) > 200:
        raise HttpError(401, GENERIC_LOGIN_ERROR, "credenciales")
    row = db.one("""SELECT login, password_hash, password_salt, scrypt_n, scrypt_r, scrypt_p, is_active,
                           CASE WHEN locked_until > SYSUTCDATETIME() THEN 1 ELSE 0 END AS locked
                    FROM app.app_user WHERE login = ?""", login_name)
    if row is None:
        hash_password(password, _DUMMY_SALT)  # mismo tiempo que con un usuario real
        raise HttpError(401, GENERIC_LOGIN_ERROR, "credenciales")
    good = verify_password(password, row["password_hash"], row["password_salt"], row["scrypt_n"], row["scrypt_r"], row["scrypt_p"])
    if row["locked"] or not row["is_active"] or not good:
        if not row["locked"]:
            db.call("app.usp_login_failed", login=login_name)
        raise HttpError(401, GENERIC_LOGIN_ERROR, "credenciales")
    token = new_session(req, login_name)
    user = _user_from_row(_session_row(token))
    resp = Response(200, {"usuario": user.public()})
    resp.cookies.append(session_cookie(req, token, SESSION_HOURS * 3600))
    return resp


def logout(req: Request) -> Response:
    token = req.cookie(COOKIE)
    if token:
        db.call("app.usp_logout", session_hash=token_hash(token))
    resp = Response(200, {"ok": True})
    resp.cookies.append(session_cookie(req, "", 0))
    return resp


def change_password(req: Request) -> Response:
    user: User = req.user
    data = req.json()
    current = str(data.get("actual") or "")
    new = str(data.get("nueva") or "")
    row = db.one("SELECT password_hash, password_salt, scrypt_n, scrypt_r, scrypt_p FROM app.app_user WHERE user_id = ?",
                 user.user_id)
    if not row or not verify_password(current, row["password_hash"], row["password_salt"], row["scrypt_n"],
                                      row["scrypt_r"], row["scrypt_p"]):
        raise HttpError(422, "La contraseña actual no es correcta.", "credenciales")
    if new == current:
        raise HttpError(422, "La nueva contraseña debe ser distinta de la actual.", "politica")
    check_policy(new, user.login)
    digest, salt = hash_password(new)
    db.call("app.usp_user_set_password", login=user.login, password_hash=digest, password_salt=salt,
            scrypt_n=SCRYPT_N, scrypt_r=SCRYPT_R, scrypt_p=SCRYPT_P, must_change=False)
    # Cambiar la contraseña cierra todas las sesiones: se abre una nueva para seguir.
    token = new_session(req, user.login)
    resp = Response(200, {"ok": True})
    resp.cookies.append(session_cookie(req, token, SESSION_HOURS * 3600))
    return resp
