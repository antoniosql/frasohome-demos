from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import math
import re
import warnings

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


POSITIVE_VALUES = {
    "1", "S", "SI", "SÍ", "YES", "Y", "TRUE", "T", "ACTIVO", "CONTACTABLE"
}

CATEGORY_CANONICAL_MAP = {
    "TEXTIL HOGAR": "Textil Hogar",
    "TEXTIL HOGAR ": "Textil Hogar",
    "TEXTIL HOGAR": "Textil Hogar",
    "TEXTIL HOGAR": "Textil Hogar",
    "DECORACIÓN": "Decoración",
    "DECORACION": "Decoración",
    "MUEBLES": "Muebles",
    "ILUMINACIÓN": "Iluminación",
    "ILUMINACION": "Iluminación",
    "MULTICATEGORÍA": "Multicategoría",
    "MULTICATEGORIA": "Multicategoría",
    "MULTICATEGORÍA ": "Multicategoría",
}

VOC_THEME_RECOMMENDATIONS = {
    "precio_promocion": "Revisar arquitectura promocional, claridad de condiciones y elasticidad por segmento antes de ampliar descuentos.",
    "calidad_producto": "Mejorar contenido de producto, pruebas sociales y control de calidad en categorías con mayor fricción.",
    "entrega_servicio": "Reducir incertidumbre logística con mensajes proactivos y tracking más visible en postcompra.",
    "medidas_ajuste": "Aumentar información visual y guías de dimensiones para reducir devoluciones por desajuste.",
    "tienda_experiencia": "Ajustar activación local y experiencia en tienda, con foco en disponibilidad y asesoramiento.",
    "info_producto": "Reforzar fichas de producto, materiales, dimensiones y FAQs para elevar conversión cualificada.",
    "info producto": "Reforzar fichas de producto, materiales, dimensiones y FAQs para elevar conversión cualificada.",
    "cupon": "Simplificar condiciones de canje y comunicar con más transparencia los límites promocionales.",
    "fidelizacion": "Redefinir beneficios visibles del club y su conexión con frecuencia, margen y exclusividad.",
    "devolucion": "Reducir fricción operativa y anticipar objeciones precompra en categorías con mayor retorno.",
    "entrega": "Reducir fricción logística con avisos proactivos, SLA visible y expectativas realistas.",
}


@dataclass
class ProjectPaths:
    root: Path
    data: Path
    mp: Path
    outputs: Path


def title_case(val: object) -> Optional[str]:
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not s:
        return None
    return s[:1].upper() + s[1:]


def canonical_category(val: object) -> Optional[str]:
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not s:
        return None
    s_up = s.upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    s_up = re.sub(r"\s+", " ", s_up)
    if s_up in CATEGORY_CANONICAL_MAP:
        return CATEGORY_CANONICAL_MAP[s_up]
    return title_case(s)


MONTHS_ES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


SCENARIO_DIR = Path(__file__).resolve().parents[1]


def resolve_project_root(start: Optional[Path] = None) -> ProjectPaths:
    """Localiza la raíz de frasohome-demos (carpeta que contiene `datos/`)."""
    if start is None:
        start = Path(__file__).resolve().parent
    start = Path(start).resolve()
    for c in [start] + list(start.parents):
        data_dir = c / "datos" / "retail_omnicanal" / "raw_csv"
        mp_dir = c / "datos" / "marketing_precision" / "raw_csv"
        if data_dir.exists() and mp_dir.exists():
            return ProjectPaths(c, data_dir, mp_dir, _resolve_outputs(c))
    raise FileNotFoundError(
        "No se encontró la raíz del repositorio. Deben existir 'datos/retail_omnicanal/raw_csv' "
        "y 'datos/marketing_precision/raw_csv'."
    )


def _resolve_outputs(root: Path) -> Path:
    """Usa las salidas regeneradas por los notebooks si existen; si no, las de ejemplo."""
    regenerated = SCENARIO_DIR / "outputs"
    if regenerated.exists() and any(regenerated.glob("nb*.csv")):
        return regenerated
    return SCENARIO_DIR / "sample_outputs"



def clean_customer_id(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.upper()
        .str.strip()
        .str.replace(r"[^A-Z0-9]", "", regex=True)
        .replace({"NAN": np.nan, "NONE": np.nan, "": np.nan})
    )


def to_datetime(series: pd.Series) -> pd.Series:
    s = series.astype("string").str.strip()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dt = pd.to_datetime(s, errors="coerce", dayfirst=True)
    mask = dt.isna() & s.notna() & s.str.contains(r"\bde\b", case=False, regex=True)
    if mask.any():
        pat = re.compile(
            r"^\s*(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+de\s+(\d{4})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?\s*$",
            re.IGNORECASE,
        )
        parsed = []
        for val in s[mask].astype(str).str.lower().tolist():
            m = pat.match(val)
            if not m:
                parsed.append(pd.NaT)
                continue
            mon = MONTHS_ES.get(m.group(2).lower())
            if mon is None:
                parsed.append(pd.NaT)
                continue
            parsed.append(
                pd.Timestamp(
                    year=int(m.group(3)),
                    month=mon,
                    day=int(m.group(1)),
                    hour=int(m.group(4) or 0),
                    minute=int(m.group(5) or 0),
                    second=int(m.group(6) or 0),
                )
            )
        dt.loc[mask] = pd.to_datetime(pd.Series(parsed, index=s[mask].index), errors="coerce")
    return dt



def parse_mixed_number(val: object) -> float:
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float, np.integer, np.floating)):
        return float(val)
    s = str(val).strip()
    if not s:
        return np.nan
    s = s.replace("€", "").replace("EUR", "").replace("%", "")
    s = re.sub(r"[^0-9,\.\-]", "", s)
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
            s = "".join(parts[:-1]) + "." + parts[-1] if len(parts) > 1 else s.replace(",", ".")
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



def to_number(series: pd.Series) -> pd.Series:
    return series.map(parse_mixed_number)



def yes_no_to_bool(val: object) -> Optional[bool]:
    if pd.isna(val):
        return None
    s = str(val).strip().upper()
    return s in POSITIVE_VALUES



def first_non_null(series: pd.Series):
    notna = series.dropna()
    if notna.empty:
        return np.nan
    return notna.iloc[0]



def dedupe_customer_rows(df: pd.DataFrame, customer_col: str = "customer_id", score_cols: Optional[List[str]] = None) -> pd.DataFrame:
    if df.empty or customer_col not in df.columns:
        return df
    tmp = df.copy()
    score_cols = score_cols or []
    sort_cols = [customer_col]
    ascending = [True]
    for c in score_cols:
        if c in tmp.columns:
            tmp[c] = pd.to_numeric(tmp[c], errors="coerce")
            sort_cols.append(c)
            ascending.append(False)
    tmp = tmp.sort_values(sort_cols, ascending=ascending)
    return tmp.drop_duplicates(subset=[customer_col], keep="first")



def read_csv_mixed(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)



