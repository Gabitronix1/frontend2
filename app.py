
import streamlit as st
import requests
import uuid

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
            raw = res.json().get("response", "(Sin respuesta del agente)")
            if isinstance(raw, list):
                reply = "\n\n".join(str(x) for x in raw)
            else:
                reply = str(raw)
        except Exception as e:
            reply = f"⚠️ Error al contactar con el agente: {e}"

    # Mostrar respuesta del agente
    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)

# Panel lateral con opciones
st.sidebar.title("Opciones")
if st.sidebar.button("🔄 Reiniciar conversación"):
    st.session_state.chat_history = []
    st.session_state.session_id = str(uuid.uuid4())
    st.experimental_rerun()
