"""
Laboratorio Final — Starbucks Rewards
App de Streamlit construida a partir de streamlit_starter.py.

Permite a alguien de negocio explorar:
  - la curva Qini del T-learner (vs. el modelo de riesgo/churn y el azar)
  - la tabla de políticas del Paso 3 (valor por cliente y total por % contactado)
con controles interactivos: % de la base a contactar y modelo base del T-learner.

Correr con:  streamlit run streamlit_starter.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split

st.set_page_config(page_title="Laboratorio Final — Starbucks Rewards", page_icon="☕", layout="wide")

GREEN = "#00704A"
ORANGE = "#C4512F"
GRAY = "#9A988E"
FEATURES = ["recency_days", "frequency", "monetary", "email_open_rate", "tenure_days"]
BASE_DIR = Path(__file__).parent  # rutas robustas para Streamlit Community Cloud

MODELOS = {
    "Logística (la del notebook)": lambda: LogisticRegression(max_iter=1000),
    "Random Forest (max_depth=6, min_samples_leaf=100)": lambda: RandomForestClassifier(
        n_estimators=300, max_depth=6, min_samples_leaf=100, random_state=42, n_jobs=-1),
    "Gradient Boosting (max_depth=3, lr=0.05)": lambda: GradientBoostingClassifier(
        n_estimators=200, max_depth=3, learning_rate=0.05, min_samples_leaf=100, random_state=42),
}


@st.cache_data
def load_data():
    return pd.read_csv(BASE_DIR / "data" / "uplift_campaign.csv")


@st.cache_data
def entrenar_t_learner(df: pd.DataFrame, test_size: float, seed: int, nombre_modelo: str):
    train, test = train_test_split(df, test_size=test_size, random_state=seed, stratify=df["treatment_group"])

    # T-learner: un modelo entrenado solo con tratados, otro solo con control
    train_t = train[train["treatment_group"] == "treatment"]
    train_c = train[train["treatment_group"] == "control"]
    fabrica = MODELOS[nombre_modelo]
    modelo_tratado = fabrica().fit(train_t[FEATURES], train_t["responded_60d"])
    modelo_control = fabrica().fit(train_c[FEATURES], train_c["responded_60d"])

    # Modelo de riesgo/churn (referencia, Paso 1)
    train_churn = train.copy()
    train_churn["churned"] = 1 - train_churn["responded_60d"]
    modelo_riesgo = LogisticRegression(max_iter=1000).fit(train_churn[FEATURES], train_churn["churned"])

    test = test.copy()
    X_test = test[FEATURES]
    test["p_tratado"] = modelo_tratado.predict_proba(X_test)[:, 1]
    test["p_control"] = modelo_control.predict_proba(X_test)[:, 1]
    test["uplift_estimado"] = test["p_tratado"] - test["p_control"]
    test["prob_churn"] = modelo_riesgo.predict_proba(X_test)[:, 1]
    return train, test


def valor_de_la_politica(test_df, seleccionados):
    sel = test_df.loc[seleccionados]
    valor_tratado = sel.loc[sel["treatment_group"] == "treatment", "utilidad_neta_60d"].mean()
    valor_control = sel.loc[sel["treatment_group"] == "control", "margin_60d"].mean()
    return valor_tratado - valor_control, len(sel)


def curva_qini(test_df, score_col, steps=40, start=1):
    orden = test_df.sort_values(score_col, ascending=False).reset_index(drop=True)
    es_tratado = (orden["treatment_group"] == "treatment").values
    respondio = orden["responded_60d"].values
    acum_t = np.cumsum(np.where(es_tratado, respondio, 0))
    acum_c = np.cumsum(np.where(~es_tratado, respondio, 0))
    n_t = np.cumsum(es_tratado)
    n_c = np.cumsum(~es_tratado)
    n = len(orden)
    xs, ys = [0.0], [0.0]
    for i in np.linspace(start, n, steps).astype(int):
        tasa_t = acum_t[i - 1] / n_t[i - 1] if n_t[i - 1] > 0 else 0
        tasa_c = acum_c[i - 1] / n_c[i - 1] if n_c[i - 1] > 0 else 0
        xs.append(i / n)
        ys.append((tasa_t - tasa_c) * n)
    return np.array(xs), np.array(ys)


def coeficiente_qini(xs, ys, n):
    area_modelo = np.trapezoid(ys, xs)
    area_azar = np.trapezoid(np.linspace(0, ys[-1], len(xs)), xs)
    return (area_modelo - area_azar) / n


@st.cache_data
def tabla_politicas(test_df: pd.DataFrame, paso: int):
    filas = []
    ordenado = test_df.sort_values("uplift_estimado", ascending=False)
    for pct in range(paso, 101, paso):
        n_c = int(len(test_df) * pct / 100)
        v, n = valor_de_la_politica(test_df, ordenado.head(n_c).index)
        filas.append({"% contactado": pct, "Clientes contactados": n,
                      "Valor por cliente ($)": round(v, 2), "Valor total ($)": round(v * n, 2)})
    return pd.DataFrame(filas)


# --- Título y carga de datos ---
st.title("☕ Laboratorio Final — Starbucks Rewards")
st.caption("¿A quién le enviamos el cupón de $5? Esta app ordena a los clientes por el efecto causal "
           "del cupón (uplift) y muestra cuánto dinero deja contactar a cada porcentaje de la base.")

df = load_data()

with st.sidebar:
    st.header("Parámetros")
    pct_contactar = st.slider("% de la base a contactar", min_value=5, max_value=100, value=20, step=5,
                              help="Se contacta a los clientes con mayor uplift estimado.")
    nombre_modelo = st.selectbox("Modelo base del T-learner", list(MODELOS.keys()), index=0)
    paso_tabla = st.radio("Granularidad de la tabla de políticas", [10, 5], horizontal=True,
                          format_func=lambda p: f"cada {p}%")
    st.divider()
    st.caption("Datos: 40,000 clientes, 50/50 tratamiento/control, cupón $5, ventana de 60 días. "
               "Todas las cifras se miden en el 30% de prueba (12,000 clientes) que el modelo nunca vio.")

with st.spinner("Entrenando el T-learner..."):
    train, test = entrenar_t_learner(df, test_size=0.30, seed=42, nombre_modelo=nombre_modelo)

# --- KPIs de la política elegida ---
n_sel = int(len(test) * pct_contactar / 100)
idx_uplift = test.sort_values("uplift_estimado", ascending=False).head(n_sel).index
idx_riesgo = test.sort_values("prob_churn", ascending=False).head(n_sel).index
v_uplift, _ = valor_de_la_politica(test, idx_uplift)
v_riesgo, _ = valor_de_la_politica(test, idx_riesgo)
v_todos, n_todos = valor_de_la_politica(test, test.index)

xs_u, ys_u = curva_qini(test, "uplift_estimado")
xs_r, ys_r = curva_qini(test, "prob_churn")
qini_u = coeficiente_qini(xs_u, ys_u, len(test))
qini_r = coeficiente_qini(xs_r, ys_r, len(test))
# Para la gráfica se omite el punto calculado con un solo cliente (genera un pico artificial)
inicio_grafica = len(test) // 40
xs_u_g, ys_u_g = curva_qini(test, "uplift_estimado", start=inicio_grafica)
xs_r_g, ys_r_g = curva_qini(test, "prob_churn", start=inicio_grafica)

def dinero(v, decimales=2):
    signo = "-" if v < 0 else "+"
    return f"{signo}${abs(v):,.{decimales}f}"


k1, k2, k3, k4 = st.columns(4)
k1.metric(f"Valor total · top {pct_contactar}% por uplift", dinero(v_uplift * n_sel, 0),
          f"{dinero(v_uplift)} por cliente")
k2.metric(f"Valor total · top {pct_contactar}% por riesgo", dinero(v_riesgo * n_sel, 0),
          f"{dinero(v_riesgo)} por cliente")
k3.metric("Contactar a todos", dinero(v_todos * n_todos, 0), f"{dinero(v_todos)} por cliente")
k4.metric("Coeficiente Qini", f"{qini_u:+.3f}", f"{qini_u - qini_r:+.3f} vs. riesgo")

# --- Curva Qini ---
col_g, col_t = st.columns([3, 2])
with col_g:
    st.subheader("Curva Qini")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(xs_u_g, ys_u_g, color=GREEN, linewidth=3, label=f"T-learner (Qini={qini_u:+.3f})")
    ax.plot(xs_r_g, ys_r_g, color=ORANGE, linewidth=3, label=f"Riesgo/churn (Qini={qini_r:+.3f})")
    ax.plot([0, 1], [0, ys_u_g[-1]], color=GRAY, linestyle="--", label="Al azar")
    ax.axvline(pct_contactar / 100, color="black", linestyle=":", linewidth=1.5)
    ax.text(pct_contactar / 100 + 0.01, ax.get_ylim()[1] * 0.92, f"Contactar {pct_contactar}%", fontsize=9)
    ax.set_xlabel("% de la base contactada (de prueba)")
    ax.set_ylabel("Respuestas incrementales acumuladas")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    plt.tight_layout()
    st.pyplot(fig)
    st.caption("Mientras más se despega la curva verde de la diagonal, mejor separa el modelo a los "
               "clientes que el cupón sí mueve. La curva naranja muestra que ordenar por riesgo de churn "
               "es casi igual que repartir al azar.")

# --- Tabla de políticas ---
with col_t:
    st.subheader("Tabla de políticas")
    tabla = tabla_politicas(test, paso_tabla)
    fila_opt = tabla["Valor total ($)"].idxmax()
    pct_opt = int(tabla.loc[fila_opt, "% contactado"])

    def resaltar(row):
        if row["% contactado"] == pct_opt:
            return ["background-color: #d9efe5; color: #11241C; font-weight: bold"] * len(row)
        if row["% contactado"] == pct_contactar:
            return ["background-color: #fff3cd; color: #11241C"] * len(row)
        return [""] * len(row)

    st.dataframe(
        tabla.style.apply(resaltar, axis=1).format(
            {"Valor por cliente ($)": lambda v: dinero(v), "Valor total ($)": lambda v: dinero(v, 0), "Clientes contactados": "{:,}"}),
        hide_index=True, width="stretch")
    st.success(f"Óptimo con este modelo: contactar al **{pct_opt}%** "
               f"(${tabla.loc[fila_opt, 'Valor total ($)']:,.0f} en prueba).")
    st.caption("Verde = % que maximiza el valor total · Amarillo = % elegido en el slider.")

st.subheader("Valor total según el % contactado")
st.bar_chart(tabla.set_index("% contactado")["Valor total ($)"], color=GREEN)
st.caption("Pasado el óptimo, cada cliente adicional cuesta más en cupones (Sure Things) y en clientes "
           "espantados (Sleeping Dogs) de lo que aporta.")
