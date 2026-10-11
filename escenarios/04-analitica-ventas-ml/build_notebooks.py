from __future__ import annotations

from pathlib import Path

import nbformat as nbf


BASE = Path(__file__).resolve().parent


def md(text: str):
    return nbf.v4.new_markdown_cell(text.strip() + "\n")


def code(text: str):
    return nbf.v4.new_code_cell(text.strip() + "\n")


def write_nb(path: Path, cells: list):
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.x"},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, path)
    print(f"written {path}")


SETUP = r'''
from pathlib import Path
import sys
import warnings
from datetime import datetime

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", 160)
pd.set_option("display.width", 160)

def find_project_root(start=None):
    current = Path(start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "datos").exists() and (candidate / "escenarios").exists():
            return candidate
    raise FileNotFoundError("No se ha encontrado la raíz del proyecto FraSoHome.")

PROJECT_ROOT = find_project_root()
DEMO_DIR = PROJECT_ROOT / "escenarios" / "04-analitica-ventas-ml"
ARTIFACT_DIR = DEMO_DIR / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(DEMO_DIR))

from common.frasohome_ml import (
    build_campaign_dataset,
    build_churn_dataset,
    build_return_risk_dataset,
    clean_fact_for_ml,
    load_artifact,
    load_operational_tables,
    model_importance,
    prepare_crm,
    prepare_fact,
    save_artifact,
    score_deciles,
    train_binary_model,
    transformed_feature_names,
)

print("PROJECT_ROOT:", PROJECT_ROOT)
'''


