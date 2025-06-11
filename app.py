import streamlit as st
import requests
import uuid
import pandas as pd
from supabase_client import get_client
import plotly.express as px

# Configuración de la página y tema
st.set_page_config(page_title='Agente Tronix', layout='wide', page_icon='🤖')
# Paleta corporativa ARAUCO: verde institucional (#00563F) y gris (#7E7E7E)
px.defaults.color_discrete_sequence = ['#00563F', '#7E7E7E']
px.defaults.template = 'plotly_white'

# Estilos CSS inline para componentes Streamlit
st.markdown('''
<style>
:root { --primary-color: #00563F; --secondary-color: #7E7E7E; }
#MainMenu, footer, header { visibility: hidden; }
</style>
''', unsafe_allow_html=True)

# Inicializar sesión
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Navegación de vistas
tabs = [
    '🏠 Inicio',
    '📊 Comparativa Producción vs Proyección - Teams',
    '🚛 Panel Despachos',
    '🪵 Stock por Predios y Calidad',
    '🔍 Visión Corporativa',
    '💬 Chat con Tronix'
]
pagina = st.sidebar.selectbox('Selecciona una vista', tabs)

# Pestaña: Visión Corporativa
if pagina == '🔍 Visión Corporativa':
    st.title('🔍 Visión Corporativa')
    st.markdown('Resumen ejecutivo de todos los paneles')
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Producción Total (m³)', '0')
    c2.metric('Despachos Totales (m³)', '0')
    c3.metric('Stock Total (m³)', '0')
    c4.metric('Diferencia Total (m³)', '0')
    st.markdown('---')
    # Espacio para gráficos de resumen
    st.plotly_chart(px.bar(pd.DataFrame()), use_container_width=True)
    st.plotly_chart(px.line(pd.DataFrame()), use_container_width=True)

# Expander lateral para filtros en cada dashboard
def filtros_expander(fn):
    right, main = st.columns([1, 3])
    with right.expander('🎛️ Filtros', expanded=False):
        return fn()
    return None

# =============== DASHBOARD 1 ===============
if pagina == '📊 Comparativa Producción vs Proyección - Teams':
    st.title('📊 Comparativa Producción vs Proyección - Teams')
    @st.cache_data
    def cargar_datos():
        supabase = get_client()
        data = supabase.table('comparativa_produccion_teams').select('*').execute()
        return pd.DataFrame(data.data)
    df = cargar_datos()
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['calidad'] = df['calidad'].str.upper().str.strip()
    df['zona'] = df['zona'].str.upper().str.strip()

    # Definir filtros
    def filtros_teams():
        calidades = sorted(df['calidad'].unique())
        zonas = sorted(df['zona'].unique())
        calidad_sel = st.multiselect('Calidad', options=calidades, default=calidades, key='cal_1')
        zona_sel = st.multiselect('Zona', options=zonas, default=zonas, key='zon_1')
        fecha_sel = st.date_input('Fechas', value=[df['fecha'].min(), df['fecha'].max()], key='fec_1')
        return calidad_sel, zona_sel, fecha_sel

    res = filtros_expander(filtros_teams)
    if res:
        calidad_sel, zona_sel, fecha_sel = res
    else:
        calidad_sel, zona_sel, fecha_sel = df['calidad'].unique(), df['zona'].unique(), [df['fecha'].min(), df['fecha'].max()]
    df = df[(df['calidad'].isin(calidad_sel)) & (df['zona'].isin(zona_sel)) &
            (df['fecha'] >= pd.to_datetime(fecha_sel[0])) & (df['fecha'] <= pd.to_datetime(fecha_sel[1]))]

    # Métricas generales
    produccion = df['produccion_total'].sum()
    proyeccion = df['volumen_proyectado'].sum()
    diferencia = produccion - proyeccion
    c1, c2, c3 = st.columns(3)
    c1.metric('📦 Producción Total', f'{produccion:,.0f} m³')
    c2.metric('🧮 Proyección Total', f'{proyeccion:,.0f} m³')
    c3.metric('📉 Diferencia', f'{diferencia:,.0f} m³')

    # Gráficos
    st.subheader('Volumen Total por Team')
    graf1 = df.groupby('team')[['produccion_total','volumen_proyectado']].sum().reset_index()
    fig1 = px.bar(graf1, x='team', y=['produccion_total','volumen_proyectado'], barmode='group')
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader('Volumen Total por Fecha')
    graf2 = df.groupby('fecha')[['produccion_total','volumen_proyectado']].sum().reset_index()
    fig2 = px.line(graf2, x='fecha', y=['produccion_total','volumen_proyectado'], markers=True)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader('Volumen Total por Calidad')
    graf3 = df.groupby('calidad')[['produccion_total','volumen_proyectado']].sum().reset_index()
    fig3 = px.bar(graf3, x='calidad', y=['produccion_total','volumen_proyectado'], barmode='group')
    st.plotly_chart(fig3, use_container_width=True)

