# app_frasohome_streamlit.py
# ------------------------------------------------------------
# Streamlit app (formativa) para explorar el caso FraSoHome
# Omnicanal (E-commerce + POS) con problemas intencionales de calidad de datos.
#
# Para ejecutar:
#   pip install -r requirements_streamlit.txt
#   streamlit run app_frasohome_streamlit.py
#
# Estructura recomendada:
#   .
#   ├─ app_frasohome_streamlit.py
#   ├─ requirements_streamlit.txt
#   ├─ ../../../datos/retail_omnicanal/raw_csv/
#   │  ├─ crm.csv
#   │  ├─ productos.csv
#   │  ├─ tiendas.csv
#   │  ├─ pedidos.csv
#   │  ├─ lineas_pedido.csv
#   │  ├─ devoluciones_online.csv
#   │  ├─ ventas_pos.csv
#   │  ├─ devoluciones_tienda.csv
#   │  ├─ pagos_tienda.csv
#   │  ├─ stock_diario.csv
#   │  └─ fact_transacciones.csv   (recomendado)
#   └─ output_integrated/ (opcional)
#      └─ fact_transacciones_integrada.csv
# ------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from itertools import combinations
import math
import re
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt


# -----------------------------
# Configuración UI
# -----------------------------
st.set_page_config(
    page_title="FraSoHome | Omnicanal Retail (Demo)",
    page_icon="🛋️",
    layout="wide",
)

st.title("🛋️ FraSoHome — Exploración Omnicanal (E-commerce + POS)")
st.caption(
    "App formativa para visualizar KPIs, calidad de datos, clientes (RFM/churn), productos/stock y cesta. "
    "Los datos contienen errores intencionales para prácticas de *data cleaning*."
)


# -----------------------------
# Utilidades de carga y parseo
# -----------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DEFAULT_DIR = REPO_ROOT / "datos" / "retail_omnicanal" / "raw_csv"
INTEGRATED_CANDIDATES = [
    Path("output_integrated/fact_transacciones_integrada.csv"),
    Path("fact_transacciones_integrada.csv"),
    Path("data/fact_transacciones_integrada.csv"),
    Path("data/fact_transacciones.csv"),
    Path("fact_transacciones.csv"),
]

RAW_FILES = {
    "CRM (clientes)": "crm.csv",
    "Productos (maestro)": "productos.csv",
    "Tiendas (maestro)": "tiendas.csv",
    "Pedidos online": "pedidos.csv",
    "Líneas pedido online": "lineas_pedido.csv",
    "Devoluciones online": "devoluciones_online.csv",
    "Ventas POS": "ventas_pos.csv",
    "Devoluciones tienda": "devoluciones_tienda.csv",
    "Pagos tienda": "pagos_tienda.csv",
    "Stock diario": "stock_diario.csv",
    "Fact transacciones": "fact_transacciones.csv",
}


def _safe_read_csv(path: Path, nrows: Optional[int] = None) -> pd.DataFrame:
    """Lee CSV de forma 'segura' para entornos formativos con problemas de calidad.
    - dtype=str para preservar formatos y errores.
    - keep_default_na=True para interpretar NaN típicos, pero respetando strings raros.
    """
    return pd.read_csv(
        path,
        dtype=str,
        nrows=nrows,
        encoding="utf-8",
        on_bad_lines="skip",
        low_memory=False,
    )


def standardize_id(s: pd.Series) -> pd.Series:
    """Normaliza IDs: trim + upper + colapsar espacios internos."""
    if s is None:
        return s
    out = s.astype("string")
    out = out.str.strip()
    out = out.str.replace(r"\s+", " ", regex=True)
    out = out.str.upper()
    return out


MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

