
import streamlit as st
import requests
import uuid
import pandas as pd
import base64
import streamlit.components.v1 as components  # ← NUEVO

# Configuración de la página
st.set_page_config(page_title="Agente Tronix", layout="wide", page_icon="🤖")
st.markdown("""
    <style>
    .stChatMessage {margin-bottom: 1.5rem;}
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Selector de módulo principal
st.sidebar.title("Menú Principal")
modo = st.sidebar.radio("Selecciona una vista:", [
    "Agente Tronix",
    "📊 Comparativa Producción vs Teams"
])

if modo == "Agente Tronix":
    # Inicializar historial de conversación y sesión
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    st.title("🤖 Agente Tronix")
    from supabase_client import get_client
    import plotly.express as px
    st.markdown("Bienvenido al panel de interacción con tu agente automatizado Tronix. Utiliza el campo inferior para enviar mensajes.")

    # 🚀 Dashboard predictivo integrado
    st.subheader("📊 Panel Predictivo Tronix")
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

    # Funcion pro para mostrar cualquier respuesta
    def render_agent_response(resp):
        if isinstance(resp, str):
            import re
            match = re.search(r"!\\[.*?\\]\\((https://[^\\s\\)]+grafico_id=[^\\s\\)]+)\\)", resp)
            if match:
                url = match.group(1).strip()
                texto_limpio = re.sub(r"!\\[.*?\\]\\((https://[^\\s\\)]+grafico_id=[^\\s\\)]+)\\)", "", resp).strip()
                return f'''{texto_limpio}<br><br><iframe src="{url}" height="620" width="100%" frameborder="0" allowfullscreen></iframe>'''

            if resp.startswith("http") and "?grafico_id=" in resp:
                return f'''<iframe src="{resp.strip()}" height="620" width="100%" frameborder="0" allowfullscreen></iframe>'''

            if resp.startswith("http"):
                return f"[{resp}]({resp})"

            return resp

        if isinstance(resp, list):
            rendered = ""
            for idx, item in enumerate(resp):
                rendered += f"**{idx+1}.** {render_agent_response(item)}\n\n"
            return rendered

        if isinstance(resp, dict):
            rendered = ""
            if "table" in resp and isinstance(resp["table"], (list, dict)):
                try:
                    df = pd.DataFrame(resp["table"])
                    rendered += "#### Tabla de resultados\n"
                    rendered += df.to_markdown(index=False)
                except Exception:
                    rendered += str(resp["table"])
            elif "image" in resp:
                try:
                    img = resp["image"]
                    if not img.startswith("data:image"):
                        img = f"data:image/png;base64,{img}"
                    st.image(img)
                    rendered += ""
                except Exception:
                    rendered += "(No se pudo renderizar imagen)"
            if "text" in resp:
                rendered += f"\n\n{resp['text']}"
            for k, v in resp.items():
                if k not in {"table", "image", "text"}:
                    rendered += f"\n**{k.capitalize()}:** {render_agent_response(v)}"
            if rendered.strip() == "":
                rendered = str(resp)
            return rendered

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
                    json={"message": prompt, "sessionId": st.session_state.session_id}
                )
                res.raise_for_status()
                json_response = res.json()
                if isinstance(json_response, dict) and "response" in json_response:
                    original_reply = json_response["response"]
                else:
                    original_reply = json_response
                rendered_reply = render_agent_response(original_reply)
            except Exception as e:
                reply = f"⚠️ Error al contactar con el agente: {e}"

        st.session_state.chat_history.append({"role": "assistant", "original": original_reply, "rendered": rendered_reply})
        with st.chat_message("assistant"):
            st.markdown(rendered_reply, unsafe_allow_html=True)

    st.sidebar.title("Opciones")
    if st.sidebar.button("🔄 Reiniciar conversación"):
        st.session_state.chat_history = []
        st.session_state.session_id = str(uuid.uuid4())
        st.experimental_rerun()

elif modo == "📊 Comparativa Producción vs Teams":
    st.title("📊 Comparativa Producción vs Teams")
    st.markdown("Visualización interactiva con filtros…")

    components.iframe(
        src="https://graficos2-production.up.railway.app/?view=comparativa",
        height=760, width=1200
    )

    st.markdown("---")
    st.subheader("💬 Pregúntale a Tronix sobre este gráfico")

    # Capturamos la selección de filtros (de tu propio código)
    # Por ejemplo asumimos que tienes zona_sel, fecha_sel, calidad_sel definidos
    pregunta = st.text_input(
        "¿Qué quieres saber?",
        placeholder="Escribe algo como: '¿Qué pasa si aumentan los despachos un 25%?'"
    )

    if st.button("Enviar a Tronix"):
        # Construimos el prompt con contexto
        prompt = (
            f"Basado en la comparativa de Producción vs Proyección para "
            f"zona {zona_sel}, calidad {calidad_sel} y fecha {fecha_sel}, "
            f"responde: {pregunta}"
        )
        with st.spinner("Consultando a Tronix…"):
            res = requests.post(
                "https://n8n-production-993e.up.railway.app/webhook/01103618-3424-4455-bde6-aa8d295157b2",
                json={"message": prompt, "sessionId": st.session_state.session_id}
            )
            data = res.json()
            # Asumiendo que tu render_agent_response sigue disponible
            st.markdown(render_agent_response(data.get("response", data)), unsafe_allow_html=True)