def instructor_sales():
    cells = [
        md(
            """
            # Demo instructor 01 · Analítica de ventas y construcción de modelos

            La dirección comercial de FraSoHome quiere priorizar dos decisiones: retener clientes con riesgo de inactividad y ordenar contactos de campaña según su probabilidad de conversión. Esta demo recorre el proceso completo de un proyecto de ML aplicado a ventas: carga de fuentes operativas, limpieza, ventanas temporales, ingeniería de características, preprocesado, entrenamiento y generación de artefactos para interpretabilidad.

            No se crean CSV nuevos. La fuente de verdad son los ficheros raw de `datos`.
            """
        ),
        code(SETUP),
        md(
            """
            ## 1. Carga y diagnóstico de fuentes

            Trabajamos con transacciones, CRM, campañas, navegación digital, feedback y tickets. En negocio, esto representa una vista incompleta pero realista del cliente: compra, relación, servicio y activación.
            """
        ),
        code(
            r'''
tables = load_operational_tables(PROJECT_ROOT)
summary = pd.DataFrame([
    {"tabla": name, "filas": df.shape[0], "columnas": df.shape[1]}
    for name, df in tables.items()
])
display(summary)
'''
        ),
        md(
            """
            ## 2. Limpieza y tipado para ML

            La tabla integrada conserva problemas intencionales: fechas fuera de ventana, importes mixtos, devoluciones, IDs no normalizados y registros sin cliente. Primero tipamos y después aplicamos un filtro analítico 2024-2025, dejando trazabilidad de la reducción.
            """
        ),
        code(
            r'''
fact_typed = prepare_fact(tables["fact"])
fact = clean_fact_for_ml(fact_typed)
crm = prepare_crm(tables["crm"])

quality = pd.DataFrame({
    "métrica": ["filas raw", "filas ML", "clientes ML", "productos ML", "min raw", "max raw", "min ML", "max ML"],
    "valor": [
        len(fact_typed), len(fact), fact["customer_id_std"].nunique(), fact["product_id_std"].nunique(),
        fact_typed["event_dt"].min(), fact_typed["event_dt"].max(), fact["event_dt"].min(), fact["event_dt"].max()
    ],
})
display(quality)
'''
        ),
        md(
            """
            ## 3. Caso 1: riesgo de inactividad a 90 días

            Cada fila es una fotografía de cliente. Usamos 180 días de histórico para construir variables y observamos los 90 días posteriores para etiquetar si el cliente queda inactivo. Así evitamos entrenar con información futura.
            """
        ),
        code(
            r'''
churn_df = build_churn_dataset(
    fact=fact,
    crm=crm,
    web=tables.get("web"),
    feedback=tables.get("feedback"),
    tickets=tables.get("tickets"),
    lookback_days=180,
    horizon_days=90,
    max_snapshots=8,
)
print("churn_df:", churn_df.shape)
display(churn_df["label_inactive_90d"].value_counts(normalize=True).rename("proporción").to_frame())
display(churn_df.head())
'''
        ),
        code(
            r'''
CHURN_TARGET = "label_inactive_90d"
CHURN_EXCLUDED = ["customer_id_std", "snapshot_date", "first_purchase_dt", "last_purchase_dt"]
churn_result = train_binary_model(churn_df, CHURN_TARGET, CHURN_EXCLUDED, model_kind="rf", random_state=42)

display(pd.Series(churn_result["metrics"]).to_frame("valor"))
display(model_importance(churn_result["pipeline"], top_n=15))

churn_test = churn_result["X_test"].copy()
churn_test[CHURN_TARGET] = churn_result["y_test"].values
churn_score = churn_result["pipeline"].predict_proba(churn_result["X_test"])[:, 1]
display(score_deciles(churn_test, churn_score, CHURN_TARGET))
'''
        ),
        md(
            """
            ## 4. Caso 2: propensión de conversión de campañas

            Ahora bajamos al contacto comercial. La etiqueta es conversión a 30 días y las variables combinan contexto del contacto con historial anterior del cliente. Excluimos resultados posteriores al contacto para evitar fuga de información.
            """
        ),
        code(
            r'''
campaign_df = build_campaign_dataset(
    contactos_raw=tables["contactos"],
    fact=fact,
    crm=crm,
    web=tables.get("web"),
    feedback=tables.get("feedback"),
    tickets=tables.get("tickets"),
    lookback_days=180,
)
print("campaign_df:", campaign_df.shape)
display(campaign_df["conversion_30d_flag"].value_counts(normalize=True).rename("proporción").to_frame())
'''
        ),
        code(
            r'''
CAMPAIGN_TARGET = "conversion_30d_flag"
CAMPAIGN_EXCLUDED = [
    "contact_id", "campaign_id", "customer_id", "customer_id_std", "fecha_contacto", "contact_dt",
    "conversion_30d_flag", "order_id_conversion_30d", "ticket_id_conversion_30d", "fecha_conversion_30d",
    "revenue_30d_eur", "margen_30d_eur", "first_purchase_dt", "last_purchase_dt",
]
campaign_result = train_binary_model(campaign_df, CAMPAIGN_TARGET, CAMPAIGN_EXCLUDED, model_kind="rf", random_state=42)

display(pd.Series(campaign_result["metrics"]).to_frame("valor"))
display(model_importance(campaign_result["pipeline"], top_n=15))

campaign_test = campaign_result["X_test"].copy()
campaign_test[CAMPAIGN_TARGET] = campaign_result["y_test"].values
campaign_score = campaign_result["pipeline"].predict_proba(campaign_result["X_test"])[:, 1]
display(score_deciles(campaign_test, campaign_score, CAMPAIGN_TARGET))
'''
        ),
        md(
            """
            ## 5. Guardado del artefacto

            Este artefacto será la entrada de la sesión de interpretabilidad. Contiene datasets, modelos, columnas, métricas y particiones de entrenamiento/test.
            """
        ),
        code(
            r'''
artifact = {
    "created_at": datetime.now().isoformat(timespec="seconds"),
    "source": "CSV operativos FraSoHome 2024-2025",
    "churn": {"dataset": churn_df, "target": CHURN_TARGET, "excluded": CHURN_EXCLUDED, "result": churn_result},
    "campaign": {"dataset": campaign_df, "target": CAMPAIGN_TARGET, "excluded": CAMPAIGN_EXCLUDED, "result": campaign_result},
}
path = save_artifact(artifact, ARTIFACT_DIR / "sales_models_artifact.joblib")
print("Artefacto guardado:", path)
'''
        ),
    ]
    write_nb(BASE / "notebooks_instructor" / "01_demo_ventas_feature_engineering_modelos.ipynb", cells)