def parse_datetime_es(series: pd.Series) -> pd.Series:
    """Parse robusto para fechas heterogéneas (ISO, DD/MM/YY, DD/MM/YYYY, texto en español).
    Devuelve datetime64[ns] con NaT donde no parsea.
    """
    s = series.astype("string").str.strip()
    # 1) Intento directo con pandas (ISO + muchas variantes)
    dt = pd.to_datetime(s, errors="coerce", dayfirst=True, utc=False)

    # 2) Texto tipo: "10 de Enero de 2023" (con o sin hora)
    mask = dt.isna() & s.notna() & s.str.contains(r"\bde\b", case=False, regex=True)
    if mask.any():
        tmp = s[mask].str.lower()
        # Extraer: dia, mes (texto), año, y hora opcional
        pat = re.compile(r"^\s*(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+de\s+(\d{4})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?\s*$", re.IGNORECASE)
        parsed = []
        for val in tmp.tolist():
            m = pat.match(val or "")
            if not m:
                parsed.append(pd.NaT)
                continue
            day = int(m.group(1))
            mon_txt = (m.group(2) or "").lower()
            year = int(m.group(3))
            hh = int(m.group(4) or 0)
            mm = int(m.group(5) or 0)
            ss = int(m.group(6) or 0)
            mon = MONTHS_ES.get(mon_txt, None)
            if mon is None:
                parsed.append(pd.NaT)
            else:
                parsed.append(pd.Timestamp(year=year, month=mon, day=day, hour=hh, minute=mm, second=ss))
        dt.loc[mask] = pd.to_datetime(pd.Series(parsed, index=s[mask].index), errors="coerce")
    return dt


def parse_numeric_mixed(series: pd.Series) -> pd.Series:
    """Parse tolerante de importes:
    - admite € y texto tipo 'EUR'
    - coma/punto decimal
    - separadores de miles
    Devuelve float con NaN donde no parsea.
    """
    s = series.astype("string").str.strip()
    # limpiar símbolos y letras
    s = s.str.replace("€", "", regex=False)
    s = s.str.replace("EUR", "", case=False, regex=False)
    s = s.str.replace(r"[^\d\.,\-]", "", regex=True)
    # Heurística:
    # - si tiene coma y punto: asumimos punto miles y coma decimal -> eliminar puntos y cambiar coma por punto
    both = s.str.contains(",", na=False) & s.str.contains(".", na=False)
    s2 = s.copy()
    s2.loc[both] = s2.loc[both].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    # - si solo coma: coma decimal -> cambiar por punto
    only_comma = s2.str.contains(",", na=False) & ~s2.str.contains(".", na=False)
    s2.loc[only_comma] = s2.loc[only_comma].str.replace(",", ".", regex=False)

    return pd.to_numeric(s2, errors="coerce")


@dataclass
class LoadStatus:
    ok: bool
    path: Optional[Path]
    rows: int = 0
    cols: int = 0
    error: Optional[str] = None


@st.cache_data(show_spinner=False)
def load_fact_table(data_dir: Path) -> Tuple[pd.DataFrame, LoadStatus]:
    """Carga la tabla fact integrada (recomendada)."""
    for cand in INTEGRATED_CANDIDATES:
        p = cand
        # si la ruta es relativa, intentar desde data_dir y desde cwd
        if not p.is_absolute():
            if p.parts and p.parts[0] == "data":
                p_try = data_dir / Path(*p.parts[1:])
            else:
                p_try = p
        else:
            p_try = p

        if p_try.exists():
            try:
                df = _safe_read_csv(p_try)
                status = LoadStatus(True, p_try, df.shape[0], df.shape[1], None)
                return df, status
            except Exception as e:
                return pd.DataFrame(), LoadStatus(False, p_try, error=str(e))
    return pd.DataFrame(), LoadStatus(False, None, error="No se encontró fact_transacciones*.csv")


@st.cache_data(show_spinner=False)
def load_raw_files(data_dir: Path) -> Dict[str, Tuple[pd.DataFrame, LoadStatus]]:
    out: Dict[str, Tuple[pd.DataFrame, LoadStatus]] = {}
    for label, fname in RAW_FILES.items():
        p = data_dir / fname
        if p.exists():
            try:
                df = _safe_read_csv(p)
                out[label] = (df, LoadStatus(True, p, df.shape[0], df.shape[1]))
            except Exception as e:
                out[label] = (pd.DataFrame(), LoadStatus(False, p, error=str(e)))
        else:
            out[label] = (pd.DataFrame(), LoadStatus(False, p, error="No encontrado"))
    return out


