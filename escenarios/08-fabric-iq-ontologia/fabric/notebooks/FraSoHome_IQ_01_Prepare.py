# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# # FraSoHome IQ — preparación de datos para ontología
#
# Convierte los CSV originales de `datos` en tablas Delta gobernadas para una
# ontología de 15 entidades y 25 relaciones. Mantiene los problemas de calidad en
# la zona raw, normaliza las claves en la capa de demo y evita exponer email o
# teléfono en las tablas enlazadas a la ontología.

# CELL ********************

from __future__ import annotations

import json
from datetime import datetime, timezone

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F
from pyspark.sql import types as T

RAW_ROOT = "Files/frasohome_iq/raw"
TABLE_SCHEMA = "dbo"
INVALID_TOKENS = ["", "N/A", "NA", "??", "NULL", "NONE", "NAN"]
SPANISH_MONTHS = {
    "enero": "01",
    "febrero": "02",
    "marzo": "03",
    "abril": "04",
    "mayo": "05",
    "junio": "06",
    "julio": "07",
    "agosto": "08",
    "septiembre": "09",
    "setiembre": "09",
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12",
}

spark.conf.set("spark.sql.ansi.enabled", "false")
# Cada fecha se prueba contra varios patrones en as_timestamp(). Con la política
# EXCEPTION, Spark aborta al primer patrón que no coincide (por ejemplo,
# "21/12/24" frente a "yyyy-MM-dd") y no permite que coalesce pruebe d/M/yy.
# CORRECTED convierte esos intentos incompatibles en NULL y conserva el primer
# patrón que sí encaja.
spark.conf.set("spark.sql.legacy.timeParserPolicy", "CORRECTED")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {TABLE_SCHEMA}")


def read_raw(domain: str, filename: str) -> DataFrame:
    path = f"{RAW_ROOT}/{domain}/{filename}"
    df = (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "false")
        .option("encoding", "UTF-8")
        .option("mode", "PERMISSIVE")
        .option("quote", '"')
        .option("escape", '"')
        .load(path)
    )
    for name, dtype in df.dtypes:
        if dtype == "string":
            df = df.withColumn(name, F.trim(F.col(name)))
    return df


def clean_text(column: str | F.Column) -> F.Column:
    value = F.trim(F.col(column) if isinstance(column, str) else column)
    return F.when(F.upper(value).isin(INVALID_TOKENS), F.lit(None)).otherwise(value)


def clean_id(column: str | F.Column) -> F.Column:
    return F.upper(clean_text(column))


def clean_label(column: str | F.Column) -> F.Column:
    return F.initcap(F.lower(clean_text(column)))


def as_double(column: str | F.Column) -> F.Column:
    value = F.lower(clean_text(column))
    value = F.regexp_replace(value, r"(?i)\b(?:eur|usd|uds?|unidades?)\b", "")
    value = F.regexp_replace(value, r"[€$%\s]", "")

    comma_count = F.length(value) - F.length(F.regexp_replace(value, ",", ""))
    dot_count = F.length(value) - F.length(F.regexp_replace(value, "\\.", ""))
    comma_is_decimal = F.instr(F.reverse(value), ",") < F.instr(F.reverse(value), ".")

    normalized = (
        F.when(
            (comma_count > 0) & (dot_count > 0) & comma_is_decimal,
            F.regexp_replace(F.regexp_replace(value, "\\.", ""), ",", "."),
        )
        .when((comma_count > 0) & (dot_count > 0), F.regexp_replace(value, ",", ""))
        .when(comma_count == 1, F.regexp_replace(value, ",", "."))
        .when((comma_count > 1) & value.rlike(r"^-?\d{1,3}(,\d{3})+$"), F.regexp_replace(value, ",", ""))
        .when(comma_count > 1, F.lit(None).cast("string"))
        .when((dot_count == 1) & value.rlike(r"^-?\d{1,3}\.\d{3}$"), F.regexp_replace(value, "\\.", ""))
        .when((dot_count > 1) & value.rlike(r"^-?\d{1,3}(\.\d{3})+$"), F.regexp_replace(value, "\\.", ""))
        .when(dot_count > 1, F.lit(None).cast("string"))
        .otherwise(value)
    )
    return F.when(normalized.rlike(r"^-?\d+(?:\.\d+)?$"), normalized.cast("double"))


