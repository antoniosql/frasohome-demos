from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


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


def find_project_root(start: Path | None = None) -> Path:
    current = Path(start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "datos").exists() and (candidate / "escenarios").exists():
            return candidate
    raise FileNotFoundError("No se ha encontrado la raiz del proyecto FraSoHome.")


def data_paths(project_root: Path) -> dict[str, Path]:
    retail = project_root / "datos" / "retail_omnicanal" / "raw_csv"
    marketing = project_root / "datos" / "marketing_precision" / "raw_csv"
    return {
        "fact": retail / "fact_transacciones.csv",
        "crm": retail / "crm.csv",
        "productos": retail / "productos.csv",
        "stock": retail / "stock_diario.csv",
        "contactos": marketing / "contactos_campana.csv",
        "web": marketing / "eventos_web_app.csv",
        "feedback": marketing / "feedback_clientes.csv",
        "tickets": marketing / "tickets_atencion_cliente.csv",
        "costes": marketing / "costes_operativos_transaccion.csv",
    }


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, na_values=["", "NA", "N/A", "NULL", "null", "None"])


def load_operational_tables(project_root: Path | None = None) -> dict[str, pd.DataFrame]:
    root = find_project_root(project_root)
    return {name: load_csv(path) for name, path in data_paths(root).items() if path.exists()}


def standardize_id(series: pd.Series) -> pd.Series:
    out = series.astype(str).str.strip().str.upper().str.replace(r"\s+", "", regex=True)
    out = out.replace({"": np.nan, "NAN": np.nan, "NONE": np.nan, "NULL": np.nan, "GUEST": np.nan})
    return out


def parse_numeric_mixed(series: pd.Series) -> pd.Series:
    raw = series.astype(str).str.strip()
    raw = raw.replace({"": np.nan, "nan": np.nan, "None": np.nan, "NULL": np.nan})
    raw = raw.str.replace("€", "", regex=False).str.replace("EUR", "", regex=False).str.replace("eur", "", regex=False)
    raw = raw.str.replace(r"[^\d,.\-]", "", regex=True)

    def convert(value: object) -> float:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return np.nan
        text = str(value)
        if not text:
            return np.nan
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".") if text.rfind(",") > text.rfind(".") else text.replace(",", "")
        elif "," in text:
            text = text.replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return np.nan

    return raw.apply(convert)


def _parse_spanish_text_date(value: object):
    text = str(value).strip().lower()
    match = re.search(r"(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+de\s+(\d{4})(?:\s+(\d{1,2}):(\d{2}))?", text)
    if not match:
        return None
    month_name = (
        match.group(2)
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )
    month = MONTHS_ES.get(month_name)
    if month is None:
        return None
    try:
        return pd.Timestamp(
            int(match.group(3)),
            month,
            int(match.group(1)),
            int(match.group(4) or 0),
            int(match.group(5) or 0),
        )
    except ValueError:
        return None


def parse_datetime_es(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)
    mask = parsed.isna() & series.notna()
    if mask.any():
        parsed.loc[mask] = pd.to_datetime([_parse_spanish_text_date(v) for v in series.loc[mask]], errors="coerce")
    return parsed


def safe_divide(num: pd.Series, den: pd.Series) -> pd.Series:
    den = den.replace(0, np.nan)
    return num / den