def load_tables(paths: ProjectPaths) -> Dict[str, pd.DataFrame]:
    base = paths.data
    mp = paths.mp
    tables: Dict[str, pd.DataFrame] = {}

    # Base datasets
    crm = read_csv_mixed(base / "crm.csv")
    crm["customer_id"] = clean_customer_id(crm["customer_id"])
    for c in ["fecha_alta_programa", "fecha_baja", "ultima_actualizacion", "fecha_nacimiento"]:
        if c in crm.columns:
            crm[c + "_dt"] = to_datetime(crm[c])
    tables["crm"] = crm

    fact = read_csv_mixed(base / "fact_transacciones.csv")
    fact["customer_id"] = clean_customer_id(fact.get("customer_id_std", pd.Series(dtype="string")))
    fact["fecha_movimiento_dt"] = to_datetime(fact.get("fecha_movimiento", fact.get("fecha_movimiento_raw", pd.Series(dtype="string"))))
    for c in ["importe_abs_num", "importe_signed_num", "margen_bruto_num", "descuento_pct_num", "coste_total_num", "precio_venta_num", "cantidad_signed"]:
        if c in fact.columns:
            fact[c] = pd.to_numeric(fact[c], errors="coerce")
    if "es_devolucion" in fact.columns:
        fact["es_devolucion"] = pd.to_numeric(fact["es_devolucion"], errors="coerce").fillna(0).astype(int)
    for c in ["categoria", "subcategoria"]:
        if c in fact.columns:
            fact[c] = fact[c].map(canonical_category if c == "categoria" else title_case)
    tables["fact"] = fact

    productos = read_csv_mixed(base / "productos.csv")
    productos["categoria"] = productos["categoria"].map(canonical_category)
    productos["subcategoria"] = productos["subcategoria"].map(title_case)
    for c in ["precio_venta", "coste_unitario"]:
        if c in productos.columns:
            productos[c + "_num"] = to_number(productos[c])
    tables["productos"] = productos

    tiendas = read_csv_mixed(base / "tiendas.csv")
    tiendas["fecha_apertura_dt"] = to_datetime(tiendas["fecha_apertura"])
    tables["tiendas"] = tiendas

    stock = read_csv_mixed(base / "stock_diario.csv")
    stock["fecha_dt"] = to_datetime(stock["fecha"])
    for c in ["stock_cierre", "stock_reservado", "stock_en_transito", "stock_minimo"]:
        if c in stock.columns:
            stock[c] = to_number(stock[c])
    tables["stock"] = stock

    pedidos = read_csv_mixed(base / "pedidos.csv")
    pedidos["customer_id"] = clean_customer_id(pedidos["customer_id"])
    pedidos["fecha_pedido_dt"] = to_datetime(pedidos["fecha_pedido"])
    for c in ["importe_total", "gastos_envio"]:
        if c in pedidos.columns:
            pedidos[c + "_num"] = to_number(pedidos[c])
    tables["pedidos"] = pedidos

    ventas_pos = read_csv_mixed(base / "ventas_pos.csv")
    ventas_pos["customer_id"] = clean_customer_id(ventas_pos["customer_id"])
    ventas_pos["fecha_hora_dt"] = to_datetime(ventas_pos["fecha_hora"])
    for c in ["precio_unitario", "descuento_importe", "importe_linea"]:
        if c in ventas_pos.columns:
            ventas_pos[c + "_num"] = to_number(ventas_pos[c])
    ventas_pos["descuento_pct"] = pd.to_numeric(ventas_pos.get("descuento_pct"), errors="coerce")
    ventas_pos["categoria"] = ventas_pos["categoria"].map(canonical_category)
    ventas_pos["subcategoria"] = ventas_pos["subcategoria"].map(title_case)
    tables["ventas_pos"] = ventas_pos

    lineas_pedido = read_csv_mixed(base / "lineas_pedido.csv")
    for c in ["precio_unitario", "descuento_importe", "importe_linea"]:
        if c in lineas_pedido.columns:
            lineas_pedido[c + "_num"] = to_number(lineas_pedido[c])
    lineas_pedido["descuento_pct"] = pd.to_numeric(lineas_pedido.get("descuento_pct"), errors="coerce")
    lineas_pedido["categoria"] = lineas_pedido["categoria"].map(canonical_category)
    lineas_pedido["subcategoria"] = lineas_pedido["subcategoria"].map(title_case)
    tables["lineas_pedido"] = lineas_pedido

    devoluciones_online = read_csv_mixed(base / "devoluciones_online.csv")
    for c in ["importe_reembolsado"]:
        if c in devoluciones_online.columns:
            devoluciones_online[c + "_num"] = to_number(devoluciones_online[c])
    if "fecha_devolucion" in devoluciones_online.columns:
        devoluciones_online["fecha_devolucion_dt"] = to_datetime(devoluciones_online["fecha_devolucion"])
    tables["devoluciones_online"] = devoluciones_online

    devoluciones_tienda = read_csv_mixed(base / "devoluciones_tienda.csv")
    if "customer_id" in devoluciones_tienda.columns:
        devoluciones_tienda["customer_id"] = clean_customer_id(devoluciones_tienda["customer_id"])
    for c in ["importe_reembolsado"]:
        if c in devoluciones_tienda.columns:
            devoluciones_tienda[c + "_num"] = to_number(devoluciones_tienda[c])
    if "fecha_devolucion" in devoluciones_tienda.columns:
        devoluciones_tienda["fecha_devolucion_dt"] = to_datetime(devoluciones_tienda["fecha_devolucion"])
    tables["devoluciones_tienda"] = devoluciones_tienda

    pagos_tienda = read_csv_mixed(base / "pagos_tienda.csv")
    if "fecha_hora" in pagos_tienda.columns:
        pagos_tienda["fecha_hora_dt"] = to_datetime(pagos_tienda["fecha_hora"])
    tables["pagos_tienda"] = pagos_tienda

    # Marketing precision datasets
    ids = read_csv_mixed(mp / "identidades_cliente.csv")
    if "customer_id_raw" in ids.columns:
        ids["customer_id_raw"] = clean_customer_id(ids["customer_id_raw"])
    if "fecha_evento" in ids.columns:
        ids["fecha_evento_dt"] = to_datetime(ids["fecha_evento"])
    tables["identidades"] = ids

    gt = read_csv_mixed(mp / "identidades_cliente_ground_truth.csv")
    if "customer_id_canonico" in gt.columns:
        gt["customer_id_canonico"] = clean_customer_id(gt["customer_id_canonico"])
    tables["identity_gt"] = gt

    campanas = read_csv_mixed(mp / "campanas_marketing.csv")
    for c in ["fecha_inicio", "fecha_fin"]:
        if c in campanas.columns:
            campanas[c + "_dt"] = to_datetime(campanas[c])
    num_campaign_cols = [
        "descuento_pct", "presupuesto_plan_eur", "grupo_control_pct", "audiencia_estimada", "contactos",
        "audiencias", "control", "entregados", "conversiones_30d", "revenue_30d_total_eur", "margen_30d_total_eur",
        "coste_contacto_total_eur", "cnt_click", "cnt_open", "cnt_purchase", "cnt_store_visit_estimada",
        "cnt_unsubscribe", "cupones_emitidos", "cupones_canjeados"
    ]
    for c in num_campaign_cols:
        if c in campanas.columns:
            campanas[c] = pd.to_numeric(campanas[c], errors="coerce")
    tables["campanas"] = campanas

    contactos = read_csv_mixed(mp / "contactos_campana.csv")
    if "customer_id" in contactos.columns:
        contactos["customer_id"] = clean_customer_id(contactos["customer_id"])
    if "fecha_contacto" in contactos.columns:
        contactos["fecha_contacto_dt"] = to_datetime(contactos["fecha_contacto"])
    for c in ["coste_contacto_eur", "revenue_30d_eur", "margen_30d_eur"]:
        if c in contactos.columns:
            contactos[c] = pd.to_numeric(contactos[c], errors="coerce")
    tables["contactos"] = contactos

    eventos_campana = read_csv_mixed(mp / "eventos_campana.csv")
    if "customer_id" in eventos_campana.columns:
        eventos_campana["customer_id"] = clean_customer_id(eventos_campana["customer_id"])
    if "fecha_evento" in eventos_campana.columns:
        eventos_campana["fecha_evento_dt"] = to_datetime(eventos_campana["fecha_evento"])
    for c in ["revenue_atribuido_eur", "margen_atribuido_eur"]:
        if c in eventos_campana.columns:
            eventos_campana[c] = pd.to_numeric(eventos_campana[c], errors="coerce")
    tables["eventos_campana"] = eventos_campana

    eventos_web = read_csv_mixed(mp / "eventos_web_app.csv")
    if "customer_id" in eventos_web.columns:
        eventos_web["customer_id"] = clean_customer_id(eventos_web["customer_id"])
    if "fecha_hora_evento" in eventos_web.columns:
        eventos_web["fecha_hora_evento_dt"] = to_datetime(eventos_web["fecha_hora_evento"])
    if "valor_evento_eur" in eventos_web.columns:
        eventos_web["valor_evento_eur"] = pd.to_numeric(eventos_web["valor_evento_eur"], errors="coerce")
    if "categoria" in eventos_web.columns:
        eventos_web["categoria"] = eventos_web["categoria"].map(canonical_category)
    if "subcategoria" in eventos_web.columns:
        eventos_web["subcategoria"] = eventos_web["subcategoria"].map(title_case)
    tables["eventos_web"] = eventos_web

    promociones = read_csv_mixed(mp / "promociones_calendario.csv")
    for c in ["fecha_inicio", "fecha_fin"]:
        if c in promociones.columns:
            promociones[c + "_dt"] = to_datetime(promociones[c])
    for c in ["descuento_pct", "descuento_importe_eur", "umbral_cesta_eur", "objetivo_margen_min_pct"]:
        if c in promociones.columns:
            promociones[c] = pd.to_numeric(promociones[c], errors="coerce")
    tables["promociones"] = promociones

    cupones = read_csv_mixed(mp / "cupones_clientes.csv")
    if "customer_id" in cupones.columns:
        cupones["customer_id"] = clean_customer_id(cupones["customer_id"])
    for c in ["fecha_emision", "fecha_inicio_validez", "fecha_fin_validez", "fecha_canje"]:
        if c in cupones.columns:
            cupones[c + "_dt"] = to_datetime(cupones[c])
    for c in ["descuento_pct", "descuento_importe_eur", "gasto_minimo_eur", "importe_cesta_eur", "descuento_aplicado_eur", "margen_post_descuento_eur"]:
        if c in cupones.columns:
            cupones[c] = pd.to_numeric(cupones[c], errors="coerce")
    tables["cupones"] = cupones

    tickets = read_csv_mixed(mp / "tickets_atencion_cliente.csv")
    if "customer_id" in tickets.columns:
        tickets["customer_id"] = clean_customer_id(tickets["customer_id"])
    for c in ["fecha_apertura", "fecha_cierre"]:
        if c in tickets.columns:
            tickets[c + "_dt"] = to_datetime(tickets[c])
    for c in ["sla_horas", "csat_1_5", "importe_compensacion_eur"]:
        if c in tickets.columns:
            tickets[c] = pd.to_numeric(tickets[c], errors="coerce")
    tables["tickets"] = tickets

    feedback = read_csv_mixed(mp / "feedback_clientes.csv")
    if "customer_id" in feedback.columns:
        feedback["customer_id"] = clean_customer_id(feedback["customer_id"])
    if "fecha_feedback" in feedback.columns:
        feedback["fecha_feedback_dt"] = to_datetime(feedback["fecha_feedback"])
    for c in ["rating_1_5", "nps_0_10"]:
        if c in feedback.columns:
            feedback[c] = pd.to_numeric(feedback[c], errors="coerce")
    tables["feedback"] = feedback

    costes = read_csv_mixed(mp / "costes_operativos_transaccion.csv")
    if "customer_id" in costes.columns:
        costes["customer_id"] = clean_customer_id(costes["customer_id"])
    if "fecha_transaccion" in costes.columns:
        costes["fecha_transaccion_dt"] = to_datetime(costes["fecha_transaccion"])
    for c in [
        "ingreso_bruto_eur", "descuento_total_eur", "coste_producto_eur", "coste_logistico_eur", "coste_packaging_eur",
        "coste_ultima_milla_eur", "coste_pago_eur", "coste_servicio_eur", "coste_devolucion_esperado_eur", "cac_asignado_eur",
        "margen_contribucion_neto_eur"
    ]:
        if c in costes.columns:
            costes[c] = pd.to_numeric(costes[c], errors="coerce")
    if "categoria_principal" in costes.columns:
        costes["categoria_principal"] = costes["categoria_principal"].map(canonical_category)
    tables["costes"] = costes

    afinidad = read_csv_mixed(mp / "afinidad_tienda_cliente.csv")
    if "customer_id" in afinidad.columns:
        afinidad["customer_id"] = clean_customer_id(afinidad["customer_id"])
    for c in ["distancia_km_store_mas_cercana", "gasto_tienda_12m_eur", "gasto_online_12m_eur", "click_collect_propension", "probabilidad_visita_30d"]:
        if c in afinidad.columns:
            afinidad[c] = pd.to_numeric(afinidad[c], errors="coerce")
    tables["afinidad"] = afinidad

    creatividades = read_csv_mixed(mp / "creatividades_segmento.csv")
    for c in ["open_rate", "ctr", "cvr", "revenue_por_1000_envios_eur", "winning_variant_flag"]:
        if c in creatividades.columns:
            creatividades[c] = pd.to_numeric(creatividades[c], errors="coerce")
    tables["creatividades"] = creatividades

    guardrails = read_csv_mixed(mp / "guardrails_marca_genai.csv")
    tables["guardrails"] = guardrails

    # Documentation tables
    for extra in [
        "mapeo_casos_marketing_precision.csv",
        "catalogo_datasets_marketing_precision.csv",
        "diccionario_columnas_marketing_precision.csv",
        "validacion_datasets_marketing_precision.csv",
    ]:
        p = mp / extra
        if p.exists():
            tables[extra.replace(".csv", "")] = read_csv_mixed(p)

    return tables



