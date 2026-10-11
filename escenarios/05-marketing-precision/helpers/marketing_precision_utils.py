
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Dict, List, Optional
import re
import math
import warnings
import pandas as pd
import numpy as np

# Estructura del repositorio frasohome-demos:
#   datos/retail_omnicanal/raw_csv       -> datasets base del caso
#   datos/marketing_precision/raw_csv    -> datasets de marketing de precisión
#   escenarios/05-marketing-precision/   -> notebooks, helpers y salidas
SCENARIO_DIR = Path(__file__).resolve().parents[1]
BASE_REL = Path("datos") / "retail_omnicanal" / "raw_csv"
MP_REL = Path("datos") / "marketing_precision" / "raw_csv"


def resolve_case_root(start: Optional[Path] = None) -> Path:
    """Devuelve la raíz del repositorio (carpeta que contiene `datos/`)."""
    starts = [Path(start).resolve()] if start is not None else []
    starts += [Path.cwd().resolve(), SCENARIO_DIR]
    for s in starts:
        for p in [s] + list(s.parents):
            if (p / BASE_REL).exists() and (p / MP_REL).exists():
                return p
    raise FileNotFoundError(
        "No se encontró la raíz del repositorio frasohome-demos. Debe existir "
        "'datos/retail_omnicanal/raw_csv' y 'datos/marketing_precision/raw_csv'."
    )

def get_paths(start: Optional[Path] = None) -> Dict[str, Path]:
    root = resolve_case_root(start)
    out = SCENARIO_DIR / "outputs"
    out.mkdir(exist_ok=True)
    return {
        "root": root,
        "base": root / BASE_REL,
        "mp": root / MP_REL,
        "outputs": out,
    }

def parse_mixed_number(val):
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float, np.integer, np.floating)):
        return float(val)
    s = str(val).strip().replace("€", "").replace("%", "")
    s = re.sub(r"[^0-9,.\-]", "", s)
    if s == "":
        return np.nan
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        if len(parts[-1]) in (1, 2):
            s = "".join(parts[:-1]).replace(".", "") + "." + parts[-1] if len(parts) > 1 else s.replace(",", ".")
        else:
            s = s.replace(",", "")
    else:
        parts = s.split(".")
        if len(parts) > 2:
            s = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return float(s)
    except Exception:
        return np.nan

def clean_customer_id(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.upper()
        .str.strip()
        .str.replace(r"[^A-Z0-9]", "", regex=True)
        .replace({"NAN": np.nan, "NONE": np.nan, "": np.nan})
    )

def to_datetime(series: pd.Series) -> pd.Series:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pd.to_datetime(series, errors="coerce", dayfirst=True)

def to_number(series: pd.Series) -> pd.Series:
    return series.map(parse_mixed_number)

def read_base(name: str, start: Optional[Path] = None) -> pd.DataFrame:
    return pd.read_csv(get_paths(start)["base"] / name)

def read_mp(name: str, start: Optional[Path] = None) -> pd.DataFrame:
    return pd.read_csv(get_paths(start)["mp"] / name)

