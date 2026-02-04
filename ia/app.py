import streamlit as st
import os
from dotenv import load_dotenv

# Charger les variables d'environnement au plus tôt
load_dotenv()

import speech_recognition as sr
from gtts import gTTS
import tempfile
from src.rag_chain import query_rag
from src.utils.metadata import get_all_metadata
from src.utils.db_manager import (
    load_all_chats, save_chat, create_new_session, 
    delete_chat, delete_all_chats, sign_in, sign_up, sign_out,
    get_supabase_client
)
import base64

# Configuration de la page
st.set_page_config(
    page_title="Tèwou Agro-Assistant",
    page_icon="🌱",
    layout="wide"
)

# Chemins des fichiers
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "static", "logo.png")

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

logo_b64 = get_base64_of_bin_file(LOGO_PATH)

# Chargement du CSS Premium (Dark Emerald Theme + Button Fix)
st.markdown("""
    <style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .stApp {
        background: radial-gradient(circle at top right, #0a2e1a 0%, #000000 100%);
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Animation & Glassmorphism */
    @keyframes pulse-glow {
        0% { box-shadow: 0 0 20px rgba(46, 125, 50, 0.4); transform: scale(1); }
        50% { box-shadow: 0 0 50px rgba(46, 125, 50, 0.6); transform: scale(1.02); }
        100% { box-shadow: 0 0 20px rgba(46, 125, 50, 0.4); transform: scale(1); }
    }
    
    .header-container {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 3rem 1rem;
        text-align: center;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    
    /* The Agro-Orb */
    .agro-orb {
        width: 120px;
        height: 120px;
        background: radial-gradient(circle, #4caf50 0%, #1b5e20 100%);
        border-radius: 50%;
        margin: 0 auto 1.5rem;
        animation: pulse-glow 3s infinite ease-in-out;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 3rem;
        filter: drop-shadow(0 0 15px #4caf50);
    }
    
    /* Sidebar restyling */
    section[data-testid="stSidebar"] {
        background: radial-gradient(circle at top left, #0a2e1a 0%, #000000 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .sidebar-title {
        color: #81c784;
        font-weight: 800;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
    
    /* Chat inputs & messages */
    .stTextInput>div>div>input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 12px;
    }
    
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px !important;
        padding: 1.2rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(5px);
    }

    /* Fix Chat Input Bar Background - CLEAN GREEN GRADIENT */
    .stChatInputContainer {
        padding-bottom: 2.5rem;
        padding-top: 1rem;
        background: linear-gradient(to top, #1b5e20 0%, #0a2e1a 100%) !important;
        border-top: 1px solid #4caf50;
    }
    
    /* Ensure no white background interference */
    .stChatInputContainer > div, [data-testid="stAudioInput"] > div {
        background: transparent !important;
    }
    
    /* Logout button specific styling */
    .logout-btn {
        margin-top: 2rem;
        color: #ef5350 !important;
    }
    
    h1 {
        background: linear-gradient(90deg, #ffffff, #81c784);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3.5rem !important;
        margin-bottom: 0px;
    }
    
    /* White Text for Chat */
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div {
        color: #FFFFFF !important;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: rgba(0,0,0,0.1); }
    ::-webkit-scrollbar-thumb { background: rgba(46, 125, 50, 0.3); border-radius: 10px; }
    
    /* Sidebar Text Fixes */
    .stTextInput label, .stSelectbox label { color: #FFFFFF !important; font-weight: 600; }
    .streamlit-expanderHeader { color: #FFFFFF !important; background-color: transparent !important; font-weight: 600; }
    
    /* --- CUSTOM BUTTON COLOR FIX --- */
    div.stButton > button[kind="primary"] {
        background-color: #4caf50 !important;
        border-color: #4caf50 !important;
        color: white !important;
    }
    div.stButton > button[kind="secondary"] {
        background-color: rgba(255, 255, 255, 0.05);
        color: #e0e0e0;
        border: none;
        text-align: left;
        display: block;
        width: 100%;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- AUTHENTICATION UI ---

def show_login_page():
    st.markdown('<div class="header-container"><div class="agro-orb">🌱</div><h1>Accès Tèwou Agro</h1><p style="font-size: 1.2rem; opacity: 0.8; margin-top: 1rem;">Connectez-vous pour accéder à votre assistant personnalisé</p></div>', unsafe_allow_html=True)
    
    # Outil de diagnostic (visible uniquement si config manquante)
    if not get_supabase_client():
        with st.expander("🛠️ Diagnostic de connexion (Problème détecté)", expanded=True):
            st.error("L'application ne trouve pas vos clés de sécurité Supabase.")
            st.info("Vérifiez que vous avez bien ajouté `SUPABASE_URL` et `SUPABASE_KEY` dans les **Secrets** de Streamlit Cloud.")
            st.write("**État des variables :**")
            st.write(f"- SUPABASE_URL: {'✅ Détectée' if os.getenv('SUPABASE_URL') or (hasattr(st, 'secrets') and 'SUPABASE_URL' in st.secrets) else '❌ Manquante'}")
            st.write(f"- SUPABASE_KEY: {'✅ Détectée' if os.getenv('SUPABASE_KEY') or (hasattr(st, 'secrets') and 'SUPABASE_KEY' in st.secrets) else '❌ Manquante'}")
    
    # Center the login form
    _, col, _ = st.columns([1, 2, 1])
    
    with col:
        tab1, tab2 = st.tabs(["Connexion", "Créer un compte"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Mot de passe", type="password")
                submit = st.form_submit_button("Se connecter", use_container_width=True, type="primary")
                
                if submit:
                    user, error = sign_in(email, password)
                    if error:
                        st.error(f"Erreur : {error}")
                    else:
                        st.session_state.user = user
                        st.success("Connexion réussie !")
                        st.rerun()
                        
        with tab2:
            st.info("Un email de confirmation peut vous être envoyé selon la configuration Supabase.")
            with st.form("signup_form"):
                new_email = st.text_input("Nouvel Email")
                new_password = st.text_input("Nouveau Mot de passe", type="password")
                confirm_password = st.text_input("Confirmer le mot de passe", type="password")
                submit_signup = st.form_submit_button("Créer mon compte", use_container_width=True)
                
                if submit_signup:
                    if new_password != confirm_password:
                        st.error("Les mots de passe ne correspondent pas.")
                    elif len(new_password) < 6:
                        st.error("Le mot de passe doit faire au moins 6 caractères.")
                    else:
                        user, error = sign_up(new_email, new_password)
                        if error:
                            st.error(f"Erreur : {error}")
                        else:
                            st.success("Compte créé avec succès !")

# --- GESTION DE SESSION ---

if "user" not in st.session_state:
    show_login_page()
    st.stop()

# Utilisateur actuel
user = st.session_state.user

if "session_id" not in st.session_state:
    st.session_state.session_id = create_new_session()
    st.session_state.messages = []

# --- SIDEBAR ---
with st.sidebar:
    # Infos Utilisateur
    st.markdown(f'<div class="sidebar-title">👤 {user.email}</div>', unsafe_allow_html=True)
    if st.button("🚪 Déconnexion", use_container_width=True):
        sign_out()
        del st.session_state["user"]
        st.rerun()
        
    st.markdown("---")
    
    # 1. Action: Nouveau Chat
    cols_nav = st.columns([0.8, 0.2])
    with cols_nav[0]:
        if st.button("➕ Nouveau chat", use_container_width=True, type="primary"):
            st.session_state.session_id = create_new_session()
            st.session_state.messages = []
            st.rerun()
    with cols_nav[1]:
        if st.button("🗑️", help="Supprimer tout votre historique"):
            if delete_all_chats(user_id=user.id):
                st.session_state.session_id = create_new_session()
                st.session_state.messages = []
                st.rerun()
    
    st.markdown("---")
    
    # 2. Recherche
    st.markdown('<div class="sidebar-title">🔍 Recherche</div>', unsafe_allow_html=True)
    search_query = st.text_input("Chercher dans l'historique...", placeholder="Mots-clés...")
    
    # 3. Historique (Vos chats)
    st.markdown("---")
    st.markdown('<div class="sidebar-title">🗂️ Vos discussions</div>', unsafe_allow_html=True)
    
    # Chargement de l'historique FILTRÉ PAR L'UTILISATEUR
    all_chats = load_all_chats(user_id=user.id)
    
    # Filtrage et tri
    sorted_sessions = sorted(all_chats.items(), key=lambda x: x[1]['updated_at'], reverse=True)
    
    found_chats = 0
    with st.container(height=300):
        for s_id, data in sorted_sessions:
            title = data.get("title", "Discussion sans titre")
            
            if search_query:
                messages_content = " ".join([m["content"] for m in data["messages"]])
                if (search_query.lower() not in title.lower()) and (search_query.lower() not in messages_content.lower()):
                    continue

            found_chats += 1
            cols = st.columns([0.85, 0.15])
            with cols[0]:
                if st.button(f"📄 {title}", key=f"hist_{s_id}", use_container_width=True):
                    st.session_state.session_id = s_id
                    st.session_state.messages = data["messages"]
                    st.rerun()
            with cols[1]:
                if st.button("❌", key=f"del_{s_id}", help="Supprimer cette discussion"):
                    delete_chat(s_id)
                    if st.session_state.session_id == s_id:
                        st.session_state.session_id = create_new_session()
                        st.session_state.messages = []
                    st.rerun()
        
        if found_chats == 0:
            st.caption("Aucune discussion." if not search_query else "Aucun résultat.")

    st.markdown("---")
    
    # 4. Configuration
    with st.expander("📍 Configuration"):
        soil_types = ["Sols sablonneux (Dior)", "Sols sablo-argileux (Deck)", "Sols argileux (Deck-Dior)", "Sols ferrugineux tropicaux", "Sols halomorphes (Salés)", "Non spécifié"]
        selected_soil = st.selectbox("Type de sol", soil_types, index=5)
        location = st.text_input("Localité", "Sénégal")
    
    st.markdown('<div class="sidebar-title" style="margin-top: 2rem;">📚 Bibliothèque Tèwou</div>', unsafe_allow_html=True)
    try:
        metadata = get_all_metadata()
        if metadata:
            st.info(f"{len(metadata)} documents indexés")
    except:
        pass

# --- MAIN CHAT AREA ---

# Header
logo_html = f'<center><img src="data:image/png;base64,{logo_b64}" width="350" style="margin-bottom: 2rem; filter: drop-shadow(0 0 15px rgba(129, 199, 132, 0.4));"></center>' if logo_b64 else ""
st.markdown(f"""
<div class="header-container">
{logo_html}
<div class="agro-orb">🌱</div>
<h1>Tèwou Agro-Assistant</h1>
<p style="font-size: 1.2rem; opacity: 0.8; margin-top: 1rem;">
Votre compagnon agricole intelligent pour le Sénégal
</p>
</div>
""", unsafe_allow_html=True)

# Affichage des messages
for message in st.session_state.messages:
    avatar = "🧑‍🌾" if message["role"] == "user" else LOGO_PATH
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Saisie utilisateur
text_input = st.chat_input("Posez votre question agricole ici...")

if text_input:
    # Message Utilisateur
    with st.chat_message("user", avatar="🧑‍🌾"):
        st.markdown(text_input)
    st.session_state.messages.append({"role": "user", "content": text_input})
    
    # SAUVEGARDE (avec user_id)
    save_chat(st.session_state.session_id, st.session_state.messages, user_id=user.id)
    
    # Réponse Assistant
    history = [(m["content"], r["content"]) for m, r in zip(st.session_state.messages[::2], st.session_state.messages[1::2])]
    
    with st.chat_message("assistant", avatar=LOGO_PATH):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.status("Analyse de votre demande...", expanded=True) as status:
            try:
                stream = query_rag(text_input, soil_type=selected_soil, location=location, chat_history=history)
                
                for event in stream:
                    if event["type"] == "status":
                        status.update(label=event["content"], state="running")
                    elif event["type"] == "chunk":
                        full_response += event["content"]
                        message_placeholder.markdown(full_response + "▌")
                
                status.update(label="Réponse terminée", state="complete", expanded=False)
                message_placeholder.markdown(full_response)
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                save_chat(st.session_state.session_id, st.session_state.messages, user_id=user.id)
                
            except Exception as e:
                status.update(label="Erreur rencontrée", state="error")
                message_placeholder.error(f"Désolé, j'ai rencontré une difficulté : {str(e)}")

# Footer
st.markdown("""
<div style="text-align: center; color: #9e9e9e; font-size: 0.8rem; margin-top: 5rem; padding: 2rem;">
© 2026 Tèwou Agro - L'IA au service de la souveraineté alimentaire. fait par Fadel ADAM
</div>
""", unsafe_allow_html=True)