def load_outputs(paths: ProjectPaths) -> Dict[str, pd.DataFrame]:
    out_dir = paths.outputs
    output_map: Dict[str, str] = {
        "identity_mapping": "nb09_identity_mapping.csv",
        "customer360": "nb09_customer360.csv",
        "value_segmentation": "nb10_customer_value_segmentation.csv",
        "segment_summary": "nb10_segment_summary.csv",
        "churn_training": "nb11_churn_training_dataset.csv",
        "churn_scoring": "nb11_churn_scoring_latest.csv",
        "propensity_training": "nb12_propension_categoria_training.csv",
        "propensity_scoring": "nb12_propension_categoria_scoring.csv",
        "cross_sell_rules": "nb13_cross_sell_rules.csv",
        "cross_sell_candidates": "nb13_cross_sell_customer_candidates.csv",
        "promo_scoreboard": "nb14_promo_scoreboard.csv",
        "promo_decisions": "nb14_promo_decisions.csv",
        "return_risk_scoring": "nb15_return_risk_scoring.csv",
        "return_risk_products": "nb15_product_return_risk_summary.csv",
        "local_activation": "nb16_local_activation_plan.csv",
        "store_category_summary": "nb16_store_category_summary.csv",
        "voc_issue_matrix": "nb17_voc_issue_matrix.csv",
        "voc_prompt_pack": "nb17_voc_prompt_pack.csv",
        "copy_briefs": "nb18_genai_copy_briefs.csv",
        "prompt_library": "nb18_genai_prompt_library.csv",
    }
    outputs: Dict[str, pd.DataFrame] = {}
    for key, fname in output_map.items():
        p = out_dir / fname
        if p.exists():
            df = read_csv_mixed(p)
            if "customer_id" in df.columns:
                df["customer_id"] = clean_customer_id(df["customer_id"])
            # date parsing for known columns
            for c in [
                "fecha_evento", "fecha_evento_dt", "primera_compra", "ultima_compra", "last_web_event", "snapshot_date",
                "fecha_movimiento_dt"
            ]:
                if c in df.columns:
                    df[c] = to_datetime(df[c])
            outputs[key] = df
    return outputs