def prepare_fact(fact_raw: pd.DataFrame) -> pd.DataFrame:
    df = fact_raw.copy()
    df["customer_id_std"] = standardize_id(df.get("customer_id_std", df.get("customer_id_raw", pd.Series(index=df.index))))
    df["product_id_std"] = standardize_id(df.get("product_id_std", df.get("product_id_raw", pd.Series(index=df.index))))
    df["store_id_std"] = standardize_id(df.get("store_id_std", df.get("store_id_raw", pd.Series(index=df.index))))
    df["doc_id_std"] = standardize_id(df.get("doc_id_std", df.get("doc_id_raw", pd.Series(index=df.index))))
    df["line_id_std"] = standardize_id(df.get("line_id_std", df.get("line_id_raw", pd.Series(index=df.index))))
    df["event_dt"] = parse_datetime_es(df.get("fecha_movimiento", df.get("fecha_movimiento_raw", pd.Series(index=df.index))))
    df["amount"] = parse_numeric_mixed(df.get("importe_signed_num", df.get("importe_linea_raw", pd.Series(index=df.index))))
    df["margin"] = parse_numeric_mixed(df.get("margen_bruto_num", pd.Series(index=df.index)))
    df["quantity"] = parse_numeric_mixed(df.get("cantidad_signed", df.get("cantidad_raw", pd.Series(index=df.index))))
    df["discount_pct"] = parse_numeric_mixed(df.get("descuento_pct_num", df.get("descuento_pct_raw", pd.Series(index=df.index)))).fillna(0)
    df["unit_price"] = parse_numeric_mixed(df.get("precio_unitario_num", df.get("precio_unitario_raw", pd.Series(index=df.index))))
    df["cost_unit"] = parse_numeric_mixed(df.get("coste_unitario_num", pd.Series(index=df.index)))
    df["channel"] = df.get("canal_origen", pd.Series(index=df.index)).astype(str).str.strip().str.upper()
    df["movement_type"] = df.get("tipo_movimiento", pd.Series(index=df.index)).astype(str).str.strip().str.upper()
    df["is_return"] = df["movement_type"].str.contains("DEV", na=False)
    df["is_sale"] = ~df["is_return"]
    for col in ["categoria", "subcategoria", "estado_producto", "metodo_pago", "estado_pedido", "origen"]:
        if col in df.columns:
            df[col] = df[col].astype(str).replace({"nan": np.nan, "None": np.nan}).str.strip()
    return df


def clean_fact_for_ml(
    fact: pd.DataFrame,
    min_date: str = "2024-01-01",
    max_date: str = "2025-12-31 23:59:59",
) -> pd.DataFrame:
    df = fact.copy()
    df["flag_ml_valid_date"] = df["event_dt"].between(pd.Timestamp(min_date), pd.Timestamp(max_date))
    df["flag_ml_valid_customer"] = df["customer_id_std"].notna()
    df["flag_ml_valid_product"] = df["product_id_std"].notna()
    df = df[df["flag_ml_valid_date"] & df["flag_ml_valid_customer"] & df["flag_ml_valid_product"]].copy()
    df = df[df["amount"].notna() & df["quantity"].notna()].copy()
    return df


def prepare_crm(crm_raw: pd.DataFrame) -> pd.DataFrame:
    df = crm_raw.copy()
    df["customer_id_std"] = standardize_id(df["customer_id"])
    df["points"] = parse_numeric_mixed(df.get("puntos_acumulados", pd.Series(index=df.index)))
    df["birth_dt"] = parse_datetime_es(df.get("fecha_nacimiento", pd.Series(index=df.index)))
    df["program_start_dt"] = parse_datetime_es(df.get("fecha_alta_programa", pd.Series(index=df.index)))
    df["last_update_dt"] = parse_datetime_es(df.get("ultima_actualizacion", pd.Series(index=df.index)))
    df = df.sort_values("last_update_dt").drop_duplicates("customer_id_std", keep="last")
    keep = [
        "customer_id_std",
        "tier_fidelizacion",
        "points",
        "estado_cliente",
        "consentimiento_marketing",
        "origen_alta",
        "canal_preferido_declarado",
        "ciudad",
        "provincia",
        "birth_dt",
        "program_start_dt",
    ]
    return df[[c for c in keep if c in df.columns]].copy()