def ensure_fact_types(fact_raw: pd.DataFrame) -> pd.DataFrame:
    """Convierte columnas clave a tipos útiles para la app, manteniendo el enfoque formativo."""
    df = fact_raw.copy()

    # IDs estandarizados
    for c in ["store_id_std", "customer_id_std", "product_id_std", "doc_id_std", "line_id_std", "tipo_movimiento", "canal_origen"]:
        if c in df.columns:
            df[c] = standardize_id(df[c])

    # Fechas
    if "fecha_movimiento" in df.columns:
        df["event_dt"] = parse_datetime_es(df["fecha_movimiento"])
    elif "fecha_movimiento_raw" in df.columns:
        df["event_dt"] = parse_datetime_es(df["fecha_movimiento_raw"])
    else:
        df["event_dt"] = pd.NaT

    # Importes y cantidades
    if "importe_signed_num" in df.columns:
        df["amount_signed"] = pd.to_numeric(df["importe_signed_num"], errors="coerce")
    elif "importe_linea_raw" in df.columns:
        df["amount_signed"] = parse_numeric_mixed(df["importe_linea_raw"])
    else:
        df["amount_signed"] = np.nan

    if "cantidad_signed" in df.columns:
        df["qty_signed"] = pd.to_numeric(df["cantidad_signed"], errors="coerce")
    elif "cantidad_raw" in df.columns:
        df["qty_signed"] = pd.to_numeric(df["cantidad_raw"], errors="coerce")
    else:
        df["qty_signed"] = np.nan

    # Bandera devolución
    if "tipo_movimiento" in df.columns:
        df["is_return"] = df["tipo_movimiento"].astype("string").str.upper().eq("DEVOLUCION")
    elif "es_devolucion" in df.columns:
        df["is_return"] = df["es_devolucion"].astype("string").str.lower().isin(["1", "true", "yes", "si", "sí"])
    else:
        df["is_return"] = False

    # Monto absoluto útil para ratios
    df["amount_abs"] = df["amount_signed"].abs()
    df["qty_abs"] = df["qty_signed"].abs()

    return df


def filter_fact(df: pd.DataFrame, date_range: Tuple[pd.Timestamp, pd.Timestamp], stores: List[str], channels: List[str]) -> pd.DataFrame:
    out = df.copy()
    start, end = date_range
    if pd.notna(start) and pd.notna(end):
        out = out[(out["event_dt"].notna()) & (out["event_dt"] >= start) & (out["event_dt"] <= end)]
    if stores:
        if "store_id_std" in out.columns:
            out = out[out["store_id_std"].isin(stores)]
    if channels:
        if "canal_origen" in out.columns:
            out = out[out["canal_origen"].isin(channels)]
    return out


# -----------------------------
# Sidebar: selección de datos y filtros
# -----------------------------
with st.sidebar:
    st.header("⚙️ Configuración")
    data_dir_str = st.text_input("Directorio de datos (CSV)", value=str(DATA_DEFAULT_DIR))
    data_dir = Path(data_dir_str)

    st.markdown("**Sugerencia:** usa `datos/retail_omnicanal/raw_csv` como directorio de CSV.")

    fact_raw, fact_status = load_fact_table(data_dir)
    raw_map = load_raw_files(data_dir)

    st.subheader("Estado de ficheros")
    if fact_status.ok:
        st.success(f"Fact encontrada: {fact_status.path} ({fact_status.rows} filas)")
    else:
        st.warning(f"No fact integrada. Motivo: {fact_status.error}")

    # Mostrar estado de raw files (compacto)
    with st.expander("Ver estado de archivos origen"):
        for name, (_, stt) in raw_map.items():
            icon = "✅" if stt.ok else "⚠️"
            st.write(f"{icon} {name}: {stt.path} — {stt.rows}x{stt.cols}" if stt.ok else f"{icon} {name}: {stt.path} — {stt.error}")

    if not fact_status.ok:
        st.info("Para mejores visualizaciones, recuerda usar `fact_transacciones.csv` (o la integrada del Notebook 4).")

# Si no hay fact, salir con mensaje
if not fact_status.ok or fact_raw.empty:
    st.stop()

fact = ensure_fact_types(fact_raw)

# Filtros dependientes de datos
min_dt = fact["event_dt"].min()
max_dt = fact["event_dt"].max()

with st.sidebar:
    st.subheader("Filtros")
    if pd.isna(min_dt) or pd.isna(max_dt):
        st.warning("No se han podido parsear fechas en la fact table. Revisa 'Calidad de datos'.")
        date_range = (pd.Timestamp("1900-01-01"), pd.Timestamp("2100-01-01"))
    else:
        date_range = st.date_input(
            "Rango de fechas",
            value=(min_dt.date(), max_dt.date()),
            min_value=min_dt.date(),
            max_value=max_dt.date(),
        )
        date_range = (pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1))

    stores_avail = sorted([x for x in fact.get("store_id_std", pd.Series([], dtype="string")).dropna().unique().tolist() if x != ""])
    channels_avail = sorted([x for x in fact.get("canal_origen", pd.Series([], dtype="string")).dropna().unique().tolist() if x != ""])

    stores_sel = st.multiselect("Tiendas (store_id)", stores_avail, default=stores_avail[:3] if len(stores_avail) > 0 else [])
    channels_sel = st.multiselect("Canal origen", channels_avail, default=channels_avail)

    include_returns = st.checkbox("Incluir devoluciones en KPIs", value=True)

