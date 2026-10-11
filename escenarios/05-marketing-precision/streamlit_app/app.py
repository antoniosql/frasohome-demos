from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import app_utils as u


st.set_page_config(
    page_title="FraSoHome | Marketing de Precisión",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    .metric-card {
        border: 1px solid rgba(120,120,120,.18);
        padding: .9rem 1rem;
        border-radius: 12px;
        background: linear-gradient(180deg, rgba(248,249,251,.9), rgba(255,255,255,.96));
    }
    .small-muted {color: #6b7280; font-size: .9rem;}
    .section-intro {font-size: 1.0rem; color: #374151; margin-bottom: .5rem;}
    .codebox {border: 1px solid rgba(120,120,120,.18); border-radius: 10px; padding: 1rem; background: #fafafa;}
    </style>
    """,
    unsafe_allow_html=True,
)


APP_ROOT = Path(__file__).resolve().parent


@st.cache_data(show_spinner=False)
def load_app_state(root: str):
    paths = u.resolve_project_root(Path(root))
    tables = u.load_tables(paths)
    outputs = u.load_outputs(paths)
    master = u.build_customer_master(tables, outputs)
    audience = u.build_audience_plan(master)
    return paths, tables, outputs, master, audience


@st.cache_resource(show_spinner=False)
def cached_churn_model(train_df: pd.DataFrame, algo: str, threshold: float, test_size: float):
    return u.train_churn_model(train_df, algo=algo, threshold=threshold, test_size=test_size)


@st.cache_resource(show_spinner=False)
def cached_propensity_model(train_df: pd.DataFrame, algo: str, test_size: float):
    return u.train_propensity_model(train_df, algo=algo, test_size=test_size)


@st.cache_resource(show_spinner=False)
def cached_segmentation_model(seg_df: pd.DataFrame, n_clusters: int):
    return u.train_segmentation_model(seg_df, n_clusters=n_clusters)


paths, tables, outputs, master, audience = load_app_state(str(APP_ROOT))
CATALOG = u.dataset_catalog(tables, outputs)


def metric_row(metrics: List[Tuple[str, str, str]]):
    cols = st.columns(len(metrics))
    for col, (label, value, help_text) in zip(cols, metrics):
        with col:
            st.markdown(f"<div class='metric-card'><div class='small-muted'>{label}</div><div style='font-size:1.7rem;font-weight:700'>{value}</div><div class='small-muted'>{help_text}</div></div>", unsafe_allow_html=True)



def chart_line(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str | None = None, height: int = 300):
    if df.empty:
        st.info("No hay datos suficientes para mostrar este gráfico.")
        return
    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X(x, title=None),
        y=alt.Y(y, title=None),
        color=alt.Color(color, title=None) if color else alt.value("#1f77b4"),
        tooltip=list(df.columns),
    ).properties(height=height, title=title)
    st.altair_chart(chart, width='stretch')



def chart_bar(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str | None = None, height: int = 320):
    if df.empty:
        st.info("No hay datos suficientes para mostrar este gráfico.")
        return
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(x, sort="-y", title=None),
        y=alt.Y(y, title=None),
        color=alt.Color(color, title=None) if color else alt.value("#4c78a8"),
        tooltip=list(df.columns),
    ).properties(height=height, title=title)
    st.altair_chart(chart, width='stretch')



def chart_scatter(df: pd.DataFrame, x: str, y: str, color: str | None = None, size: str | None = None, title: str | None = None, height: int = 320):
    if df.empty:
        st.info("No hay datos suficientes para mostrar este gráfico.")
        return
    chart = alt.Chart(df).mark_circle(opacity=0.75).encode(
        x=alt.X(x, title=None),
        y=alt.Y(y, title=None),
        color=alt.Color(color, title=None) if color else alt.value("#72b7b2"),
        size=alt.Size(size, title=None) if size else alt.value(85),
        tooltip=list(df.columns),
    ).properties(height=height, title=title)
    st.altair_chart(chart, width='stretch')



def dataframe_download(df: pd.DataFrame, label: str, filename: str):
    if df.empty:
        return
    st.download_button(label, df.to_csv(index=False).encode("utf-8"), file_name=filename, mime="text/csv")



def page_resumen():
    st.title("FraSoHome · Marketing de precisión")
    st.markdown(
        "<div class='section-intro'>App Streamlit para explorar el caso, navegar los datasets adicionales y activar decisiones de marketing basadas en customer analytics, IA y GenAI.</div>",
        unsafe_allow_html=True,
    )

    gm = u.compute_global_metrics(tables, outputs, master)
    metric_row([
        ("Clientes CRM", f"{int(gm['clientes_crm']):,}".replace(",", "."), "Base original del caso"),
        ("Clientes activables", f"{int(gm['clientes_contactables']):,}".replace(",", "."), "Con consentimiento de marketing"),
        ("Revenue total", u.format_eur(gm["revenue_total"]), "Fact transacciones"),
        ("Margen total", u.format_eur(gm["margen_total"]), "Margen bruto agregado"),
        ("Campañas", f"{int(gm['campanas'])}", "Datasets adicionales de marketing"),
    ])

    m1, m2 = st.columns([1.4, 1])
    with m1:
        monthly = u.revenue_monthly_by_channel(tables.get("fact", pd.DataFrame()))
        chart_line(monthly, "month:T", "revenue:Q", "canal_movimiento:N", "Evolución mensual del revenue por canal")
    with m2:
        seg_summary = outputs.get("segment_summary", pd.DataFrame()).copy()
        if not seg_summary.empty:
            seg_summary = seg_summary.rename(columns={"segmento_valor": "segmento", "customers": "clientes"})
            chart_bar(seg_summary, "segmento:N", "clientes:Q", title="Distribución de segmentos de valor")
        else:
            st.info("No se encontró la salida de segmentación.")

    c1, c2 = st.columns([1, 1])
    with c1:
        camp = u.campaign_summary(tables.get("campanas", pd.DataFrame())).head(10)
        if not camp.empty:
            plot = camp[["nombre_campana", "revenue_30d_total_eur", "margen_30d_total_eur"]].copy()
            plot = plot.rename(columns={"nombre_campana": "campaña", "revenue_30d_total_eur": "revenue_30d", "margen_30d_total_eur": "margen_30d"})
            chart_bar(plot, "campaña:N", "revenue_30d:Q", title="Top campañas por revenue a 30 días")
        else:
            st.info("No hay campañas cargadas.")
    with c2:
        local = outputs.get("store_category_summary", pd.DataFrame()).copy()
        if not local.empty:
            plot = local.rename(columns={"nombre_tienda": "tienda", "clientes_target": "clientes_target"})
            chart_scatter(plot, "stock_total:Q", "score_medio:Q", color="categoria_target:N", size="clientes_target:Q", title="Store marketing: stock vs score medio")
        else:
            st.info("No se encontró la salida de activación local.")

    st.subheader("Cómo está pensada la app")
    cols = st.columns(4)
    cards = [
        ("Customer 360", "Consolida señal transaccional, digital, fidelización y service para cada cliente."),
        ("Audiencias", "Filtra y exporta audiencias activables según churn, CLV, afinidad de categoría o store marketing."),
        ("Laboratorio", "Permite inspeccionar y simular modelos de churn, propensión, segmentación, promociones y devoluciones."),
        ("VOC + GenAI", "Convierte feedback y tickets en insight accionable y genera borradores de copy con guardrails."),
    ]
    for col, (title, desc) in zip(cols, cards):
        with col:
            st.markdown(f"<div class='metric-card'><div style='font-weight:700'>{title}</div><div class='small-muted' style='margin-top:.4rem'>{desc}</div></div>", unsafe_allow_html=True)

    st.subheader("Casos cubiertos")
    if "mapeo_casos_marketing_precision" in tables:
        st.dataframe(tables["mapeo_casos_marketing_precision"], width='stretch', height=320)
    else:
        st.info("No se encontró el mapeo de casos.")



def page_explorador():
    st.title("Explorador de datos")
    st.caption("Navega cualquier dataset del caso, aplica filtros rápidos y exporta subconjuntos.")

    group = st.sidebar.selectbox("Grupo de datasets", list(CATALOG.keys()), key="explorer_group")
    dataset_name = st.sidebar.selectbox("Dataset", list(CATALOG[group].keys()), key="explorer_dataset")
    df = CATALOG[group][dataset_name].copy()

    if df.empty:
        st.warning("Este dataset no está disponible en el bundle actual.")
        return

    metric_row([
        ("Filas", f"{len(df):,}".replace(",", "."), ""),
        ("Columnas", str(df.shape[1]), ""),
        ("Nulos", f"{int(df.isna().sum().sum()):,}".replace(",", "."), "Celdas vacías"),
        ("% nulos", u.format_pct(df.isna().mean().mean()), "Promedio por celda"),
    ])

    filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 1])
    with filter_col1:
        sample_size = st.slider("Máximo de filas a mostrar", min_value=20, max_value=min(1000, len(df)), value=min(200, len(df)), step=20)
    with filter_col2:
        text_columns = [c for c in df.columns if df[c].dtype == "object" or str(df[c].dtype).startswith("string")]
        text_filter_col = st.selectbox("Filtrar por texto en columna", ["(sin filtro)"] + text_columns)
    with filter_col3:
        text_query = st.text_input("Texto contiene", value="") if text_columns else ""

    filtered = df.copy()
    if text_filter_col != "(sin filtro)" and text_query:
        filtered = filtered[filtered[text_filter_col].astype(str).str.contains(text_query, case=False, na=False)]

    numeric_columns = filtered.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_columns:
        with st.expander("Filtro numérico", expanded=False):
            num_col = st.selectbox("Columna numérica", numeric_columns)
            ser = pd.to_numeric(filtered[num_col], errors="coerce")
            if ser.notna().any():
                val_min, val_max = float(ser.min()), float(ser.max())
                selected = st.slider("Rango", min_value=val_min, max_value=val_max, value=(val_min, val_max))
                filtered = filtered[(ser >= selected[0]) & (ser <= selected[1])]

    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.subheader("Vista previa")
        st.dataframe(filtered.head(sample_size), width='stretch', height=420)
        dataframe_download(filtered, "Descargar dataset filtrado", f"{dataset_name}_filtrado.csv")
    with c2:
        st.subheader("Diagnóstico rápido")
        nulls = filtered.isna().mean().sort_values(ascending=False).head(15).reset_index()
        nulls.columns = ["columna", "pct_nulos"]
        chart_bar(nulls, "columna:N", "pct_nulos:Q", title="Columnas con más nulos")

        dtypes = pd.DataFrame({"columna": filtered.columns, "dtype": filtered.dtypes.astype(str)})
        st.dataframe(dtypes, width='stretch', height=230)



def page_customer360():
    st.title("Customer 360")
    st.caption("Perfil unificado con métricas de valor, churn, propensión, activación local y experiencia.")

    if master.empty:
        st.warning("No hay customer master disponible.")
        return

    search = st.text_input("Buscar cliente por ID, nombre, email, ciudad o provincia", value="")
    view = master.copy()
    if search:
        mask = (
            view["customer_id"].astype(str).str.contains(search, case=False, na=False)
            | view["customer_name"].astype(str).str.contains(search, case=False, na=False)
            | view.get("email", pd.Series(index=view.index, dtype="object")).astype(str).str.contains(search, case=False, na=False)
            | view.get("ciudad", pd.Series(index=view.index, dtype="object")).astype(str).str.contains(search, case=False, na=False)
            | view.get("provincia", pd.Series(index=view.index, dtype="object")).astype(str).str.contains(search, case=False, na=False)
        )
        view = view[mask]
    options = view[["customer_id", "customer_name"]].fillna("").drop_duplicates()
    options["label"] = options["customer_id"] + " · " + options["customer_name"].replace("", "(sin nombre)")
    selected_label = st.selectbox("Selecciona cliente", options["label"].tolist())
    customer_id = options.loc[options["label"] == selected_label, "customer_id"].iloc[0]
    row = master[master["customer_id"] == customer_id].iloc[0]

    metric_row([
        ("Segmento", str(row.get("segmento_valor") or "—"), ""),
        ("Churn", u.format_pct(row.get("score_churn")), str(row.get("next_best_action") or "Sin acción")),
        ("CLV proxy", u.format_eur(row.get("clv_master")), ""),
        ("Categoría top", str(row.get("categoria_rank_1") or "—"), f"score {u.format_pct(row.get('score_rank_1'))}"),
        ("Store target", str(row.get("nombre_tienda") or row.get("store_id_target") or "—"), str(row.get("accion_sugerida") or "")),
    ])

    left, right = st.columns([1.15, 1])
    with left:
        st.subheader("Perfil")
        profile = pd.DataFrame({
            "campo": [
                "customer_id", "nombre", "apellidos", "email", "telefono", "ciudad", "provincia", "tier_fidelizacion",
                "contactable", "canal_preferido_declarado", "estado_cliente", "origen_alta",
            ],
            "valor": [
                row.get("customer_id"), row.get("nombre"), row.get("apellidos"), row.get("email"), row.get("telefono"), row.get("ciudad"), row.get("provincia"),
                row.get("tier_fidelizacion"), row.get("contactable"), row.get("canal_preferido_declarado"), row.get("estado_cliente"), row.get("origen_alta"),
            ],
        })
        st.dataframe(profile, width='stretch', hide_index=True, height=360)

        timeline = u.customer_timeline_monthly(tables.get("fact", pd.DataFrame()), customer_id)
        chart_line(timeline, "month:T", "revenue:Q", title="Histórico mensual de revenue")
    with right:
        st.subheader("Señales clave")
        signals = pd.DataFrame({
            "métrica": [
                "Revenue total", "Margen neto / margen bruto", "Transacciones", "Omnicanal", "Sesiones web", "Pageviews", "Add to cart", "Búsquedas",
                "Prob. visita 30d", "Targetability", "Cross-sell score", "Recomendación prioritaria",
            ],
            "valor": [
                u.format_eur(row.get("gross_revenue_master")), u.format_eur(row.get("net_margin_master")), row.get("tx_count_master"), row.get("omnichannel_flag"),
                row.get("sesiones"), row.get("pageviews"), row.get("add_to_cart"), row.get("searches"), u.format_pct(row.get("prob_visita_30d")),
                u.format_pct(row.get("targetability_score")), row.get("cross_sell_score"), row.get("recomendacion_prioritaria"),
            ],
        })
        st.dataframe(signals, width='stretch', hide_index=True, height=360)

    tab_tx, tab_camp, tab_voc, tab_activate = st.tabs(["Compras", "Campañas", "VOC / soporte", "Activación sugerida"])
    with tab_tx:
        tx = u.customer_transactions(tables.get("fact", pd.DataFrame()), customer_id)
        st.dataframe(tx.head(100), width='stretch', height=380)
        dataframe_download(tx, "Descargar transacciones del cliente", f"customer_{customer_id}_transactions.csv")
    with tab_camp:
        campaigns = u.customer_campaigns(tables.get("contactos", pd.DataFrame()), tables.get("campanas", pd.DataFrame()), customer_id)
        st.dataframe(campaigns, width='stretch', height=380)
    with tab_voc:
        fb, tk = u.customer_feedback(tables.get("feedback", pd.DataFrame()), tables.get("tickets", pd.DataFrame()), customer_id)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Feedback**")
            st.dataframe(fb.head(20), width='stretch', height=340)
        with col2:
            st.markdown("**Soporte / tickets**")
            st.dataframe(tk.head(20), width='stretch', height=340)
    with tab_activate:
        activation = pd.DataFrame({
            "bloque": ["Objetivo", "Canal sugerido", "Acción recomendada", "Oferta sugerida", "Categoría a priorizar", "Store target", "Copy de apoyo"],
            "detalle": [
                row.get("objetivo_sugerido"), row.get("canal_activacion_sugerido"), row.get("recomendacion_prioritaria"), row.get("offer_type_suggested"),
                row.get("categoria_rank_1") or row.get("categoria_target"), row.get("nombre_tienda") or row.get("store_id_target"),
                f"CTA: {row.get('next_best_action') or 'Explorar selección recomendada'}",
            ],
        })
        st.dataframe(activation, width='stretch', hide_index=True)



def page_audiencias():
    st.title("Audiencias y activación")
    st.caption("Construye listas accionables cruzando valor, churn, afinidad de categoría, activación local y consentimiento.")

    if audience.empty:
        st.warning("No hay datos de audiencia disponibles.")
        return

    seg_options = sorted([x for x in audience.get("segmento_valor", pd.Series(dtype="object")).dropna().unique().tolist()])
    cat_options = sorted([x for x in audience.get("categoria_rank_1", pd.Series(dtype="object")).dropna().unique().tolist()])
    store_options = sorted([x for x in audience.get("store_id_target", pd.Series(dtype="object")).dropna().unique().tolist()])
    objective_options = sorted([x for x in audience.get("objetivo_sugerido", pd.Series(dtype="object")).dropna().unique().tolist()])

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        selected_segments = st.multiselect("Segmento de valor", seg_options, default=[])
        only_contactable = st.checkbox("Solo contactables", value=True)
    with f2:
        churn_min = st.slider("Score churn mínimo", 0.0, 1.0, 0.45, 0.05)
        clv_min = st.number_input("CLV proxy mínimo", min_value=0.0, value=0.0, step=500.0)
    with f3:
        selected_category = st.selectbox("Categoría top", ["(todas)"] + cat_options)
        selected_store = st.selectbox("Store target", ["(todas)"] + store_options)
    with f4:
        selected_objective = st.selectbox("Objetivo sugerido", ["(todos)"] + objective_options)
        omnichannel_only = st.checkbox("Solo omnicanal", value=False)

    filtered = audience.copy()
    if selected_segments:
        filtered = filtered[filtered["segmento_valor"].isin(selected_segments)]
    if only_contactable:
        filtered = filtered[filtered["contactable"]]
    filtered = filtered[filtered.get("score_churn", pd.Series(index=filtered.index, dtype="float")).fillna(0) >= churn_min]
    filtered = filtered[filtered.get("clv_master", pd.Series(index=filtered.index, dtype="float")).fillna(0) >= clv_min]
    if selected_category != "(todas)":
        filtered = filtered[filtered.get("categoria_rank_1") == selected_category]
    if selected_store != "(todas)":
        filtered = filtered[filtered.get("store_id_target") == selected_store]
    if selected_objective != "(todos)":
        filtered = filtered[filtered.get("objetivo_sugerido") == selected_objective]
    if omnichannel_only:
        filtered = filtered[filtered.get("omnichannel_flag", pd.Series(index=filtered.index, dtype="float")).fillna(0) >= 1]

    summary_cols = st.columns(4)
    summary = {
        "clientes": len(filtered),
        "uplift": filtered.get("expected_margin_uplift_eur", pd.Series(dtype="float")).fillna(0).sum(),
        "clv": filtered.get("clv_master", pd.Series(dtype="float")).fillna(0).mean(),
        "churn": filtered.get("score_churn", pd.Series(dtype="float")).fillna(0).mean(),
    }
    with summary_cols[0]:
        st.metric("Clientes", f"{summary['clientes']:,}".replace(",", "."))
    with summary_cols[1]:
        st.metric("Margen uplift potencial", u.format_eur(summary["uplift"]))
    with summary_cols[2]:
        st.metric("CLV medio", u.format_eur(summary["clv"]))
    with summary_cols[3]:
        st.metric("Churn medio", u.format_pct(summary["churn"]))

    display_cols = [
        "customer_id", "customer_name", "ciudad", "segmento_valor", "clv_master", "score_churn", "categoria_rank_1", "score_rank_1",
        "store_id_target", "nombre_tienda", "targetability_score", "objetivo_sugerido", "offer_type_suggested", "recomendacion_prioritaria",
        "canal_activacion_sugerido", "expected_margin_uplift_eur",
    ]
    table = filtered[[c for c in display_cols if c in filtered.columns]].copy().sort_values(
        [c for c in ["prioridad_marketing_score", "expected_margin_uplift_eur", "score_churn"] if c in filtered.columns],
        ascending=False,
    )
    st.dataframe(table, width='stretch', height=420)
    dataframe_download(table, "Descargar audiencia", "audiencia_marketing_precision.csv")

    st.subheader("Mix de objetivos")
    mix = filtered.get("objetivo_sugerido", pd.Series(dtype="object")).value_counts().rename_axis("objetivo").reset_index(name="clientes")
    chart_bar(mix, "objetivo:N", "clientes:Q")



def page_modelos():
    st.title("Laboratorio de modelos")
    st.caption("Reentrena benchmarks rápidos, ajusta umbrales y simula clientes o decisiones." )

    tabs = st.tabs(["Segmentación de valor", "Churn", "Propensión", "Cross-sell", "Promociones", "Devoluciones", "Activación local"])

    with tabs[0]:
        st.subheader("Segmentación de valor omnicanal")
        seg_df = outputs.get("value_segmentation", pd.DataFrame()).copy()
        if seg_df.empty:
            st.warning("No se encontró el dataset de segmentación.")
        else:
            n_clusters = st.slider("Número de clusters", 3, 6, 4)
            seg_model = cached_segmentation_model(seg_df, n_clusters)
            metric_row([
                ("Clientes", f"{len(seg_df):,}".replace(",", "."), ""),
                ("Clusters", str(n_clusters), ""),
                ("Silhouette", f"{seg_model['silhouette']:.3f}", "Separación media del modelo"),
                ("Segmentos conocidos", str(seg_df['segmento_valor'].nunique()), "Etiquetas docentes"),
            ])

            scatter = seg_df[[c for c in ["customer_id", "segmento_valor", "clv_proxy_12m", "net_margin", "discount_rate", "recency_days"] if c in seg_df.columns]].copy()
            scatter = scatter.rename(columns={"segmento_valor": "segmento"})
            chart_scatter(scatter, "clv_proxy_12m:Q", "net_margin:Q", color="segmento:N", size="discount_rate:Q", title="CLV vs margen por segmento")

            st.markdown("**Simulador de cliente**")
            c1, c2, c3 = st.columns(3)
            with c1:
                gross_revenue = st.number_input("Gross revenue", 0.0, 50000.0, 4000.0, 500.0, key="seg_gross")
                net_margin = st.number_input("Net margin", 0.0, 20000.0, 1500.0, 250.0, key="seg_margin")
                discount_rate = st.slider("Discount rate", 0.0, 0.5, 0.1, 0.01, key="seg_discount")
            with c2:
                coupon_redemption_rate = st.slider("Coupon redemption", 0.0, 1.0, 0.1, 0.05, key="seg_coupon")
                recency_days = st.number_input("Recency days", 0.0, 365.0, 60.0, 5.0, key="seg_recency")
                omnichannel_flag = st.selectbox("Omnicanal", [0, 1], index=1, key="seg_omni")
            with c3:
                margin_per_tx = st.number_input("Margin per tx", 0.0, 5000.0, 250.0, 25.0, key="seg_mptx")
                tx_per_year = st.number_input("Tx per year", 0.0, 100.0, 8.0, 1.0, key="seg_tpy")
                clv_proxy_12m = st.number_input("CLV proxy 12m", 0.0, 60000.0, 4500.0, 500.0, key="seg_clv")
            sim = {
                "gross_revenue": gross_revenue,
                "net_margin": net_margin,
                "discount_rate": discount_rate,
                "coupon_redemption_rate": coupon_redemption_rate,
                "recency_days": recency_days,
                "omnichannel_flag": omnichannel_flag,
                "margin_per_tx": margin_per_tx,
                "tx_per_year": tx_per_year,
                "clv_proxy_12m": clv_proxy_12m,
            }
            cluster, label = u.simulate_segment(seg_model, sim)
            st.success(f"Cluster estimado: {cluster} · segmento más próximo: {label}")

    with tabs[1]:
        st.subheader("Modelo de churn")
        train_df = outputs.get("churn_training", pd.DataFrame()).copy()
        score_df = outputs.get("churn_scoring", pd.DataFrame()).copy()
        if train_df.empty:
            st.warning("No se encontró el dataset de entrenamiento de churn.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                algo = st.selectbox("Algoritmo", ["Random Forest", "Regresión logística"])
            with c2:
                threshold = st.slider("Umbral de clasificación", 0.1, 0.9, 0.5, 0.05)
            with c3:
                test_size = st.slider("Porción test", 0.2, 0.4, 0.3, 0.05)

            model, metrics, importance = cached_churn_model(train_df, algo, threshold, test_size)
            metric_row([
                ("ROC AUC", f"{metrics['roc_auc']:.3f}", ""),
                ("Precision", f"{metrics['precision']:.3f}", ""),
                ("Recall", f"{metrics['recall']:.3f}", ""),
                ("F1", f"{metrics['f1']:.3f}", ""),
                ("Test rows", str(metrics['test_rows']), ""),
            ])
            col_l, col_r = st.columns([1, 1])
            with col_l:
                chart_bar(importance.rename(columns={"feature": "feature", "importance": "importance"}), "feature:N", "importance:Q", title="Variables más influyentes")
            with col_r:
                scored = u.score_churn_model(model, score_df).head(40)
                st.dataframe(scored, width='stretch', height=320)
                dataframe_download(scored, "Descargar scoring de churn", "churn_scoring_model.csv")

            st.markdown("**Simulador de churn**")
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                tx_180d = st.number_input("tx_180d", 0, 20, 2)
                revenue_180d = st.number_input("revenue_180d", 0.0, 20000.0, 1200.0, 100.0)
                margin_180d = st.number_input("margin_180d", 0.0, 10000.0, 400.0, 50.0)
            with s2:
                days_since_last_purchase = st.number_input("days_since_last_purchase", 0, 365, 60)
                returns_180d = st.number_input("returns_180d", 0, 10, 0)
                online_share_180d = st.slider("online_share_180d", 0.0, 1.0, 0.5, 0.05)
            with s3:
                discount_mean_180d = st.slider("discount_mean_180d", 0.0, 40.0, 8.0, 1.0)
                category_count_180d = st.number_input("category_count_180d", 0, 10, 3)
                srv_tickets = st.number_input("srv_tickets", 0, 10, 0)
            with s4:
                voc_neg = st.number_input("voc_neg", 0, 20, 0)
                tier = st.selectbox("tier_fidelizacion", sorted(train_df["tier_fidelizacion"].dropna().astype(str).unique().tolist()))
                canal = st.selectbox("canal_preferido", sorted(train_df["canal_preferido_declarado"].dropna().astype(str).unique().tolist()))
            sim_row = pd.DataFrame([{
                "tx_180d": tx_180d,
                "revenue_180d": revenue_180d,
                "margin_180d": margin_180d,
                "days_since_last_purchase": days_since_last_purchase,
                "returns_180d": returns_180d,
                "online_share_180d": online_share_180d,
                "discount_mean_180d": discount_mean_180d,
                "category_count_180d": category_count_180d,
                "contact_cnt": 0,
                "contact_conv": 0,
                "contact_control_ratio": np.nan,
                "camp_opens": 0,
                "camp_clicks": 0,
                "camp_purchases": 0,
                "srv_tickets": srv_tickets,
                "srv_comp": 0.0,
                "srv_csat": np.nan,
                "srv_open_ratio": np.nan,
                "voc_nps": np.nan,
                "voc_rating": np.nan,
                "voc_neg": voc_neg,
                "coupon_issued": 0,
                "coupon_redeemed": 0,
                "coupon_avg_discount": np.nan,
                "tier_fidelizacion": tier,
                "canal_preferido_declarado": canal,
                "consentimiento_marketing": "S",
                "estado_cliente": "Activo",
            }])
            risk = model.predict_proba(sim_row)[0, 1]
            st.info(f"Riesgo estimado de churn: {u.format_pct(risk)}")

    with tabs[2]:
        st.subheader("Propensión de compra por categoría")
        train_df = outputs.get("propensity_training", pd.DataFrame()).copy()
        score_df = outputs.get("propensity_scoring", pd.DataFrame()).copy()
        if train_df.empty:
            st.warning("No se encontró el dataset de entrenamiento de propensión.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                algo = st.selectbox("Algoritmo", ["Random Forest", "Regresión logística"], key="prop_algo")
            with c2:
                test_size = st.slider("Porción test", 0.2, 0.4, 0.3, 0.05, key="prop_test")
            model, metrics, importance = cached_propensity_model(train_df, algo, test_size)
            metric_row([
                ("Accuracy", f"{metrics['accuracy']:.3f}", ""),
                ("Macro F1", f"{metrics['macro_f1']:.3f}", ""),
                ("Clases", str(metrics['classes']), ""),
                ("Test rows", str(metrics['test_rows']), ""),
            ])
            col_l, col_r = st.columns([1, 1])
            with col_l:
                chart_bar(importance, "feature:N", "importance:Q", title="Variables más influyentes")
            with col_r:
                st.dataframe(score_df.head(40), width='stretch', height=320)
                dataframe_download(score_df, "Descargar scoring de propensión", "propensity_scoring.csv")

            st.markdown("**Simulador de propensión**")
            s1, s2, s3 = st.columns(3)
            with s1:
                pageviews = st.number_input("web_pageviews_30d", 0, 500, 20)
                searches = st.number_input("web_searches_30d", 0, 100, 3)
                add_to_cart = st.number_input("web_add_to_cart_30d", 0, 50, 1)
            with s2:
                checkout = st.number_input("web_checkout_30d", 0, 20, 0)
                hist_tx = st.number_input("hist_tx_120d", 0, 20, 2)
                hist_revenue = st.number_input("hist_revenue_120d", 0.0, 10000.0, 650.0, 50.0)
            with s3:
                hist_discount = st.number_input("hist_discount_120d", 0.0, 1000.0, 60.0, 10.0)
                cat_div = st.number_input("hist_category_diversity_120d", 0, 10, 2)
                last_category = st.selectbox("last_category", ["", "Muebles", "Decoración", "Iluminación", "Textil Hogar"])
                top_viewed = st.selectbox("top_viewed_category", ["", "Muebles", "Decoración", "Iluminación", "Textil Hogar"])
            sim_row = pd.DataFrame([{
                "web_pageviews_30d": pageviews,
                "web_searches_30d": searches,
                "web_add_to_cart_30d": add_to_cart,
                "web_checkout_30d": checkout,
                "hist_tx_120d": hist_tx,
                "hist_revenue_120d": hist_revenue,
                "hist_discount_120d": hist_discount,
                "hist_category_diversity_120d": cat_div,
                "last_category": last_category or np.nan,
                "top_viewed_category": top_viewed or np.nan,
            }])
            probs = u.predict_propensity_proba(model, sim_row)
            st.dataframe(probs.head(4), width='stretch', hide_index=True)
            if not probs.empty:
                st.success(f"Categoría más probable: {probs.iloc[0]['categoria']} ({u.format_pct(probs.iloc[0]['score'])})")

    with tabs[3]:
        st.subheader("Cross-sell con stock y margen")
        rules = outputs.get("cross_sell_rules", pd.DataFrame()).copy()
        candidates = outputs.get("cross_sell_candidates", pd.DataFrame()).copy()
        if rules.empty:
            st.warning("No se encontró la salida de reglas de cesta.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                min_score = st.slider("Cross-sell score mínimo", 0.0, 5.0, 1.5, 0.1)
            with c2:
                min_stock = st.slider("Stock mínimo unidades", 0, 300, 20, 5)
            with c3:
                category_filter = st.selectbox("Categoría destino", ["(todas)"] + sorted(rules.get("categoria_b", pd.Series(dtype="object")).dropna().astype(str).unique().tolist()))
            f_rules = rules[(rules.get("cross_sell_score", pd.Series(index=rules.index, dtype="float")).fillna(0) >= min_score) & (rules.get("units_available_b", pd.Series(index=rules.index, dtype="float")).fillna(0) >= min_stock)]
            if category_filter != "(todas)":
                f_rules = f_rules[f_rules.get("categoria_b") == category_filter]
            col_l, col_r = st.columns([1, 1])
            with col_l:
                st.dataframe(f_rules.head(30), width='stretch', height=360)
            with col_r:
                if not f_rules.empty:
                    plot = f_rules[["nombre_producto_a", "nombre_producto_b", "cross_sell_score", "units_available_b"]].copy()
                    plot = plot.rename(columns={"nombre_producto_a": "producto_origen", "nombre_producto_b": "producto_recomendado"})
                    chart_scatter(plot, "units_available_b:Q", "cross_sell_score:Q", color="producto_recomendado:N", title="Reglas priorizadas")
            f_candidates = candidates[(candidates.get("cross_sell_score", pd.Series(index=candidates.index, dtype="float")).fillna(0) >= min_score) & (candidates.get("units_available_b", pd.Series(index=candidates.index, dtype="float")).fillna(0) >= min_stock)]
            st.markdown("**Clientes candidatos**")
            st.dataframe(f_candidates.head(50), width='stretch', height=320)
            dataframe_download(f_candidates, "Descargar candidatos de cross-sell", "cross_sell_candidates.csv")

    with tabs[4]:
        st.subheader("Elasticidad promocional")
        promo = outputs.get("promo_scoreboard", pd.DataFrame()).copy()
        decisions = outputs.get("promo_decisions", pd.DataFrame()).copy()
        if promo.empty:
            st.warning("No se encontró la salida de promociones.")
        else:
            decision_filter = st.selectbox("Decisión recomendada", ["(todas)"] + sorted(promo["decision_recomendada"].dropna().astype(str).unique().tolist()))
            promo_f = promo.copy()
            if decision_filter != "(todas)":
                promo_f = promo_f[promo_f["decision_recomendada"] == decision_filter]
            metric_row([
                ("Promos analizadas", str(len(promo_f)), ""),
                ("Revenue uplift medio", u.format_pct(promo_f["revenue_uplift_pct"].mean() / 100 if "revenue_uplift_pct" in promo_f else np.nan), ""),
                ("Margin uplift medio", u.format_pct(promo_f["margin_uplift_pct"].mean() / 100 if "margin_uplift_pct" in promo_f else np.nan), ""),
                ("Eficiencia media", f"{promo_f['margin_efficiency'].mean():.2f}" if "margin_efficiency" in promo_f else "—", ""),
            ])
            chart_scatter(promo_f, "discount_rate_during:Q", "margin_uplift_pct:Q", color="decision_recomendada:N", size="tx_during:Q", title="Descuento durante promo vs uplift de margen")
            st.dataframe(promo_f.head(50), width='stretch', height=340)
            if not decisions.empty:
                dataframe_download(decisions, "Descargar decisiones promocionales", "promo_decisions.csv")

    with tabs[5]:
        st.subheader("Riesgo de devolución")
        risk = outputs.get("return_risk_scoring", pd.DataFrame()).copy()
        prod = outputs.get("return_risk_products", pd.DataFrame()).copy()
        if risk.empty:
            st.warning("No se encontró la salida de riesgo de devolución.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                thr = st.slider("Umbral de riesgo", 0.0, 1.0, 0.7, 0.05)
            with c2:
                cat = st.selectbox("Categoría", ["(todas)"] + sorted(risk.get("categoria", pd.Series(dtype="object")).dropna().astype(str).unique().tolist()))
            risk_f = risk[risk.get("return_risk_score", pd.Series(index=risk.index, dtype="float")).fillna(0) >= thr]
            if cat != "(todas)":
                risk_f = risk_f[risk_f.get("categoria") == cat]
            chart_scatter(risk_f.head(200), "price:Q", "return_risk_score:Q", color="categoria:N", size="margin:Q", title="Precio vs riesgo de devolución")
            st.dataframe(risk_f.head(80), width='stretch', height=320)
            st.markdown("**Productos con mayor riesgo medio**")
            st.dataframe(prod.head(30), width='stretch', height=280)
            dataframe_download(risk_f, "Descargar scoring de devolución", "return_risk_scoring.csv")

    with tabs[6]:
        st.subheader("Store marketing / activación local")
        local = outputs.get("local_activation", pd.DataFrame()).copy()
        stores = tables.get("tiendas", pd.DataFrame()).copy()
        if local.empty:
            st.warning("No se encontró la salida de activación local.")
        else:
            store = st.selectbox("Tienda", ["(todas)"] + sorted(local.get("store_id_target", pd.Series(dtype="object")).dropna().astype(str).unique().tolist()))
            category = st.selectbox("Categoría target", ["(todas)"] + sorted(local.get("categoria_target", pd.Series(dtype="object")).dropna().astype(str).unique().tolist()))
            min_target = st.slider("Targetability mínimo", 0.0, 1.0, 0.4, 0.05)
            local_f = local[local.get("targetability_score", pd.Series(index=local.index, dtype="float")).fillna(0) >= min_target]
            if store != "(todas)":
                local_f = local_f[local_f["store_id_target"] == store]
            if category != "(todas)":
                local_f = local_f[local_f["categoria_target"] == category]
            top_store = (
                local_f.groupby(["store_id_target", "nombre_tienda"], dropna=False)
                .agg(clientes=("customer_id", "nunique"), score_medio=("targetability_score", "mean"), prob_visita=("prob_visita_30d", "mean"))
                .reset_index()
            )
            chart_bar(top_store.rename(columns={"nombre_tienda": "tienda"}), "tienda:N", "clientes:Q", title="Clientes target por tienda")
            st.dataframe(local_f.head(80), width='stretch', height=320)
            dataframe_download(local_f, "Descargar plan local", "local_activation_plan.csv")
            if not stores.empty and {"lat", "lon"}.issubset(stores.columns):
                map_df = stores[["lat", "lon", "nombre_tienda"]].dropna().rename(columns={"lat": "LAT", "lon": "LON"})
                st.map(map_df.rename(columns={"LAT": "lat", "LON": "lon"}))



def page_voc_genai():
    st.title("VOC + IA generativa")
    st.caption("Analiza la voz del cliente y genera borradores de copy con guardrails de marca, sin llamadas externas a LLM.")

    issue = outputs.get("voc_issue_matrix", pd.DataFrame()).copy()
    prompts = outputs.get("voc_prompt_pack", pd.DataFrame()).copy()
    feedback = tables.get("feedback", pd.DataFrame()).copy()
    tickets = tables.get("tickets", pd.DataFrame()).copy()
    creatividades = tables.get("creatividades", pd.DataFrame()).copy()
    guardrails = tables.get("guardrails", pd.DataFrame()).copy()
    briefs = outputs.get("copy_briefs", pd.DataFrame()).copy()

    tab_voc, tab_prompts, tab_copy = st.tabs(["Matriz VOC", "Prompt packs", "Generador de copy"])

    with tab_voc:
        if issue.empty:
            st.warning("No se encontró la matriz VOC.")
        else:
            theme_options = sorted(issue["tema_principal"].dropna().astype(str).unique().tolist())
            c1, c2 = st.columns([1, 1])
            with c1:
                theme = st.selectbox("Tema", theme_options)
            with c2:
                source = st.selectbox("Fuente", ["(todas)"] + sorted(issue["fuente"].dropna().astype(str).unique().tolist()))
            issue_f = issue.copy()
            if source != "(todas)":
                issue_f = issue_f[issue_f["fuente"] == source]
            chart_bar(issue_f.groupby(["tema_principal", "sentimiento"], dropna=False)["registros"].sum().reset_index(), "tema_principal:N", "registros:Q", color="sentimiento:N", title="Menciones por tema y sentimiento")
            insight = u.voc_insight(theme, issue, feedback, tickets)
            metric_row([
                ("Tema", str(insight['theme']), ""),
                ("Menciones", str(insight['mentions']), ""),
                ("Peso negativo", u.format_pct(insight['negative_share']), ""),
                ("Recomendación", "Ver abajo", "Insight accionable"),
            ])
            st.markdown(f"**Implicación**: {insight['implication']}")
            st.markdown(f"**Recomendación**: {insight['recommendation']}")
            if insight["samples"]:
                st.markdown("**Muestras de voz del cliente**")
                for s in insight["samples"]:
                    st.write(f"- {s}")

    with tab_prompts:
        if prompts.empty:
            st.warning("No se encontró el prompt pack VOC.")
        else:
            theme = st.selectbox("Tema para prompt pack", sorted(prompts["tema_principal"].dropna().astype(str).unique().tolist()), key="prompt_theme")
            row = prompts[prompts["tema_principal"] == theme].iloc[0]
            st.markdown("**Brief determinista**")
            st.info(row.get("brief_determinista", ""))
            st.markdown("**Prompt pack**")
            st.code(row.get("prompt_pack", ""), language="markdown")
            dataframe_download(prompts[prompts["tema_principal"] == theme], "Descargar prompt pack", f"prompt_pack_{theme}.csv")

    with tab_copy:
        st.subheader("Generador de copy guiado")
        microsegmentos = sorted(creatividades.get("microsegmento", pd.Series(dtype="object")).dropna().astype(str).unique().tolist()) or ["ACTIVO_BASE", "RIESGO_CHURN", "VIP_OMNICANAL"]
        categorias = sorted(creatividades.get("categoria_objetivo", pd.Series(dtype="object")).dropna().astype(str).unique().tolist()) or ["multicategoría", "Muebles", "Decoración", "Iluminación", "Textil Hogar"]
        canales = sorted(creatividades.get("canal", pd.Series(dtype="object")).dropna().astype(str).unique().tolist()) or ["EMAIL", "SMS", "PUSH"]
        tonos = sorted(creatividades.get("tono", pd.Series(dtype="object")).dropna().astype(str).unique().tolist()) or ["práctico", "inspiracional", "urgencia_suave", "exclusivo"]
        beneficios = sorted(creatividades.get("beneficio_principal", pd.Series(dtype="object")).dropna().astype(str).unique().tolist()) or ["activar ventajas del club", "ahorrar sin perder estilo", "mejorar el ambiente del hogar"]
        ctas = sorted(creatividades.get("cta", pd.Series(dtype="object")).dropna().astype(str).unique().tolist()) or ["Descubrir", "Activar oferta", "Reservar ahora"]

        c1, c2, c3 = st.columns(3)
        with c1:
            microsegmento = st.selectbox("Microsegmento", microsegmentos)
            canal = st.selectbox("Canal", canales)
            categoria = st.selectbox("Categoría objetivo", categorias)
        with c2:
            objetivo = st.selectbox("Objetivo", ["onboarding", "reactivacion", "cross_sell", "promocion", "loyalty"])
            tono = st.selectbox("Tono", tonos)
            beneficio = st.selectbox("Beneficio principal", beneficios)
        with c3:
            cta = st.selectbox("CTA", ctas)
            tienda = st.text_input("Mención local opcional (tienda)", value="")
            condicion = st.text_input("Condición promocional opcional", value="")

        selected_guardrails = guardrails["descripcion_regla"].dropna().astype(str).tolist()[:12]
        top_ref = u.top_creatives(creatividades, microsegmento=microsegmento, categoria=categoria, limit=5)
        prueba_social = None
        if not top_ref.empty and "prueba_social" in top_ref.columns:
            prueba_social = top_ref.iloc[0]["prueba_social"]

        draft = u.draft_copy(
            microsegmento=microsegmento,
            canal=canal,
            categoria_objetivo=categoria,
            objetivo=objetivo,
            tono=tono,
            beneficio_principal=beneficio,
            cta=cta,
            guardrails=selected_guardrails,
            tienda=tienda or None,
            condicion_promocional=condicion or None,
            prueba_social=prueba_social,
        )

        st.markdown("**Asunto / titular**")
        st.success(draft["subject"])
        st.markdown("**Borrador de cuerpo**")
        st.write(draft["body"])
        st.markdown("**Justificación estratégica**")
        st.write(draft["rationale"])
        st.markdown("**Riesgo a vigilar**")
        st.warning(draft["risk"])
        with st.expander("Guardrails aplicados"):
            for g in selected_guardrails:
                st.write(f"- {g}")

        st.markdown("**Variantes históricas de referencia**")
        ref_cols = [c for c in ["campaign_id", "microsegmento", "canal", "categoria_objetivo", "tono", "cta", "asunto", "copy_corto", "open_rate", "ctr", "cvr", "revenue_por_1000_envios_eur"] if c in top_ref.columns]
        st.dataframe(top_ref[ref_cols], width='stretch', height=280)
        if not briefs.empty:
            st.markdown("**Biblioteca de prompts**")
            prompt_view = briefs[[c for c in ["creative_id", "campaign_id", "microsegmento", "categoria_objetivo", "objetivo", "performance_score", "prompt_library_entry"] if c in briefs.columns]].head(10)
            st.dataframe(prompt_view, width='stretch', height=260)



def page_documentacion():
    st.title("Documentación y ejecución")
    st.caption("Notas para usar la app, estructura del bundle y resumen de datasets y casos.")

    st.markdown("**Ruta detectada**")
    st.code(str(paths.root))

    st.markdown("**Estructura esperada**")
    st.code(
        """
frasohome-demos/
├─ datos/
│  ├─ retail_omnicanal/raw_csv/
│  └─ marketing_precision/raw_csv/
└─ escenarios/05-marketing-precision/
   ├─ streamlit_app/ (app.py, app_utils.py, requirements.txt)
   ├─ sample_outputs/
   └─ outputs/ (generado por los notebooks)
        """.strip()
    )

    st.markdown("**Ejecución local**")
    st.code(
        """
pip install -r requirements.txt
streamlit run app.py
        """.strip(),
        language="bash",
    )

    st.markdown("**Qué cubre la app**")
    bullets = [
        "Customer 360 accionable y resolución de identidad.",
        "Segmentación de valor omnicanal y CLV proxy.",
        "Churn y next best action.",
        "Propensión por categoría.",
        "Cross-sell basket-aware con stock y margen.",
        "Elasticidad promocional y decisiones de descuento.",
        "Riesgo de devolución y margen esperado.",
        "Store marketing y activación local.",
        "VOC + prompt packs y copy con guardrails.",
    ]
    for b in bullets:
        st.write(f"- {b}")

    doc_tabs = st.tabs(["Catálogo datasets", "Diccionario", "Casos", "Validación"])
    with doc_tabs[0]:
        if "catalogo_datasets_marketing_precision" in tables:
            st.dataframe(tables["catalogo_datasets_marketing_precision"], width='stretch', height=340)
    with doc_tabs[1]:
        if "diccionario_columnas_marketing_precision" in tables:
            st.dataframe(tables["diccionario_columnas_marketing_precision"].head(200), width='stretch', height=400)
    with doc_tabs[2]:
        if "mapeo_casos_marketing_precision" in tables:
            st.dataframe(tables["mapeo_casos_marketing_precision"], width='stretch', height=340)
    with doc_tabs[3]:
        if "validacion_datasets_marketing_precision" in tables:
            st.dataframe(tables["validacion_datasets_marketing_precision"], width='stretch', height=300)


with st.sidebar:
    st.markdown("## 🎯 FraSoHome")
    st.caption("Marketing de precisión · analítica de clientes · IA")
    nav = st.radio(
        "Navegación",
        [
            "Resumen ejecutivo",
            "Explorador de datos",
            "Customer 360",
            "Audiencias",
            "Laboratorio de modelos",
            "VOC + GenAI",
            "Documentación",
        ],
    )
    st.markdown("---")
    st.markdown(f"**Root**\n`{paths.root}`")
    st.markdown(f"**Outputs**\n`{paths.outputs}`")
    st.markdown("---")
    st.caption("El bundle incluye datos base, datasets adicionales y salidas de scoring de los notebooks.")


if nav == "Resumen ejecutivo":
    page_resumen()
elif nav == "Explorador de datos":
    page_explorador()
elif nav == "Customer 360":
    page_customer360()
elif nav == "Audiencias":
    page_audiencias()
elif nav == "Laboratorio de modelos":
    page_modelos()
elif nav == "VOC + GenAI":
    page_voc_genai()
else:
    page_documentacion()