def instructor_interpretability():
    cells = [
        md(
            """
            # Demo instructor 02 · Interpretabilidad sobre los modelos de ventas

            Esta demo continúa desde la anterior. Carga los mismos modelos de inactividad y propensión y aplica interpretabilidad global y local: importancias, permutation importance, PDP, SHAP y LIME. El objetivo no es explicar por explicar, sino traducir señales del modelo a decisiones comerciales defendibles.
            """
        ),
        code(
            SETUP
            + r'''
from sklearn.inspection import PartialDependenceDisplay, permutation_importance
import shap
from lime import lime_tabular
'''
        ),
        md("## 1. Carga del artefacto generado en la demo de ventas"),
        code(
            r'''
artifact = load_artifact(ARTIFACT_DIR / "sales_models_artifact.joblib")
print("Creado:", artifact["created_at"])
churn = artifact["churn"]
campaign = artifact["campaign"]
'''
        ),
        md(
            """
            ## 2. Importancia global

            Las importancias internas ayudan a abrir conversación, pero no son causalidad. Sirven para detectar qué señales está usando el modelo y si esas señales tienen sentido comercial.
            """
        ),
        code(
            r'''
display(pd.Series(churn["result"]["metrics"]).to_frame("churn"))
display(model_importance(churn["result"]["pipeline"], top_n=20))
display(pd.Series(campaign["result"]["metrics"]).to_frame("campaign"))
display(model_importance(campaign["result"]["pipeline"], top_n=20))
'''
        ),
        md("## 3. Permutation importance sobre test"),
        code(
            r'''
def permutation_table(result, target_name):
    perm = permutation_importance(
        result["pipeline"], result["X_test"], result["y_test"],
        scoring="roc_auc", n_repeats=8, random_state=42, n_jobs=-1,
    )
    return pd.DataFrame({
        "target": target_name,
        "feature": result["X_test"].columns,
        "mean_auc_drop": perm.importances_mean,
        "std": perm.importances_std,
    }).sort_values("mean_auc_drop", ascending=False)

display(permutation_table(churn["result"], "inactividad").head(12))
display(permutation_table(campaign["result"], "propensión").head(12))
'''
        ),
        md("## 4. PDP: sensibilidad media de variables accionables"),
        code(
            r'''
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
PartialDependenceDisplay.from_estimator(churn["result"]["pipeline"], churn["result"]["X_test"], ["recency_days"], ax=axes[0])
axes[0].set_title("Inactividad · recency_days")
PartialDependenceDisplay.from_estimator(campaign["result"]["pipeline"], campaign["result"]["X_test"], ["frequency_docs"], ax=axes[1])
axes[1].set_title("Propensión · frequency_docs")
plt.tight_layout()
plt.show()
'''
        ),
        md("## 5. SHAP global y local"),
        code(
            r'''
def shap_values_for_tree_pipeline(result, sample_size=80):
    pipe = result["pipeline"]
    pre = pipe.named_steps["preprocess"]
    model = pipe.named_steps["model"]
    X_sample = result["X_test"].sample(min(sample_size, len(result["X_test"])), random_state=42)
    X_trans = pre.transform(X_sample)
    feature_names = transformed_feature_names(pipe)
    explainer = shap.TreeExplainer(model)
    values = explainer.shap_values(X_trans)
    if isinstance(values, list):
        values = values[1]
    elif hasattr(values, "ndim") and values.ndim == 3:
        values = values[:, :, 1]
    return X_sample, X_trans, feature_names, values

X_sample, X_trans, names, values = shap_values_for_tree_pipeline(churn["result"])
shap.summary_plot(values, X_trans, feature_names=names, show=False, max_display=15)
plt.title("SHAP summary · riesgo de inactividad")
plt.tight_layout()
plt.show()
'''
        ),
        code(
            r'''
def local_shap_table(result, top_n=12):
    pipe = result["pipeline"]
    pre = pipe.named_steps["preprocess"]
    model = pipe.named_steps["model"]
    X_test = result["X_test"]
    scores = pipe.predict_proba(X_test)[:, 1]
    row_position = int(np.argmax(scores))
    row_raw = X_test.iloc[[row_position]]
    row_trans = pre.transform(row_raw)
    feature_names = transformed_feature_names(pipe)
    explainer = shap.TreeExplainer(model)
    values = explainer.shap_values(row_trans)
    if isinstance(values, list):
        values = values[1][0]
    elif hasattr(values, "ndim") and values.ndim == 3:
        values = values[0, :, 1]
    else:
        values = values[0]
    out = pd.DataFrame({"feature": feature_names, "shap_value": values})
    out["abs_value"] = out["shap_value"].abs()
    return scores[row_position], row_raw, out.sort_values("abs_value", ascending=False).head(top_n)

score, row_raw, explanation = local_shap_table(churn["result"])
print(f"Score alto de inactividad: {score:.3f}")
display(row_raw.T.head(25))
display(explanation)
'''
        ),
        md("## 6. LIME para una explicación local de campaña"),
        code(
            r'''
def lime_explanation(result, top_n=10):
    pipe = result["pipeline"]
    pre = pipe.named_steps["preprocess"]
    model = pipe.named_steps["model"]
    X_train_trans = pre.transform(result["X_train"])
    X_test_trans = pre.transform(result["X_test"])
    feature_names = transformed_feature_names(pipe)
    scores = pipe.predict_proba(result["X_test"])[:, 1]
    row_position = int(np.argmax(scores))
    explainer = lime_tabular.LimeTabularExplainer(
        training_data=np.asarray(X_train_trans, dtype=float),
        feature_names=feature_names,
        class_names=["no", "sí"],
        mode="classification",
        discretize_continuous=True,
        random_state=42,
    )
    exp = explainer.explain_instance(
        np.asarray(X_test_trans[row_position], dtype=float),
        model.predict_proba,
        num_features=top_n,
    )
    return scores[row_position], pd.DataFrame(exp.as_list(), columns=["condición local", "peso"])

score, lime_table = lime_explanation(campaign["result"])
print(f"Score alto de conversión: {score:.3f}")
display(lime_table)
'''
        ),
        md(
            """
            ## 7. Traducción final a negocio

            Una explicación útil termina en acción: priorizar deciles, personalizar canal/categoría, revisar experiencia posventa y monitorizar estabilidad. La cautela central es no confundir explicación predictiva con causalidad.
            """
        ),
    ]
    write_nb(BASE / "notebooks_instructor" / "02_demo_interpretabilidad_modelos_ventas.ipynb", cells)