def as_long(column: str | F.Column) -> F.Column:
    value = F.lower(clean_text(column))
    value = F.regexp_replace(value, r"(?i)\b(?:eur|usd|uds?|unidades?)\b", "")
    value = F.regexp_replace(value, r"[€$%\s]", "")
    grouped = value.rlike(r"^-?\d{1,3}(?:[.,]\d{3})+$")
    normalized = F.when(grouped, F.regexp_replace(value, "[.,]", "")).otherwise(
        F.regexp_replace(value, ",", ".")
    )
    return F.when(normalized.rlike(r"^-?\d+(?:\.0+)?$"), normalized.cast("double").cast("long"))


def as_bool(column: str | F.Column) -> F.Column:
    value = F.lower(clean_text(column))
    return (
        F.when(value.isin("1", "true", "sí", "si", "yes", "y", "s"), F.lit(True))
        .when(value.isin("0", "false", "no", "n"), F.lit(False))
        .otherwise(F.lit(None).cast("boolean"))
    )


def as_timestamp(column: str | F.Column) -> F.Column:
    value = F.lower(clean_text(column))
    for month_name, month_number in SPANISH_MONTHS.items():
        value = F.regexp_replace(
            value,
            rf"(?i)\s+de\s+{month_name}\s+de\s+",
            f"/{month_number}/",
        )
    return F.coalesce(
        F.to_timestamp(value, "yyyy-MM-dd HH:mm:ss"),
        F.to_timestamp(value, "yyyy-MM-dd HH:mm"),
        F.to_timestamp(value, "yyyy-MM-dd"),
        F.to_timestamp(value, "yyyy/M/d HH:mm:ss"),
        F.to_timestamp(value, "yyyy/M/d HH:mm"),
        F.to_timestamp(value, "yyyy/M/d"),
        F.to_timestamp(value, "d/M/yyyy HH:mm:ss"),
        F.to_timestamp(value, "d/M/yyyy HH:mm"),
        F.to_timestamp(value, "d/M/yyyy"),
        F.to_timestamp(value, "d/M/yy HH:mm:ss"),
        F.to_timestamp(value, "d/M/yy HH:mm"),
        F.to_timestamp(value, "d/M/yy"),
    )


def deterministic_dedupe(df: DataFrame, keys: list[str], order_columns: list[str] | None = None) -> DataFrame:
    order_columns = order_columns or []
    fingerprint = F.sha2(
        F.concat_ws(
            "||",
            *[F.coalesce(F.col(name).cast("string"), F.lit("")) for name in sorted(df.columns)],
        ),
        256,
    )
    prepared = df.withColumn("_row_fingerprint", fingerprint)
    ordering = [F.col(name).desc_nulls_last() for name in order_columns]
    ordering.append(F.col("_row_fingerprint").desc())
    window = Window.partitionBy(*keys).orderBy(*ordering)
    return (
        prepared.withColumn("_row_number", F.row_number().over(window))
        .where(F.col("_row_number") == 1)
        .drop("_row_number", "_row_fingerprint")
    )


def stable_id(prefix: str, *columns: F.Column) -> F.Column:
    digest = F.sha2(F.concat_ws("|", *[F.coalesce(c.cast("string"), F.lit("")) for c in columns]), 256)
    return F.concat(F.lit(prefix), F.substring(digest, 1, 16))


def write_table(name: str, df: DataFrame) -> int:
    count = df.count()
    (
        df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"{TABLE_SCHEMA}.{name}")
    )
    print(f"{name}: {count:,} filas")
    return count


