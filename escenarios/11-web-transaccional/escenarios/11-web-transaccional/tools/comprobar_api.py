"""FraSoHome Live · comprobaciones de la API publicada (solo biblioteca estándar).

    python comprobar_api.py --url https://proud-bay-08785f303.4.azurestaticapps.net
    python comprobar_api.py --url https://frasohome.dataging.com --json resultado.json

Sin credenciales comprueba lo público y las defensas: salud de SQL y Cosmos, catálogo,
CSRF, mensaje de error genérico, rutas protegidas, /.auth bloqueado y cabeceras de
seguridad. Con FSH_CHECK_LOGIN y FSH_CHECK_PASSWORD (un usuario que ya cambió su
contraseña) prueba además la sesión completa: cookie, /auth/me y salida.
Sale con código 1 si alguna comprobación falla.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from http.client import HTTPResponse


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: D401 - no seguir redirecciones
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def call(base: str, method: str, path: str, body: dict | None = None, headers: dict | None = None,
         cookie: str | None = None, timeout: int = 90) -> tuple[int, dict, object]:
    h = {"Accept": "application/json", "User-Agent": "comprobar_api"}
    h.update(headers or {})
    if cookie:
        h["Cookie"] = cookie
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, method=method, headers=h)
    try:
        resp: HTTPResponse = OPENER.open(req, timeout=timeout)
    except urllib.error.HTTPError as exc:
        resp = exc  # type: ignore[assignment]
    raw = resp.read()
    try:
        payload = json.loads(raw) if raw else None
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = raw[:200].decode("utf-8", "replace")
    headers_out = {k.lower(): v for k, v in resp.headers.items()}
    headers_out["set-cookie-all"] = resp.headers.get_all("Set-Cookie") or []
    return resp.status, headers_out, payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True, help="raíz del sitio, con https://")
    ap.add_argument("--json", help="fichero donde guardar el detalle")
    args = ap.parse_args()
    base = args.url.rstrip("/")
    results: list[dict] = []

    def check(name: str, ok: bool, detail) -> None:
        results.append({"comprobacion": name, "ok": bool(ok), "detalle": detail})
        print(f"[{'OK ' if ok else 'MAL'}] {name}" + ("" if ok else f" · {json.dumps(detail, ensure_ascii=False)[:300]}"))

    # La primera llamada puede despertar la base gratuita.
    status, _, health = call(base, "GET", "/api/salud", timeout=120)
    ok = status == 200 and isinstance(health, dict) and health.get("ok")
    check("Salud: SQL y Cosmos DB responden", ok, health)
    if isinstance(health, dict):
        check("Python 3.11 en las managed Functions", str(health.get("python", "")).startswith("3.11"), health.get("python"))

    status, _, cat = call(base, "GET", "/api/catalogo/productos?tamano=1")
    check("Catálogo público", status == 200 and isinstance(cat, dict) and cat.get("productos"), {"status": status})

    status, _, body = call(base, "POST", "/api/auth/login", {"login": "x", "password": "y"})
    check("Escritura sin cabecera X-FSH-CSRF rechazada", status == 403 and (body or {}).get("codigo") == "csrf", body)

    status, _, body = call(base, "POST", "/api/auth/login", {"login": "no.existe", "password": "mal"},
                           headers={"X-FSH-CSRF": "1"})
    check("Login incorrecto con mensaje genérico", status == 401 and (body or {}).get("codigo") == "credenciales", body)

    status, _, body = call(base, "GET", "/api/clientes")
    check("Ruta protegida sin sesión", status == 401, {"status": status})

    status, headers, _ = call(base, "GET", "/.auth/login/github")
    check("/.auth bloqueado (404, sin redirección)", status == 404 and "location" not in headers, {"status": status})

    status, headers, _ = call(base, "GET", "/")
    csp = headers.get("content-security-policy", "")
    check("Página y cabeceras de seguridad", status == 200 and "default-src 'self'" in csp
          and headers.get("x-frame-options") == "DENY", {"status": status, "csp": csp[:80]})

    login, password = os.environ.get("FSH_CHECK_LOGIN"), os.environ.get("FSH_CHECK_PASSWORD")
    if login and password:
        status, headers, body = call(base, "POST", "/api/auth/login", {"login": login, "password": password},
                                     headers={"X-FSH-CSRF": "1"})
        cookies = headers.get("set-cookie-all", [])
        session = next((c for c in cookies if c.startswith("fsh_session=")), "")
        attrs = session.lower()   # el host de Functions reescribe los atributos en minúsculas
        good = status == 200 and "httponly" in attrs and "secure" in attrs and "domain=" in attrs
        check("Login con cookie HttpOnly, Secure y Domain explícito", good, {"status": status})
        cookie = session.split(";")[0] if session else None
        status, _, me = call(base, "GET", "/api/auth/me", cookie=cookie)
        check("La cookie vuelve: /api/auth/me", status == 200 and (me or {}).get("usuario", {}).get("login") == login,
              {"status": status})
        call(base, "POST", "/api/auth/logout", {}, headers={"X-FSH-CSRF": "1"}, cookie=cookie)
        status, _, _ = call(base, "GET", "/api/auth/me", cookie=cookie)
        check("Tras salir, la sesión ya no vale", status == 401, {"status": status})
    else:
        print("      (sin FSH_CHECK_LOGIN/FSH_CHECK_PASSWORD: no se prueba la sesión completa)")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(results, fh, ensure_ascii=False, indent=2, default=str)
    failed = [r for r in results if not r["ok"]]
    print(f"\n{len(results) - len(failed)} de {len(results)} comprobaciones correctas.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