# =============== DASHBOARD 2 ===============
if pagina == '🚛 Panel Despachos':
    st.title('🚛 Panel Despachos')
    @st.cache_data
    def cargar_despachos():
        data = get_client().table('comparativa_despachos').select('*').execute().data
        return pd.DataFrame(data)
    df = cargar_despachos()
    df['anio'] = pd.to_numeric(df['anio'], errors='coerce')
    df['mes'] = pd.to_numeric(df['mes'], errors='coerce')
    df['volumen_planificado'] = pd.to_numeric(df['volumen_planificado'], errors='coerce')
    df['volumen_despachado'] = pd.to_numeric(df['volumen_despachado'], errors='coerce')
    df['diferencia_volumen'] = pd.to_numeric(df['diferencia_volumen'], errors='coerce')
    df['fecha'] = pd.to_datetime(dict(year=df['anio'], month=df['mes'], day=1))

    # Filtros
    def filtros_despachos():
        zonas = sorted(df['codigo_destino'].unique())
        especies = sorted(df['especie'].unique())
        calidades = sorted(df['calidad'].unique())
        largos = sorted(df['largo'].unique())
        zona_sel = st.multiselect('Destino', options=zonas, default=zonas, key='des_z')
        especie_sel = st.multiselect('Especie', options=especies, default=especies, key='des_e')
        calidad_sel = st.multiselect('Calidad', options=calidades, default=calidades, key='des_c')
        largo_sel = st.multiselect('Largo', options=largos, default=largos, key='des_l')
        return zona_sel, especie_sel, calidad_sel, largo_sel

    res = filtros_expander(filtros_despachos)
    if res:
        zona_sel, especie_sel, calidad_sel, largo_sel = res
    else:
        zona_sel, especie_sel, calidad_sel, largo_sel = df['codigo_destino'].unique(), df['especie'].unique(), df['calidad'].unique(), df['largo'].unique()
    df_filtrado = df[(df['codigo_destino'].isin(zona_sel)) &
                     (df['especie'].isin(especie_sel)) &
                     (df['calidad'].isin(calidad_sel)) &
                     (df['largo'].isin(largo_sel))]

    # Métricas generales
    vol_plan = df_filtrado['volumen_planificado'].sum()
    vol_des = df_filtrado['volumen_despachado'].sum()
    diff = vol_des - vol_plan
    m1, m2, m3 = st.columns(3)
    m1.metric('✅ Planificado (m³)', f'{vol_plan:,.0f}')
    m2.metric('🚛 Despachado (m³)', f'{vol_des:,.0f}')
    m3.metric('📉 Diferencia', f'{diff:,.0f}')

    # Eliminado gráfico de evolución mensual duplicado
    st.subheader('🌲 Comparativa por Especie')
    graf2 = df_filtrado.groupby('especie')[['volumen_planificado','volumen_despachado']].sum().reset_index()
    fig2 = px.bar(graf2, x='especie', y=['volumen_planificado','volumen_despachado'], barmode='group')
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader('📏 Comparativa por Largo')
    graf3 = df_filtrado.groupby('largo')[['volumen_planificado','volumen_despachado']].sum().reset_index()
    fig3 = px.bar(graf3, x='largo', y=['volumen_planificado','volumen_despachado'], barmode='group')
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader('🏷️ Comparativa por Calidad')
    graf4 = df_filtrado.groupby('calidad')[['volumen_planificado','volumen_despachado']].sum().reset_index()
    fig4 = px.bar(graf4, x='calidad', y=['volumen_planificado','volumen_despachado'], barmode='group')
    st.plotly_chart(fig4, use_container_width=True)

    st.subheader('🌍 Comparativa por Destino')
    graf5 = df_filtrado.groupby('codigo_destino')[['volumen_planificado','volumen_despachado']].sum().reset_index()
    fig5 = px.bar(graf5, x='codigo_destino', y=['volumen_planificado','volumen_despachado'], barmode='group')
    st.plotly_chart(fig5, use_container_width=True)