def valid_edge(
    evidence: DataFrame,
    source_column: str,
    target_column: str,
    source_entity: DataFrame,
    source_key: str,
    target_entity: DataFrame,
    target_key: str,
) -> DataFrame:
    candidates = (
        evidence.select(
            F.col(source_column).cast("string").alias("source_id"),
            F.col(target_column).cast("string").alias("target_id"),
        )
        .where(F.col("source_id").isNotNull() & F.col("target_id").isNotNull())
        .dropDuplicates(["source_id", "target_id"])
    )
    source_keys = source_entity.select(F.col(source_key).cast("string").alias("source_id")).dropDuplicates()
    target_keys = target_entity.select(F.col(target_key).cast("string").alias("target_id")).dropDuplicates()
    return candidates.join(source_keys, "source_id", "inner").join(target_keys, "target_id", "inner")


raw = {
    "crm": read_raw("retail_omnicanal", "crm.csv"),
    "products": read_raw("retail_omnicanal", "productos.csv"),
    "stores": read_raw("retail_omnicanal", "tiendas.csv"),
    "orders": read_raw("retail_omnicanal", "pedidos.csv"),
    "order_lines": read_raw("retail_omnicanal", "lineas_pedido.csv"),
    "pos_lines": read_raw("retail_omnicanal", "ventas_pos.csv"),
    "payments": read_raw("retail_omnicanal", "pagos_tienda.csv"),
    "returns_online": read_raw("retail_omnicanal", "devoluciones_online.csv"),
    "returns_store": read_raw("retail_omnicanal", "devoluciones_tienda.csv"),
    "inventory": read_raw("retail_omnicanal", "stock_diario.csv"),
    "campaigns": read_raw("marketing_precision", "campanas_marketing.csv"),
    "contacts": read_raw("marketing_precision", "contactos_campana.csv"),
    "promotions": read_raw("marketing_precision", "promociones_calendario.csv"),
    "web_events": read_raw("marketing_precision", "eventos_web_app.csv"),
    "affinity": read_raw("marketing_precision", "afinidad_tienda_cliente.csv"),
}
raw_counts = {name: df.count() for name, df in raw.items()}
print(json.dumps(raw_counts, ensure_ascii=False, indent=2))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Entidades de negocio
#
# La capa `iq_*` contiene vocabulario de negocio estable. Las columnas técnicas
# necesarias para contextualizar relaciones se conservan, pero solo las propiedades
# declaradas en la ontología se exponen al consumidor.

# CELL ********************

customer_base = raw["crm"].withColumn("customer_id", clean_id("customer_id"))
customer_base = deterministic_dedupe(customer_base, ["customer_id"], ["ultima_actualizacion"])
customer = (
    customer_base.where(F.col("customer_id").isNotNull())
    .select(
        "customer_id",
        F.concat_ws(" ", clean_text("nombre"), clean_text("apellidos")).alias("customer_name"),
        clean_label("tier_fidelizacion").alias("loyalty_tier"),
        as_long("puntos_acumulados").alias("loyalty_points"),
        clean_label("ciudad").alias("city"),
        clean_label("provincia").alias("province"),
        as_bool("consentimiento_marketing").alias("marketing_consent"),
        clean_label("estado_cliente").alias("customer_status"),
        clean_label("canal_preferido_declarado").alias("preferred_channel"),
    )
)

order_base = (
    raw["orders"]
    .withColumn("order_id", clean_id("order_id"))
    .withColumn("customer_id", clean_id("customer_id"))
)
order_base = deterministic_dedupe(order_base, ["order_id"], ["ultima_actualizacion"])
order = (
    order_base.where(F.col("order_id").isNotNull())
    .select(
        "order_id",
        "customer_id",
        as_timestamp("fecha_pedido").alias("order_date"),
        as_double("importe_total").alias("order_total"),
        F.upper(clean_text("moneda")).alias("currency"),
        as_double("gastos_envio").alias("shipping_cost"),
        clean_label("estado_pedido").alias("order_status"),
        F.lower(clean_text("origen")).alias("order_origin"),
        clean_label("ciudad_envio").alias("destination_city"),
    )
)