# Aplicar filtros
fact_f = filter_fact(fact, date_range, stores_sel, channels_sel)

# -----------------------------
# Pages
# -----------------------------
page = st.tabs(["📌 Overview", "🧪 Calidad de datos", "👤 Clientes (RFM/Churn)", "📦 Productos & Stock", "🧺 Cesta (Basket)", "🗃️ Datos (Raw)"])

# ---- Overview ----
with page[0]:
    st.subheader("KPIs principales (según filtros)")
    dfk = fact_f.copy()
    if not include_returns:
        dfk = dfk[~dfk["is_return"]]

    # KPI base (tolerante)
    sales = dfk[dfk["tipo_movimiento"].astype("string").str.upper().eq("VENTA")] if "tipo_movimiento" in dfk.columns else dfk[~dfk["is_return"]]
    returns = dfk[dfk["tipo_movimiento"].astype("string").str.upper().eq("DEVOLUCION")] if "tipo_movimiento" in dfk.columns else dfk[dfk["is_return"]]

    gross_sales = sales["amount_signed"].where(sales["amount_signed"] > 0).sum(skipna=True)
    gross_returns = returns["amount_signed"].abs().sum(skipna=True)
    net_sales = dfk["amount_signed"].sum(skipna=True)

    n_docs_sales = sales.get("doc_id_std", pd.Series([], dtype="string")).nunique(dropna=True)
    n_lines = len(dfk)
    n_customers = sales.get("customer_id_std", pd.Series([], dtype="string")).replace("GUEST", pd.NA).dropna().nunique()

    units_sold = sales["qty_abs"].where(sales["qty_abs"] > 0).sum(skipna=True)
    units_returned = returns["qty_abs"].where(returns["qty_abs"] > 0).sum(skipna=True)
    return_rate_units = (units_returned / units_sold) if units_sold and units_sold > 0 else np.nan

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Ventas brutas (€)", f"{gross_sales:,.0f}")
    c2.metric("Devoluciones (€)", f"{gross_returns:,.0f}")
    c3.metric("Ventas netas (€)", f"{net_sales:,.0f}")
    c4.metric("Docs venta (pedidos/tickets)", f"{n_docs_sales:,}")
    c5.metric("Clientes únicos (identificados)", f"{n_customers:,}")

    st.write("")
    c6, c7, c8 = st.columns(3)
    c6.metric("Líneas (filtradas)", f"{n_lines:,}")
    c7.metric("Unidades vendidas", f"{units_sold:,.0f}")
    c8.metric("Tasa devolución (unid.)", f"{return_rate_units:.1%}" if pd.notna(return_rate_units) else "—")

    # Serie temporal
    st.markdown("#### Evolución temporal (ventas netas)")
    if dfk["event_dt"].notna().any():
        tmp = dfk[dfk["event_dt"].notna()].copy()
        tmp["month"] = tmp["event_dt"].dt.to_period("M").dt.to_timestamp()
        ts = tmp.groupby("month", as_index=False)["amount_signed"].sum()
        chart = alt.Chart(ts).mark_line(point=True).encode(
            x=alt.X("month:T", title="Mes"),
            y=alt.Y("amount_signed:Q", title="€ neto"),
            tooltip=["month:T", "amount_signed:Q"]
        ).properties(height=320)
        st.altair_chart(chart, width="stretch")
    else:
        st.info("No hay fechas parseadas para representar la serie temporal.")

    # Top categorías
    st.markdown("#### Top categorías (ventas brutas)")
    if "categoria" in sales.columns:
        cat = sales.copy()
        cat["amount_pos"] = cat["amount_signed"].where(cat["amount_signed"] > 0)
        top_cat = cat.groupby("categoria", as_index=False)["amount_pos"].sum().sort_values("amount_pos", ascending=False).head(10)
        bar = alt.Chart(top_cat).mark_bar().encode(
            x=alt.X("amount_pos:Q", title="€ ventas brutas"),
            y=alt.Y("categoria:N", sort="-x", title="Categoría"),
            tooltip=["categoria:N", "amount_pos:Q"]
        ).properties(height=320)
        st.altair_chart(bar, width="stretch")
    else:
        st.info("No se encontró la columna 'categoria' en la fact para agrupar.")

    # Descargar fact filtrada
    st.markdown("#### Export rápido")
    csv_bytes = dfk.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar fact filtrada (CSV)", data=csv_bytes, file_name="fact_filtrada.csv", mime="text/csv")


