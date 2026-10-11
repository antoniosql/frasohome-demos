# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# # FraSoHome IQ — validación previa a la demo
#
# Comprueba que las 15 entidades y 25 relaciones existen, contienen datos y
# cumplen las condiciones mínimas para que las vinculaciones de la ontología y
# la carga del grafo no fallen.

# CELL ********************

from __future__ import annotations

import json

from pyspark.sql import functions as F

TABLE_SCHEMA = "dbo"

ENTITY_KEYS = {
    "iq_customer": "customer_id",
    "iq_order": "order_id",
    "iq_product": "product_id",
    "iq_order_line": "order_line_id",
    "iq_category": "category_id",
    "iq_store": "store_id",
    "iq_region": "region_id",
    "iq_store_sale": "sale_id",
    "iq_payment": "payment_id",
    "iq_return": "return_id",
    "iq_inventory_position": "inventory_id",
    "iq_demand_signal": "demand_signal_id",
    "iq_campaign": "campaign_id",
    "iq_promotion": "promotion_id",
    "iq_campaign_contact": "contact_id",
}

RELATIONSHIPS = [
    "rel_customer_places_order",
    "rel_order_includes_product",
    "rel_order_has_line",
    "rel_line_references_product",
    "rel_product_in_category",
    "rel_store_in_region",
    "rel_customer_prefers_store",
    "rel_customer_completes_sale",
    "rel_sale_at_store",
    "rel_sale_includes_product",
    "rel_payment_settles_sale",
    "rel_return_for_order",
    "rel_return_for_sale",
    "rel_return_concerns_product",
    "rel_inventory_at_store",
    "rel_inventory_tracks_product",
    "rel_signal_from_customer",
    "rel_signal_about_product",
    "rel_signal_leads_to_order",
    "rel_campaign_has_contact",
    "rel_contact_addresses_customer",
    "rel_contact_recommends_product",
    "rel_contact_converts_to_order",
    "rel_campaign_offers_promotion",
    "rel_promotion_at_store",
]

available = {row.tableName for row in spark.sql(f"SHOW TABLES IN {TABLE_SCHEMA}").collect()}
required = set(ENTITY_KEYS) | set(RELATIONSHIPS) | {"iq_deployment_manifest", "iq_source_profile"}
missing = sorted(required - available)
errors = []
checks = []

if missing:
    errors.append(f"Faltan tablas: {', '.join(missing)}")

for table_name, key_name in ENTITY_KEYS.items():
    if table_name not in available:
        continue
    df = spark.table(f"{TABLE_SCHEMA}.{table_name}")
    row_count = df.count()
    null_keys = df.where(F.col(key_name).isNull()).count()
    duplicate_keys = df.groupBy(key_name).count().where(F.col("count") > 1).count()
    checks.append(
        {
            "table": table_name,
            "kind": "Entity",
            "rows": row_count,
            "nullKeys": null_keys,
            "duplicateKeys": duplicate_keys,
        }
    )
    if row_count == 0:
        errors.append(f"{table_name} no contiene filas.")
    if null_keys:
        errors.append(f"{table_name} contiene {null_keys} claves nulas.")
    if duplicate_keys:
        errors.append(f"{table_name} contiene {duplicate_keys} claves duplicadas.")

for table_name in RELATIONSHIPS:
    if table_name not in available:
        continue
    df = spark.table(f"{TABLE_SCHEMA}.{table_name}")
    row_count = df.count()
    invalid_keys = df.where(F.col("source_id").isNull() | F.col("target_id").isNull()).count()
    duplicate_edges = df.groupBy("source_id", "target_id").count().where(F.col("count") > 1).count()
    checks.append(
        {
            "table": table_name,
            "kind": "Relationship",
            "rows": row_count,
            "nullKeys": invalid_keys,
            "duplicateKeys": duplicate_edges,
        }
    )
    if row_count == 0:
        errors.append(f"{table_name} no contiene relaciones.")
    if invalid_keys:
        errors.append(f"{table_name} contiene {invalid_keys} pares incompletos.")
    if duplicate_edges:
        errors.append(f"{table_name} contiene {duplicate_edges} pares duplicados.")

manifest = spark.table(f"{TABLE_SCHEMA}.iq_deployment_manifest") if "iq_deployment_manifest" in available else None
if manifest is not None:
    manifest_rows = manifest.count()
    if manifest_rows != 40:
        errors.append(f"El manifiesto contiene {manifest_rows} objetos; se esperaban 40.")

summary = {
    "status": "failed" if errors else "success",
    "entityTables": len(ENTITY_KEYS),
    "relationshipTables": len(RELATIONSHIPS),
    "errors": errors,
    "checks": checks,
}
print(json.dumps(summary, ensure_ascii=False, indent=2))

if errors:
    raise AssertionError(" | ".join(errors))

try:
    from notebookutils import mssparkutils

    mssparkutils.notebook.exit(json.dumps({k: v for k, v in summary.items() if k != "checks"}, ensure_ascii=False))
except Exception:
    pass

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