def dataset_catalog(tables: Dict[str, pd.DataFrame], outputs: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, pd.DataFrame]]:
    return {
        "Base del caso": {
            "crm": tables.get("crm", pd.DataFrame()),
            "fact": tables.get("fact", pd.DataFrame()),
            "productos": tables.get("productos", pd.DataFrame()),
            "tiendas": tables.get("tiendas", pd.DataFrame()),
            "stock": tables.get("stock", pd.DataFrame()),
            "pedidos": tables.get("pedidos", pd.DataFrame()),
            "ventas_pos": tables.get("ventas_pos", pd.DataFrame()),
            "lineas_pedido": tables.get("lineas_pedido", pd.DataFrame()),
            "devoluciones_online": tables.get("devoluciones_online", pd.DataFrame()),
            "devoluciones_tienda": tables.get("devoluciones_tienda", pd.DataFrame()),
            "pagos_tienda": tables.get("pagos_tienda", pd.DataFrame()),
        },
        "Marketing de precisión": {
            "campanas": tables.get("campanas", pd.DataFrame()),
            "contactos": tables.get("contactos", pd.DataFrame()),
            "eventos_campana": tables.get("eventos_campana", pd.DataFrame()),
            "eventos_web": tables.get("eventos_web", pd.DataFrame()),
            "promociones": tables.get("promociones", pd.DataFrame()),
            "cupones": tables.get("cupones", pd.DataFrame()),
            "tickets": tables.get("tickets", pd.DataFrame()),
            "feedback": tables.get("feedback", pd.DataFrame()),
            "costes": tables.get("costes", pd.DataFrame()),
            "afinidad": tables.get("afinidad", pd.DataFrame()),
            "creatividades": tables.get("creatividades", pd.DataFrame()),
            "guardrails": tables.get("guardrails", pd.DataFrame()),
            "identidades": tables.get("identidades", pd.DataFrame()),
            "identity_gt": tables.get("identity_gt", pd.DataFrame()),
        },
        "Salidas de modelos": outputs,
        "Documentación": {
            k: v
            for k, v in tables.items()
            if k.startswith("mapeo_") or k.startswith("catalogo_") or k.startswith("diccionario_") or k.startswith("validacion_")
        },
    }



