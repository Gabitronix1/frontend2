
import streamlit as st
import streamlit.components.v1 as components
import requests
import uuid
import pandas as pd
import base64
import re

# ===== CONFIGURACIÓN GENERAL =====
st.set_page_config(page_title="Agente Tronix", layout="wide", page_icon="🌲")

# ===== ESTILOS PERSONALIZADOS (Arauco) =====
st.markdown("""
    <style>
        body {
            background-color: #f0f4f3;
        }
        .stApp {
            font-family: 'Segoe UI', sans-serif;
        }
        .stChatMessage {
            margin-bottom: 1.5rem;
        }
        .st-bx {
            background-color: #e2edea;
        }
        #MainMenu, header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ===== PORTAL DE ACCESO =====
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Acceso al Agente Tronix")
    user = st.text_input("Usuario")
    passwd = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if user == "Tronix" and passwd == "Tronix":
            st.session_state.authenticated = True
            st.experimental_rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

# ===== INICIALIZACIÓN DE SESIÓN =====
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# ===== TÍTULO =====
st.title("🌲 Agente Tronix")
st.markdown("Bienvenido al panel de consulta forestal. Ingresa tus preguntas en el campo inferior.")

# ===== FUNCIÓN PARA MOSTRAR RESPUESTA =====
def render_agent_response(resp):
    if isinstance(resp, str):
        # Verificar si contiene un link a gráfico interactivo
        match = re.search(r"https?://[\w\-\./\?=]+grafico_id=[\w\-]+", resp)
        if match:
            url = match.group(0)
            components.html(
                f'<iframe src="{url}" width="100%" height="500px" frameborder="0" allowfullscreen></iframe>',
                height=520,
                scrolling=True
            )
        # Verificar si es imagen base64
        elif resp.startswith("data:image") or resp.startswith("/9j/"):
            img_data = f"data:image/png;base64,{resp}" if resp.startswith("/9j/") else resp
            st.image(img_data)
        else:
            st.markdown(resp)
        return

    elif isinstance(resp, list):
        for idx, item in enumerate(resp):
            st.markdown(f"**{idx+1}.**")
            render_agent_response(item)

    elif isinstance(resp, dict):
        if "grafico_url" in resp:
            components.html(
                f'<iframe src="{resp["grafico_url"]}" width="100%" height="500px" frameborder="0" allowfullscreen></iframe>',
                height=520,
                scrolling=True
            )
        if "image" in resp:
            img = resp["image"]
            if not img.startswith("data:image"):
                img = f"data:image/png;base64,{img}"
            st.image(img)
        if "table" in resp:
            df = pd.DataFrame(resp["table"])
            st.dataframe(df)
        if "text" in resp:
            st.markdown(resp["text"])
        for k, v in resp.items():
            if k not in {"grafico_url", "image", "table", "text"}:
                st.markdown(f"**{k.capitalize()}:**")
                render_agent_response(v)
    else:
        st.markdown(str(resp))

# ===== HISTORIAL DE CONVERSACIÓN =====
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        render_agent_response(msg["content"])

# ===== ENTRADA DEL USUARIO =====
prompt = st.chat_input("Escribe tu mensaje aquí...")

if prompt:
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Consultando al agente Tronix..."):
        try:
            res = requests.post(
                "https://n8n-production-993e.up.railway.app/webhook/01103618-3424-4455-bde6-aa8d295157b2",
                json={"message": prompt, "sessionId": st.session_state.session_id}
            )
            res.raise_for_status()
            json_response = res.json()
            reply = json_response["response"] if isinstance(json_response, dict) and "response" in json_response else json_response
        except Exception as e:
            reply = f"⚠️ Error al contactar con el agente: {e}"

    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        render_agent_response(reply)

# ===== PANEL LATERAL =====
st.sidebar.title("Opciones")
if st.sidebar.button("🔄 Reiniciar conversación"):
    st.session_state.chat_history = []
    st.session_state.session_id = str(uuid.uuid4())
    st.experimental_rerun()
