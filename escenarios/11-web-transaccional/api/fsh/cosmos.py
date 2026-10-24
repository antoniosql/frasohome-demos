"""FraSoHome Live · Cosmos DB y outbox.

Regla de las escrituras a dos bases: primero SQL (la verdad del dinero) y después
Cosmos DB. Los documentos se encolan en app.outbox (dentro de la transacción de
SQL cuando la hay) y `flush` los envía. Si Cosmos falla, quedan pendientes y se
reintentan en la siguiente escritura o desde administración.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any

from . import db
from .web import HttpError

log = logging.getLogger("fsh.cosmos")
_lock = threading.Lock()
_db = None
CONTAINERS = {"eventos_web", "eventos_campana", "senales_identidad", "feedback", "atencion_cliente",
              "creatividades", "encuesta_clima", "entrevistas_salida", "carritos"}
MAX_ATTEMPTS = 10


def database():
    global _db
    if _db is None:
        with _lock:
            if _db is None:
                endpoint = os.environ.get("COSMOS_ENDPOINT", "").strip()
                key = os.environ.get("COSMOS_KEY", "").strip()
                if not endpoint or not key:
                    raise HttpError(503, "La API no tiene configurado Cosmos DB.", "sin_configuracion")
                from azure.cosmos import CosmosClient
                client = CosmosClient(endpoint, credential=key)
                _db = client.get_database_client(os.environ.get("COSMOS_DATABASE", "frasohome"))
    return _db


def container(name: str):
    if name not in CONTAINERS:
        raise ValueError(f"Contenedor desconocido: {name}")
    return database().get_container_client(name)


def read(name: str, doc_id: str, pk: str) -> dict[str, Any] | None:
    from azure.cosmos import exceptions
    try:
        return _clean(container(name).read_item(doc_id, partition_key=pk))
    except exceptions.CosmosResourceNotFoundError:
        return None


def query(name: str, sql: str, params: dict[str, Any] | None = None, pk: str | None = None,
          max_items: int = 200) -> list[dict[str, Any]]:
    parameters = [{"name": k if k.startswith("@") else "@" + k, "value": v} for k, v in (params or {}).items()]
    kwargs: dict[str, Any] = {"parameters": parameters, "max_item_count": min(max_items, 1000)}
    if pk is None:
        kwargs["enable_cross_partition_query"] = True
    else:
        kwargs["partition_key"] = pk
    out = []
    for item in container(name).query_items(sql, **kwargs):
        out.append(_clean(item) if isinstance(item, dict) else item)
        if len(out) >= max_items:
            break
    return out


def find_by_id(name: str, doc_id: str) -> dict[str, Any] | None:
    """Busca un documento sin conocer su partición (consulta entre particiones por id)."""
    rows = query(name, "SELECT * FROM c WHERE c.id = @id", {"id": doc_id}, max_items=1)
    return rows[0] if rows else None


def upsert_direct(name: str, doc: dict[str, Any]) -> None:
    """Escritura directa, sin outbox: solo para datos efímeros (carritos, eventos de navegación)."""
    container(name).upsert_item(doc)


def delete_direct(name: str, doc_id: str, pk: str) -> None:
    from azure.cosmos import exceptions
    try:
        container(name).delete_item(doc_id, partition_key=pk)
    except exceptions.CosmosResourceNotFoundError:
        pass


def _clean(doc: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in doc.items() if not k.startswith("_")}


# ------------------------------------------------------------------ outbox

def enqueue(name: str, doc: dict[str, Any], operation: str = "upsert") -> int:
    if name not in CONTAINERS:
        raise ValueError(f"Contenedor desconocido: {name}")
    row = db.call_one("app.usp_outbox_enqueue", container_name=name,
                      document_json=json.dumps(doc, ensure_ascii=False, default=str), operation=operation)
    return int(row["outbox_id"])


def flush(limit: int = 50) -> dict[str, int]:
    """Envía a Cosmos lo pendiente del outbox, en orden. Devuelve {enviados, fallidos}."""
    pending = db.query(
        "SELECT TOP (?) outbox_id, container_name, operation, document_json FROM app.outbox "
        "WHERE sent_at IS NULL AND attempts < ? ORDER BY outbox_id", limit, MAX_ATTEMPTS)
    sent = failed = 0
    for row in pending:
        try:
            doc = json.loads(row["document_json"])
            if row["operation"] == "delete":
                delete_direct(row["container_name"], doc["id"], doc["pk"])
            else:
                container(row["container_name"]).upsert_item(doc)
            db.call("app.usp_outbox_mark", outbox_id=row["outbox_id"], ok=True)
            sent += 1
        except HttpError:
            raise
        except Exception as exc:  # noqa: BLE001 - se reintenta más tarde
            failed += 1
            log.warning("Outbox %s pendiente: %s", row["outbox_id"], exc)
            db.call("app.usp_outbox_mark", outbox_id=row["outbox_id"], ok=False, error=str(exc)[:1000])
            break  # si Cosmos no responde, no tiene sentido seguir con el resto ahora
    return {"enviados": sent, "fallidos": failed}


def next_ids(kind: str, count: int = 1) -> list[str]:
    sets = db.call("app.usp_next_ids", kind=kind, count=count)
    return [r["id"] for r in sets[-1]]