product_base = raw["products"].withColumn("product_id", clean_id("product_id"))
product_base = deterministic_dedupe(product_base, ["product_id"], ["fecha_alta_catalogo"])
product = (
    product_base.where(F.col("product_id").isNotNull())
    .withColumn("category_name", clean_label("categoria"))
    .withColumn("category_id", stable_id("CAT-", F.col("category_name")))
    .select(
        "product_id",
        clean_text("nombre_producto").alias("product_name"),
        "category_id",
        "category_name",
        clean_label("subcategoria").alias("subcategory_name"),
        clean_text("marca").alias("brand"),
        clean_text("material").alias("material"),
        clean_label("color").alias("color"),
        as_double("precio_venta").alias("sale_price"),
        as_double("coste_unitario").alias("unit_cost"),
        clean_label("estado_producto").alias("product_status"),
    )
)
category = product.select("category_id", "category_name").where(F.col("category_name").isNotNull()).dropDuplicates()

order_line_base = (
    raw["order_lines"]
    .withColumn("order_line_id", clean_id("order_line_id"))
    .withColumn("order_id", clean_id("order_id"))
    .withColumn("product_id", clean_id("product_id"))
)
order_line_base = deterministic_dedupe(order_line_base, ["order_line_id"])
order_line = (
    order_line_base.where(F.col("order_line_id").isNotNull())
    .select(
        "order_line_id",
        "order_id",
        "product_id",
        clean_text("descripcion_producto").alias("line_description"),
        as_long("cantidad").alias("quantity"),
        as_double("precio_unitario").alias("unit_price"),
        as_double("descuento_pct").alias("discount_pct"),
        as_double("descuento_importe").alias("discount_amount"),
        as_double("importe_linea").alias("line_amount"),
    )
)

store_base = raw["stores"].withColumn("store_id", clean_id("store_id"))
store_base = deterministic_dedupe(store_base, ["store_id"])
store = (
    store_base.where(F.col("store_id").isNotNull())
    .withColumn(
        "region_name",
        F.when(F.lower(clean_text("region")).isin("central", "centro"), F.lit("Centro"))
        .otherwise(clean_label("region")),
    )
    .withColumn("region_id", stable_id("REG-", F.col("region_name")))
    .select(
        "store_id",
        F.regexp_replace(clean_text("nombre_tienda"), "(?i)\\s*\\(dup\\)\\s*$", "").alias("store_name"),
        clean_label("tipo_ubicacion").alias("location_type"),
        F.upper(clean_text("canal")).alias("store_channel"),
        clean_label("ciudad").alias("city"),
        clean_label("provincia").alias("province"),
        "region_id",
        "region_name",
        clean_label("estado").alias("store_status"),
    )
)
region = store.select("region_id", "region_name").where(F.col("region_name").isNotNull()).dropDuplicates()

pos_line_base = (
    raw["pos_lines"]
    .withColumn("ticket_line_id", clean_id("ticket_line_id"))
    .withColumn("sale_id", clean_id("ticket_id"))
    .withColumn("store_id", clean_id("store_id"))
    .withColumn("customer_id", clean_id("customer_id"))
    .withColumn("product_id", clean_id("product_id"))
)
pos_line_base = deterministic_dedupe(pos_line_base, ["ticket_line_id"])
pos_line = (
    pos_line_base.where(F.col("ticket_line_id").isNotNull() & F.col("sale_id").isNotNull())
    .select(
        "ticket_line_id",
        "sale_id",
        "store_id",
        "customer_id",
        "product_id",
        as_timestamp("fecha_hora").alias("sale_date"),
        as_double("importe_linea").alias("line_amount"),
        F.upper(clean_text("moneda")).alias("currency"),
        F.upper(clean_text("canal")).alias("sale_channel"),
    )
)
store_sale = (
    pos_line.groupBy("sale_id")
    .agg(
        F.max("sale_date").alias("sale_date"),
        F.max("store_id").alias("store_id"),
        F.max("customer_id").alias("customer_id"),
        F.sum(F.coalesce(F.col("line_amount"), F.lit(0.0))).alias("sale_amount"),
        F.max("currency").alias("currency"),
        F.countDistinct("ticket_line_id").cast("long").alias("line_count"),
        F.max("sale_channel").alias("sale_channel"),
    )
)