def student_notebooks():
    cells = [
        md(
            """
            # Ejercicio alumnos 01 · Dataset y modelos de ventas

            Construye dos modelos conectados con el caso FraSoHome: inactividad a 90 días y propensión de campaña a 30 días. Usa solo los CSV operativos existentes y guarda un artefacto `alumnos_sales_models_artifact.joblib` para el ejercicio de interpretabilidad.
            """
        ),
        code(SETUP),
        md("## Tarea 1. Carga, tipado y limpieza"),
        code(
            r'''
# TODO: carga tablas y prepara fact/crm.
# tables = load_operational_tables(PROJECT_ROOT)
# fact_typed = prepare_fact(tables["fact"])
# fact = clean_fact_for_ml(fact_typed)
# crm = prepare_crm(tables["crm"])

# Muestra: filas por tabla, filas raw/ML, clientes, productos y rango de fechas.
'''
        ),
        md("## Tarea 2. Dataset y modelo de inactividad"),
        code(
            r'''
# TODO: construye churn_df con build_churn_dataset(...).
# TODO: comprueba balance de label_inactive_90d.
# TODO: define CHURN_TARGET y CHURN_EXCLUDED.
# TODO: entrena churn_result con train_binary_model(...).
# TODO: muestra métricas, importancias y deciles de score.
'''
        ),
        md("## Tarea 3. Dataset y modelo de propensión de campaña"),
        code(
            r'''
# TODO: construye campaign_df con build_campaign_dataset(...).
# TODO: excluye IDs, fechas y outcomes posteriores al contacto.
# TODO: entrena campaign_result y revisa métricas, importancias y deciles.
'''
        ),
        md("## Tarea 4. Guardado"),
        code(
            r'''
# TODO: guarda un diccionario con datasets, targets, exclusiones y resultados.
# save_artifact(artifact, ARTIFACT_DIR / "alumnos_sales_models_artifact.joblib")
'''
        ),
    ]
    write_nb(BASE / "notebooks_alumnos" / "01_ejercicio_ventas_feature_engineering_modelos.ipynb", cells)

    cells = [
        md(
            """
            # Ejercicio alumnos 02 · Interpretabilidad de modelos de ventas

            Carga el artefacto del ejercicio 01 y explica los modelos con importancias, permutation importance, PDP y una explicación local con SHAP o LIME. Termina con una recomendación ejecutiva para dirección comercial.
            """
        ),
        code(
            SETUP
            + r'''
from sklearn.inspection import PartialDependenceDisplay, permutation_importance
import shap
from lime import lime_tabular
'''
        ),
        md("## Tarea 1. Carga del artefacto"),
        code(
            r'''
# TODO: carga ARTIFACT_DIR / "alumnos_sales_models_artifact.joblib"
# artifact = load_artifact(...)
# churn = artifact["churn"]
# campaign = artifact["campaign"]
'''
        ),
        md("## Tarea 2. Interpretabilidad global"),
        code(
            r'''
# TODO: calcula model_importance(...) para ambos modelos.
# TODO: calcula permutation_importance(...) sobre test y compara resultados.
'''
        ),
        md("## Tarea 3. PDP"),
        code(
            r'''
# TODO: genera PDP para dos variables numéricas.
# Candidatas: recency_days, frequency_docs, monetary_gross, avg_discount_pct.
'''
        ),
        md("## Tarea 4. Explicación local"),
        code(
            r'''
# TODO: selecciona una instancia con score alto.
# TODO: genera una explicación local con SHAP o LIME.
# TODO: traduce los factores principales a una acción comercial.
'''
        ),
        md(
            """
            ## Tarea 5. Recomendación ejecutiva

            Redacta 8-10 líneas: modelo a usar primero, segmentos/contactos prioritarios, variables accionables y cautelas antes de desplegar.
            """
        ),
    ]
    write_nb(BASE / "notebooks_alumnos" / "02_ejercicio_interpretabilidad_modelos_ventas.ipynb", cells)