def build_customer_master(tables: Dict[str, pd.DataFrame], outputs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    customer_ids: List[pd.Series] = []
    for source in [
        tables.get("crm"),
        tables.get("fact"),
        outputs.get("customer360"),
        outputs.get("value_segmentation"),
        outputs.get("churn_scoring"),
        outputs.get("propensity_scoring"),
        outputs.get("cross_sell_candidates"),
        outputs.get("local_activation"),
        tables.get("afinidad"),
    ]:
        if isinstance(source, pd.DataFrame) and "customer_id" in source.columns:
            customer_ids.append(clean_customer_id(source["customer_id"]))
    all_ids = pd.concat(customer_ids, ignore_index=True).dropna().drop_duplicates().sort_values().reset_index(drop=True)
    master = pd.DataFrame({"customer_id": all_ids})

    crm = dedupe_customer_rows(tables.get("crm", pd.DataFrame()).copy(), score_cols=["puntos_acumulados"])
    if not crm.empty:
        keep_cols = [
            "customer_id", "nombre", "apellidos", "email", "telefono", "ciudad", "provincia", "pais", "codigo_postal",
            "fecha_alta_programa", "fecha_alta_programa_dt", "tier_fidelizacion", "puntos_acumulados", "estado_cliente",
            "consentimiento_marketing", "canal_preferido_declarado", "origen_alta"
        ]
        master = master.merge(crm[[c for c in keep_cols if c in crm.columns]], on="customer_id", how="left")

    c360 = outputs.get("customer360", pd.DataFrame()).copy()
    if not c360.empty:
        c360 = dedupe_customer_rows(c360, score_cols=["revenue_total_eur", "transacciones"])
        c360_cols = [
            "customer_id", "pred_cluster_id", "revenue_total_eur", "margen_bruto_total_eur", "transacciones", "categorias",
            "primera_compra", "ultima_compra", "revenue_online", "revenue_pos", "omnichannel_flag", "sesiones",
            "pageviews", "add_to_cart", "searches", "last_web_event", "days_since_last_purchase"
        ]
        master = master.merge(c360[[c for c in c360_cols if c in c360.columns]], on="customer_id", how="left")
        # backfill profile fields from customer360 if missing in CRM
        for c in ["nombre", "apellidos", "email", "telefono", "ciudad", "provincia", "pais", "codigo_postal", "tier_fidelizacion", "canal_preferido_declarado", "consentimiento_marketing", "estado_cliente"]:
            if c in c360.columns:
                backfill = c360[["customer_id", c]].rename(columns={c: c + "_c360"})
                master = master.merge(backfill, on="customer_id", how="left")
                master[c] = master[c].combine_first(master[c + "_c360"])
                master = master.drop(columns=[c + "_c360"])

    seg = outputs.get("value_segmentation", pd.DataFrame()).copy()
    if not seg.empty:
        seg = dedupe_customer_rows(seg, score_cols=["clv_proxy_12m", "net_margin"])
        master = master.merge(seg, on="customer_id", how="left", suffixes=("", "_seg"))

    churn = outputs.get("churn_scoring", pd.DataFrame()).copy()
    if not churn.empty:
        churn = dedupe_customer_rows(churn, score_cols=["score_churn", "expected_margin_uplift_eur"])
        churn_cols = [c for c in ["customer_id", "score_churn", "next_best_action", "expected_margin_uplift_eur", "snapshot_date"] if c in churn.columns]
        master = master.merge(churn[churn_cols], on="customer_id", how="left")

    prop = outputs.get("propensity_scoring", pd.DataFrame()).copy()
    if not prop.empty:
        prop = dedupe_customer_rows(prop, score_cols=["score_rank_1"])
        master = master.merge(prop, on="customer_id", how="left")
        if "categoria_rank_1" in master.columns:
            master["categoria_rank_1"] = master["categoria_rank_1"].map(canonical_category)
        if "categoria_rank_2" in master.columns:
            master["categoria_rank_2"] = master["categoria_rank_2"].map(canonical_category)
        if "categoria_rank_3" in master.columns:
            master["categoria_rank_3"] = master["categoria_rank_3"].map(canonical_category)

    cross = outputs.get("cross_sell_candidates", pd.DataFrame()).copy()
    if not cross.empty:
        cross = dedupe_customer_rows(cross, score_cols=["cross_sell_score", "margen_unitario_est_b"])
        cross_cols = [
            "customer_id", "anchor_product", "recommended_product", "recommended_product_name",
            "cross_sell_score", "units_available_b", "margen_unitario_est_b", "categoria", "subcategoria"
        ]
        cross = cross[[c for c in cross_cols if c in cross.columns]].rename(columns={
            "categoria": "cross_sell_categoria_anchor",
            "subcategoria": "cross_sell_subcategoria_anchor",
        })
        master = master.merge(cross, on="customer_id", how="left")

    local = outputs.get("local_activation", pd.DataFrame()).copy()
    if not local.empty:
        local = dedupe_customer_rows(local, score_cols=["targetability_score", "prob_visita_30d"])
        local_cols = [
            "customer_id", "store_id_target", "categoria_target", "prob_visita_30d", "distance_km",
            "targetability_score", "accion_sugerida", "nombre_tienda", "ciudad", "provincia"
        ]
        local = local[[c for c in local_cols if c in local.columns]]
        master = master.merge(local, on="customer_id", how="left", suffixes=("", "_local"))
        # preserve residence city/province from CRM if available
        if "ciudad_local" in master.columns:
            master["ciudad_residencia"] = master["ciudad"]
            master["ciudad_tienda_target"] = master["ciudad_local"]
            master = master.drop(columns=["ciudad_local"])
        else:
            master["ciudad_residencia"] = master.get("ciudad")
            master["ciudad_tienda_target"] = np.nan
        if "provincia_local" in master.columns:
            master["provincia_residencia"] = master["provincia"]
            master["provincia_tienda_target"] = master["provincia_local"]
            master = master.drop(columns=["provincia_local"])
        else:
            master["provincia_residencia"] = master.get("provincia")
            master["provincia_tienda_target"] = np.nan
    else:
        master["ciudad_residencia"] = master.get("ciudad")
        master["provincia_residencia"] = master.get("provincia")
        master["ciudad_tienda_target"] = np.nan
        master["provincia_tienda_target"] = np.nan

    afinidad = dedupe_customer_rows(tables.get("afinidad", pd.DataFrame()).copy(), score_cols=["probabilidad_visita_30d", "gasto_online_12m_eur"])
    if not afinidad.empty:
        affinity_cols = [
            "customer_id", "store_id_preferida", "store_id_mas_cercana", "distancia_km_store_mas_cercana",
            "frecuencia_visita_tienda_12m", "gasto_tienda_12m_eur", "gasto_online_12m_eur", "click_collect_propension",
            "probabilidad_visita_30d", "cluster_local", "es_capturable_localmente"
        ]
        master = master.merge(afinidad[[c for c in affinity_cols if c in afinidad.columns]], on="customer_id", how="left", suffixes=("", "_afinidad"))

    # Derived fields
    master["customer_name"] = (
        master.get("nombre", pd.Series(index=master.index, dtype="object")).fillna("").astype(str).str.strip()
        + " "
        + master.get("apellidos", pd.Series(index=master.index, dtype="object")).fillna("").astype(str).str.strip()
    ).str.strip()
    master["contactable"] = master.get("consentimiento_marketing").map(yes_no_to_bool).eq(True)

    # choose primary economic metrics
    master["gross_revenue_master"] = master.get("gross_revenue").combine_first(master.get("revenue_total_eur"))
    master["net_margin_master"] = master.get("net_margin").combine_first(master.get("margen_bruto_total_eur"))
    master["tx_count_master"] = master.get("tx_count").combine_first(master.get("transacciones"))
    master["clv_master"] = master.get("clv_proxy_12m")

    # top recommended channel
    channel_pref = master.get("canal_preferido_declarado", pd.Series(index=master.index, dtype="object")).astype("string").str.lower()
    master["canal_activacion_sugerido"] = np.where(
        ~master["contactable"],
        "No activar por CRM",
        np.where(channel_pref.fillna("").str.contains("tienda"), "Email + apoyo tienda", np.where(channel_pref.fillna("").str.contains("mixto"), "Email + push", "Email")),
    )

    master["recomendacion_prioritaria"] = master.apply(prioritized_recommendation, axis=1)
    master["prioridad_marketing_score"] = (
        master.get("score_churn", pd.Series(index=master.index, dtype="float")).fillna(0) * 0.4
        + master.get("score_rank_1", pd.Series(index=master.index, dtype="float")).fillna(0) * 0.2
        + master.get("targetability_score", pd.Series(index=master.index, dtype="float")).fillna(0) * 0.2
        + master.get("cross_sell_score", pd.Series(index=master.index, dtype="float")).clip(upper=5).fillna(0) / 5 * 0.2
    )
    master = master.sort_values(["prioridad_marketing_score", "gross_revenue_master"], ascending=[False, False]).reset_index(drop=True)
    return master



def prioritized_recommendation(row: pd.Series) -> str:
    if pd.notna(row.get("score_churn")) and row.get("score_churn", 0) >= 0.75:
        nba = row.get("next_best_action")
        if pd.notna(nba):
            return f"Retención prioritaria: {nba}"
        return "Retención prioritaria sobre clientes en riesgo."
    if pd.notna(row.get("targetability_score")) and row.get("targetability_score", 0) >= 0.55:
        action = row.get("accion_sugerida")
        store = row.get("nombre_tienda") or row.get("store_id_target")
        if pd.notna(action):
            if pd.notna(store):
                return f"Activación local: {action} ({store})"
            return f"Activación local: {action}"
        return "Activación local con stock y probabilidad de visita altos."
    if pd.notna(row.get("cross_sell_score")) and row.get("cross_sell_score", 0) >= 1.5:
        prod = row.get("recommended_product_name") or row.get("recommended_product")
        if pd.notna(prod):
            return f"Cross-sell recomendado: {prod}"
        return "Activación de cross-sell sobre afinidad de cesta."
    if pd.notna(row.get("categoria_rank_1")) and row.get("score_rank_1", 0) >= 0.45:
        cat = row.get("categoria_rank_1")
        return f"Campaña de afinidad de categoría: {cat}"
    if pd.notna(row.get("recomendacion_marketing")):
        return str(row.get("recomendacion_marketing"))
    return "Priorizar experiencia, valor y activación según historial disponible."



def compute_global_metrics(tables: Dict[str, pd.DataFrame], outputs: Dict[str, pd.DataFrame], master: pd.DataFrame) -> Dict[str, float]:
    fact = tables.get("fact", pd.DataFrame())
    campanas = tables.get("campanas", pd.DataFrame())
    feedback = tables.get("feedback", pd.DataFrame())
    tickets = tables.get("tickets", pd.DataFrame())
    metrics = {
        "clientes_crm": float(tables.get("crm", pd.DataFrame())["customer_id"].dropna().nunique()) if not tables.get("crm", pd.DataFrame()).empty else 0,
        "clientes_master": float(master["customer_id"].nunique()) if not master.empty else 0,
        "clientes_contactables": float(master.loc[master["contactable"], "customer_id"].nunique()) if not master.empty else 0,
        "revenue_total": float(fact.get("importe_abs_num", pd.Series(dtype="float")).sum()) if not fact.empty else 0,
        "margen_total": float(fact.get("margen_bruto_num", pd.Series(dtype="float")).sum()) if not fact.empty else 0,
        "transacciones": float(fact.get("doc_id_std", pd.Series(dtype="object")).dropna().nunique()) if not fact.empty else 0,
        "campanas": float(campanas.get("campaign_id", pd.Series(dtype="object")).dropna().nunique()) if not campanas.empty else 0,
        "tickets": float(tickets.get("service_ticket_id", pd.Series(dtype="object")).dropna().nunique()) if not tickets.empty else 0,
        "feedback": float(feedback.get("feedback_id", pd.Series(dtype="object")).dropna().nunique()) if not feedback.empty else 0,
    }
    return metrics



def revenue_monthly_by_channel(fact: pd.DataFrame) -> pd.DataFrame:
    if fact.empty:
        return pd.DataFrame(columns=["month", "canal_movimiento", "revenue"])
    tmp = fact.copy()
    tmp = tmp[tmp["fecha_movimiento_dt"].notna()]
    tmp["month"] = tmp["fecha_movimiento_dt"].dt.to_period("M").dt.to_timestamp()
    out = (
        tmp.groupby(["month", "canal_movimiento"], dropna=False)["importe_abs_num"]
        .sum()
        .reset_index(name="revenue")
    )
    return out



def campaign_summary(campanas: pd.DataFrame) -> pd.DataFrame:
    if campanas.empty:
        return campanas
    cols = [
        "campaign_id", "nombre_campana", "objetivo", "canal", "segmento_objetivo", "categoria_objetivo",
        "contactos", "conversiones_30d", "revenue_30d_total_eur", "margen_30d_total_eur", "cnt_open", "cnt_click",
        "cupones_emitidos", "cupones_canjeados"
    ]
    out = campanas[[c for c in cols if c in campanas.columns]].copy()
    if {"cnt_click", "contactos"}.issubset(out.columns):
        out["ctr_aprox"] = out["cnt_click"] / out["contactos"].replace({0: np.nan})
    if {"conversiones_30d", "contactos"}.issubset(out.columns):
        out["cvr_30d"] = out["conversiones_30d"] / out["contactos"].replace({0: np.nan})
    return out.sort_values("revenue_30d_total_eur", ascending=False)



def customer_transactions(fact: pd.DataFrame, customer_id: str) -> pd.DataFrame:
    if fact.empty:
        return fact
    tmp = fact[fact["customer_id"] == customer_id].copy()
    if not tmp.empty:
        tmp = tmp.sort_values("fecha_movimiento_dt", ascending=False)
    return tmp



def customer_campaigns(contactos: pd.DataFrame, campanas: pd.DataFrame, customer_id: str) -> pd.DataFrame:
    if contactos.empty:
        return contactos
    tmp = contactos[contactos["customer_id"] == customer_id].copy()
    if tmp.empty:
        return tmp
    if not campanas.empty and "campaign_id" in tmp.columns and "campaign_id" in campanas.columns:
        tmp = tmp.merge(campanas[[c for c in ["campaign_id", "nombre_campana", "objetivo", "canal", "fecha_inicio_dt"] if c in campanas.columns]], on="campaign_id", how="left")
    return tmp.sort_values("fecha_contacto_dt", ascending=False)



def customer_feedback(feedback: pd.DataFrame, tickets: pd.DataFrame, customer_id: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    fb = feedback[feedback["customer_id"] == customer_id].copy() if not feedback.empty else pd.DataFrame()
    tk = tickets[tickets["customer_id"] == customer_id].copy() if not tickets.empty else pd.DataFrame()
    if not fb.empty and "fecha_feedback_dt" in fb.columns:
        fb = fb.sort_values("fecha_feedback_dt", ascending=False)
    if not tk.empty and "fecha_apertura_dt" in tk.columns:
        tk = tk.sort_values("fecha_apertura_dt", ascending=False)
    return fb, tk



def customer_timeline_monthly(fact: pd.DataFrame, customer_id: str) -> pd.DataFrame:
    tmp = customer_transactions(fact, customer_id)
    if tmp.empty:
        return pd.DataFrame(columns=["month", "revenue", "margin"])
    tmp["month"] = tmp["fecha_movimiento_dt"].dt.to_period("M").dt.to_timestamp()
    out = tmp.groupby("month").agg(revenue=("importe_abs_num", "sum"), margin=("margen_bruto_num", "sum")).reset_index()
    return out



def build_audience_plan(master: pd.DataFrame) -> pd.DataFrame:
    if master.empty:
        return master
    audience = master.copy()
    audience["objetivo_sugerido"] = np.select(
        [
            audience.get("score_churn", pd.Series(index=audience.index, dtype="float")).fillna(0) >= 0.75,
            audience.get("cross_sell_score", pd.Series(index=audience.index, dtype="float")).fillna(0) >= 1.5,
            audience.get("targetability_score", pd.Series(index=audience.index, dtype="float")).fillna(0) >= 0.55,
            audience.get("score_rank_1", pd.Series(index=audience.index, dtype="float")).fillna(0) >= 0.45,
        ],
        ["Retención", "Cross-sell", "Store marketing", "Afinidad de categoría"],
        default="Nurturing / loyalty",
    )
    audience["offer_type_suggested"] = np.select(
        [
            audience["objetivo_sugerido"].eq("Retención"),
            audience["objetivo_sugerido"].eq("Cross-sell"),
            audience["objetivo_sugerido"].eq("Store marketing"),
            audience["objetivo_sugerido"].eq("Afinidad de categoría"),
        ],
        ["Experiencia + contenido", "Pack complementario", "Evento local + stock", "Inspiración guiada"],
        default="Contenido editorial",
    )
    return audience



def _select_model(algo: str):
    if algo == "Regresión logística":
        return LogisticRegression(max_iter=1500)
    return RandomForestClassifier(
        n_estimators=250,
        max_depth=8,
        min_samples_leaf=3,
        random_state=42,
        class_weight="balanced_subsample",
    )



def _feature_pipeline(X: pd.DataFrame, algo: str) -> Tuple[Pipeline, List[str], List[str]]:
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = [c for c in X.columns if c not in numeric_cols]
    numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
    if algo == "Regresión logística":
        numeric_steps.append(("scaler", StandardScaler()))
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline(steps=numeric_steps), numeric_cols),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_cols,
            ),
        ],
        remainder="drop",
    )
    model = _select_model(algo)
    pipe = Pipeline(steps=[("prep", preprocessor), ("model", model)])
    return pipe, numeric_cols, categorical_cols