payment_base = (
    raw["payments"]
    .withColumn("payment_id", clean_id("payment_id"))
    .withColumn("sale_id", clean_id("ticket_id"))
)
payment_base = deterministic_dedupe(payment_base, ["payment_id"])
payment = (
    payment_base.where(F.col("payment_id").isNotNull())
    .select(
        "payment_id",
        "sale_id",
        as_timestamp("fecha_pago").alias("payment_date"),
        clean_label("metodo_pago").alias("payment_method"),
        as_double("importe_pagado").alias("payment_amount"),
        F.upper(clean_text("moneda")).alias("currency"),
        F.upper(clean_text("estado_pago")).alias("payment_status"),
    )
)

returns_online_base = (
    raw["returns_online"]
    .withColumn("return_id", clean_id("return_id"))
    .withColumn("order_id", clean_id("order_id"))
    .withColumn("product_id", clean_id("product_id"))
)
returns_online_base = deterministic_dedupe(returns_online_base, ["return_id"])
returns_online = (
    returns_online_base.where(F.col("return_id").isNotNull())
    .select(
        "return_id",
        "order_id",
        F.lit(None).cast("string").alias("sale_id"),
        F.lit(None).cast("string").alias("store_id"),
        "product_id",
        as_timestamp("fecha_devolucion").alias("return_date"),
        F.lit("ONLINE").alias("return_channel"),
        clean_text("motivo_devolucion").alias("return_reason"),
        clean_label("metodo_devolucion").alias("return_method"),
        clean_label("estado_devolucion").alias("return_status"),
        as_double("importe_reembolsado").alias("return_amount"),
        F.upper(clean_text("moneda")).alias("currency"),
        as_long("cantidad_devuelta").alias("return_quantity"),
    )
)

returns_store_base = (
    raw["returns_store"]
    .withColumn("return_id", clean_id("return_id"))
    .withColumn("order_id", clean_id("order_id_original"))
    .withColumn("sale_id", clean_id("ticket_id_original"))
    .withColumn("store_id", clean_id("store_id"))
    .withColumn("product_id", clean_id("product_id"))
)
returns_store_base = deterministic_dedupe(returns_store_base, ["return_id"])
returns_store = (
    returns_store_base.where(F.col("return_id").isNotNull())
    .select(
        "return_id",
        "order_id",
        "sale_id",
        "store_id",
        "product_id",
        as_timestamp("fecha_devolucion").alias("return_date"),
        F.upper(clean_text("canal_origen_venta")).alias("return_channel"),
        clean_text("motivo_devolucion").alias("return_reason"),
        clean_label("metodo_reembolso").alias("return_method"),
        clean_label("estado_devolucion").alias("return_status"),
        as_double("importe_reembolsado").alias("return_amount"),
        F.upper(clean_text("moneda")).alias("currency"),
        as_long("cantidad_devuelta").alias("return_quantity"),
    )
)
returns = deterministic_dedupe(returns_online.unionByName(returns_store), ["return_id"])

inventory_base = (
    raw["inventory"]
    .withColumn("store_id", clean_id("store_id"))
    .withColumn("product_id", clean_id("product_id"))
    .withColumn("inventory_date", as_timestamp("fecha"))
)
inventory_base = deterministic_dedupe(inventory_base, ["inventory_date", "store_id", "product_id"])
inventory = (
    inventory_base.where(
        F.col("inventory_date").isNotNull() & F.col("store_id").isNotNull() & F.col("product_id").isNotNull()
    )
    .withColumn(
        "inventory_id",
        stable_id("INV-", F.col("inventory_date"), F.col("store_id"), F.col("product_id")),
    )
    .withColumn("stock_closing", as_double("stock_cierre"))
    .withColumn("stock_minimum", as_double("stock_minimo"))
    .select(
        "inventory_id",
        "inventory_date",
        "store_id",
        "product_id",
        "stock_closing",
        as_double("stock_reservado").alias("stock_reserved"),
        as_double("stock_en_transito").alias("stock_in_transit"),
        "stock_minimum",
        (F.col("stock_closing") - F.col("stock_minimum")).alias("stock_gap"),
        clean_text("fuente").alias("inventory_source"),
    )
)

