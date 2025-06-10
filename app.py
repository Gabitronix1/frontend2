
import streamlit as st
import requests
import uuid
import pandas as pd
import base64
import streamlit.components.v1 as components
from supabase_client import get_client
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Agente Tronix", layout="wide", page_icon="🤖")
st.markdown("""
    <style>
    .stChatMessage {margin-bottom: 1.5rem;}
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Inicializar sesión
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Selector de vistas
st.sidebar.title("📁 Navegación")
pagina = st.sidebar.selectbox(
    "Selecciona una vista",
    [
        "🏠 Inicio",
        "📊 Comparativa Producción vs Proyección - Teams",
        "🚛 Panel Despachos",
        "🪵 Stock por Predios y Calidad",
        "💬 Chat con Tronix"
    ]
)

# =============== INICIO ===============

if pagina == "🏠 Inicio":
    st.title("🌲 Bienvenido al Portal de Tronix - Forestal Arauco")
    st.markdown("### 🤖 Inteligencia para el manejo y monitoreo de producción forestal")
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Arauco_logo.svg/2560px-Arauco_logo.svg.png", width=250)

    st.markdown("""
    ---
    #### 📋 ¿Cómo usar este panel?
    En el menú lateral izquierdo podrás acceder a los distintos dashboards que ofrece **Tronix**, organizados así:

    - **📊 Comparativa Producción vs Proyección - Teams**: Visualiza el desempeño de producción vs lo proyectado por equipo y calidad.
    - **🚛 Panel Despachos**: Compara los despachos reales contra lo planificado por destino, especie, largo y calidad.
    - **🪵 Stock por Predios y Calidad**: Monitorea el stock actual en los predios con filtros interactivos.
    - **💬 Chat con Tronix**: Pregúntale directamente al agente IA usando lenguaje natural.

    ---
    """, unsafe_allow_html=True)

    st.title("🤖 Agente Tronix")
    st.markdown("Bienvenido al panel de interacción con tu agente automatizado Tronix.")



# =============== DASHBOARD 1 ===============
if pagina == "📊 Comparativa Producción vs Proyección - Teams":
    st.title("📊 Comparativa Producción vs Proyección - Teams")

    @st.cache_data
    def cargar_datos():
        supabase = get_client()
        data = supabase.table("comparativa_produccion_teams").select("*").execute()
        return pd.DataFrame(data.data)

    df = cargar_datos()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["calidad"] = df["calidad"].str.upper().str.strip()
    df["zona"] = df["zona"].str.upper().str.strip()

    # Filtrar desde la primera fecha con volumen proyectado > 0
    fecha_inicio = df[df["volumen_proyectado"] > 0]["fecha"].min()
    df = df[df["fecha"] >= fecha_inicio]

    # Filtros
    st.sidebar.markdown("### 🎛️ Filtros Comparativa")
    calidades = sorted(df["calidad"].dropna().unique())
    zonas = sorted(df["zona"].dropna().unique())
    fechas = sorted(df["fecha"].dropna().unique())

    calidad_sel = st.sidebar.multiselect("Calidad", options=calidades, default=calidades)
    zona_sel = st.sidebar.multiselect("Zona", options=zonas, default=zonas)
    fecha_sel = st.sidebar.date_input("Días", value=[fechas[0], fechas[-1]])

    df = df[
        (df["calidad"].isin(calidad_sel)) &
        (df["zona"].isin(zona_sel)) &
        (df["fecha"] >= pd.to_datetime(fecha_sel[0])) &
        (df["fecha"] <= pd.to_datetime(fecha_sel[1]))
    ]

    # Resumen general
    produccion = df["produccion_total"].sum()
    proyeccion = df["volumen_proyectado"].sum()
    diferencia = produccion - proyeccion
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Producción Total", f"{produccion:,.0f} m³")
    col2.metric("🧮 Proyección Total", f"{proyeccion:,.0f} m³")
    col3.metric("📉 Diferencia", f"{diferencia:,.0f} m³")

    # Gráficos
    st.subheader("Volumen Total por Team")
    graf1 = df.groupby("team")[["produccion_total", "volumen_proyectado"]].sum().reset_index()
    fig1 = px.bar(graf1, x="team", y=["produccion_total", "volumen_proyectado"], barmode="group")
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Volumen Total por Fecha")
    graf2 = df.groupby("fecha")[["produccion_total", "volumen_proyectado"]].sum().reset_index()
    fig2 = px.line(graf2, x="fecha", y=["produccion_total", "volumen_proyectado"], markers=True)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Volumen Total por Calidad")
    graf3 = df.groupby("calidad")[["produccion_total", "volumen_proyectado"]].sum().reset_index()
    fig3 = px.bar(graf3, x="calidad", y=["produccion_total", "volumen_proyectado"], barmode="group")
    st.plotly_chart(fig3, use_container_width=True)

if pagina == "📊 Comparativa Producción vs Proyección - Teams":
    st.title("📊 Comparativa Producción vs Proyección - Teams")

    @st.cache_data
    def cargar_datos():
        supabase = get_client()
        data = supabase.table("comparativa_produccion_teams").select("*").execute()
        return pd.DataFrame(data.data)

    df = cargar_datos()

    df["fecha"] = pd.to_datetime(df["fecha"])
    df["team"] = df["team"].str.upper().str.strip()
    df["calidad"] = df["calidad"].str.upper().str.strip()
    df["zona"] = df["zona"].str.upper().str.strip()
    df["nombre_origen"] = df["nombre_origen"].str.upper().str.strip()

    # Filtros
    st.sidebar.markdown("### 🎛️ Filtros Comparativa Team")
    teams = sorted(df["team"].dropna().unique())
    calidades = sorted(df["calidad"].dropna().unique())
    zonas = sorted(df["zona"].dropna().unique())
    predios = sorted(df["nombre_origen"].dropna().unique())
    fechas = sorted(df["fecha"].dropna().unique())

    team_sel = st.sidebar.multiselect("Team", options=teams, default=teams)
    calidad_sel = st.sidebar.multiselect("Calidad", options=calidades, default=calidades)
    zona_sel = st.sidebar.multiselect("Zona", options=zonas, default=zonas)
    predio_sel = st.sidebar.multiselect("Predio", options=predios, default=predios)
    fecha_sel = st.sidebar.multiselect("Fecha", options=fechas, default=fechas)

    df = df[
        (df["team"].isin(team_sel)) &
        (df["calidad"].isin(calidad_sel)) &
        (df["zona"].isin(zona_sel)) &
        (df["nombre_origen"].isin(predio_sel)) &
        (df["fecha"].isin(fecha_sel))
    ]

    st.info(f"📅 Mostrando datos desde el **{df['fecha'].min().date()}** hasta **{df['fecha'].max().date()}**")

    # 1. Volumen por Team
    st.subheader("Volumen Total por Team")
    graf1 = df.groupby("team")[["produccion_total", "volumen_proyectado"]].sum().reset_index()
    fig1 = px.bar(graf1, x="team", y=["produccion_total", "volumen_proyectado"], barmode="group")
    st.plotly_chart(fig1, use_container_width=True)

    # 2. Volumen por Fecha
    st.subheader("Volumen Total por Fecha")
    graf2 = df.groupby("fecha")[["produccion_total", "volumen_proyectado"]].sum().reset_index()
    fig2 = px.line(graf2, x="fecha", y=["produccion_total", "volumen_proyectado"], markers=True)
    st.plotly_chart(fig2, use_container_width=True)

    # 3. Volumen por Calidad
    st.subheader("Volumen Total por Calidad")
    graf3 = df.groupby("calidad")[["produccion_total", "volumen_proyectado"]].sum().reset_index()
    fig3 = px.bar(graf3, x="calidad", y=["produccion_total", "volumen_proyectado"], barmode="group")
    st.plotly_chart(fig3, use_container_width=True)

    # 4. Resumen Total
    st.subheader("Resumen General")
    produccion = df["produccion_total"].sum()
    proyeccion = df["volumen_proyectado"].sum()
    diferencia = produccion - proyeccion
    st.metric("📦 Producción Total", f"{produccion:,.0f} m³")
    st.metric("📦 Proyección Total", f"{proyeccion:,.0f} m³")
    st.metric("📉 Diferencia", f"{diferencia:,.0f} m³")

if pagina == "📊 Comparativa Producción vs Proyección - Teams":
    st.title("📊 Comparativa Producción vs Proyección - Teams")
    @st.cache_data
    def cargar_datos():
        supabase = get_client()
        data = supabase.table("comparativa_produccion_teams").select("*").execute()
        return pd.DataFrame(data.data)
    df = cargar_datos()
    df["calidad"] = df["calidad"].str.upper().str.strip()
    df["team"] = df["team"].str.upper().str.strip()
    fecha_inicio = df[df["volumen_proyectado"] > 0]["fecha"].min()
    df = df[df["fecha"] >= fecha_inicio]
    st.info(f"📅 Mostrando datos desde el **{fecha_inicio}**")
    st.subheader("Volumen Total por Team")
    graf1 = df.groupby("team")[["produccion_total", "volumen_proyectado"]].sum().reset_index()
    fig1 = px.bar(graf1, x="team", y=["produccion_total", "volumen_proyectado"], barmode="group")
    st.plotly_chart(fig1, use_container_width=True)
    st.subheader("Volumen Total por Fecha")
    graf2 = df.groupby("fecha")[["produccion_total", "volumen_proyectado"]].sum().reset_index()
    fig2 = px.line(graf2, x="fecha", y=["produccion_total", "volumen_proyectado"], markers=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.subheader("Volumen Total por Calidad")
    graf3 = df.groupby("calidad")[["produccion_total", "volumen_proyectado"]].sum().reset_index()
    fig3 = px.bar(graf3, x="calidad", y=["produccion_total", "volumen_proyectado"], barmode="group")
    st.plotly_chart(fig3, use_container_width=True)
    st.subheader("Resumen General")
    st.metric("📦 Producción Total", f"{df['produccion_total'].sum():,.0f} m³")
    st.metric("📦 Proyección Total", f"{df['volumen_proyectado'].sum():,.0f} m³")
    st.metric("📉 Diferencia", f"{df['produccion_total'].sum() - df['volumen_proyectado'].sum():,.0f} m³")


# =============== DASHBOARD 2 ===============
if pagina == "🚛 Panel Despachos":
    st.title("🚛 Panel Despachos")

    @st.cache_data
    def cargar_despachos():
        data = get_client().table("comparativa_despachos").select("*").execute().data
        return pd.DataFrame(data)

    df = cargar_despachos()
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce")
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce")
    df["volumen_planificado"] = pd.to_numeric(df["volumen_planificado"], errors="coerce")
    df["volumen_despachado"] = pd.to_numeric(df["volumen_despachado"], errors="coerce")
    df["diferencia_volumen"] = pd.to_numeric(df["diferencia_volumen"], errors="coerce")
    df["fecha"] = pd.to_datetime(dict(year=df["anio"], month=df["mes"], day=1))

    # Filtros interactivos
    st.sidebar.markdown("### 🎛️ Filtros de Despachos")
    zonas = sorted(df["codigo_destino"].dropna().unique())
    especies = sorted(df["especie"].dropna().unique())
    calidades = sorted(df["calidad"].dropna().unique())
    largos = sorted(df["largo"].dropna().unique())
    

    zona_sel = st.sidebar.multiselect("Destino", options=zonas, default=zonas)
    especie_sel = st.sidebar.multiselect("Especie", options=especies, default=especies)
    calidad_sel = st.sidebar.multiselect("Calidad", options=calidades, default=calidades)
    largo_sel = st.sidebar.multiselect("Largo", options=largos, default=largos)
    

    df_filtrado = df[
        (df["codigo_destino"].isin(zona_sel)) &
        (df["especie"].isin(especie_sel)) &
        (df["calidad"].isin(calidad_sel)) &
        (df["largo"].isin(largo_sel))
    ]

    # Métricas generales
    volumen_planificado = df_filtrado["volumen_planificado"].sum()
    volumen_despachado = df_filtrado["volumen_despachado"].sum()
    diferencia = volumen_despachado - volumen_planificado

    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Planificado (m³)", f"{volumen_planificado:,.0f}")
    col2.metric("🚛 Despachado (m³)", f"{volumen_despachado:,.0f}")
    col3.metric("📉 Diferencia", f"{diferencia:,.0f}")

    # Gráfico 1: Evolución mensual
    # (Gráfico de evolución mensual eliminado)
    graf1 = df_filtrado.groupby("fecha")[["volumen_planificado", "volumen_despachado"]].sum().reset_index()
    fig1 = px.line(graf1, x="fecha", y=["volumen_planificado", "volumen_despachado"], markers=True)
    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico 2: Por especie
    st.subheader("🌲 Comparativa por Especie")
    graf2 = df_filtrado.groupby("especie")[["volumen_planificado", "volumen_despachado"]].sum().reset_index()
    fig2 = px.bar(graf2, x="especie", y=["volumen_planificado", "volumen_despachado"], barmode="group")
    st.plotly_chart(fig2, use_container_width=True)

    # Gráfico 3: Por largo
    st.subheader("📏 Comparativa por Largo")
    graf3 = df_filtrado.groupby("largo")[["volumen_planificado", "volumen_despachado"]].sum().reset_index()
    fig3 = px.bar(graf3, x="largo", y=["volumen_planificado", "volumen_despachado"], barmode="group")
    st.plotly_chart(fig3, use_container_width=True)

    # Gráfico 4: Por calidad
    st.subheader("🏷️ Comparativa por Calidad")
    graf4 = df_filtrado.groupby("calidad")[["volumen_planificado", "volumen_despachado"]].sum().reset_index()
    fig4 = px.bar(graf4, x="calidad", y=["volumen_planificado", "volumen_despachado"], barmode="group")
    st.plotly_chart(fig4, use_container_width=True)

    # Gráfico 5: Por destino
    st.subheader("🌍 Comparativa por Destino")
    graf5 = df_filtrado.groupby("codigo_destino")[["volumen_planificado", "volumen_despachado"]].sum().reset_index()
    fig5 = px.bar(graf5, x="codigo_destino", y=["volumen_planificado", "volumen_despachado"], barmode="group")
    st.plotly_chart(fig5, use_container_width=True)

if pagina == "🚛 Panel Despachos":
    st.title("🚛 Panel Despachos")
    supabase = get_client()
    data = supabase.table("comparativa_despachos").select("*").execute().data
    df = pd.DataFrame(data)
    if not df.empty:
        volumen_planificado = df["volumen_planificado"].sum()
        volumen_despachado = df["volumen_despachado"].sum()
        diferencia = volumen_despachado - volumen_planificado
        col1, col2, col3 = st.columns(3)
        col1.metric("✅ Planificado (m³)", f"{volumen_planificado:,.0f}")
        col2.metric("🚛 Despachado (m³)", f"{volumen_despachado:,.0f}")
        col3.metric("📉 Diferencia", f"{diferencia:,.0f}")
        df_zona = df.groupby("codigo_destino")[["volumen_planificado", "volumen_despachado"]].sum().reset_index()
        fig = px.bar(df_zona, x="codigo_destino", y=["volumen_planificado", "volumen_despachado"],
                     barmode="group", title="Volumen por Zona")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos para mostrar el panel.")

# =============== DASHBOARD 3 ===============
if pagina == "🪵 Stock por Predios y Calidad":
    st.title("🪵 Stock en Predios por Zona, Calidad y Largo")
    @st.cache_data
    def cargar_stock_predios():
        data = get_client().table("vista_dashboard_stock_predios_detallado").select("*").execute().data
        return pd.DataFrame(data)
    df_stock = cargar_stock_predios()
    df_stock["volumen_total"] = pd.to_numeric(df_stock["volumen_total"], errors="coerce")
    df_stock["fecha_stock"] = pd.to_datetime(df_stock["fecha_stock"])
    st.sidebar.markdown("### 📅 Filtros de Stock")
    zona_filtro = st.sidebar.multiselect("Zona", df_stock["zona"].unique(), default=list(df_stock["zona"].unique()))
    calidad_filtro = st.sidebar.multiselect("Calidad", df_stock["calidad"].unique(), default=list(df_stock["calidad"].unique()))
    fecha_filtro = st.sidebar.date_input("Fecha stock", value=df_stock["fecha_stock"].max())
    df_filtrado = df_stock[
        (df_stock["zona"].isin(zona_filtro)) &
        (df_stock["calidad"].isin(calidad_filtro)) &
        (df_stock["fecha_stock"] == pd.to_datetime(fecha_filtro))
    ]
    st.subheader("🔹 Stock total por Zona")
    fig1 = px.bar(df_filtrado.groupby("zona", as_index=False)["volumen_total"].sum(),
                  x="zona", y="volumen_total", title="Volumen total por zona")
    st.plotly_chart(fig1, use_container_width=True)
    st.subheader("🔹 Stock por Calidad en cada Zona")
    fig2 = px.bar(df_filtrado, x="zona", y="volumen_total", color="calidad",
                  barmode="group", title="Volumen por calidad y zona")
    st.plotly_chart(fig2, use_container_width=True)
    st.subheader("🔹 Distribución de Largos por Calidad")
    fig3 = px.histogram(df_filtrado, x="largo", color="calidad", barmode="group",
                        title="Frecuencia de largos por calidad")
    st.plotly_chart(fig3, use_container_width=True)
    st.subheader("🔹 Stock total por Predio")
    fig4 = px.bar(df_filtrado.groupby("nombre_origen", as_index=False)["volumen_total"].sum().sort_values(by="volumen_total", ascending=False),
                  x="nombre_origen", y="volumen_total", title="Stock total por predio")
    st.plotly_chart(fig4, use_container_width=True)
    # Resumen general
    vol_total = df_filtrado["volumen_total"].sum()
    predios_unicos = df_filtrado["nombre_origen"].nunique()
    largo_unico = df_filtrado["largo"].nunique()

    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Volumen Total", f"{vol_total:,.0f} m³")
    col2.metric("🌲 Predios únicos", predios_unicos)
    col3.metric("📏 Largos únicos", largo_unico)

# =============== CHAT ===============
if pagina == "💬 Chat con Tronix":
    st.title("💬 Chat con Tronix")
    def render_agent_response(resp):
        if isinstance(resp, str):
            import re
            match = re.search(r"!\[.*?\]\((https://[^\s\)]+grafico_id=[^\s\)]+)\)", resp)
            if match:
                url = match.group(1).strip()
                texto_limpio = re.sub(r"!\[.*?\]\((https://[^\s\)]+grafico_id=[^\s\)]+)\)", "", resp).strip()
                return f'''{texto_limpio}<br><br><iframe src="{url}" height="620" width="100%" frameborder="0" allowfullscreen></iframe>'''
            if resp.startswith("http") and "?grafico_id=" in resp:
                return f'''<iframe src="{resp.strip()}" height="620" width="100%" frameborder="0" allowfullscreen></iframe>'''
            if resp.startswith("http"):
                return f"[{resp}]({resp})"
            return resp
        if isinstance(resp, list):
            return "\n\n".join([f"**{i+1}.** {render_agent_response(item)}" for i, item in enumerate(resp)])
        if isinstance(resp, dict):
            rendered = ""
            if "table" in resp:
                try:
                    df = pd.DataFrame(resp["table"])
                    rendered += "#### Tabla de resultados\n" + df.to_markdown(index=False)
                except:
                    rendered += str(resp["table"])
            elif "image" in resp:
                try:
                    img = resp["image"]
                    if not img.startswith("data:image"):
                        img = f"data:image/png;base64,{img}"
                    st.image(img)
                except:
                    rendered += "(No se pudo renderizar imagen)"
            if "text" in resp:
                rendered += f"\n\n{resp['text']}"
            for k, v in resp.items():
                if k not in {"table", "image", "text"}:
                    rendered += f"\n**{k.capitalize()}:** {render_agent_response(v)}"
            return rendered or str(resp)
        return str(resp)

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            if "rendered" in msg:
                st.markdown(msg["rendered"], unsafe_allow_html=True)
            else:
                st.markdown(render_agent_response(msg["content"]), unsafe_allow_html=True)

    prompt = st.chat_input("Escribe tu mensaje aquí...")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.spinner("Procesando respuesta del agente Tronix..."):
            try:
                res = requests.post(
                    "https://n8n-production-993e.up.railway.app/webhook/01103618-3424-4455-bde6-aa8d295157b2",
                    json={
                        "message": prompt,
                        "sessionId": st.session_state.session_id
                    }
                )
                res.raise_for_status()
                json_response = res.json()
                original_reply = json_response["response"] if isinstance(json_response, dict) and "response" in json_response else json_response
                rendered_reply = render_agent_response(original_reply)
            except Exception as e:
                rendered_reply = f"⚠️ Error al contactar con el agente: {e}"
        st.session_state.chat_history.append({"role": "assistant", "original": original_reply, "rendered": rendered_reply})
        with st.chat_message("assistant"):
            st.markdown(rendered_reply, unsafe_allow_html=True)

    if st.sidebar.button("🔄 Reiniciar conversación"):
        st.session_state.chat_history = []
        st.session_state.session_id = str(uuid.uuid4())
        st.experimental_rerun()

