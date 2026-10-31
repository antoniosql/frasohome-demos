"""FraSoHome Live · alta y mantenimiento de usuarios de la web.

Lo usan la pantalla de administración (rol admin) y tools/users.py desde la línea de
comandos. Las contraseñas temporales se generan aquí y se muestran una sola vez: en la
base solo queda su hash scrypt, y el usuario debe cambiarla en el primer acceso.
"""
from __future__ import annotations

import re
from typing import Any

from . import auth, db
from .web import HttpError

LOGIN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,49}$")
SCOPE_TYPES = {"customer", "employee", "store"}
SCOPE_PATTERNS = {"customer": r"C\d{4}", "employee": r"FSH\d{4}", "store": r"S\d{3}|ONLINE"}
# Qué ámbito necesita cada rol para poder trabajar.
REQUIRED_SCOPE = {"cliente": "customer", "cajero": "store", "tienda": "store", "empleado": "employee",
                  "manager": "employee"}


def _check_login(login: str) -> str:
    login = (login or "").strip().lower()
    if not LOGIN.match(login):
        raise HttpError(400, "El login debe tener de 3 a 50 caracteres: minúsculas, números, punto, guion o guion bajo.",
                        "peticion_invalida")
    return login


def _check_scope(kind: str, value: str) -> str:
    if kind not in SCOPE_TYPES:
        raise HttpError(400, "Tipo de ámbito no válido (customer, employee o store).", "peticion_invalida")
    value = (value or "").strip().upper()
    if not re.fullmatch(SCOPE_PATTERNS[kind], value):
        raise HttpError(400, f"Valor de ámbito {kind} no válido: {value}.", "peticion_invalida")
    return value


def create(login: str, display_name: str, roles: list[str], scopes: dict[str, list[str]] | None = None,
           password: str | None = None, must_change: bool = True, actor: str | None = None) -> dict[str, Any]:
    login = _check_login(login)
    if not display_name or len(display_name.strip()) < 3:
        raise HttpError(400, "Indica el nombre visible del usuario.", "peticion_invalida")
    roles = sorted(set(roles or []))
    if not roles or not set(roles) <= auth.ROLES:
        raise HttpError(400, f"Roles no válidos. Usa: {', '.join(sorted(auth.ROLES))}.", "peticion_invalida")
    scopes = {k: [_check_scope(k, v) for v in vals] for k, vals in (scopes or {}).items()}
    for role in roles:
        need = REQUIRED_SCOPE.get(role)
        if need and not scopes.get(need):
            raise HttpError(400, f"El rol {role} necesita un ámbito {need}.", "peticion_invalida")
    if password:
        auth.check_policy(password, login)
    temp = password or auth.generate_password()
    digest, salt = auth.hash_password(temp)
    db.call("app.usp_user_create", login=login, display_name=display_name.strip(), password_hash=digest, password_salt=salt,
            scrypt_n=auth.SCRYPT_N, scrypt_r=auth.SCRYPT_R, scrypt_p=auth.SCRYPT_P, must_change=must_change)
    for role in roles:
        db.call("app.usp_user_set_role", login=login, role_name=role, grant=True)
    for kind, values in scopes.items():
        for value in values:
            db.call("app.usp_user_set_scope", login=login, scope_type=kind, scope_value=value, grant=True)
    db.call("app.usp_audit", user_login=actor, action_name="user_create", entity_name="app_user", entity_id=login,
            detail=",".join(roles))
    return {"login": login, "contrasena_temporal": None if password else temp, "roles": roles, "ambitos": scopes}


def reset_password(login: str, actor: str | None = None) -> dict[str, Any]:
    login = _check_login(login)
    temp = auth.generate_password()
    digest, salt = auth.hash_password(temp)
    db.call("app.usp_user_set_password", login=login, password_hash=digest, password_salt=salt, scrypt_n=auth.SCRYPT_N,
            scrypt_r=auth.SCRYPT_R, scrypt_p=auth.SCRYPT_P, must_change=True)
    db.call("app.usp_audit", user_login=actor, action_name="user_reset", entity_name="app_user", entity_id=login, detail=None)
    return {"login": login, "contrasena_temporal": temp}


def set_active(login: str, active: bool, actor: str | None = None) -> None:
    login = _check_login(login)
    db.call("app.usp_user_set_active", login=login, is_active=active)
    db.call("app.usp_audit", user_login=actor, action_name="user_active", entity_name="app_user", entity_id=login,
            detail=str(active))


def set_role(login: str, role: str, grant: bool, actor: str | None = None) -> None:
    if role not in auth.ROLES:
        raise HttpError(400, f"Rol no válido: {role}.", "peticion_invalida")
    db.call("app.usp_user_set_role", login=_check_login(login), role_name=role, grant=grant)
    db.call("app.usp_audit", user_login=actor, action_name="user_role", entity_name="app_user", entity_id=login,
            detail=f"{role}={grant}")


def set_scope(login: str, kind: str, value: str, grant: bool, actor: str | None = None) -> None:
    db.call("app.usp_user_set_scope", login=_check_login(login), scope_type=kind, scope_value=_check_scope(kind, value),
            grant=grant)
    db.call("app.usp_audit", user_login=actor, action_name="user_scope", entity_name="app_user", entity_id=login,
            detail=f"{kind}:{value}={grant}")


def listing() -> list[dict[str, Any]]:
    """Usuarios con sus roles (lista) y ámbitos ({customer|employee|store: [...]})."""
    rows = db.query("""SELECT u.login, u.display_name, u.is_active, u.must_change_password, u.failed_attempts,
                              CASE WHEN u.locked_until > SYSUTCDATETIME() THEN u.locked_until END AS bloqueado_hasta,
                              u.created_at, u.last_login_at,
                              (SELECT STRING_AGG(r.role_name, N',') FROM app.user_role r WHERE r.user_id = u.user_id) AS roles,
                              (SELECT STRING_AGG(s.scope_type + N':' + s.scope_value, N',') FROM app.user_scope s
                                WHERE s.user_id = u.user_id) AS ambitos
                       FROM app.app_user u ORDER BY u.login""")
    for r in rows:
        r["roles"] = sorted((r["roles"] or "").split(",")) if r["roles"] else []
        scopes: dict[str, list[str]] = {}
        for item in (r["ambitos"] or "").split(","):
            if item:
                kind, _, value = item.partition(":")
                scopes.setdefault(kind, []).append(value)
        r["ambitos"] = {k: sorted(v) for k, v in scopes.items()}
    return rows