signal_base = (
    raw["web_events"]
    .withColumn("demand_signal_id", clean_id("event_id"))
    .withColumn("customer_id", clean_id("customer_id"))
    .withColumn("product_id", clean_id("product_id"))
    .withColumn("order_id", clean_id("order_id"))
)
signal_base = deterministic_dedupe(signal_base, ["demand_signal_id"])
demand_signal = (
    signal_base.where(F.col("demand_signal_id").isNotNull())
    .select(
        "demand_signal_id",
        "customer_id",
        "product_id",
        "order_id",
        as_timestamp("fecha_hora_evento").alias("signal_date"),
        F.lower(clean_text("tipo_evento")).alias("signal_type"),
        F.lower(clean_text("canal_adquisicion")).alias("acquisition_channel"),
        F.lower(clean_text("page_type")).alias("page_type"),
        clean_id("session_id").alias("session_id"),
        as_double("valor_evento_eur").alias("signal_value"),
        as_bool("logged_in_flag").alias("logged_in"),
    )
)

campaign_base = raw["campaigns"].withColumn("campaign_id", clean_id("campaign_id"))
campaign_base = deterministic_dedupe(campaign_base, ["campaign_id"])
campaign = (
    campaign_base.where(F.col("campaign_id").isNotNull())
    .select(
        "campaign_id",
        clean_text("nombre_campana").alias("campaign_name"),
        clean_text("objetivo").alias("campaign_objective"),
        F.upper(clean_text("canal")).alias("campaign_channel"),
        as_timestamp("fecha_inicio").alias("campaign_start"),
        as_timestamp("fecha_fin").alias("campaign_end"),
        clean_text("segmento_objetivo").alias("target_segment"),
        clean_label("estado").alias("campaign_state"),
        as_double("presupuesto_plan_eur").alias("planned_budget"),
        as_double("revenue_30d_total_eur").alias("revenue_30d"),
        as_double("margen_30d_total_eur").alias("margin_30d"),
        as_long("conversiones_30d").alias("conversions_30d"),
    )
)

promotion_base = (
    raw["promotions"]
    .withColumn("promotion_id", clean_id("promo_id"))
    .withColumn("campaign_id", clean_id("campana_id_relacionada"))
    .withColumn("store_id", clean_id("store_id"))
)
promotion_base = deterministic_dedupe(promotion_base, ["promotion_id"])
promotion = (
    promotion_base.where(F.col("promotion_id").isNotNull())
    .select(
        "promotion_id",
        "campaign_id",
        "store_id",
        clean_text("nombre_promocion").alias("promotion_name"),
        clean_text("tipo_promocion").alias("promotion_type"),
        as_timestamp("fecha_inicio").alias("promotion_start"),
        as_timestamp("fecha_fin").alias("promotion_end"),
        clean_text("ambito").alias("promotion_scope"),
        F.upper(clean_text("canal")).alias("promotion_channel"),
        as_double("descuento_pct").alias("discount_pct"),
        as_double("descuento_importe_eur").alias("discount_amount"),
        as_bool("combinable").alias("combinable"),
    )
)

contact_base = (
    raw["contacts"]
    .withColumn("contact_id", clean_id("contact_id"))
    .withColumn("campaign_id", clean_id("campaign_id"))
    .withColumn("customer_id", clean_id("customer_id"))
    .withColumn("order_id", clean_id("order_id_conversion_30d"))
    .withColumn("recommended_product_1", clean_id("product_id_recomendado_1"))
    .withColumn("recommended_product_2", clean_id("product_id_recomendado_2"))
)
contact_base = deterministic_dedupe(contact_base, ["contact_id"])
campaign_contact = (
    contact_base.where(F.col("contact_id").isNotNull())
    .select(
        "contact_id",
        "campaign_id",
        "customer_id",
        "order_id",
        "recommended_product_1",
        "recommended_product_2",
        as_timestamp("fecha_contacto").alias("contact_date"),
        F.upper(clean_text("canal_contacto")).alias("contact_channel"),
        clean_text("segmento_asignado").alias("assigned_segment"),
        clean_text("estado_entrega").alias("delivery_state"),
        clean_label("prioridad_contacto").alias("contact_priority"),
        as_bool("conversion_30d_flag").alias("converted_30d"),
        as_double("revenue_30d_eur").alias("contact_revenue_30d"),
        as_double("margen_30d_eur").alias("contact_margin_30d"),
    )
)

