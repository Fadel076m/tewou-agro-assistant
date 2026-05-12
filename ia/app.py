"""
app.py - Point d'entree de Tewou Agro-Assistant.

Cycle de vie de la persistance :
  1. Connexion  -> warm_cache_from_db() : charge l'historique depuis PostgreSQL
  2. Utilisation -> save_chat()         : sauvegarde en temps reel (cache + DB)
  3. Deconnexion -> sync_cache_to_db()  : filet de securite avant nettoyage
"""
import streamlit as st
from config import Config
from components.styles import apply_global_styles
from components.auth import show_auth_page
from components.sidebar import render_sidebar
from components.chat import render_chat, render_footer
from src.utils.db_manager import create_new_session, warm_cache_from_db

# 1. Configuration de la page
st.set_page_config(
    page_title=Config.APP_NAME,
    page_icon=Config.APP_ICON,
    layout="wide",
)

# 2. Initialisation
Config.init_from_streamlit_secrets()
apply_global_styles()

# 3. Auth gate
if "user" not in st.session_state:
    show_auth_page()
    st.stop()

user = st.session_state.user

# 4. Premiere ouverture apres connexion : restaurer l'historique depuis la DB
if "session_id" not in st.session_state:
    st.session_state.session_id = create_new_session()
    st.session_state.messages = []
    # Charger l'historique persistant de cet utilisateur
    warm_cache_from_db(user.id)

# 5. Sidebar
profile = render_sidebar(user)

# 6. Chat
render_chat(
    user=user,
    session_id=st.session_state.session_id,
    messages=st.session_state.messages,
    soil_type=profile["soil"],
    location=profile["location"],
)

render_footer()
