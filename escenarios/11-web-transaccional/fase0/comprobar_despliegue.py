"""FraSoHome Live · fase 0 · comprueba el despliegue real desde fuera.

Solo usa la biblioteca estándar. Ejemplos:
  python comprobar_despliegue.py --url https://<nombre>.azurestaticapps.net
  python comprobar_despliegue.py --url https://frasohome.dataging.com

Comprobaciones:
  1. La página carga y trae las cabeceras de seguridad
  2. Las rutas /.auth/* de la autenticación integrada devuelven 404 (sin redirigir)
  3. /api/health conecta a Azure SQL (mssql-python y pyodbc) y a Cosmos DB
  4. La cookie HttpOnly; Secure; SameSite=Strict se fija y vuelve en la siguiente petición
  5. Sin la cabecera X-FSH-CSRF la API rechaza la escritura
Sale con código 1 si alguna falla. --json guarda el detalle en un fichero.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: D401
        return None


def request(opener, url, method="GET", headers=None, timeout=90):
    req = urllib.request.Request(url, method=method, headers=headers or {}, data=b"" if method == "POST" else None)
    try:
        with opener.open(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, dict(err.headers), err.read().decode("utf-8", "replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="raíz del sitio, con https://")
    ap.add_argument("--json", help="fichero donde guardar el detalle")
    args = ap.parse_args()
    base = args.url.rstrip("/")
    if not base.startswith("https://"):
        print("La URL debe empezar por https:// (la cookie es Secure).")
        return 2

    web = urllib.request.build_opener()
    raw = urllib.request.build_opener(NoRedirect)
    checks: list[tuple[str, bool, str]] = []
    detail: dict = {"url": base}

    # 1. Página y cabeceras
    status, headers, body = request(web, base + "/")
    lower = {k.lower(): v for k, v in headers.items()}
    missing = [h for h in ("content-security-policy", "x-content-type-options", "x-frame-options") if h not in lower]
    checks.append(("Página principal", status == 200 and "FraSoHome Live" in body, f"HTTP {status}"))
    checks.append(("Cabeceras de seguridad", not missing, "faltan: " + ", ".join(missing) if missing else "presentes"))

    # 2. Autenticación integrada bloqueada: los proveedores de login dan 404. /.auth/me es
    #    interno de SWA y no se puede bloquear, pero debe decir que no hay nadie identificado.
    auth = {}
    for path in ("/.auth/login/github", "/.auth/login/aad"):
        st, hd, _ = request(raw, base + path)
        auth[path] = st if st != 302 else "302 -> " + hd.get("Location", "")
    st, _, body = request(raw, base + "/.auth/me")
    try:
        me_ok = st == 404 or (st == 200 and json.loads(body).get("clientPrincipal") is None)
    except json.JSONDecodeError:
        me_ok = False
    auth["/.auth/me"] = f"{st} {body.strip()[:60]}"
    detail["auth"] = auth
    checks.append(("Login integrado de SWA bloqueado", all(auth[p] == 404 for p in ("/.auth/login/github", "/.auth/login/aad")) and me_ok,
                   json.dumps(auth, ensure_ascii=False)))

    # 3. Salud: SQL y Cosmos (la base gratuita puede estar en pausa: hasta 3 intentos)
    health = None
    for attempt in range(1, 4):
        st, _, body = request(web, base + "/api/health", timeout=120)
        try:
            health = json.loads(body)
        except json.JSONDecodeError:
            health = {"ok": False, "raw": body[:300]}
        if st == 200 and health.get("ok"):
            break
        time.sleep(20)
    detail["health"] = health
    for key, label in (("sql_mssql_python", "SQL con mssql-python"), ("sql_pyodbc", "SQL con pyodbc"), ("cosmos", "Cosmos DB")):
        part = (health or {}).get(key) or {}
        info = f"{part.get('seconds', '?')} s" if part.get("ok") else str(part.get("error") or part.get("errors") or "sin datos")[:160]
        checks.append((label, bool(part.get("ok")), info))

    # 4. Cookie de sesión
    st, hd, body = request(web, base + "/api/cookie", method="POST", headers={"X-FSH-CSRF": "1"})
    set_cookie = next((v for k, v in hd.items() if k.lower() == "set-cookie"), "")
    flags_ok = all(f.lower() in set_cookie.lower() for f in ("httponly", "secure", "samesite=strict"))
    sent = json.loads(body).get("sent") if st == 200 else None
    # Se reenvía a mano, como haría un navegador: el host de Functions añade un atributo
    # "domain=" vacío que los navegadores ignoran (RFC 6265) pero http.cookiejar no.
    pair = set_cookie.split(";", 1)[0].strip()
    st2, _, body2 = request(raw, base + "/api/cookie", headers={"Cookie": pair} if pair else None)
    received = json.loads(body2).get("received") if st2 == 200 else None
    detail["cookie"] = {"set_cookie": set_cookie, "sent": sent, "received": received,
                        "empty_domain_attribute": "domain=;" in set_cookie.replace(" ", "").lower()}
    checks.append(("Cookie con HttpOnly, Secure y SameSite=Strict", flags_ok, set_cookie or "sin Set-Cookie"))
    checks.append(("La cookie vuelve en la siguiente petición", sent is not None and sent == received, f"{sent} / {received}"))

    # Diagnóstico: qué variantes de cookie deja pasar Static Web Apps (no cuenta como comprobación).
    variants = {}
    for variant in ("dominio", "sin-dominio", "expires"):
        st_v, hd_v, _ = request(raw, base + "/api/cookie?variante=" + variant, method="POST", headers={"X-FSH-CSRF": "1"})
        variants[variant] = next((v for k, v in hd_v.items() if k.lower() == "set-cookie"), None) if st_v == 200 else f"HTTP {st_v}"
    detail["cookie_variants"] = variants

    # 5. Escritura sin cabecera CSRF
    st, _, _ = request(raw, base + "/api/cookie", method="POST")
    checks.append(("Escritura sin X-FSH-CSRF rechazada", st == 400, f"HTTP {st}"))

    width = max(len(c[0]) for c in checks)
    for name, ok, info in checks:
        print(f"{'OK ' if ok else 'MAL'}  {name.ljust(width)}  {info}")
    print()
    print("Diagnóstico de cookies (qué variante llega al navegador):")
    for variant, header in variants.items():
        print(f"  {variant.ljust(12)} {'llega   ' if header and not str(header).startswith('HTTP') else 'NO llega'}  {header or ''}")
    detail["checks"] = [{"check": n, "ok": ok, "info": i} for n, ok, i in checks]
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(detail, fh, ensure_ascii=False, indent=2)
    return 0 if all(ok for _, ok, _ in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
