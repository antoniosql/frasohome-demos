"""FraSoHome Live · carga inicial de Cosmos DB desde los CSV de datos/.

    python load_cosmos.py              # carga sobre contenedores vacíos
    python load_cosmos.py --recrear    # vacía los contenedores (los borra y los crea) y carga

Necesita que load_sql.py haya cargado antes SQL: valida las referencias contra
clientes, productos, tiendas, campañas y empleados, y deja sus incidencias en
quality.data_quality_issue (source_schema = 'cosmos').

Variables: FSH_COSMOS_ENDPOINT, FSH_COSMOS_KEY, FSH_COSMOS_DATABASE (frasohome)
y FSH_SQL_CONNECTION_STRING. El ritmo se limita a --ru unidades por segundo
(700 por defecto) para no pasar de las 1.000 RU/s gratuitas que comparte la base.
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from comun import connect_sql, insert_rows, save_report
from fuentes_cosmos import CargaCosmos, Referencias
from load_sql import seed_counters

# Los 9 contenedores de infra/main.bicep. «carritos» no tiene CSV: nace vacío.
ALL_CONTAINERS = ["eventos_web", "eventos_campana", "senales_identidad", "feedback", "atencion_cliente",
                  "creatividades", "encuesta_clima", "entrevistas_salida", "carritos"]
INDEXING = {"indexingMode": "consistent", "automatic": True, "includedPaths": [{"path": "/*"}],
            "excludedPaths": [{"path": '/"_etag"/?'}]}
COUNTER_KINDS = {"eventos_web": ["web_event", "web_session"], "eventos_campana": ["campaign_event"],
                 "senales_identidad": ["identity"], "feedback": ["feedback"], "atencion_cliente": ["service"],
                 "creatividades": ["creative"], "encuesta_clima": ["survey"], "entrevistas_salida": ["exit"]}


class RuLimiter:
    """Reparte un presupuesto de RU por segundo entre los hilos de escritura."""

    def __init__(self, rate: float):
        self.rate = rate
        self.lock = threading.Lock()
        self.start = time.monotonic()
        self.used = 0.0
        self.total = 0.0

    def wait(self) -> None:
        while True:
            with self.lock:
                now = time.monotonic()
                if now - self.start >= 1:
                    self.start, self.used = now, 0.0
                if self.used < self.rate:
                    return
                pause = self.start + 1 - now
            time.sleep(max(pause, 0.01))

    def add(self, ru: float) -> None:
        with self.lock:
            self.used += ru
            self.total += ru


def cosmos_database():
    from azure.cosmos import CosmosClient
    endpoint = os.environ.get("FSH_COSMOS_ENDPOINT", "").strip()
    key = os.environ.get("FSH_COSMOS_KEY", "").strip()
    if not endpoint or not key:
        raise SystemExit("Faltan FSH_COSMOS_ENDPOINT y FSH_COSMOS_KEY (las pone seed/cargar_datos.ps1).")
    client = CosmosClient(endpoint, credential=key)
    name = os.environ.get("FSH_COSMOS_DATABASE", "frasohome")
    # En Azure la base ya existe (Bicep, 1.000 RU/s compartidas); en el emulador se crea igual.
    return client.create_database_if_not_exists(id=name, offer_throughput=1000)


def container(db, name: str, recreate: bool):
    from azure.cosmos import PartitionKey, exceptions
    if recreate:
        try:
            db.delete_container(name)
        except exceptions.CosmosResourceNotFoundError:
            pass
        return db.create_container(id=name, partition_key=PartitionKey(path="/pk"), indexing_policy=INDEXING)
    return db.create_container_if_not_exists(id=name, partition_key=PartitionKey(path="/pk"), indexing_policy=INDEXING)


def count_docs(cont) -> int:
    return list(cont.query_items("SELECT VALUE COUNT(1) FROM c", enable_cross_partition_query=True))[0]


def load_refs(conn) -> Referencias:
    cur = conn.cursor()

    def keys(sql: str) -> set[str]:
        cur.execute(sql)
        return {r[0] for r in cur.fetchall()}

    return Referencias(
        customers=keys("SELECT customer_id FROM crm.customer"), products=keys("SELECT product_id FROM catalog.product"),
        stores=keys("SELECT store_id FROM store.store"), campaigns=keys("SELECT campaign_id FROM mkt.campaign"),
        contacts=keys("SELECT contact_id FROM mkt.campaign_contact"), employees=keys("SELECT employee_id FROM hr.employee"))


def upsert_all(cont, docs: list[dict], limiter: RuLimiter, workers: int) -> tuple[int, list[str]]:
    errors: list[str] = []

    def one(doc: dict) -> None:
        limiter.wait()
        charge = {}
        cont.upsert_item(doc, response_hook=lambda headers, _body: charge.update(
            ru=float(headers.get("x-ms-request-charge", 0) or 0)))
        limiter.add(charge.get("ru", 10.0))

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(one, d): d["id"] for d in docs}
        for fut in as_completed(futures):
            exc = fut.exception()
            if exc:
                errors.append(f"{futures[fut]}: {str(exc).splitlines()[0][:200]}")
            else:
                done += 1
    return done, errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--recrear", action="store_true", help="borra y crea los 9 contenedores antes de cargar")
    ap.add_argument("--ru", type=float, default=700, help="RU por segundo como máximo (por defecto 700)")
    ap.add_argument("--hilos", type=int, default=8, help="escrituras en paralelo (por defecto 8)")
    args = ap.parse_args()

    t0 = time.time()
    conn = connect_sql()
    refs = load_refs(conn)
    if not refs.customers:
        raise SystemExit("SQL está vacía: ejecuta antes load_sql.py.")
    db = cosmos_database()
    print("Conectado a SQL y a Cosmos DB.")

    conts = {}
    for name in ALL_CONTAINERS:
        conts[name] = container(db, name, args.recrear)
    if args.recrear:
        print("Contenedores vaciados (borrados y creados de nuevo).")
    else:
        busy = [n for n in ALL_CONTAINERS if count_docs(conts[n]) > 0]
        if busy:
            print(f"Ya hay documentos en {', '.join(busy)}. Usa --recrear (o seed/reset.py).")
            return 2

    carga = CargaCosmos(refs)
    carga.ejecutar()
    limiter = RuLimiter(args.ru)
    summary, all_issues = {}, []
    for c in carga.containers:
        t = time.time()
        ok, errors = upsert_all(conts[c.name], c.docs, limiter, args.hilos)
        for e in errors:
            c.log.add("rechazo", "error_cosmos", f"Cosmos rechazó el documento: {e}", e.split(":")[0])
        summary[c.name] = {"fichero": c.csv.rel, "filas_csv": len(c.csv.rows), "documentos": ok,
                           "rechazos": c.log.count("rechazo"), "corregidos": c.log.count("corregido"),
                           "avisos": c.log.count("aviso"), "segundos": round(time.time() - t, 1)}
        all_issues.extend(i.as_row() for i in c.log.issues)
        print(f"    {c.name:<20} {ok:>6} documentos en {summary[c.name]['segundos']:>6} s"
              + (f"  ({len(errors)} errores)" if errors else ""))

    try:
        conn.cursor().execute("DELETE FROM quality.data_quality_issue WHERE source_schema = 'cosmos'")
        insert_rows(conn, "quality.data_quality_issue", all_issues)
        kinds: dict[str, list[str]] = {}
        for c in carga.containers:
            for kind in COUNTER_KINDS.get(c.name, []):
                field = "session_id" if kind == "web_session" else None
                kinds[kind] = [d[field] if field else d["id"] for d in c.docs]
        counters = seed_counters(conn, kinds)
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    sev = Counter(i["issue_severity"] for i in all_issues)
    report = {"fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"), "segundos": round(time.time() - t0, 1),
              "ru_consumidas": round(limiter.total), "contenedores": summary, "incidencias": dict(sev),
              "contadores": counters}
    path = save_report("carga_cosmos.json", report)
    total = sum(s["documentos"] for s in summary.values())
    print(f"\nCarga de Cosmos DB terminada en {report['segundos']} s: {total} documentos, {report['ru_consumidas']} RU.")
    print(f"Incidencias: {sev.get('rechazo', 0)} rechazos, {sev.get('corregido', 0)} correcciones, {sev.get('aviso', 0)} avisos.")
    print(f"Detalle: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