def get_feature_names(pipe: Pipeline) -> List[str]:
    prep = pipe.named_steps["prep"]
    try:
        return prep.get_feature_names_out().tolist()
    except Exception:
        names: List[str] = []
        for name, trans, cols in prep.transformers_:
            if name == "remainder":
                continue
            if hasattr(trans, "get_feature_names_out"):
                try:
                    fn = trans.get_feature_names_out(cols)
                except Exception:
                    fn = trans.get_feature_names_out()
                names.extend(list(fn))
            else:
                names.extend(list(cols))
        return names



def model_importance(pipe: Pipeline, top_n: int = 12) -> pd.DataFrame:
    model = pipe.named_steps["model"]
    feature_names = get_feature_names(pipe)
    if hasattr(model, "coef_"):
        coef = np.abs(np.ravel(model.coef_))
        imp = pd.DataFrame({"feature": feature_names[: len(coef)], "importance": coef})
    elif hasattr(model, "feature_importances_"):
        imp = pd.DataFrame({"feature": feature_names[: len(model.feature_importances_)], "importance": model.feature_importances_})
    else:
        return pd.DataFrame(columns=["feature", "importance"])
    return imp.sort_values("importance", ascending=False).head(top_n)



def train_churn_model(df: pd.DataFrame, algo: str = "Random Forest", threshold: float = 0.5, test_size: float = 0.3):
    if df.empty:
        raise ValueError("No hay dataset de entrenamiento para churn.")
    use = df.copy()
    target = "is_churn_90d"
    drop_cols = ["snapshot_date", "customer_id", target]
    X = use.drop(columns=[c for c in drop_cols if c in use.columns])
    y = pd.to_numeric(use[target], errors="coerce").fillna(0).astype(int)
    pipe, _, _ = _feature_pipeline(X, algo)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
    pipe.fit(X_train, y_train)
    prob = pipe.predict_proba(X_test)[:, 1]
    pred = (prob >= threshold).astype(int)
    metrics = {
        "roc_auc": roc_auc_score(y_test, prob) if y_test.nunique() > 1 else np.nan,
        "precision": precision_score(y_test, pred, zero_division=0),
        "recall": recall_score(y_test, pred, zero_division=0),
        "f1": f1_score(y_test, pred, zero_division=0),
        "accuracy": accuracy_score(y_test, pred),
        "test_rows": int(len(y_test)),
        "positive_rate": float(y.mean()),
    }
    return pipe, metrics, model_importance(pipe)