# ---- Calidad de datos ----
with page[1]:
    st.subheader("Calidad de datos (checks rápidos)")
    st.caption("Se muestran métricas útiles para el entrenamiento: parseo de fechas/importes, integridad con maestros, outliers evidentes, etc.")

    cols = st.columns(4)
    # Parse flags (si existen)
    if "flag_fecha_parseada" in fact.columns:
        rate_date = pd.to_numeric(fact["flag_fecha_parseada"], errors="coerce").mean()
        cols[0].metric("% fechas parseadas (flag)", f"{rate_date:.1%}" if pd.notna(rate_date) else "—")
    else:
        rate_date = fact["event_dt"].notna().mean()
        cols[0].metric("% fechas parseadas (event_dt)", f"{rate_date:.1%}")

    if "flag_importe_parseado" in fact.columns:
        rate_amt = pd.to_numeric(fact["flag_importe_parseado"], errors="coerce").mean()
        cols[1].metric("% importes parseados (flag)", f"{rate_amt:.1%}" if pd.notna(rate_amt) else "—")
    else:
        cols[1].metric("% importes parseados", f"{fact['amount_signed'].notna().mean():.1%}")

    # Claves huérfanas
    if "flag_customer_in_crm" in fact.columns:
        miss_c = 1 - pd.to_numeric(fact["flag_customer_in_crm"], errors="coerce").mean()
        cols[2].metric("% cliente NO en CRM", f"{miss_c:.1%}" if pd.notna(miss_c) else "—")
    else:
        cols[2].metric("Cliente en CRM", "—")

    if "flag_product_in_master" in fact.columns:
        miss_p = 1 - pd.to_numeric(fact["flag_product_in_master"], errors="coerce").mean()
        cols[3].metric("% producto NO en maestro", f"{miss_p:.1%}" if pd.notna(miss_p) else "—")
    else:
        cols[3].metric("Producto en maestro", "—")

    st.markdown("#### Nulos por columna (fact filtrada)")
    nulls = fact_f.isna().mean().sort_values(ascending=False).head(20)
    st.dataframe(nulls.rename("pct_null").to_frame(), width="stretch")

    st.markdown("#### Duplicados exactos (fact filtrada)")
    dup_exact = fact_f.duplicated().sum()
    st.write(f"Filas duplicadas exactas: **{dup_exact:,}**")

    st.markdown("#### Outliers básicos (formativo)")
    # Cantidades y importes negativos en ventas (deberían ser raros)
    venta_mask = fact_f["tipo_movimiento"].astype("string").str.upper().eq("VENTA")
    neg_sales_amount = fact_f[venta_mask & (fact_f["amount_signed"] < 0)]
    zero_qty = fact_f[(fact_f["qty_signed"] == 0)]
    st.write(f"- Ventas con importe negativo (posible error): **{len(neg_sales_amount):,}**")
    st.write(f"- Líneas con cantidad = 0: **{len(zero_qty):,}**")

    if len(neg_sales_amount) > 0:
        st.caption("Ejemplos de ventas con importe negativo (muestra)")
        st.dataframe(neg_sales_amount.head(20), width="stretch")

    st.markdown("#### Rango temporal")
    st.write(f"Min fecha parseada: **{fact['event_dt'].min()}**")
    st.write(f"Max fecha parseada: **{fact['event_dt'].max()}**")


