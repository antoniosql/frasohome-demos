"""FraSoHome Live · usuarios de la web desde la línea de comandos.

    python users.py list
    python users.py add --login cajero.coruna --nombre "Caja A Coruña" --rol cajero --tienda S001 --empleado FSH0040
    python users.py reset --login cajero.coruna
    python users.py disable --login cajero.coruna        (enable para reactivar)
    python users.py add-role --login maria --rol marketing     (remove-role para quitarlo)
    python users.py add-scope --login maria --tipo store --valor S002
    python users.py demo [--guardar]                     un usuario por rol y doce clientes del CRM

La contraseña temporal se muestra una sola vez y el usuario debe cambiarla al entrar.
Con --guardar, las de demo se escriben además en .local/frasohome-live/usuarios_demo.txt
(Git lo ignora). Conexión: SQL_CONNECTION_STRING (la pone tools/usuarios.ps1).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "api"))

from fsh import db, usuarios  # noqa: E402
from fsh.web import HttpError  # noqa: E402

LOCAL = HERE.parents[2] / ".local" / "frasohome-live"


def _scopes(args) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for kind, values in (("customer", args.cliente), ("employee", args.empleado), ("store", args.tienda)):
        if values:
            out[kind] = values
    return out


def demo_plan() -> list[dict]:
    """Usuarios de demostración elegidos de los datos cargados, siempre los mismos."""
    store_emp = db.one("""SELECT TOP 1 a.canonical_employee_id AS employee_id, s.canonical_store_id AS store_id
                          FROM xref.employee_alias a
                          JOIN xref.employee_store s ON s.employee_id = a.canonical_employee_id
                          JOIN hr.employee e ON e.employee_id = a.canonical_employee_id AND e.employee_status = N'Activo'
                          WHERE a.source_system = N'POS' AND s.canonical_store_id = N'S001'
                          ORDER BY a.canonical_employee_id""")
    manager = db.one("""SELECT TOP 1 m.employee_id, COUNT(*) AS team FROM hr.employee m
                        JOIN hr.employee e ON e.manager_id = m.employee_id AND e.employee_status = N'Activo'
                        WHERE m.employee_status = N'Activo' GROUP BY m.employee_id ORDER BY COUNT(*) DESC, m.employee_id""")
    report = db.one("""SELECT TOP 1 employee_id FROM hr.employee WHERE manager_id = ? AND employee_status = N'Activo'
                       ORDER BY employee_id""", manager["employee_id"])
    customers = db.query("""SELECT TOP 12 c.customer_id, c.first_name, c.last_name FROM crm.customer c
                            WHERE c.customer_status = N'Activo'
                            ORDER BY (SELECT COUNT(*) FROM sales.online_order o WHERE o.customer_id = c.customer_id)
                                   + (SELECT COUNT(*) FROM sales.pos_ticket t WHERE t.customer_id = c.customer_id) DESC,
                                     c.customer_id""")
    plan = [
        {"login": "cajero.madrid", "nombre": "Caja Madrid Centro", "roles": ["cajero", "empleado"],
         "ambitos": {"store": [store_emp["store_id"]], "employee": [store_emp["employee_id"]]}},
        {"login": "tienda.madrid", "nombre": "Responsable Madrid Centro", "roles": ["tienda"], "ambitos": {"store": ["S001"]}},
        {"login": "almacen.online", "nombre": "Almacén e-commerce", "roles": ["tienda"], "ambitos": {"store": ["ONLINE"]}},
        {"login": "atencion.demo", "nombre": "Atención al cliente", "roles": ["atencion"], "ambitos": {}},
        {"login": "marketing.demo", "nombre": "Marketing", "roles": ["marketing"], "ambitos": {}},
        {"login": "rrhh.demo", "nombre": "Recursos Humanos", "roles": ["rrhh"], "ambitos": {}},
        {"login": "manager.demo", "nombre": "Manager de equipo", "roles": ["manager", "empleado"],
         "ambitos": {"employee": [manager["employee_id"]]}},
        {"login": "empleado.demo", "nombre": "Empleado", "roles": ["empleado"], "ambitos": {"employee": [report["employee_id"]]}},
        {"login": "direccion.demo", "nombre": "Dirección", "roles": ["direccion"], "ambitos": {}},
        {"login": "profesor.demo", "nombre": "Profesor", "roles": ["profesor"], "ambitos": {}},
        {"login": "admin.demo", "nombre": "Administración", "roles": ["admin"], "ambitos": {}},
    ]
    for c in customers:
        plan.append({"login": f"cliente.{c['customer_id'].lower()}", "nombre": f"{c['first_name']} {c['last_name']}",
                     "roles": ["cliente"], "ambitos": {"customer": [c["customer_id"]]}})
    return plan


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["list", "add", "reset", "disable", "enable", "add-role", "remove-role", "add-scope",
                                       "remove-scope", "demo"])
    ap.add_argument("--login")
    ap.add_argument("--nombre")
    ap.add_argument("--rol", action="append", default=[])
    ap.add_argument("--cliente", action="append", default=[])
    ap.add_argument("--empleado", action="append", default=[])
    ap.add_argument("--tienda", action="append", default=[])
    ap.add_argument("--tipo")
    ap.add_argument("--valor")
    ap.add_argument("--guardar", action="store_true", help="demo: guarda las contraseñas en .local/frasohome-live/")
    args = ap.parse_args()
    actor = "tools/users.py"
    try:
        if args.accion == "list":
            for u in usuarios.listing():
                state = "activo" if u["is_active"] else "DESACTIVADO"
                if u["bloqueado_hasta"]:
                    state = f"bloqueado hasta {u['bloqueado_hasta']:%H:%M} UTC"
                roles = ",".join(u["roles"])
                scopes = ",".join(f"{k}:{v}" for k, vals in u["ambitos"].items() for v in vals)
                print(f"{u['login']:<24} {roles:<22} {scopes:<34} {state}")
        elif args.accion == "add":
            r = usuarios.create(args.login, args.nombre or args.login, args.rol, _scopes(args), actor=actor)
            print(f"Usuario {r['login']} creado. Contraseña temporal (solo se muestra ahora): {r['contrasena_temporal']}")
        elif args.accion == "reset":
            r = usuarios.reset_password(args.login, actor=actor)
            print(f"Nueva contraseña temporal de {r['login']} (solo se muestra ahora): {r['contrasena_temporal']}")
        elif args.accion in ("disable", "enable"):
            usuarios.set_active(args.login, args.accion == "enable", actor=actor)
            print(f"{args.login}: {'activado' if args.accion == 'enable' else 'desactivado (sesiones cerradas)'}.")
        elif args.accion in ("add-role", "remove-role"):
            for role in args.rol:
                usuarios.set_role(args.login, role, args.accion == "add-role", actor=actor)
            print("Hecho.")
        elif args.accion in ("add-scope", "remove-scope"):
            usuarios.set_scope(args.login, args.tipo, args.valor, args.accion == "add-scope", actor=actor)
            print("Hecho.")
        elif args.accion == "demo":
            existing = {u["login"] for u in usuarios.listing()}
            lines = []
            for p in demo_plan():
                if p["login"] in existing:
                    print(f"  {p['login']:<20} ya existe (no se toca; usa reset si necesitas otra contraseña)")
                    continue
                r = usuarios.create(p["login"], p["nombre"], p["roles"], p["ambitos"], actor=actor)
                scope = " ".join(f"{k}:{','.join(v)}" for k, v in r["ambitos"].items())
                line = f"{r['login']:<20} {','.join(r['roles']):<16} {scope:<32} {r['contrasena_temporal']}"
                lines.append(line)
                print("  " + line)
            if lines and args.guardar:
                LOCAL.mkdir(parents=True, exist_ok=True)
                path = LOCAL / "usuarios_demo.txt"
                with path.open("a", encoding="utf-8") as fh:
                    fh.write("\n".join(lines) + "\n")
                print(f"Guardadas en {path} (Git lo ignora). Cada usuario debe cambiar su contraseña al entrar.")
            elif lines:
                print("Apunta las contraseñas: no se vuelven a mostrar. Cada usuario debe cambiarla al entrar.")
        return 0
    except HttpError as exc:
        print(f"Error: {exc.message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