def score_churn_model(pipe: Pipeline, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    score_df = df.copy()
    id_cols = [c for c in ["customer_id", "snapshot_date", "next_best_action", "expected_margin_uplift_eur"] if c in score_df.columns]
    drop_cols = [c for c in ["snapshot_date", "customer_id", "is_churn_90d", "score_churn", "next_best_action", "expected_margin_uplift_eur"] if c in score_df.columns]
    X = score_df.drop(columns=drop_cols)
    score_df["score_churn_model"] = pipe.predict_proba(X)[:, 1]
    score_df = score_df.sort_values("score_churn_model", ascending=False)
    return score_df[id_cols + ["score_churn_model"] + [c for c in ["score_churn", "next_best_action", "expected_margin_uplift_eur"] if c in score_df.columns]]



def train_propensity_model(df: pd.DataFrame, algo: str = "Random Forest", test_size: float = 0.3):
    if df.empty:
        raise ValueError("No hay dataset de entrenamiento para propensión de categoría.")
    use = df.copy()
    target = "target_category"
    use[target] = use[target].map(canonical_category)
    drop_cols = ["snapshot_date", "customer_id", target]
    X = use.drop(columns=[c for c in drop_cols if c in use.columns])
    if "last_category" in X.columns:
        X["last_category"] = X["last_category"].map(canonical_category)
    if "top_viewed_category" in X.columns:
        X["top_viewed_category"] = X["top_viewed_category"].map(canonical_category)
    y = use[target].fillna("Sin categoría")
    pipe, _, _ = _feature_pipeline(X, algo)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    metrics = {
        "accuracy": accuracy_score(y_test, pred),
        "macro_f1": f1_score(y_test, pred, average="macro", zero_division=0),
        "test_rows": int(len(y_test)),
        "classes": int(y.nunique()),
    }
    return pipe, metrics, model_importance(pipe)



def predict_propensity_proba(pipe: Pipeline, row: pd.DataFrame) -> pd.DataFrame:
    classes = pipe.named_steps["model"].classes_
    probs = pipe.predict_proba(row)[0]
    out = pd.DataFrame({"categoria": classes, "score": probs}).sort_values("score", ascending=False)
    return out.reset_index(drop=True)



def train_segmentation_model(df: pd.DataFrame, n_clusters: int = 4):
    if df.empty:
        raise ValueError("No hay dataset de segmentación.")
    use = df.copy()
    feature_cols = [
        "gross_revenue", "net_margin", "discount_rate", "coupon_redemption_rate",
        "recency_days", "omnichannel_flag", "margin_per_tx", "tx_per_year", "clv_proxy_12m"
    ]
    feature_cols = [c for c in feature_cols if c in use.columns]
    X = use[feature_cols].copy()
    X = X.replace([np.inf, -np.inf], np.nan)
    X_imputed = pd.DataFrame(SimpleImputer(strategy="median").fit_transform(X), columns=feature_cols)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_imputed)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    clusters = kmeans.fit_predict(X_scaled)
    silhouette = silhouette_score(X_scaled, clusters) if len(set(clusters)) > 1 else np.nan
    cluster_map = (
        pd.DataFrame({"cluster": clusters, "segmento_valor": use.get("segmento_valor")})
        .dropna()
        .groupby("cluster")["segmento_valor"]
        .agg(lambda s: s.value_counts().idxmax())
        .to_dict()
    )
    out = use[[c for c in ["customer_id", "segmento_valor", "clv_proxy_12m", "net_margin", "discount_rate", "recency_days"] if c in use.columns]].copy()
    out["cluster_pred"] = clusters
    out["segmento_modelo"] = out["cluster_pred"].map(cluster_map)
    return {"scaler": scaler, "kmeans": kmeans, "features": feature_cols, "cluster_map": cluster_map, "silhouette": silhouette, "labeled": out}



def simulate_segment(model: dict, values: Dict[str, float]) -> Tuple[int, str]:
    X = pd.DataFrame([values], columns=model["features"])
    X_imputed = X.fillna(pd.Series(X.median(numeric_only=True)))
    X_scaled = model["scaler"].transform(X_imputed)
    cluster = int(model["kmeans"].predict(X_scaled)[0])
    return cluster, model["cluster_map"].get(cluster, f"Cluster {cluster}")