affinity = (
    raw["affinity"]
    .withColumn("customer_id", clean_id("customer_id"))
    .withColumn("preferred_store_id", clean_id("store_id_preferida"))
)
affinity = deterministic_dedupe(affinity, ["customer_id"])

entity_tables = {
    "iq_customer": (1, customer),
    "iq_order": (1, order),
    "iq_product": (1, product),
    "iq_order_line": (2, order_line),
    "iq_category": (2, category),
    "iq_store": (3, store),
    "iq_region": (3, region),
    "iq_store_sale": (4, store_sale),
    "iq_payment": (4, payment),
    "iq_return": (4, returns),
    "iq_inventory_position": (5, inventory),
    "iq_demand_signal": (5, demand_signal),
    "iq_campaign": (6, campaign),
    "iq_promotion": (6, promotion),
    "iq_campaign_contact": (6, campaign_contact),
}

manifest = []
for table_name, (stage, table_df) in entity_tables.items():
    manifest.append((table_name, "Entity", stage, write_table(table_name, table_df)))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Relaciones contextualizadas
#
# Cada tabla `rel_*` contiene únicamente pares de claves válidos (`source_id`,
# `target_id`). Las claves huérfanas permanecen en raw para los ejercicios de
# calidad, pero no bloquean la carga del grafo.

# CELL ********************

contact_product = (
    campaign_contact.select("contact_id", F.col("recommended_product_1").alias("product_id"))
    .unionByName(campaign_contact.select("contact_id", F.col("recommended_product_2").alias("product_id")))
    .where(F.col("product_id").isNotNull())
)

