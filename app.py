
import streamlit as st
import requests
import uuid
import pandas as pd
import base64

# Configuración de la página
st.set_page_config(page_title="Agente Tronix", layout="wide", page_icon="🤖")
st.markdown("""
    <style>
    .stChatMessage {margin-bottom: 1.5rem;}
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Inicializar historial de conversación y sesión
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

st.title("🤖 Agente Tronix")
st.markdown("Bienvenido al panel de interacción con tu agente automatizado Tronix. Utiliza el campo inferior para enviar mensajes.")

# Función pro para mostrar cualquier respuesta
def render_agent_response(resp):
    # String
    if isinstance(resp, str):
        # Si es base64 de imagen
        if resp.startswith("data:image") or resp.startswith("/9j/"):
            try:
                img_data = resp
                if resp.startswith("/9j/"):  # Base64 "pura"
                    img_data = f"data:image/png;base64,{resp}"
                st.image(img_data)
                return ""
            except Exception:
                return resp
        # Si es URL, lo pone como enlace
        if resp.startswith("http"):
            return f"[{resp}]({resp})"
        return resp

    # Lista
    if isinstance(resp, list):
        rendered = ""
        for idx, item in enumerate(resp):
            rendered += f"**{idx+1}.** {render_agent_response(item)}\n\n"
        return rendered

    # Diccionario
    if isinstance(resp, dict):
        rendered = ""
        # Si trae tabla en formato estándar
        if "table" in resp and isinstance(resp["table"], (list, dict)):
            try:
                df = pd.DataFrame(resp["table"])
                rendered += "#### Tabla de resultados\n"
                rendered += df.to_markdown(index=False)
            except Exception:
                rendered += str(resp["table"])
        # Si trae imagen en base64
        elif "image" in resp:
            try:
                img = resp["image"]
                if not img.startswith("data:image"):
                    img = f"data:image/png;base64,{img}"
                st.image(img)
                rendered += ""
            except Exception:
                rendered += "(No se pudo renderizar imagen)"
        # Texto
        if "text" in resp:
            rendered += f"\n\n{resp['text']}"
        # Otros campos
        for k, v in resp.items():
            if k not in {"table", "image", "text"}:
                rendered += f"\n**{k.capitalize()}:** {render_agent_response(v)}"
        if rendered.strip() == "":
            rendered = str(resp)
        return rendered

    # Otros tipos
    return str(resp)

# Mostrar historial de conversación
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Captura de entrada del usuario
prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    # Registrar mensaje del usuario
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
            # Si el json tiene 'response', úsalo; sino, todo el json
            reply = render_agent_response(json_response.get("response", json_response))
        except Exception as e:
            reply = f"⚠️ Error al contactar con el agente: {e}"

    # Mostrar respuesta del agente
    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply, unsafe_allow_html=True)

# Panel lateral con opciones
st.sidebar.title("Opciones")
if st.sidebar.button("🔄 Reiniciar conversación"):
    st.session_state.chat_history = []
    st.session_state.session_id = str(uuid.uuid4())
    st.experimental_rerun()