def theme_samples(theme: str, feedback: pd.DataFrame, tickets: pd.DataFrame, limit: int = 5) -> List[str]:
    samples: List[str] = []
    if not feedback.empty:
        fb = feedback[feedback.get("tema_principal").astype(str).str.lower() == str(theme).lower()]
        if "texto_feedback" in fb.columns:
            samples.extend(fb["texto_feedback"].dropna().astype(str).head(limit).tolist())
    if len(samples) < limit and not tickets.empty:
        mask = pd.Series(False, index=tickets.index)
        for col in ["motivo_contacto", "tipo_caso", "subtipo_caso"]:
            if col in tickets.columns:
                mask = mask | tickets[col].astype(str).str.lower().str.contains(str(theme).lower(), na=False)
        tk = tickets[mask]
        if "texto_cliente" in tk.columns:
            samples.extend(tk["texto_cliente"].dropna().astype(str).head(limit - len(samples)).tolist())
    return samples[:limit]



def voc_insight(theme: str, issue_matrix: pd.DataFrame, feedback: pd.DataFrame, tickets: pd.DataFrame) -> Dict[str, object]:
    if issue_matrix.empty:
        return {"theme": theme, "mentions": 0, "negative_share": np.nan, "recommendation": "Sin datos suficientes."}
    tmp = issue_matrix[issue_matrix["tema_principal"].astype(str).str.lower() == str(theme).lower()].copy()
    mentions = int(tmp.get("registros", pd.Series(dtype="int")).sum()) if not tmp.empty else 0
    neg = int(tmp.loc[tmp["sentimiento"].astype(str).str.lower() == "negativo", "registros"].sum()) if not tmp.empty else 0
    negative_share = neg / mentions if mentions else np.nan
    recommendation = VOC_THEME_RECOMMENDATIONS.get(str(theme).lower(), "Analizar causas raíz y traducir el insight a una hipótesis de contenido, UX o servicio.")
    samples = theme_samples(theme, feedback, tickets, limit=5)
    if negative_share is not np.nan and not pd.isna(negative_share):
        if negative_share >= 0.4:
            implication = "El tema presenta una fricción alta y puede estar afectando conversión, repetición o satisfacción."
        elif negative_share >= 0.2:
            implication = "Existe una fricción relevante, aunque convive con señales positivas; conviene priorizar mejoras selectivas."
        else:
            implication = "El tema tiene más peso informativo que problemático; puede servir para afinar mensajes y expectativas."
    else:
        implication = "No hay base suficiente para inferir gravedad relativa."
    return {
        "theme": theme,
        "mentions": mentions,
        "negative_share": negative_share,
        "recommendation": recommendation,
        "implication": implication,
        "samples": samples,
    }



def draft_copy(
    microsegmento: str,
    canal: str,
    categoria_objetivo: str,
    objetivo: str,
    tono: str,
    beneficio_principal: str,
    cta: str,
    guardrails: Iterable[str],
    tienda: Optional[str] = None,
    condicion_promocional: Optional[str] = None,
    prueba_social: Optional[str] = None,
) -> Dict[str, str]:
    tono_map = {
        "práctico": "claro y útil",
        "practico": "claro y útil",
        "inspiracional": "inspirador y visual",
        "urgencia_suave": "ágil pero sin presión excesiva",
        "exclusivo": "premium y selectivo",
        "cercano": "cercano y resolutivo",
    }
    tono_desc = tono_map.get(str(tono).lower(), "cercano y premium")
    cat_text = categoria_objetivo if categoria_objetivo and categoria_objetivo != "multicategoría" else "una selección curada para tu hogar"

    if str(objetivo).lower() == "reactivacion":
        subject = f"Vuelve a descubrir {cat_text.lower()} con una propuesta más precisa"
    elif str(objetivo).lower() == "cross_sell":
        subject = f"Completa tu espacio con {cat_text.lower()} que encaja contigo"
    elif str(objetivo).lower() == "promocion":
        subject = f"Una oportunidad más afinada para renovar tu hogar"
    else:
        subject = f"Ideas de {cat_text.lower()} que encajan mejor con tu momento"

    intro = (
        f"Hemos preparado una propuesta de {cat_text.lower()} con foco en {beneficio_principal}. "
        f"El tono debe ser {tono_desc} y mantener un único CTA: {cta}."
    )
    local_line = f" Puedes encontrar inspiración adicional en {tienda}." if tienda else ""
    social_line = f" {prueba_social}." if prueba_social else ""
    promo_line = f" Si aplicas promoción, expresa esta condición con claridad: {condicion_promocional}." if condicion_promocional else ""
    body = (
        f"{intro}{local_line}{social_line} "
        f"Prioriza utilidad real, diseño y contexto de uso frente al descuento puro."
        f"{promo_line} CTA sugerido: {cta}."
    )
    guardrails_applied = " | ".join([g for g in guardrails if g][:6])
    rationale = (
        f"Pieza pensada para el microsegmento {microsegmento}, canal {canal} y objetivo {objetivo}. "
        f"La personalización se apoya en afinidad de categoría y comportamiento reciente, sin usar atributos sensibles."
    )
    risk = "Controlar presión promocional, claridad de stock y evitar claims absolutos de precio o disponibilidad."
    return {
        "subject": subject,
        "body": body,
        "guardrails_applied": guardrails_applied,
        "rationale": rationale,
        "risk": risk,
    }



def top_creatives(creatividades: pd.DataFrame, microsegmento: Optional[str] = None, categoria: Optional[str] = None, objetivo: Optional[str] = None, limit: int = 10) -> pd.DataFrame:
    if creatividades.empty:
        return creatividades
    tmp = creatividades.copy()
    if microsegmento:
        tmp = tmp[tmp["microsegmento"] == microsegmento]
    if categoria and "categoria_objetivo" in tmp.columns:
        tmp = tmp[tmp["categoria_objetivo"].astype(str).str.lower() == str(categoria).lower()]
    if objetivo and "campaign_id" in tmp.columns:
        # objective lives in copy briefs, not in creatividades. If absent, ignore.
        pass
    score = (
        tmp.get("revenue_por_1000_envios_eur", pd.Series(index=tmp.index, dtype="float")).fillna(0) * 0.5
        + tmp.get("ctr", pd.Series(index=tmp.index, dtype="float")).fillna(0) * 1000 * 0.3
        + tmp.get("cvr", pd.Series(index=tmp.index, dtype="float")).fillna(0) * 1000 * 0.2
    )
    tmp = tmp.assign(_score=score)
    return tmp.sort_values("_score", ascending=False).head(limit)



def format_eur(x: object) -> str:
    try:
        if pd.isna(x):
            return "—"
        return f"€{float(x):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"



def format_pct(x: object, decimals: int = 1) -> str:
    try:
        if pd.isna(x):
            return "—"
        return f"{float(x) * 100:.{decimals}f}%"
    except Exception:
        return "—"



def safe_div(a: float, b: float) -> float:
    if b in (0, None) or pd.isna(b):
        return np.nan
    return a / b
