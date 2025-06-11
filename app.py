
import streamlit as st
import plotly.express as px
import pandas as pd
from supabase_client import get_client
from datetime import datetime

st.set_page_config(page_title="Tronix – ARAUCO", layout="wide")

# -------------------------- PALETA CORPORATIVA -------------------------------
PLOTLY_TEMPLATE = {
    "layout": {
        "colorway": [
            "#005f2d",  # Verde corporativo principal
            "#007b3c",  # Verde claro
            "#8fa99c",  # Gris verdoso
            "#4d4d4d",  # Gris medio
            "#b8bbb9",  # Gris claro
        ],
        "paper_bgcolor": "#f8f9fa",
        "plot_bgcolor": "#f8f9fa",
        "font": {"color": "#2f2f2f"},
    }
}

st.markdown(
    """
    <style>
        /* Headings y texto */
        h1, h2, h3, h4 { color: #005f2d; }
        /* Sidebar */
        section[data-testid="stSidebar"] > div:first-child {
            background-color: #005f2d;
            color: white;
        }
        /* Filtros colapsables */
        .stExpander > summary { background-color:#8fa99c !important; color:white; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------- UTILIDADES ---------------------------------------

@st.cache_data(ttl=600)
def load_table(table_name: str):
    """Carga datos de Supabase y devuelve DataFrame."""
    supabase = get_client()
    res = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(res.data)

# KPI helpers -----------------------------------------------------------------

def fetch_kpis():
    """Genera KPIs ejecutivos usando tablas existentes."""
    df_prod = load_table("comparativa_produccion_teams")
    df_desp = load_table("comparativa_despachos")

    # Cumplimiento producción vs proyección
    cumplimiento_prod = (
        df_prod["volumen"].sum() / df_prod["volumen_proyectado"].sum() * 100
        if df_prod["volumen_proyectado"].sum() else 0
    )
    # Cumplimiento despachos
    cumplimiento_desp = (
        df_desp["volumen_despachado"].sum() / df_desp["volumen_planificado"].sum() * 100
        if df_desp["volumen_planificado"].sum() else 0
    )
    # Brecha total (m3)
    brecha_total = (
        df_desp["volumen_despachado"].sum() - df_desp["volumen_planificado"].sum()
        + df_prod["volumen"].sum() - df_prod["volumen_proyectado"].sum()
    )

    return cumplimiento_prod, cumplimiento_desp, brecha_total

# -------------------------- LAYOUT PRINCIPAL ---------------------------------

st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/9/9c/Arauco_logo.svg",
    use_column_width=True,
)

pagina = st.sidebar.radio(
    "Navegación",
    (
        "🤖 Agente Tronix",
        "📊 Producción vs Proyección – Teams",
        "🚛 Despachos vs Planificado",
        "🌲 Stock de Predios",
        "🔍 Visión Corporativa",
    ),
)

# -------------------------- PÁGINAS ------------------------------------------

# 1. Agente Tronix (embed existente --------------------------------------------------
if pagina == "🤖 Agente Tronix":
    st.title("🤖 Agente Tronix")
    st.info("Chat embebido; la conexión se mantiene como en la versión anterior.")
    st.components.v1.iframe(src="/chat", height=700, scrolling=True)

# 2. Producción vs Proyección – Teams -------------------------------------
if pagina == "📊 Producción vs Proyección – Teams":

    st.title("📊 Producción vs Proyección – Teams")

    df = load_table("comparativa_produccion_teams")
    df["fecha"] = pd.to_datetime(df["fecha"])

    # -------------- GRID LAYOUT -----------------------------------------
    col1, col2 = st.columns([4, 1], gap="large")

    # ----------- MAIN VISUAL -------------------------------------------
    with col1:
        # KPI cards on top
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total Proyectado (m3)", f"{df['volumen_proyectado'].sum():,.0f}")
        kpi2.metric("Total Producido (m3)", f"{df['volumen'].sum():,.0f}")
        delta = df["volumen"].sum() - df["volumen_proyectado"].sum()
        kpi3.metric("Brecha (m3)", f"{delta:,.0f}", delta=f"{delta:,.0f}")

        # Gráfico principal
        fig_pp = px.bar(
            df,
            x="team",
            y=["volumen_proyectado", "volumen"],
            barmode="group",
            title="Proyección vs Producción por Team",
            template=PLOTLY_TEMPLATE,
        )
        st.plotly_chart(fig_pp, use_container_width=True)

    # ----------- SIDEBAR / FILTROS -------------------------------------
    with col2:
        with st.expander("🎛️ Filtros", expanded=False):
            teams = sorted(df["team"].unique())
            team_sel = st.multiselect("Team", teams, default=teams, key="team_filter_pp")

            calidades = sorted(df["calidad"].unique())
            calidad_sel = st.multiselect(
                "Calidad", calidades, default=calidades, key="calidad_filter_pp"
            )

            df = df[df["team"].isin(team_sel) & df["calidad"].isin(calidad_sel)]

# 3. Despachos vs Planificado ------------------------------------------
if pagina == "🚛 Despachos vs Planificado":

    st.title("🚛 Despachos vs Planificado")

    df_desp = load_table("comparativa_despachos")

    # Conversión tipos
    df_desp["fecha"] = pd.to_datetime(dict(year=df_desp["anio"], month=df_desp["mes"], day=1))

    col1, col2 = st.columns([4, 1], gap="large")

    # ----------- MAIN ---------------------------------------------
    with col1:
        # KPI
        k1, k2, k3 = st.columns(3)
        k1.metric("Planificado (m3)", f"{df_desp['volumen_planificado'].sum():,.0f}")
        k2.metric("Despachado (m3)", f"{df_desp['volumen_despachado'].sum():,.0f}")
        diff = df_desp["volumen_despachado"].sum() - df_desp["volumen_planificado"].sum()
        k3.metric("Brecha (m3)", f"{diff:,.0f}", delta=f"{diff:,.0f}")

        # Gráfico único (el primer gráfico duplicado fue eliminado)
        fig_desp = px.bar(
            df_desp,
            x="fecha",
            y=["volumen_planificado", "volumen_despachado"],
            barmode="group",
            title="Despachos vs Planificados en el tiempo",
            template=PLOTLY_TEMPLATE,
        )
        st.plotly_chart(fig_desp, use_container_width=True)

    # -------------- FILTROS ---------------------------------------
    with col2:
        with st.expander("🎛️ Filtros", expanded=False):
            destinos = sorted(df_desp["codigo_destino"].unique())
            dest_sel = st.multiselect(
                "Destino", destinos, default=destinos, key="destinos_filter_desp"
            )
            df_desp = df_desp[df_desp["codigo_destino"].isin(dest_sel)]

# 4. Stock de Predios ----------------------------------------------------
if pagina == "🌲 Stock de Predios":
    st.title("🌲 Stock de Predios")

    df_stock = load_table("stock_predios")  # Asegúrate que exista esta vista
    df_stock["fecha"] = pd.to_datetime(df_stock["fecha"])

    col1, col2 = st.columns([4, 1], gap="large")

    with col1:
        fig_stock = px.area(
            df_stock,
            x="fecha",
            y="volumen_stock",
            color="codigo_predio",
            title="Evolución Stock por Predio",
            template=PLOTLY_TEMPLATE,
        )
        st.plotly_chart(fig_stock, use_container_width=True)

    with col2:
        with st.expander("🎛️ Filtros", expanded=False):
            predios = sorted(df_stock["codigo_predio"].unique())
            pred_sel = st.multiselect(
                "Predio", predios, default=predios, key="predio_filter_stock"
            )
            df_stock = df_stock[df_stock["codigo_predio"].isin(pred_sel)]

# 5. Visión Corporativa --------------------------------------------------
if pagina == "🔍 Visión Corporativa":
    st.title("🔍 Visión Corporativa – KPIs Ejecutivos")

    cumplimiento_prod, cumplimiento_desp, brecha_total = fetch_kpis()

    col1, col2, col3 = st.columns(3)
    col1.metric("Cumplimiento Producción (%)", f"{cumplimiento_prod:.1f}%")
    col2.metric("Cumplimiento Despachos (%)", f"{cumplimiento_desp:.1f}%")
    col3.metric("Brecha Total (m3)", f"{brecha_total:,.0f}")

    # Indicador semáforo global
    st.markdown("### Semáforo Global")
    status_color = "🟢" if cumplimiento_prod >= 95 and cumplimiento_desp >= 95 else "🟡" if cumplimiento_prod >= 90 else "🔴"
    st.subheader(f"{status_color} Cumplimiento corporativo")

    # Brecha timelines
    df_desp = load_table("comparativa_despachos")
    df_desp["fecha"] = pd.to_datetime(dict(year=df_desp["anio"], month=df_desp["mes"], day=1))
    df_line = (
        df_desp.groupby("fecha")[["volumen_planificado", "volumen_despachado"]]
        .sum()
        .reset_index()
    )
    fig_line = px.line(
        df_line,
        x="fecha",
        y=["volumen_planificado", "volumen_despachado"],
        title="Planificado vs Despachado (línea histórica)",
        template=PLOTLY_TEMPLATE,
    )
    st.plotly_chart(fig_line, use_container_width=True)

# -------------------------- FOOTER -------------------------------------------

st.caption("© 2025 ARAUCO – Tronix Analytics Dashboard • Última actualización: " + datetime.now().strftime("%d-%m-%Y %H:%M"))

