"""FraSoHome Live · despachador de la API.

Orden de comprobaciones en cada petición:
  1. ruta y método;
  2. escrituras: cabecera X-FSH-CSRF: 1 (además de la cookie SameSite=Strict);
  3. sesión y rol (salvo rutas públicas); con contraseña pendiente de cambiar
     solo se admiten las rutas de la propia sesión;
  4. Idempotency-Key en las operaciones que mueven dinero o stock: una
     repetición devuelve la respuesta guardada sin volver a ejecutar;
  5. tras una escritura correcta, se envía lo pendiente del outbox a Cosmos DB.
"""
from __future__ import annotations

import json
import logging
import re

from . import auth, cosmos, db
from .web import HttpError, Request, Response, router

# Registra las rutas de todos los módulos.
from .rutas import (admin, atencion, campanas, catalogo, clientes, devoluciones, inventario,  # noqa: F401
                    laboratorio, paneles, pedidos, portal, rrhh, sesion, tpv, voz_cliente)

log = logging.getLogger("fsh.app")
_IDEM = re.compile(r"^[A-Za-z0-9_\-:.]{8,100}$")
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _normalize(result) -> Response:
    if isinstance(result, Response):
        return result
    if result is None:
        return Response(200, {"ok": True})
    return Response(200, result)


def _replay(req: Request, key: str) -> Response | None:
    row = db.one("SELECT request_path, status_code, response_body FROM app.idempotency_key "
                 "WHERE user_id = ? AND idempotency_key = ?", req.user.user_id, key)
    if row is None:
        return None
    if row["request_path"] != f"{req.method} {req.path}":
        raise HttpError(422, "Esa Idempotency-Key ya se usó en otra operación.", "idempotencia")
    resp = Response(int(row["status_code"]), json.loads(row["response_body"]))
    resp.headers["Idempotent-Replayed"] = "true"
    return resp


def handle(req: Request) -> Response:
    try:
        resp = _dispatch(req)
    except HttpError as exc:
        resp = Response(exc.status, {"error": exc.message, "codigo": exc.code})
    except Exception:  # noqa: BLE001
        log.exception("Error no controlado en %s %s", req.method, req.path)
        resp = Response(500, {"error": "Error interno. Vuelve a intentarlo.", "codigo": "interno"})
    resp.headers.setdefault("Cache-Control", "no-store")
    resp.headers.setdefault("Content-Type", "application/json; charset=utf-8")
    return resp


def _dispatch(req: Request) -> Response:
    rt, params, other = router.match(req.method, req.path)
    if rt is None:
        raise HttpError(405 if other else 404, "Método no permitido." if other else "No existe esa ruta.",
                        "metodo" if other else "ruta")
    req.params = params
    write = req.method in WRITE_METHODS
    if write and req.headers.get("x-fsh-csrf") != "1":
        raise HttpError(403, "Falta la cabecera X-FSH-CSRF.", "csrf")

    if rt.roles is None:
        req.user = auth.current_user(req) if req.cookie(auth.COOKIE) else None
    else:
        user = auth.current_user(req)
        if user is None:
            raise HttpError(401, "Inicia sesión para continuar.", "sin_sesion")
        if user.must_change_password and not rt.allow_pending_password:
            raise HttpError(403, "Cambia tu contraseña antes de continuar.", "cambiar_contrasena")
        if rt.roles and not user.has(*rt.roles):
            raise HttpError(403, "Tu rol no permite esta operación.", "prohibido")
        req.user = user

    key = None
    if rt.idempotent:
        key = req.headers.get("idempotency-key", "")
        if not _IDEM.match(key):
            raise HttpError(400, "Falta la cabecera Idempotency-Key (8 a 100 caracteres).", "idempotencia")
        replay = _replay(req, key)
        if replay is not None:
            return replay

    resp = _normalize(rt.handler(req))

    if key and 200 <= resp.status < 300:
        db.call("app.usp_idempotency_save", idempotency_key=key, user_id=req.user.user_id,
                request_path=f"{req.method} {req.path}", status_code=resp.status,
                response_body=resp.encoded().decode("utf-8"))
    if write and 200 <= resp.status < 300:
        try:
            cosmos.flush()
        except Exception:  # noqa: BLE001 - lo pendiente se reintenta en la siguiente escritura
            log.warning("No se pudo vaciar el outbox", exc_info=True)
    return resp