relationship_tables = {
    "rel_customer_places_order": (
        1,
        valid_edge(order, "customer_id", "order_id", customer, "customer_id", order, "order_id"),
    ),
    "rel_order_includes_product": (
        1,
        valid_edge(order_line, "order_id", "product_id", order, "order_id", product, "product_id"),
    ),
    "rel_order_has_line": (
        2,
        valid_edge(order_line, "order_id", "order_line_id", order, "order_id", order_line, "order_line_id"),
    ),
    "rel_line_references_product": (
        2,
        valid_edge(order_line, "order_line_id", "product_id", order_line, "order_line_id", product, "product_id"),
    ),
    "rel_product_in_category": (
        2,
        valid_edge(product, "product_id", "category_id", product, "product_id", category, "category_id"),
    ),
    "rel_store_in_region": (
        3,
        valid_edge(store, "store_id", "region_id", store, "store_id", region, "region_id"),
    ),
    "rel_customer_prefers_store": (
        3,
        valid_edge(affinity, "customer_id", "preferred_store_id", customer, "customer_id", store, "store_id"),
    ),
    "rel_customer_completes_sale": (
        4,
        valid_edge(store_sale, "customer_id", "sale_id", customer, "customer_id", store_sale, "sale_id"),
    ),
    "rel_sale_at_store": (
        4,
        valid_edge(store_sale, "sale_id", "store_id", store_sale, "sale_id", store, "store_id"),
    ),
    "rel_sale_includes_product": (
        4,
        valid_edge(pos_line, "sale_id", "product_id", store_sale, "sale_id", product, "product_id"),
    ),
    "rel_payment_settles_sale": (
        4,
        valid_edge(payment, "payment_id", "sale_id", payment, "payment_id", store_sale, "sale_id"),
    ),
    "rel_return_for_order": (
        4,
        valid_edge(returns, "return_id", "order_id", returns, "return_id", order, "order_id"),
    ),
    "rel_return_for_sale": (
        4,
        valid_edge(returns, "return_id", "sale_id", returns, "return_id", store_sale, "sale_id"),
    ),
    "rel_return_concerns_product": (
        4,
        valid_edge(returns, "return_id", "product_id", returns, "return_id", product, "product_id"),
    ),
    "rel_inventory_at_store": (
        5,
        valid_edge(inventory, "inventory_id", "store_id", inventory, "inventory_id", store, "store_id"),
    ),
    "rel_inventory_tracks_product": (
        5,
        valid_edge(inventory, "inventory_id", "product_id", inventory, "inventory_id", product, "product_id"),
    ),
    "rel_signal_from_customer": (
        5,
        valid_edge(demand_signal, "demand_signal_id", "customer_id", demand_signal, "demand_signal_id", customer, "customer_id"),
    ),
    "rel_signal_about_product": (
        5,
        valid_edge(demand_signal, "demand_signal_id", "product_id", demand_signal, "demand_signal_id", product, "product_id"),
    ),
    "rel_signal_leads_to_order": (
        5,
        valid_edge(demand_signal, "demand_signal_id", "order_id", demand_signal, "demand_signal_id", order, "order_id"),
    ),
    "rel_campaign_has_contact": (
        6,
        valid_edge(campaign_contact, "campaign_id", "contact_id", campaign, "campaign_id", campaign_contact, "contact_id"),
    ),
    "rel_contact_addresses_customer": (
        6,
        valid_edge(campaign_contact, "contact_id", "customer_id", campaign_contact, "contact_id", customer, "customer_id"),
    ),
    "rel_contact_recommends_product": (
        6,
        valid_edge(contact_product, "contact_id", "product_id", campaign_contact, "contact_id", product, "product_id"),
    ),
    "rel_contact_converts_to_order": (
        6,
        valid_edge(campaign_contact, "contact_id", "order_id", campaign_contact, "contact_id", order, "order_id"),
    ),
    "rel_campaign_offers_promotion": (
        6,
        valid_edge(promotion, "campaign_id", "promotion_id", campaign, "campaign_id", promotion, "promotion_id"),
    ),
    "rel_promotion_at_store": (
        6,
        valid_edge(promotion, "promotion_id", "store_id", promotion, "promotion_id", store, "store_id"),
    ),
}

for table_name, (stage, table_df) in relationship_tables.items():
    manifest.append((table_name, "Relationship", stage, write_table(table_name, table_df)))

loaded_at = datetime.now(timezone.utc).replace(tzinfo=None)
manifest_schema = T.StructType(
    [
        T.StructField("table_name", T.StringType(), False),
        T.StructField("object_kind", T.StringType(), False),
        T.StructField("introduced_in_stage", T.IntegerType(), False),
        T.StructField("row_count", T.LongType(), False),
    ]
)
manifest_df = spark.createDataFrame(manifest, manifest_schema).withColumn("loaded_at_utc", F.lit(loaded_at).cast("timestamp"))
write_table("iq_deployment_manifest", manifest_df)

source_profile = [(name, int(count)) for name, count in sorted(raw_counts.items())]
source_profile_schema = T.StructType(
    [
        T.StructField("source_name", T.StringType(), False),
        T.StructField("raw_row_count", T.LongType(), False),
    ]
)
source_profile_df = spark.createDataFrame(source_profile, source_profile_schema).withColumn(
    "profiled_at_utc", F.lit(loaded_at).cast("timestamp")
)
write_table("iq_source_profile", source_profile_df)

summary = {
    "status": "success",
    "entities": len(entity_tables),
    "relationships": len(relationship_tables),
    "entity_rows": sum(row_count for _, kind, _, row_count in manifest if kind == "Entity"),
    "relationship_rows": sum(row_count for _, kind, _, row_count in manifest if kind == "Relationship"),
}
print(json.dumps(summary, ensure_ascii=False, indent=2))

try:
    from notebookutils import mssparkutils

    mssparkutils.notebook.exit(json.dumps(summary, ensure_ascii=False))
except Exception:
    pass

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