# ---- Clientes (RFM/Churn) ----
def compute_rfm(fact_df: pd.DataFrame) -> pd.DataFrame:
    """RFM didáctico sobre ventas (VENTA) con IDs de cliente."""
    df = fact_df.copy()
    df = df[df["event_dt"].notna()]
    # Considerar ventas "positivas" para monetario (evita outliers negativos por errores)
    df_sales = df[df["tipo_movimiento"].astype("string").str.upper().eq("VENTA")].copy()
    df_sales = df_sales[df_sales["customer_id_std"].notna()]
    df_sales = df_sales[df_sales["customer_id_std"].ne("GUEST")]
    df_sales["amount_pos"] = df_sales["amount_signed"].where(df_sales["amount_signed"] > 0)

    as_of = df_sales["event_dt"].max()
    grp = df_sales.groupby("customer_id_std")
    rfm = pd.DataFrame({
        "customer_id": grp.size().index,
        "last_purchase_dt": grp["event_dt"].max().values,
        "frequency_docs": grp["doc_id_std"].nunique().values if "doc_id_std" in df_sales.columns else grp.size().values,
        "monetary_gross": grp["amount_pos"].sum().values,
    })

    rfm["recency_days"] = (as_of - pd.to_datetime(rfm["last_purchase_dt"])).dt.days
    # Scores por quintiles (didáctico)
    def qscore(s, ascending=True):
        # ascending=True -> menor valor = peor (p.ej. F/M), False -> menor mejor (p.ej. R)
        try:
            return pd.qcut(s.rank(method="first"), 5, labels=[1,2,3,4,5]) if ascending else pd.qcut(s.rank(method="first"), 5, labels=[5,4,3,2,1])
        except Exception:
            return pd.Series([np.nan]*len(s))

    rfm["R"] = qscore(rfm["recency_days"], ascending=False).astype("float")
    rfm["F"] = qscore(rfm["frequency_docs"], ascending=True).astype("float")
    rfm["M"] = qscore(rfm["monetary_gross"], ascending=True).astype("float")
    rfm["RFM_sum"] = rfm[["R","F","M"]].sum(axis=1)
    return rfm.sort_values("RFM_sum", ascending=False)


with page[2]:
    st.subheader("Clientes — RFM y señales de churn (demo)")

    if "customer_id_std" not in fact_f.columns:
        st.info("La fact no incluye customer_id_std. No se puede calcular RFM.")
    else:
        rfm = compute_rfm(fact_f)
        st.markdown("#### Top clientes por RFM (demo)")
        st.dataframe(rfm.head(20), width="stretch")

        st.markdown("#### Distribución recency/frequency/monetary")
        c1, c2, c3 = st.columns(3)
        c1.altair_chart(alt.Chart(rfm).mark_bar().encode(x=alt.X("recency_days:Q", bin=True), y="count()").properties(height=240), width="stretch")
        c2.altair_chart(alt.Chart(rfm).mark_bar().encode(x=alt.X("frequency_docs:Q", bin=True), y="count()").properties(height=240), width="stretch")
        c3.altair_chart(alt.Chart(rfm).mark_bar().encode(x=alt.X("monetary_gross:Q", bin=True), y="count()").properties(height=240), width="stretch")

        st.markdown("#### Señal simple de churn (formativa)")
        st.caption("Ejemplo: churn si recency_days > 180. (Ajusta según el curso)")
        churn = rfm.copy()
        churn["label_churn_180d"] = (churn["recency_days"] > 180).astype(int)
        st.write("Clientes en churn (según regla):", int(churn["label_churn_180d"].sum()))
        st.dataframe(churn.sort_values(["label_churn_180d","recency_days"], ascending=[False, False]).head(20), width="stretch")

        st.markdown("#### Scoring (si existe output_scoring/...)")
        # Intentar cargar scoring exportado por Notebook 8
        churn_score_path = Path("output_scoring/churn_scoring.csv")
        if churn_score_path.exists():
            try:
                sc = pd.read_csv(churn_score_path)
                st.success(f"Cargado: {churn_score_path} ({len(sc)} filas)")
                st.dataframe(sc.head(20), width="stretch")
            except Exception as e:
                st.warning(f"No se pudo leer {churn_score_path}: {e}")
        else:
            st.info("No se encontró output_scoring/churn_scoring.csv (opcional).")


