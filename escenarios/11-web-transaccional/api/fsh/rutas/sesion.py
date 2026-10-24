"""Sesión y estado de la API."""
from __future__ import annotations

import os
import platform

from .. import auth, cosmos, db
from ..web import PUBLIC, Request, route


@route("GET", "/salud", PUBLIC)
def salud(req: Request):
    """Estado de SQL y Cosmos DB (sin datos)."""
    out = {"ok": True, "python": platform.python_version(), "version": os.environ.get("FSH_VERSION", "dev")}
    try:
        out["sql"] = {"ok": True, "hora_servidor": db.scalar("SELECT SYSUTCDATETIME()")}
    except Exception as exc:  # noqa: BLE001
        out["ok"] = False
        out["sql"] = {"ok": False, "error": getattr(exc, "message", "sin conexión")}
    try:
        cosmos.database().read()
        pending = db.scalar("SELECT COUNT(*) FROM app.outbox WHERE sent_at IS NULL") if out["sql"]["ok"] else None
        out["cosmos"] = {"ok": True, "outbox_pendiente": pending}
    except Exception as exc:  # noqa: BLE001
        out["ok"] = False
        out["cosmos"] = {"ok": False, "error": getattr(exc, "message", "sin conexión")}
    return out


@route("POST", "/auth/login", PUBLIC)
def login(req: Request):
    return auth.login(req)


@route("POST", "/auth/logout", PUBLIC)
def logout(req: Request):
    return auth.logout(req)


@route("GET", "/auth/me", "auth", allow_pending_password=True)
def me(req: Request):
    return {"usuario": req.user.public()}


@route("POST", "/auth/password", "auth", allow_pending_password=True)
def password(req: Request):
    return auth.change_password(req)
