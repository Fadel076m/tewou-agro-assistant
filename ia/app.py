"""
app.py — Point d'entrée de Tèwou Agro-Assistant.

Ce fichier se limite à :
  1. Configurer Streamlit
  2. Initialiser les clés (env + st.secrets)
  3. Gérer la session utilisateur (auth gate)
  4. Orchestrer les composants : sidebar → chat
"""
import streamlit as st
from config import Config
from components.styles import apply_global_styles
from components.auth import show_auth_page
from components.sidebar import render_sidebar
from components.chat import render_chat, render_footer
from src.utils.db_manager import create_new_session

# ── 1. Configuration de la page ───────────────────────────────────────────────
st.set_page_config(
    page_title=Config.APP_NAME,
    page_icon=Config.APP_ICON,
    layout="wide",
)

# ── 2. Initialisation (secrets Streamlit Cloud + styles) ──────────────────────
Config.init_from_streamlit_secrets()
apply_global_styles()

# ── 3. Auth gate — si non connecté, afficher la page de login ─────────────────
if "user" not in st.session_state:
    show_auth_page()
    st.stop()

user = st.session_state.user

# ── 4. Initialisation de la session de chat ───────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = create_new_session()
    st.session_state.messages = []

# ── 5. Sidebar (retourne soil_type et location) ───────────────────────────────
profile = render_sidebar(user)

# ── 6. Interface de chat ──────────────────────────────────────────────────────
render_chat(
    user=user,
    session_id=st.session_state.session_id,
    messages=st.session_state.messages,
    soil_type=profile["soil"],
    location=profile["location"],
)

render_footer()