def _category_revenue_features(sales: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    if "categoria" not in sales.columns or sales.empty:
        return pd.DataFrame(columns=["customer_id_std"])
    sales = sales.copy()
    sales["category_slug"] = sales["categoria"].map(_slug)
    top_categories = sales.groupby("category_slug")["amount"].sum().abs().sort_values(ascending=False).head(top_n).index
    pivot = (
        sales[sales["category_slug"].isin(top_categories)]
        .pivot_table(index="customer_id_std", columns="category_slug", values="amount", aggfunc="sum", fill_value=0)
        .reset_index()
    )
    pivot.columns = ["customer_id_std"] + [f"revenue_cat_{c}" for c in pivot.columns[1:]]
    return pivot


def _slug(value: object) -> str:
    text = str(value).lower()
    text = (
        text.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "unknown"


def customer_history_features(
    fact: pd.DataFrame,
    crm: pd.DataFrame | None,
    web: pd.DataFrame | None,
    feedback: pd.DataFrame | None,
    tickets: pd.DataFrame | None,
    as_of_date: pd.Timestamp,
    lookback_days: int = 180,
) -> pd.DataFrame:
    as_of = pd.Timestamp(as_of_date)
    start = as_of - pd.Timedelta(days=lookback_days)
    window = fact[(fact["event_dt"] < as_of) & (fact["event_dt"] >= start) & fact["customer_id_std"].notna()].copy()
    sales = window[window["is_sale"]].copy()
    returns = window[window["is_return"]].copy()

    if sales.empty:
        return pd.DataFrame(columns=["customer_id_std"])

    base = sales.groupby("customer_id_std").agg(
        first_purchase_dt=("event_dt", "min"),
        last_purchase_dt=("event_dt", "max"),
        frequency_docs=("doc_id_std", "nunique"),
        sales_lines=("line_id_std", "count"),
        units_sold=("quantity", "sum"),
        monetary_gross=("amount", "sum"),
        margin_gross=("margin", "sum"),
        avg_discount_pct=("discount_pct", "mean"),
        pct_discounted_lines=("discount_pct", lambda s: (s.fillna(0) > 0).mean()),
        avg_unit_price=("unit_price", "mean"),
        n_categories=("categoria", "nunique"),
        n_products=("product_id_std", "nunique"),
    ).reset_index()
    base["recency_days"] = (as_of - base["last_purchase_dt"]).dt.days
    base["customer_tenure_window_days"] = (base["last_purchase_dt"] - base["first_purchase_dt"]).dt.days
    base["avg_order_value"] = safe_divide(base["monetary_gross"], base["frequency_docs"]).fillna(0)
    base["gross_margin_rate"] = safe_divide(base["margin_gross"], base["monetary_gross"]).fillna(0)

    ret = returns.groupby("customer_id_std").agg(
        return_lines=("line_id_std", "count"),
        amount_returned=("amount", lambda s: s.abs().sum()),
        units_returned=("quantity", lambda s: s.abs().sum()),
    ).reset_index()
    base = base.merge(ret, on="customer_id_std", how="left")
    base[["return_lines", "amount_returned", "units_returned"]] = base[["return_lines", "amount_returned", "units_returned"]].fillna(0)
    base["return_amount_rate"] = safe_divide(base["amount_returned"], base["monetary_gross"]).fillna(0)
    base["return_unit_rate"] = safe_divide(base["units_returned"], base["units_sold"]).fillna(0)

    channel = sales.pivot_table(index="customer_id_std", columns="channel", values="amount", aggfunc="sum", fill_value=0).reset_index()
    channel.columns = ["customer_id_std"] + [f"revenue_channel_{_slug(c)}" for c in channel.columns[1:]]
    base = base.merge(channel, on="customer_id_std", how="left")
    online_col = "revenue_channel_online"
    pos_col = "revenue_channel_pos"
    base["online_revenue_share"] = safe_divide(base.get(online_col, 0), base[[c for c in [online_col, pos_col] if c in base.columns]].sum(axis=1)).fillna(0)

    base = base.merge(_category_revenue_features(sales), on="customer_id_std", how="left")

    last_purchase = sales.sort_values("event_dt").groupby("customer_id_std").tail(1)
    base = base.merge(
        last_purchase[["customer_id_std", "channel", "categoria", "metodo_pago", "store_id_std"]].rename(
            columns={
                "channel": "last_channel",
                "categoria": "last_category",
                "metodo_pago": "last_payment_method",
                "store_id_std": "last_store_id",
            }
        ),
        on="customer_id_std",
        how="left",
    )

    if crm is not None and not crm.empty:
        crm_enriched = crm.copy()
        crm_enriched["age_years"] = ((as_of - crm_enriched["birth_dt"]).dt.days / 365.25).clip(0, 100)
        crm_enriched["program_tenure_days"] = (as_of - crm_enriched["program_start_dt"]).dt.days.clip(lower=0)
        base = base.merge(crm_enriched.drop(columns=["birth_dt", "program_start_dt"], errors="ignore"), on="customer_id_std", how="left")

    base = base.merge(web_features(web, as_of, lookback_days), on="customer_id_std", how="left") if web is not None else base
    base = base.merge(feedback_features(feedback, as_of, lookback_days), on="customer_id_std", how="left") if feedback is not None else base
    base = base.merge(ticket_features(tickets, as_of, lookback_days), on="customer_id_std", how="left") if tickets is not None else base

    for col in base.select_dtypes(include=[np.number]).columns:
        base[col] = base[col].fillna(0)
    return base


def web_features(web_raw: pd.DataFrame, as_of: pd.Timestamp, lookback_days: int) -> pd.DataFrame:
    df = web_raw.copy()
    df["customer_id_std"] = standardize_id(df["customer_id"])
    df["event_dt"] = parse_datetime_es(df["fecha_hora_evento"])
    df["event_value"] = parse_numeric_mixed(df.get("valor_evento_eur", pd.Series(index=df.index))).fillna(0)
    df = df[(df["event_dt"] < as_of) & (df["event_dt"] >= as_of - pd.Timedelta(days=lookback_days)) & df["customer_id_std"].notna()]
    if df.empty:
        return pd.DataFrame(columns=["customer_id_std"])
    out = df.groupby("customer_id_std").agg(
        web_events=("event_id", "count"),
        web_sessions=("session_id", "nunique"),
        web_active_days=("event_dt", lambda s: s.dt.date.nunique()),
        web_value_sum=("event_value", "sum"),
        web_product_views=("tipo_evento", lambda s: s.astype(str).str.contains("product|view", case=False, regex=True).sum()),
        web_searches=("tipo_evento", lambda s: s.astype(str).str.contains("search", case=False, regex=True).sum()),
        web_add_to_cart=("tipo_evento", lambda s: s.astype(str).str.contains("cart|cesta", case=False, regex=True).sum()),
    ).reset_index()
    return out


def feedback_features(feedback_raw: pd.DataFrame, as_of: pd.Timestamp, lookback_days: int) -> pd.DataFrame:
    df = feedback_raw.copy()
    df["customer_id_std"] = standardize_id(df["customer_id"])
    df["feedback_dt"] = parse_datetime_es(df["fecha_feedback"])
    df["rating"] = parse_numeric_mixed(df.get("rating_1_5", pd.Series(index=df.index)))
    df["nps"] = parse_numeric_mixed(df.get("nps_0_10", pd.Series(index=df.index)))
    df["is_negative_feedback"] = df.get("sentimiento", "").astype(str).str.contains("neg", case=False, na=False)
    df = df[(df["feedback_dt"] < as_of) & (df["feedback_dt"] >= as_of - pd.Timedelta(days=lookback_days)) & df["customer_id_std"].notna()]
    if df.empty:
        return pd.DataFrame(columns=["customer_id_std"])
    return df.groupby("customer_id_std").agg(
        feedback_count=("feedback_id", "count"),
        avg_rating=("rating", "mean"),
        avg_nps=("nps", "mean"),
        pct_negative_feedback=("is_negative_feedback", "mean"),
    ).reset_index()


def ticket_features(tickets_raw: pd.DataFrame, as_of: pd.Timestamp, lookback_days: int) -> pd.DataFrame:
    df = tickets_raw.copy()
    df["customer_id_std"] = standardize_id(df["customer_id"])
    df["ticket_dt"] = parse_datetime_es(df["fecha_apertura"])
    df["sla_hours"] = parse_numeric_mixed(df.get("sla_horas", pd.Series(index=df.index)))
    df["csat"] = parse_numeric_mixed(df.get("csat_1_5", pd.Series(index=df.index)))
    df["compensation"] = parse_numeric_mixed(df.get("importe_compensacion_eur", pd.Series(index=df.index))).fillna(0)
    df["is_high_priority"] = df.get("prioridad", "").astype(str).str.contains("alta", case=False, na=False)
    df = df[(df["ticket_dt"] < as_of) & (df["ticket_dt"] >= as_of - pd.Timedelta(days=lookback_days)) & df["customer_id_std"].notna()]
    if df.empty:
        return pd.DataFrame(columns=["customer_id_std"])
    return df.groupby("customer_id_std").agg(
        service_tickets=("service_ticket_id", "count"),
        avg_sla_hours=("sla_hours", "mean"),
        avg_csat=("csat", "mean"),
        pct_high_priority_tickets=("is_high_priority", "mean"),
        compensation_sum=("compensation", "sum"),
    ).reset_index()


def build_churn_dataset(
    fact: pd.DataFrame,
    crm: pd.DataFrame | None,
    web: pd.DataFrame | None,
    feedback: pd.DataFrame | None,
    tickets: pd.DataFrame | None,
    lookback_days: int = 180,
    horizon_days: int = 90,
    max_snapshots: int = 8,
) -> pd.DataFrame:
    min_dt = fact["event_dt"].min()
    max_dt = fact["event_dt"].max()
    start = (min_dt + pd.Timedelta(days=lookback_days)).normalize() + pd.offsets.MonthBegin(1)
    end = (max_dt - pd.Timedelta(days=horizon_days)).normalize()
    snapshots = list(pd.date_range(start=start, end=end, freq="MS"))
    if len(snapshots) > max_snapshots:
        snapshots = snapshots[-max_snapshots:]
    rows = []
    for snap in snapshots:
        features = customer_history_features(fact, crm, web, feedback, tickets, snap, lookback_days)
        if features.empty:
            continue
        future = fact[
            fact["is_sale"]
            & fact["customer_id_std"].notna()
            & (fact["event_dt"] >= snap)
            & (fact["event_dt"] < snap + pd.Timedelta(days=horizon_days))
        ][["customer_id_std"]].drop_duplicates()
        future["has_future_purchase"] = 1
        features = features.merge(future, on="customer_id_std", how="left")
        features["has_future_purchase"] = features["has_future_purchase"].fillna(0).astype(int)
        features["label_inactive_90d"] = (1 - features["has_future_purchase"]).astype(int)
        features["snapshot_date"] = snap
        rows.append(features.drop(columns=["has_future_purchase"]))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_campaign_dataset(
    contactos_raw: pd.DataFrame,
    fact: pd.DataFrame,
    crm: pd.DataFrame | None,
    web: pd.DataFrame | None,
    feedback: pd.DataFrame | None,
    tickets: pd.DataFrame | None,
    lookback_days: int = 180,
) -> pd.DataFrame:
    contacts = contactos_raw.copy()
    contacts["customer_id_std"] = standardize_id(contacts["customer_id"])
    contacts["contact_dt"] = parse_datetime_es(contacts["fecha_contacto"])
    contacts["conversion_30d_flag"] = parse_numeric_mixed(contacts["conversion_30d_flag"]).fillna(0).astype(int)
    contacts["revenue_30d_eur"] = parse_numeric_mixed(contacts.get("revenue_30d_eur", pd.Series(index=contacts.index))).fillna(0)
    contacts["margen_30d_eur"] = parse_numeric_mixed(contacts.get("margen_30d_eur", pd.Series(index=contacts.index))).fillna(0)
    contacts["coste_contacto_eur"] = parse_numeric_mixed(contacts.get("coste_contacto_eur", pd.Series(index=contacts.index))).fillna(0)

    frames = []
    for contact_date, part in contacts.dropna(subset=["contact_dt"]).groupby("contact_dt"):
        features = customer_history_features(fact, crm, web, feedback, tickets, contact_date, lookback_days)
        if features.empty:
            continue
        frames.append(part.merge(features, on="customer_id_std", how="left"))
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if out.empty:
        return out
    for col in out.select_dtypes(include=[np.number]).columns:
        out[col] = out[col].fillna(0)
    return out


def build_return_risk_dataset(fact: pd.DataFrame) -> pd.DataFrame:
    sales = fact[fact["is_sale"] & fact["line_id_std"].notna()].copy()
    returns = fact[fact["is_return"]].copy()
    returned_line_ids = set(returns["line_id_std"].dropna()) | set(standardize_id(returns.get("order_line_id_original", pd.Series(dtype=str))).dropna())
    returned_line_ids |= set(standardize_id(returns.get("ticket_line_id_original", pd.Series(dtype=str))).dropna())

    sales["label_returned"] = sales["line_id_std"].isin(returned_line_ids).astype(int)
    keep = [
        "customer_id_std",
        "product_id_std",
        "store_id_std",
        "doc_id_std",
        "line_id_std",
        "event_dt",
        "channel",
        "categoria",
        "subcategoria",
        "metodo_pago",
        "estado_pedido",
        "origen",
        "estado_producto",
        "quantity",
        "amount",
        "margin",
        "discount_pct",
        "unit_price",
        "cost_unit",
        "label_returned",
    ]
    out = sales[[c for c in keep if c in sales.columns]].copy()
    out["gross_margin_rate_line"] = safe_divide(out["margin"], out["amount"]).fillna(0)
    return out


def infer_feature_columns(df: pd.DataFrame, target: str, excluded: Iterable[str] | None = None) -> tuple[list[str], list[str], list[str]]:
    excluded_set = set(excluded or []) | {target}
    features = [c for c in df.columns if c not in excluded_set]
    numeric_cols = [c for c in features if pd.api.types.is_numeric_dtype(df[c])]
    categorical_cols = [c for c in features if c not in numeric_cols and not pd.api.types.is_datetime64_any_dtype(df[c])]
    return features, numeric_cols, categorical_cols


def make_one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False, min_frequency=2)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def make_preprocessor(numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    numeric_pipe = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical_pipe = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", make_one_hot_encoder())])
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_cols),
            ("cat", categorical_pipe, categorical_cols),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def make_model_pipeline(
    numeric_cols: list[str],
    categorical_cols: list[str],
    model_kind: str = "rf",
    random_state: int = 42,
) -> Pipeline:
    if model_kind == "logistic":
        model = LogisticRegression(max_iter=3000, class_weight="balanced", solver="lbfgs")
    elif model_kind == "rf":
        model = RandomForestClassifier(
            n_estimators=250,
            min_samples_leaf=4,
            max_depth=8,
            class_weight="balanced_subsample",
            random_state=random_state,
            n_jobs=-1,
        )
    else:
        raise ValueError(f"model_kind no soportado: {model_kind}")
    return Pipeline([("preprocess", make_preprocessor(numeric_cols, categorical_cols)), ("model", model)])


def train_binary_model(
    df: pd.DataFrame,
    target: str,
    excluded: Iterable[str],
    model_kind: str = "rf",
    test_size: float = 0.25,
    random_state: int = 42,
) -> dict[str, object]:
    features, numeric_cols, categorical_cols = infer_feature_columns(df, target, excluded)
    X = df[features].copy()
    y = df[target].astype(int)
    if y.nunique() < 2:
        raise ValueError(f"El target {target} solo tiene una clase. Revisa ventanas temporales o filtros.")
    stratify = y if y.nunique() == 2 and y.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=stratify
    )
    pipeline = make_model_pipeline(numeric_cols, categorical_cols, model_kind=model_kind, random_state=random_state)
    pipeline.fit(X_train, y_train)
    proba = pipeline.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "rows": int(len(df)),
        "target_rate": float(y.mean()),
        "test_roc_auc": float(roc_auc_score(y_test, proba)) if y_test.nunique() == 2 else np.nan,
        "test_average_precision": float(average_precision_score(y_test, proba)) if y_test.nunique() == 2 else np.nan,
        "test_f1": float(f1_score(y_test, pred, zero_division=0)),
        "test_accuracy": float(accuracy_score(y_test, pred)),
    }
    return {
        "pipeline": pipeline,
        "features": features,
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "metrics": metrics,
    }