# ---- Productos & Stock ----
def compute_product_kpis(fact_df: pd.DataFrame) -> pd.DataFrame:
    df = fact_df.copy()
    df = df[df["event_dt"].notna()]
    # ventas y devoluciones
    df["sale_amount_pos"] = np.where(df["tipo_movimiento"].astype("string").str.upper().eq("VENTA"), df["amount_signed"].where(df["amount_signed"] > 0), 0.0)
    df["return_amount"] = np.where(df["tipo_movimiento"].astype("string").str.upper().eq("DEVOLUCION"), df["amount_abs"], 0.0)
    df["sale_units"] = np.where(df["tipo_movimiento"].astype("string").str.upper().eq("VENTA"), df["qty_abs"], 0.0)
    df["return_units"] = np.where(df["tipo_movimiento"].astype("string").str.upper().eq("DEVOLUCION"), df["qty_abs"], 0.0)

    g = df.groupby(["product_id_std"], dropna=True)
    out = g.agg(
        ventas_eur=("sale_amount_pos", "sum"),
        devol_eur=("return_amount", "sum"),
        unidades_vend=("sale_units", "sum"),
        unidades_dev=("return_units", "sum"),
        lineas=("product_id_std", "size"),
    ).reset_index()

    out["return_rate_units"] = np.where(out["unidades_vend"] > 0, out["unidades_dev"] / out["unidades_vend"], np.nan)
    out["return_rate_amount"] = np.where(out["ventas_eur"] > 0, out["devol_eur"] / out["ventas_eur"], np.nan)

    # Enriquecer si hay columnas de categoría y nombre
    if "categoria" in df.columns:
        cat = df[["product_id_std", "categoria", "subcategoria", "nombre_producto"]].dropna(subset=["product_id_std"]).drop_duplicates("product_id_std")
        out = out.merge(cat, on="product_id_std", how="left")
    return out.sort_values("ventas_eur", ascending=False)


with page[3]:
    st.subheader("Productos & Stock (demo)")

    if "product_id_std" not in fact_f.columns:
        st.info("La fact no incluye product_id_std. No se puede calcular KPIs de producto.")
    else:
        pk = compute_product_kpis(fact_f)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Top productos por ventas (€)")
            st.dataframe(pk.head(20), width="stretch")
        with c2:
            st.markdown("#### Top productos por tasa devolución (unidades)")
            st.dataframe(pk.sort_values("return_rate_units", ascending=False).head(20), width="stretch")

        st.markdown("#### Exploración de un producto")
        prod_sel = st.selectbox("Selecciona product_id", options=pk["product_id_std"].dropna().unique().tolist())
        dfp = fact_f[fact_f["product_id_std"].eq(prod_sel) & fact_f["event_dt"].notna()].copy()
        if not dfp.empty:
            dfp["day"] = dfp["event_dt"].dt.date
            daily = dfp.groupby("day", as_index=False)["amount_signed"].sum()
            st.altair_chart(
                alt.Chart(daily).mark_line(point=True).encode(
                    x=alt.X("day:T", title="Día"),
                    y=alt.Y("amount_signed:Q", title="€ neto (venta+devol)"),
                    tooltip=["day:T","amount_signed:Q"]
                ).properties(height=280),
                width="stretch"
            )

    st.markdown("#### Stock (si existe stock_diario.csv)")
    stock_label = "Stock diario"
    stock_df, stock_st = raw_map.get(stock_label, (pd.DataFrame(), LoadStatus(False, None, error="No cargado")))
    if stock_st.ok and not stock_df.empty:
        sdf = stock_df.copy()
        # Normalizaciones mínimas
        for c in ["store_id", "product_id"]:
            if c in sdf.columns:
                sdf[c] = standardize_id(sdf[c])
        if "fecha" in sdf.columns:
            sdf["fecha_dt"] = parse_datetime_es(sdf["fecha"])
        # stock num
        if "stock_cierre" in sdf.columns:
            sdf["stock_cierre_num"] = parse_numeric_mixed(sdf["stock_cierre"])
        st.caption(f"Stock cargado: {stock_st.rows} filas. Se muestran ejemplos y métricas básicas.")

        s1, s2 = st.columns(2)
        with s1:
            st.markdown("Muestra stock (10 filas)")
            st.dataframe(sdf.head(10), width="stretch")
        with s2:
            if "stock_cierre_num" in sdf.columns:
                neg = (sdf["stock_cierre_num"] < 0).sum()
                st.write(f"Stock negativo (posible error): **{int(neg)}**")
                null_rate = sdf["stock_cierre_num"].isna().mean()
                st.write(f"% stock no parseado: **{null_rate:.1%}**")
    else:
        st.info("No se encontró `stock_diario.csv` en el directorio de datos. (Opcional para esta página)")


