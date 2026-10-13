"""
Laboratorio de Recomendación — App de Streamlit (Actividad 3, Grupo 9)
Construida a partir de streamlit_starter.py.

Permite a alguien de negocio:
  - elegir un cliente y un método, y ver sus 3 recomendaciones con el "porque"
  - comparar los recomendadores (hit rate@3, precisión@3 y cobertura) en el grupo CONTROL
  - ver el efecto real del carrusel en el experimento (ΔARPU, margen neto y ΔCLV)
Controles interactivos: método, K vecinos, peso de popularidad del híbrido, costo del carrusel, r y d.

Correr con:  streamlit run streamlit_starter.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="Recomendador — Laboratorio", page_icon="☕", layout="wide")

VERDE = "#00704A"
NARANJA = "#C4512F"
GRIS = "#9A988E"
BASE_DIR = Path(__file__).parent          # rutas robustas para Streamlit Community Cloud
METODOS = ["Final (ítem + respaldo)", "Filtrado por ítem", "Filtrado por cliente",
           "Híbrido ítem + popularidad", "Popularidad"]


@st.cache_data
def cargar():
    d = BASE_DIR / "data"
    catalogo = pd.read_csv(d / "catalogo.csv")
    hist = pd.read_csv(d / "ordenes_historial.csv")
    hold = pd.read_csv(d / "ordenes_holdout.csv")
    exp = pd.read_csv(d / "experimento.csv")
    clientes = pd.read_csv(d / "clientes.csv")
    productos = list(catalogo["item"])
    M = (pd.crosstab(hist["customer_id"], hist["item"]) > 0).astype(int).reindex(
        index=clientes["customer_id"], columns=productos, fill_value=0)
    X = M.values.astype(np.float32)
    H = (pd.crosstab(hold["customer_id"], hold["item"]) > 0).astype(int).reindex(
        index=M.index, columns=productos, fill_value=0).values
    NUEVO = H * (1 - X)                                   # probó algo NUEVO en el holdout
    NUEVO[:, productos.index("Agua")] = 0
    es_control = (exp.set_index("customer_id").loc[M.index, "grupo"] == "control").values

    # ingreso y margen por cliente en los 90 días del experimento
    precio = catalogo.set_index("item")["precio"]
    margen = catalogo.set_index("item")["margen"]
    hold = hold.assign(ingreso=hold["item"].map(precio))
    hold["margen_usd"] = hold["ingreso"] * hold["item"].map(margen)
    por_cliente = hold.groupby("customer_id")[["ingreso", "margen_usd"]].sum().reindex(M.index).fillna(0)
    return productos, M.index.values, X, NUEVO, es_control, catalogo, por_cliente


productos, ids, X, NUEVO, es_control, catalogo, por_cliente = cargar()
COL_AGUA = productos.index("Agua")
popularidad = X.sum(axis=0)
precio_v = catalogo.set_index("item")["precio"].reindex(productos).values


# Tabla de similitudes producto × producto (diagonal en 0), calculada UNA vez
@st.cache_data
def similitud_items(X):
    S = cosine_similarity(X.T)
    np.fill_diagonal(S, 0)
    return S


@st.cache_data
def similitud_clientes(X):
    S = cosine_similarity(X)
    np.fill_diagonal(S, 0)
    return S.astype(np.float32)


S_it = similitud_items(X)


def normalizar(v):
    mx = v.max(axis=-1, keepdims=True)
    return v / np.where(mx == 0, 1, mx)


def puntajes(metodo, x_vec, K, w_pop=0.2, fila=None):
    """Puntajes de los 29 productos para UN cliente (x_vec = su vector de 0/1)."""
    if metodo == "Popularidad":
        return popularidad.astype(float)
    if metodo == "Filtrado por ítem":
        return x_vec @ S_it                                   # suma de similitudes con lo ya comprado
    if metodo == "Final (ítem + respaldo)":
        return x_vec @ S_it if x_vec.sum() > 0 else popularidad.astype(float)
    if metodo == "Híbrido ítem + popularidad":
        return (1 - w_pop) * normalizar(x_vec @ S_it) + w_pop * normalizar(popularidad.astype(float))
    # Filtrado por cliente: K vecinos más parecidos, sus compras ponderadas por la similitud
    sims = cosine_similarity(x_vec[None, :], X)[0]
    if fila is not None:
        sims[fila] = 0                                        # no ser vecino de sí mismo
    vec = np.argsort(-sims)[:K]
    return sims[vec] @ X[vec]


def top3(scores, x_vec):
    s = np.where(x_vec > 0, -np.inf, scores).astype(float)   # no recomendar lo ya comprado
    s[COL_AGUA] = -np.inf                                     # ni el Agua
    return np.argsort(-s)[:3]


def porque(metodo, j, x_vec, K, fila=None):
    """Texto del 'porque' de recomendar el producto j."""
    comprados = [p for p in np.where(x_vec > 0)[0] if p != COL_AGUA]
    if metodo == "Popularidad" or (metodo in ("Final (ítem + respaldo)", "Híbrido ítem + popularidad") and not comprados):
        rank = int((popularidad > popularidad[j]).sum()) + 1
        return f"Es de lo más comprado: #{rank} del catálogo ({int(popularidad[j]):,} clientes lo han comprado)."
    if metodo == "Filtrado por cliente":
        sims = cosine_similarity(x_vec[None, :], X)[0]
        if fila is not None:
            sims[fila] = 0
        vec = np.argsort(-sims)[:K]
        n = int(X[vec, j].sum())
        return f"{n} de sus {K} clientes más parecidos lo compraron (similitud promedio {sims[vec].mean():.2f})."
    contrib = sorted(((S_it[p, j], productos[p]) for p in comprados), reverse=True)[:2]
    txt = " y ".join(f"**{nom}** (similitud {s:.2f})" for s, nom in contrib if s > 0)
    return f"Porque compró {txt}." if txt else "Afinidad baja con su historial."


# ---------------------------------------------------------------- Título
st.title("☕ Recomendador de productos — carrusel “Para ti”")
st.caption("Ayuda a decidir qué 3 productos mostrar a cada cliente en el carrusel de la app y con qué método, "
           "comparando lo que cada recomendador acierta contra lo que el experimento demuestra que vende de más.")

# ---------------------------------------------------------------- Barra lateral
with st.sidebar:
    st.header("Parámetros")
    metodo = st.selectbox("Método de recomendación", METODOS, index=0)
    K = st.slider("K vecinos (filtrado por cliente)", 5, 300, 30, step=5)
    w_pop = st.slider("Peso de popularidad (híbrido)", 0.0, 1.0, 0.2, step=0.05)
    st.divider()
    st.caption("Supuestos del experimento")
    costo = st.number_input("Costo del carrusel (US$/cliente, 90 días)", 0.0, 2.0, 0.20, step=0.05)
    r = st.slider("Retención trimestral r", 0.50, 0.95, 0.78, step=0.01)
    d = st.slider("Tasa de descuento trimestral d", 0.00, 0.10, 0.03, step=0.005)

tab1, tab2, tab3 = st.tabs(["Recomendar", "Comparar métodos", "Experimento A/B"])

# ---------------------------------------------------------------- Tab 1: recomendar
with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        cid = st.number_input("ID de cliente", min_value=int(ids.min()), max_value=int(ids.max()), value=14, step=1)
        if st.button("Cliente al azar sin historial"):
            sin = ids[X.sum(axis=1) == 0]
            st.session_state["sugerido"] = int(np.random.choice(sin))
        if "sugerido" in st.session_state:
            st.caption(f"Prueben con el cliente **{st.session_state['sugerido']}** (0 productos).")
    fila = int(np.where(ids == cid)[0][0])
    x_vec = X[fila].copy()
    grupo = "control" if es_control[fila] else "tratamiento"
    ya = [productos[j] for j in np.where(x_vec > 0)[0]]
    with c2:
        st.markdown(f"**Cliente {cid}** · grupo del experimento: *{grupo}* · {len(ya)} productos en su historial")
        st.write("Ya compró:", ", ".join(ya) if ya else "— (sin historial)")

    if x_vec.sum() == 0 and metodo in ("Filtrado por ítem", "Filtrado por cliente"):
        st.warning("Cliente **sin historial**: los métodos colaborativos dan puntaje 0 a todo (el orden sería arbitrario). "
                   "Usen el método **Final (ítem + respaldo)**, que en este caso recomienda por popularidad.")

    sc = puntajes(metodo, x_vec, K, w_pop, fila)
    top = top3(sc, x_vec)
    cols = st.columns(3)
    for k, (col, j) in enumerate(zip(cols, top), start=1):
        with col:
            st.markdown(f"#### {k}. {productos[j]}")
            st.caption(f"{catalogo.loc[catalogo['item'] == productos[j], 'categoria'].iloc[0]} · "
                       f"US${precio_v[j]:.2f} · puntaje {sc[j]:.2f}")
            st.markdown(porque(metodo, j, x_vec, K, fila))

    compro = [productos[j] for j in top if NUEVO[fila, j] > 0]
    if compro:
        st.success(f"En los 90 días del experimento este cliente probó: {', '.join(compro)} (acierto).")

# ---------------------------------------------------------------- Tab 2: comparar
with tab2:
    st.markdown("Hit rate@3, precisión@3 y cobertura sobre los clientes del **grupo control** que probaron algo nuevo "
                "en los 90 días (en el control nadie vio el carrusel, así que la compra es “limpia”).")
    n_eval = st.slider("Clientes de control a evaluar (muestra aleatoria)", 300, 1797, 1797, step=100)

    @st.cache_data
    def matriz_puntajes(metodo, K, w_pop):
        if metodo == "Filtrado por cliente":
            S_us = similitud_clientes(X)
            vec = np.argsort(-S_us, axis=1)[:, :K]
            return np.einsum("ik,ikj->ij", np.take_along_axis(S_us, vec, axis=1), X[vec])
        S_item = X @ S_it
        S_pop = np.tile(popularidad.astype(float), (len(X), 1))
        if metodo == "Popularidad":
            return S_pop
        if metodo == "Filtrado por ítem":
            return S_item
        if metodo == "Final (ítem + respaldo)":
            return np.where((X.sum(axis=1) > 0)[:, None], S_item, S_pop)
        return (1 - w_pop) * normalizar(S_item) + w_pop * normalizar(S_pop)

    def top_k(scores, K=3):
        s = np.where(X > 0, -np.inf, scores).astype(np.float64)
        s[:, COL_AGUA] = -np.inf
        return np.argsort(-s, axis=1)[:, :K]

    mask_eval = es_control & (NUEVO.sum(axis=1) > 0)
    idx_eval = np.where(mask_eval)[0]
    idx_eval = np.random.default_rng(42).choice(idx_eval, size=min(n_eval, len(idx_eval)), replace=False)

    filas = {}
    with st.spinner("Calculando…"):
        for m in METODOS:
            tk = top_k(matriz_puntajes(m, K, w_pop))
            aciertos = NUEVO[idx_eval[:, None], tk[idx_eval]]
            filas[m] = {"hit rate@3": (aciertos.sum(axis=1) > 0).mean(),
                        "precisión@3": aciertos.sum(axis=1).mean() / 3,
                        "cobertura (de 28)": len(np.unique(tk))}
    res = pd.DataFrame(filas).T
    res["mejora vs popularidad"] = res["hit rate@3"] / res.loc["Popularidad", "hit rate@3"] - 1
    st.dataframe(res.style.format({"hit rate@3": "{:.3f}", "precisión@3": "{:.3f}",
                                   "cobertura (de 28)": "{:.0f}", "mejora vs popularidad": "{:+.0%}"})
                 .highlight_max(subset=["hit rate@3"], color="#d6eadf"), width="stretch")
    st.bar_chart(res["hit rate@3"].sort_values(), color=VERDE, horizontal=True)
    st.info("**Acertar no es causar.** En el control estos aciertos ocurrieron sin ninguna recomendación: miden si el "
            "método entiende el gusto del cliente, no cuánta venta extra genera. Eso solo lo dice un experimento.")

# ---------------------------------------------------------------- Tab 3: experimento
with tab3:
    ab = por_cliente.assign(control=es_control)
    t, c = ab[~ab["control"]], ab[ab["control"]]
    d_arpu = t["ingreso"].mean() - c["ingreso"].mean()
    ee = np.sqrt(t["ingreso"].var() / len(t) + c["ingreso"].var() / len(c))
    d_marg = t["margen_usd"].mean() - c["margen_usd"].mean()
    ee_m = np.sqrt(t["margen_usd"].var() / len(t) + c["margen_usd"].var() / len(c))
    neto = d_marg - costo
    factor = r / (1 + d - r)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("ΔARPU 90 días", f"${d_arpu:+.2f}", f"IC 95% {d_arpu - 1.96*ee:+.2f} a {d_arpu + 1.96*ee:+.2f}", delta_color="off")
    m2.metric("Δmargen neto", f"${neto:+.2f}", f"IC 95% {neto - 1.96*ee_m:+.2f} a {neto + 1.96*ee_m:+.2f}", delta_color="off")
    m3.metric("ΔCLV por cliente", f"${neto * factor:+.2f}", f"factor de vida {factor:.2f} trimestres", delta_color="off")
    m4.metric("ΔCLV · 8,000 clientes", f"${neto * factor * len(ab):+,.0f}")
    st.caption("El experimento probó el carrusel de **popularidad** (4,000 tratamiento vs 4,000 control, asignación al azar). "
               "CLV = ARPU × margen × r / (1 + d − r): el carrusel solo mueve el ARPU. Muevan el costo, r y d en la barra lateral.")
    if neto - 1.96 * ee_m <= 0:
        st.warning("Con estos supuestos el intervalo del margen neto incluye el 0: el carrusel podría no pagar su costo.")