def transformed_feature_names(pipeline: Pipeline) -> list[str]:
    preprocessor = pipeline.named_steps["preprocess"]
    return list(preprocessor.get_feature_names_out())


def model_importance(pipeline: Pipeline, top_n: int = 25) -> pd.DataFrame:
    model = pipeline.named_steps["model"]
    names = transformed_feature_names(pipeline)
    if hasattr(model, "feature_importances_"):
        values = model.feature_importances_
        score_name = "importance"
    elif hasattr(model, "coef_"):
        values = model.coef_[0]
        score_name = "coefficient"
    else:
        raise ValueError("El modelo no expone importancias directas.")
    out = pd.DataFrame({"feature": names, score_name: values})
    out["abs_value"] = out[score_name].abs()
    return out.sort_values("abs_value", ascending=False).head(top_n).reset_index(drop=True)


def score_deciles(df: pd.DataFrame, probabilities: np.ndarray, target: str) -> pd.DataFrame:
    scored = df[[target]].copy()
    scored["score"] = probabilities
    scored["decile"] = pd.qcut(scored["score"].rank(method="first"), 10, labels=False) + 1
    return (
        scored.groupby("decile")
        .agg(n=(target, "size"), avg_score=("score", "mean"), target_rate=(target, "mean"))
        .reset_index()
        .sort_values("decile", ascending=False)
    )


def save_artifact(obj: object, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(obj, path)
    return path


def load_artifact(path: Path) -> object:
    return joblib.load(path)
