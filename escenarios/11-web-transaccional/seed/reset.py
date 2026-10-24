"""FraSoHome Live · deja las bases como recién cargadas (antes de una demo).

    python reset.py            # pide escribir «reiniciar»
    python reset.py --si       # sin preguntar (para scripts)

Borra todos los datos de SQL y de Cosmos DB, vuelve a crear el esquema, carga los
CSV de datos/ y comprueba los recuentos. Conserva los usuarios de la web
(app.app_user, sus roles y ámbitos); sus sesiones se cierran.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def step(script: str, *args: str) -> None:
    print(f"\n=== {script} {' '.join(args)}".rstrip())
    code = subprocess.call([sys.executable, str(HERE / script), *args])
    if code != 0:
        raise SystemExit(f"{script} terminó con código {code}: el reinicio se ha detenido.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--si", action="store_true", help="no pide confirmación")
    ap.add_argument("--ru", default="700", help="RU por segundo para la carga de Cosmos DB")
    args = ap.parse_args()
    if not args.si:
        print("Se borrarán TODOS los datos de SQL y de Cosmos DB (los usuarios de la web se conservan).")
        if input('Escribe "reiniciar" para continuar: ').strip() != "reiniciar":
            print("Cancelado: no se ha tocado nada.")
            return 1
    step("load_sql.py", "--recrear")
    step("load_cosmos.py", "--recrear", "--ru", args.ru)
    step("verify.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