def load_core_tables(start: Optional[Path] = None) -> Dict[str, pd.DataFrame]:
    base = get_paths(start)["base"]
    mp = get_paths(start)["mp"]

    crm = pd.read_csv(base / "crm.csv")
    crm["customer_id"] = clean_customer_id(crm["customer_id"])
    for c in ["fecha_alta_programa", "fecha_baja", "ultima_actualizacion", "fecha_nacimiento"]:
        if c in crm.columns:
            crm[c + "_dt"] = to_datetime(crm[c])

    fact = pd.read_csv(base / "fact_transacciones.csv")
    fact["customer_id"] = clean_customer_id(fact["customer_id_std"])
    fact["fecha_movimiento_dt"] = to_datetime(fact["fecha_movimiento"])
    for c in ["importe_abs_num", "importe_signed_num", "margen_bruto_num", "descuento_pct_num", "coste_total_num", "precio_venta_num"]:
        if c in fact.columns:
            fact[c] = pd.to_numeric(fact[c], errors="coerce")
    fact["es_devolucion"] = pd.to_numeric(fact["es_devolucion"], errors="coerce").fillna(0).astype(int)

    productos = pd.read_csv(base / "productos.csv")
    for c in ["precio_venta", "coste_unitario"]:
        if c in productos.columns:
            productos[c + "_num"] = to_number(productos[c])

    stock = pd.read_csv(base / "stock_diario.csv")
    stock["fecha_dt"] = to_datetime(stock["fecha"])
    for c in ["stock_cierre", "stock_reservado", "stock_en_transito", "stock_minimo"]:
        if c in stock.columns:
            stock[c] = to_number(stock[c])

    pedidos = pd.read_csv(base / "pedidos.csv")
    pedidos["customer_id"] = clean_customer_id(pedidos["customer_id"])
    pedidos["fecha_pedido_dt"] = to_datetime(pedidos["fecha_pedido"])
    for c in ["importe_total", "gastos_envio"]:
        if c in pedidos.columns:
            pedidos[c + "_num"] = to_number(pedidos[c])

    ventas_pos = pd.read_csv(base / "ventas_pos.csv")
    ventas_pos["customer_id"] = clean_customer_id(ventas_pos["customer_id"])
    ventas_pos["fecha_hora_dt"] = to_datetime(ventas_pos["fecha_hora"])
    for c in ["precio_unitario", "descuento_importe", "importe_linea"]:
        if c in ventas_pos.columns:
            ventas_pos[c + "_num"] = to_number(ventas_pos[c])
    ventas_pos["descuento_pct"] = pd.to_numeric(ventas_pos["descuento_pct"], errors="coerce")

    lineas_pedido = pd.read_csv(base / "lineas_pedido.csv")
    for c in ["precio_unitario", "descuento_importe", "importe_linea"]:
        if c in lineas_pedido.columns:
            lineas_pedido[c + "_num"] = to_number(lineas_pedido[c])
    lineas_pedido["descuento_pct"] = pd.to_numeric(lineas_pedido["descuento_pct"], errors="coerce")

    devoluciones_online = pd.read_csv(base / "devoluciones_online.csv")
    devoluciones_online["fecha_devolucion_dt"] = to_datetime(devoluciones_online["fecha_devolucion"])
    devoluciones_online["importe_reembolsado_num"] = to_number(devoluciones_online["importe_reembolsado"])

    devoluciones_tienda = pd.read_csv(base / "devoluciones_tienda.csv")
    devoluciones_tienda["customer_id"] = clean_customer_id(devoluciones_tienda["customer_id"])
    devoluciones_tienda["fecha_devolucion_dt"] = to_datetime(devoluciones_tienda["fecha_devolucion"])
    devoluciones_tienda["importe_reembolsado_num"] = to_number(devoluciones_tienda["importe_reembolsado"])

    tiendas = pd.read_csv(base / "tiendas.csv")
    tiendas["fecha_apertura_dt"] = to_datetime(tiendas["fecha_apertura"])

    ids = pd.read_csv(mp / "identidades_cliente.csv")
    ids["customer_id_raw"] = clean_customer_id(ids["customer_id_raw"])
    ids["fecha_evento_dt"] = to_datetime(ids["fecha_evento"])

    gt = pd.read_csv(mp / "identidades_cliente_ground_truth.csv")
    gt["customer_id_canonico"] = clean_customer_id(gt["customer_id_canonico"])

    campanas = pd.read_csv(mp / "campanas_marketing.csv")
    campanas["fecha_inicio_dt"] = to_datetime(campanas["fecha_inicio"])
    campanas["fecha_fin_dt"] = to_datetime(campanas["fecha_fin"])

    contactos = pd.read_csv(mp / "contactos_campana.csv")
    contactos["customer_id"] = clean_customer_id(contactos["customer_id"])
    contactos["fecha_contacto_dt"] = to_datetime(contactos["fecha_contacto"])
    for c in ["coste_contacto_eur", "revenue_30d_eur", "margen_30d_eur"]:
        if c in contactos.columns:
            contactos[c] = pd.to_numeric(contactos[c], errors="coerce")

    eventos_campana = pd.read_csv(mp / "eventos_campana.csv")
    eventos_campana["customer_id"] = clean_customer_id(eventos_campana["customer_id"])
    eventos_campana["fecha_evento_dt"] = to_datetime(eventos_campana["fecha_evento"])
    for c in ["revenue_atribuido_eur", "margen_atribuido_eur"]:
        if c in eventos_campana.columns:
            eventos_campana[c] = pd.to_numeric(eventos_campana[c], errors="coerce")

    eventos_web = pd.read_csv(mp / "eventos_web_app.csv")
    eventos_web["customer_id"] = clean_customer_id(eventos_web["customer_id"])
    eventos_web["fecha_hora_evento_dt"] = to_datetime(eventos_web["fecha_hora_evento"])
    if "valor_evento_eur" in eventos_web.columns:
        eventos_web["valor_evento_eur"] = pd.to_numeric(eventos_web["valor_evento_eur"], errors="coerce")

    promociones = pd.read_csv(mp / "promociones_calendario.csv")
    promociones["fecha_inicio_dt"] = to_datetime(promociones["fecha_inicio"])
    promociones["fecha_fin_dt"] = to_datetime(promociones["fecha_fin"])
    for c in ["descuento_pct", "descuento_importe_eur", "umbral_cesta_eur", "objetivo_margen_min_pct"]:
        if c in promociones.columns:
            promociones[c] = pd.to_numeric(promociones[c], errors="coerce")

    cupones = pd.read_csv(mp / "cupones_clientes.csv")
    cupones["customer_id"] = clean_customer_id(cupones["customer_id"])
    for c in ["fecha_emision", "fecha_inicio_validez", "fecha_fin_validez", "fecha_canje"]:
        if c in cupones.columns:
            cupones[c + "_dt"] = to_datetime(cupones[c])
    for c in ["descuento_pct", "descuento_importe_eur", "gasto_minimo_eur", "importe_cesta_eur", "descuento_aplicado_eur", "margen_post_descuento_eur"]:
        if c in cupones.columns:
            cupones[c] = pd.to_numeric(cupones[c], errors="coerce")

    tickets = pd.read_csv(mp / "tickets_atencion_cliente.csv")
    tickets["customer_id"] = clean_customer_id(tickets["customer_id"])
    tickets["fecha_apertura_dt"] = to_datetime(tickets["fecha_apertura"])
    tickets["fecha_cierre_dt"] = to_datetime(tickets["fecha_cierre"])
    for c in ["sla_horas", "csat_1_5", "importe_compensacion_eur"]:
        if c in tickets.columns:
            tickets[c] = pd.to_numeric(tickets[c], errors="coerce")

    feedback = pd.read_csv(mp / "feedback_clientes.csv")
    feedback["customer_id"] = clean_customer_id(feedback["customer_id"])
    feedback["fecha_feedback_dt"] = to_datetime(feedback["fecha_feedback"])
    for c in ["rating_1_5", "nps_0_10"]:
        if c in feedback.columns:
            feedback[c] = pd.to_numeric(feedback[c], errors="coerce")

    costes = pd.read_csv(mp / "costes_operativos_transaccion.csv")
    costes["customer_id"] = clean_customer_id(costes["customer_id"])
    costes["fecha_transaccion_dt"] = to_datetime(costes["fecha_transaccion"])
    for c in [
        "ingreso_bruto_eur", "descuento_total_eur", "coste_producto_eur", "coste_logistico_eur",
        "coste_packaging_eur", "coste_ultima_milla_eur", "coste_pago_eur", "coste_servicio_eur",
        "coste_devolucion_esperado_eur", "cac_asignado_eur", "margen_contribucion_neto_eur"
    ]:
        if c in costes.columns:
            costes[c] = pd.to_numeric(costes[c], errors="coerce")

    afinidad = pd.read_csv(mp / "afinidad_tienda_cliente.csv")
    afinidad["customer_id"] = clean_customer_id(afinidad["customer_id"])
    for c in ["distancia_km_store_mas_cercana", "gasto_tienda_12m_eur", "gasto_online_12m_eur", "click_collect_propension", "probabilidad_visita_30d"]:
        if c in afinidad.columns:
            afinidad[c] = pd.to_numeric(afinidad[c], errors="coerce")

    creatividades = pd.read_csv(mp / "creatividades_segmento.csv")
    for c in ["open_rate", "ctr", "cvr", "revenue_por_1000_envios_eur", "winning_variant_flag"]:
        if c in creatividades.columns:
            creatividades[c] = pd.to_numeric(creatividades[c], errors="coerce")

    guardrails = pd.read_csv(mp / "guardrails_marca_genai.csv")

    return {
        "crm": crm,
        "fact": fact,
        "productos": productos,
        "stock": stock,
        "pedidos": pedidos,
        "ventas_pos": ventas_pos,
        "lineas_pedido": lineas_pedido,
        "devoluciones_online": devoluciones_online,
        "devoluciones_tienda": devoluciones_tienda,
        "tiendas": tiendas,
        "ids": ids,
        "gt": gt,
        "campanas": campanas,
        "contactos": contactos,
        "eventos_campana": eventos_campana,
        "eventos_web": eventos_web,
        "promociones": promociones,
        "cupones": cupones,
        "tickets": tickets,
        "feedback": feedback,
        "costes": costes,
        "afinidad": afinidad,
        "creatividades": creatividades,
        "guardrails": guardrails,
    }