# ---- Basket ----
def basket_pair_stats(fact_df: pd.DataFrame, min_items_per_basket: int = 2, max_pairs: int = 30) -> pd.DataFrame:
    """Cálculo didáctico de pares frecuentes (sin dependencias extra).
    - Usa ventas (VENTA) con qty_abs>0
    - Agrupa por doc_id_std (ticket/pedido) -> set de productos
    - Cuenta pares (A,B) y calcula support/confidence/lift
    """
    df = fact_df.copy()
    df = df[df["event_dt"].notna()]
    df = df[df["tipo_movimiento"].astype("string").str.upper().eq("VENTA")]
    df = df[df["qty_abs"].fillna(0) > 0]
    df = df[df["doc_id_std"].notna() & df["product_id_std"].notna()]
    if df.empty:
        return pd.DataFrame()

    baskets = df.groupby("doc_id_std")["product_id_std"].apply(lambda x: sorted(set(x.dropna().tolist())))
    baskets = baskets[baskets.apply(len) >= min_items_per_basket]

    n_baskets = len(baskets)
    if n_baskets == 0:
        return pd.DataFrame()

    # Conteo items
    item_counts: Dict[str, int] = {}
    pair_counts: Dict[Tuple[str, str], int] = {}

    for items in baskets.tolist():
        for it in items:
            item_counts[it] = item_counts.get(it, 0) + 1
        for a, b in combinations(items, 2):
            key = (a, b)
            pair_counts[key] = pair_counts.get(key, 0) + 1

    rows = []
    for (a, b), cnt in pair_counts.items():
        sup = cnt / n_baskets
        conf_ab = cnt / item_counts.get(a, 1)
        conf_ba = cnt / item_counts.get(b, 1)
        lift_ab = conf_ab / (item_counts.get(b, 1) / n_baskets)
        rows.append({
            "A": a, "B": b,
            "pair_count": cnt,
            "support": sup,
            "confidence_A_to_B": conf_ab,
            "confidence_B_to_A": conf_ba,
            "lift_A_to_B": lift_ab,
        })

    out = pd.DataFrame(rows).sort_values(["support", "lift_A_to_B"], ascending=False).head(max_pairs)
    return out


with page[4]:
    st.subheader("Análisis de cesta (Market Basket) — versión didáctica")
    st.caption("Aquí se calcula un ejemplo simple de pares frecuentes (A,B) por pedido/ticket. "
               "Para el curso, esto permite explicar soporte, confianza y lift.")

    min_items = st.slider("Mín. ítems por cesta", 2, 6, 2)
    topn = st.slider("Top pares a mostrar", 10, 100, 30, step=5)

    pairs = basket_pair_stats(fact_f, min_items_per_basket=min_items, max_pairs=topn)
    if pairs.empty:
        st.info("No hay suficientes datos (o fechas/IDs) para construir cestas con los filtros actuales.")
    else:
        st.dataframe(pairs, width="stretch")

        st.markdown("#### Visualización (support)")
        chart = alt.Chart(pairs).mark_bar().encode(
            x=alt.X("support:Q", title="Support"),
            y=alt.Y("A:N", sort="-x", title="Producto A"),
            tooltip=["A:N","B:N","pair_count:Q","support:Q","lift_A_to_B:Q"]
        ).properties(height=320)
        st.altair_chart(chart, width="stretch")


# ---- Raw data ----
with page[5]:
    st.subheader("Datos origen (raw) — inspección rápida")
    st.caption("En formación es habitual enseñar el 'raw' para discutir problemas de calidad (nulos, formatos, duplicados).")

    # Mostrar tabla fact y una tabla origen seleccionable
    st.markdown("#### Fact (muestra)")
    st.dataframe(fact_f.head(50), width="stretch")

    st.markdown("#### Orígenes")
    ds_name = st.selectbox("Selecciona dataset raw", options=list(raw_map.keys()))
    df_raw, stt = raw_map[ds_name]
    if not stt.ok:
        st.warning(f"No disponible: {stt.error}")
    else:
        st.write(f"**{ds_name}** — {stt.path} — {stt.rows} filas x {stt.cols} cols")
        st.dataframe(df_raw.head(100), width="stretch")
        st.download_button(
            f"⬇️ Descargar {ds_name} (CSV)",
            data=df_raw.to_csv(index=False).encode("utf-8"),
            file_name=Path(stt.path).name,
            mime="text/csv",
        )

st.caption("© FraSoHome (caso ficticio). App generada con fines formativos.")