def solution_sales():
    cells = [
        md("# Solución 01 · Construcción del dataset y modelos de ventas"),
        code(SETUP),
        code(
            r'''
tables = load_operational_tables(PROJECT_ROOT)
display(pd.DataFrame([{"tabla": k, "filas": v.shape[0], "columnas": v.shape[1]} for k, v in tables.items()]))

fact_typed = prepare_fact(tables["fact"])
fact = clean_fact_for_ml(fact_typed)
crm = prepare_crm(tables["crm"])

display(pd.DataFrame({
    "métrica": ["filas raw", "filas ML", "clientes ML", "productos ML", "min ML", "max ML"],
    "valor": [len(fact_typed), len(fact), fact["customer_id_std"].nunique(), fact["product_id_std"].nunique(), fact["event_dt"].min(), fact["event_dt"].max()],
}))
'''
        ),
        code(
            r'''
churn_df = build_churn_dataset(fact, crm, tables.get("web"), tables.get("feedback"), tables.get("tickets"), max_snapshots=8)
CHURN_TARGET = "label_inactive_90d"
CHURN_EXCLUDED = ["customer_id_std", "snapshot_date", "first_purchase_dt", "last_purchase_dt"]
churn_result = train_binary_model(churn_df, CHURN_TARGET, CHURN_EXCLUDED, model_kind="rf", random_state=42)
display(churn_df[CHURN_TARGET].value_counts(normalize=True).rename("proporción").to_frame())
display(pd.Series(churn_result["metrics"]).to_frame("valor"))
display(model_importance(churn_result["pipeline"], top_n=15))
tmp = churn_result["X_test"].copy()
tmp[CHURN_TARGET] = churn_result["y_test"].values
display(score_deciles(tmp, churn_result["pipeline"].predict_proba(churn_result["X_test"])[:, 1], CHURN_TARGET))
'''
        ),
        code(
            r'''
campaign_df = build_campaign_dataset(tables["contactos"], fact, crm, tables.get("web"), tables.get("feedback"), tables.get("tickets"))
CAMPAIGN_TARGET = "conversion_30d_flag"
CAMPAIGN_EXCLUDED = [
    "contact_id", "campaign_id", "customer_id", "customer_id_std", "fecha_contacto", "contact_dt",
    "conversion_30d_flag", "order_id_conversion_30d", "ticket_id_conversion_30d", "fecha_conversion_30d",
    "revenue_30d_eur", "margen_30d_eur", "first_purchase_dt", "last_purchase_dt",
]
campaign_result = train_binary_model(campaign_df, CAMPAIGN_TARGET, CAMPAIGN_EXCLUDED, model_kind="rf", random_state=42)
display(campaign_df[CAMPAIGN_TARGET].value_counts(normalize=True).rename("proporción").to_frame())
display(pd.Series(campaign_result["metrics"]).to_frame("valor"))
display(model_importance(campaign_result["pipeline"], top_n=15))
tmp = campaign_result["X_test"].copy()
tmp[CAMPAIGN_TARGET] = campaign_result["y_test"].values
display(score_deciles(tmp, campaign_result["pipeline"].predict_proba(campaign_result["X_test"])[:, 1], CAMPAIGN_TARGET))
'''
        ),
        code(
            r'''
artifact = {
    "created_at": datetime.now().isoformat(timespec="seconds"),
    "source": "Solución alumnos · CSV operativos FraSoHome 2024-2025",
    "churn": {"dataset": churn_df, "target": CHURN_TARGET, "excluded": CHURN_EXCLUDED, "result": churn_result},
    "campaign": {"dataset": campaign_df, "target": CAMPAIGN_TARGET, "excluded": CAMPAIGN_EXCLUDED, "result": campaign_result},
}
path = save_artifact(artifact, ARTIFACT_DIR / "alumnos_sales_models_artifact.joblib")
print("Guardado:", path)
'''
        ),
    ]
    write_nb(BASE / "notebooks_soluciones" / "01_solucion_ventas_feature_engineering_modelos.ipynb", cells)