def build_identity_clusters(ids: pd.DataFrame) -> pd.DataFrame:
    link_cols = [
        "email_hash", "telefono_hash", "tarjeta_fidelizacion_id",
        "cookie_id", "device_id", "app_user_id", "usuario_online_id"
    ]
    parent = {x: x for x in ids["identity_signal_id"]}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for col in link_cols:
        if col not in ids.columns:
            continue
        sub = ids.dropna(subset=[col]).copy()
        for _, g in sub.groupby(col):
            members = g["identity_signal_id"].tolist()
            first = members[0]
            for sig in members[1:]:
                union(first, sig)

    out = []
    for sig in ids["identity_signal_id"]:
        out.append((sig, find(sig)))
    clusters = pd.DataFrame(out, columns=["identity_signal_id", "pred_cluster_id"])
    cluster_sizes = clusters["pred_cluster_id"].value_counts().rename("cluster_size").reset_index().rename(columns={"index": "pred_cluster_id"})
    clusters = clusters.merge(cluster_sizes, on="pred_cluster_id", how="left")
    return clusters

def top_terms(texts: pd.Series, n: int = 20):
    from sklearn.feature_extraction.text import CountVectorizer
    clean = texts.dropna().astype(str)
    if clean.empty:
        return pd.DataFrame(columns=["termino", "frecuencia"])
    vectorizer = CountVectorizer(stop_words=spanish_stop_words(), ngram_range=(1, 2), min_df=2)
    X = vectorizer.fit_transform(clean)
    freqs = np.asarray(X.sum(axis=0)).ravel()
    terms = pd.Series(freqs, index=vectorizer.get_feature_names_out()).sort_values(ascending=False).head(n)
    return terms.reset_index().rename(columns={"index": "termino", 0: "frecuencia"})

def spanish_stop_words():
    return [
        "de", "la", "el", "que", "y", "en", "un", "una", "lo", "con", "para", "por",
        "del", "las", "los", "se", "mi", "su", "al", "es", "ha", "me", "no", "muy",
        "más", "pero", "como", "sin", "ya", "si", "porque", "cuando", "todo", "esta",
        "este", "eso", "esa", "ese", "han", "fue", "ser", "está", "sobre", "tener",
        "llegó", "pedido", "producto", "fra", "home", "frasohome"
    ]

def export_csv(df: pd.DataFrame, filename: str, start: Optional[Path] = None) -> Path:
    out_dir = get_paths(start)["outputs"]
    path = out_dir / filename
    df.to_csv(path, index=False)
    return path