# =============== DASHBOARD 3 ===============
if pagina == '🪵 Stock por Predios y Calidad':
    st.title('🪵 Stock en Predios por Zona, Calidad y Largo')
    @st.cache_data
    def cargar_stock_predios():
        data = get_client().table('vista_dashboard_stock_predios_detallado').select('*').execute().data
        return pd.DataFrame(data)
    df_stock = cargar_stock_predios()
    df_stock['volumen_total'] = pd.to_numeric(df_stock['volumen_total'], errors='coerce')
    df_stock['fecha_stock'] = pd.to_datetime(df_stock['fecha_stock'])

    def filtros_stock():
        zonas = sorted(df_stock['zona'].dropna().unique())
        calidades = sorted(df_stock['calidad'].dropna().unique())
        fecha_def = df_stock['fecha_stock'].max()
        zona_sel = st.multiselect('Zona', options=zonas, default=zonas, key='sto_z')
        calidad_sel = st.multiselect('Calidad', options=calidades, default=calidades, key='sto_c')
        fecha_sel = st.date_input('Fecha stock', value=fecha_def, key='sto_f')
        return zona_sel, calidad_sel, fecha_sel

    res = filtros_expander(filtros_stock)
    if res:
        zona_filtrado, calidad_filtrado, fecha_filtrado = res
    else:
        zona_filtrado = df_stock['zona'].dropna().unique()
        calidad_filtrado = df_stock['calidad'].dropna().unique()
        fecha_filtrado = df_stock['fecha_stock'].max()
    df_filtrado = df_stock[(df_stock['zona'].isin(zona_filtrado)) & (df_stock['calidad'].isin(calidad_filtrado)) & (df_stock['fecha_stock'] == pd.to_datetime(fecha_filtrado))]

    st.subheader('🔹 Stock total por Zona')
    fig1 = px.bar(df_filtrado.groupby('zona', as_index=False)['volumen_total'].sum(), x='zona', y='volumen_total')
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader('🔹 Stock por Calidad')
    fig2 = px.bar(df_filtrado, x='zona', y='volumen_total', color='calidad', barmode='group')
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader('🔹 Distribución de Largos')
    fig3 = px.histogram(df_filtrado, x='largo', color='calidad', barmode='group')
    st.plotly_chart(fig3, use_container_width=True)

    # Métricas de stock
    total = df_filtrado['volumen_total'].sum()
    unicos = df_filtrado['nombre_origen'].nunique()
    largos_unicos = df_filtrado['largo'].nunique()
    m1, m2, m3 = st.columns(3)
    m1.metric('📦 Volumen Total', f'{total:,.0f} m³')
    m2.metric('🌲 Predios únicos', unicos)
    m3.metric('📏 Largos únicos', largos_unicos)

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