def solution_interpretability():
    cells = [
        md("# Solución 02 · Interpretabilidad de los modelos de ventas"),
        code(
            SETUP
            + r'''
from sklearn.inspection import PartialDependenceDisplay, permutation_importance
import shap
from lime import lime_tabular
'''
        ),
        code(
            r'''
artifact_path = ARTIFACT_DIR / "alumnos_sales_models_artifact.joblib"
if not artifact_path.exists():
    artifact_path = ARTIFACT_DIR / "sales_models_artifact.joblib"
artifact = load_artifact(artifact_path)
print("Cargado:", artifact_path)
churn = artifact["churn"]
campaign = artifact["campaign"]
'''
        ),
        code(
            r'''
display(model_importance(churn["result"]["pipeline"], top_n=15))
display(model_importance(campaign["result"]["pipeline"], top_n=15))
'''
        ),
        code(
            r'''
def permutation_table(result, target_name):
    perm = permutation_importance(result["pipeline"], result["X_test"], result["y_test"], scoring="roc_auc", n_repeats=8, random_state=42, n_jobs=-1)
    return pd.DataFrame({
        "target": target_name,
        "feature": result["X_test"].columns,
        "mean_auc_drop": perm.importances_mean,
        "std": perm.importances_std,
    }).sort_values("mean_auc_drop", ascending=False)

display(permutation_table(churn["result"], "inactividad").head(12))
display(permutation_table(campaign["result"], "propensión").head(12))
'''
        ),
        code(
            r'''
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
PartialDependenceDisplay.from_estimator(churn["result"]["pipeline"], churn["result"]["X_test"], ["recency_days"], ax=axes[0])
axes[0].set_title("Inactividad · recency_days")
PartialDependenceDisplay.from_estimator(campaign["result"]["pipeline"], campaign["result"]["X_test"], ["frequency_docs"], ax=axes[1])
axes[1].set_title("Propensión · frequency_docs")
plt.tight_layout()
plt.show()
'''
        ),
        code(
            r'''
def shap_local(result, top_n=12):
    pipe = result["pipeline"]
    pre = pipe.named_steps["preprocess"]
    model = pipe.named_steps["model"]
    X_test = result["X_test"]
    scores = pipe.predict_proba(X_test)[:, 1]
    pos = int(np.argmax(scores))
    row = X_test.iloc[[pos]]
    row_trans = pre.transform(row)
    names = transformed_feature_names(pipe)
    explainer = shap.TreeExplainer(model)
    values = explainer.shap_values(row_trans)
    if isinstance(values, list):
        values = values[1][0]
    elif hasattr(values, "ndim") and values.ndim == 3:
        values = values[0, :, 1]
    else:
        values = values[0]
    out = pd.DataFrame({"feature": names, "shap_value": values})
    out["abs_value"] = out["shap_value"].abs()
    return scores[pos], row, out.sort_values("abs_value", ascending=False).head(top_n)

score, row, explanation = shap_local(churn["result"])
print(f"Score alto seleccionado: {score:.3f}")
display(row.T.head(25))
display(explanation)
'''
        ),
        code(
            r'''
def lime_table(result, top_n=10):
    pipe = result["pipeline"]
    pre = pipe.named_steps["preprocess"]
    model = pipe.named_steps["model"]
    X_train_trans = pre.transform(result["X_train"])
    X_test_trans = pre.transform(result["X_test"])
    names = transformed_feature_names(pipe)
    scores = pipe.predict_proba(result["X_test"])[:, 1]
    pos = int(np.argmax(scores))
    explainer = lime_tabular.LimeTabularExplainer(
        np.asarray(X_train_trans, dtype=float),
        feature_names=names,
        class_names=["no", "sí"],
        mode="classification",
        discretize_continuous=True,
        random_state=42,
    )
    exp = explainer.explain_instance(np.asarray(X_test_trans[pos], dtype=float), model.predict_proba, num_features=top_n)
    return scores[pos], pd.DataFrame(exp.as_list(), columns=["condición local", "peso"])

score_lime, lime_out = lime_table(campaign["result"])
print(f"Score alto de conversión: {score_lime:.3f}")
display(lime_out)
'''
        ),
        code(
            r'''
recommendation = pd.DataFrame([
    {
        "decisión": "Priorizar retención en deciles altos de inactividad",
        "evidencia": "El modelo concentra riesgo y las explicaciones apuntan a recencia, valor y experiencia",
        "acción": "Campaña de reactivación con mensaje por categoría/canal y control de presión comercial",
        "cautela": "Validar estabilidad mensual y no interpretar importancias como causalidad",
    },
    {
        "decisión": "Ordenar contactos de campaña por propensión",
        "evidencia": "Historial, canal y contexto del cliente diferencian conversión a 30 días",
        "acción": "Asignar oferta y canal según score, margen esperado y consentimiento",
        "cautela": "Excluir variables post-contacto y monitorizar sesgos por canal o segmento",
    },
])
display(recommendation)
'''
        ),
    ]
    write_nb(BASE / "notebooks_soluciones" / "02_solucion_interpretabilidad_modelos_ventas.ipynb", cells)


if __name__ == "__main__":
    instructor_sales()
    instructor_interpretability()
    student_notebooks()
    solution_sales()
    solution_interpretability()
