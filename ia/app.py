import streamlit as st
import os
import speech_recognition as sr
from gtts import gTTS
import tempfile
from src.rag_chain import query_rag
from src.utils.metadata import get_all_metadata
from src.utils.db_manager import load_all_chats, save_chat, get_chat, create_new_session, delete_chat
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
    
    /* Microphone Styling - Clean and Aligned */
    [data-testid="stAudioInput"] button {
        background-color: #4caf50 !important;
        color: white !important;
        border: none !important;
        border-radius: 50%;
        width: 3rem;
        height: 3rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    [data-testid="stAudioInput"] button:hover {
        background-color: #66bb6a !important;
        transform: scale(1.05);
    }
    [data-testid="stAudioInput"] svg {
        fill: white !important;
        width: 1.5rem;
        height: 1.5rem;
    }
    
    h1 {
        background: linear-gradient(90deg, #ffffff, #81c784);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3.5rem !important;
        margin-bottom: 0px;
    }
    
    .source-tag {
        background-color: rgba(46, 125, 50, 0.2);
        color: #81c784;
        border: 1px solid rgba(129, 199, 132, 0.3);
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.7rem;
    }
    
    /* White Text for Chat */
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div {
        color: #FFFFFF !important;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(0,0,0,0.1);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(46, 125, 50, 0.3);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(46, 125, 50, 0.5);
    }
    /* Sidebar Text Fixes */
    /* Input Labels */
    .stTextInput label, .stSelectbox label {
        color: #FFFFFF !important;
        font-weight: 600;
    }
    
    /* Expander Headers */
    .streamlit-expanderHeader {
        color: #FFFFFF !important;
        background-color: transparent !important;
        font-weight: 600;
    }
    div[data-testid="stExpander"] summary span {
        color: #FFFFFF !important;
    }
    div[data-testid="stExpander"] svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }
    
    /* Caption/Small text if needed */
    .stCaptionContainer, [data-testid="stCaptionContainer"] {
        color: #cccccc !important;
    }
    
    /* --- CUSTOM BUTTON COLOR FIX --- */
    /* Target the Primary Button and make it GREEN */
    div.stButton > button[kind="primary"] {
        background-color: #4caf50 !important;
        border-color: #4caf50 !important;
        color: white !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #43a047 !important;
        border-color: #43a047 !important;
    }
    
    /* Chat History Items as Buttons (Secondary style override) */
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

# --- GESTION DE SESSION AVANCÉE ---
if "session_id" not in st.session_state:
    st.session_state.session_id = create_new_session()
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    # 1. Action: Nouveau Chat
    cols_nav = st.columns([0.8, 0.2])
    with cols_nav[0]:
        if st.button("➕ Nouveau chat", use_container_width=True, type="primary"):
            st.session_state.session_id = create_new_session()
            st.session_state.messages = []
            st.rerun()
    with cols_nav[1]:
        if st.button("🗑️", help="Supprimer tout l'historique"):
            if delete_all_chats():
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
    
    # Chargement de l'historique
    all_chats = load_all_chats()
    
    # Filtrage
    sorted_sessions = sorted(all_chats.items(), key=lambda x: x[1]['updated_at'], reverse=True)
    
    found_chats = 0
    with st.container(height=300):
        for s_id, data in sorted_sessions:
            title = data.get("title", "Discussion sans titre")
            
            # Application du filtre de recherche
            if search_query:
                # Cherche dans le titre OU dans le contenu des messages
                messages_content = " ".join([m["content"] for m in data["messages"]])
                if (search_query.lower() not in title.lower()) and (search_query.lower() not in messages_content.lower()):
                    continue

            found_chats += 1
            # Affichage du bouton pour charger la session + Bouton supprimer
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
            if search_query:
                st.caption("Aucune discussion trouvée.")
            elif not all_chats:
                st.caption("Aucune discussion sauvegardée.")

    st.markdown("---")
    
    # 4. Configuration & Bibliothèque
    with st.expander("📍 Configuration"):
        soil_types = [
            "Sols sablonneux (Dior)", 
            "Sols sablo-argileux (Deck)", 
            "Sols argileux (Deck-Dior)", 
            "Sols ferrugineux tropicaux",
            "Sols halomorphes (Salés)",
            "Non spécifié"
        ]
        selected_soil = st.selectbox("Type de sol", soil_types, index=5)
        location = st.text_input("Localité", "Sénégal")
    
    st.markdown('<div class="sidebar-title" style="margin-top: 2rem;">📚 Bibliothèque Tèwou</div>', unsafe_allow_html=True)
    try:
        metadata = get_all_metadata()
        if metadata:
            st.info(f"{len(metadata)} documents indexés")
            with st.expander("Voir les sources"):
                for entry in metadata[-10:]:
                    st.write(f"📄 {entry.get('metadata', {}).get('title', 'Doc')}")
    except:
        pass

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

# Affichage de l'historique des messages
for message in st.session_state.messages:
    avatar = "🧑‍🌾" if message["role"] == "user" else LOGO_PATH
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])


# Zone de saisie utilisateur (Texte OU Vocal)
chat_container = st.container()
input_container = st.empty()

# CSS pour fixer le micro (Désactivé temporairement)
# st.markdown("""
# <style>
# [data-testid="stAudioInput"] {
#     position: fixed;
#     bottom: 35px;
#     right: 25px;
#     z-index: 1001;
#     width: 3rem;
# }
# </style>
# """, unsafe_allow_html=True)

# Zone de saisie
# audio_value = st.audio_input("Micro", label_visibility="collapsed")
audio_value = None
text_input = st.chat_input("Posez votre question agricole ici...")

prompt = None

# Gestion de l'audio
if audio_value:
    with st.spinner("Transcription..."):
        try:
            r = sr.Recognizer()
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
                tmp_audio.write(audio_value.read())
                tmp_audio_path = tmp_audio.name
            
            with sr.AudioFile(tmp_audio_path) as source:
                audio_data = r.record(source)
                prompt = r.recognize_google(audio_data, language="fr-FR")
            os.remove(tmp_audio_path)
        except Exception as e:
            st.error(f"Erreur audio: {e}")

# Gestion du texte (priorité au texte si les deux sont présents, ou enchaînement)
if text_input:
    prompt = text_input
    audio_value = None # Disable TTS if text input is used

if prompt:
    # Affichage du message utilisateur - ICONE UTILISATEUR
    with st.chat_message("user", avatar="🧑‍🌾"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # SAUVEGARDE UTILISATEUR
    save_chat(st.session_state.session_id, st.session_state.messages)
    
    # Préparation de l'historique
    history = [(m["content"], r["content"]) for m, r in zip(st.session_state.messages[::2], st.session_state.messages[1::2])]
    
    # Génération de la réponse
    with st.chat_message("assistant", avatar=LOGO_PATH):
        message_placeholder = st.empty()
        full_response = ""
        
        # Container pour les étapes de réflexion
        with st.status("Analyse de votre demande...", expanded=True) as status:
            try:
                # Appel du générateur (Streaming)
                stream = query_rag(
                    prompt, 
                    soil_type=selected_soil, 
                    location=location,
                    chat_history=history
                )
                
                for event in stream:
                    if event["type"] == "status":
                        status.update(label=event["content"], state="running")
                    elif event["type"] == "chunk":
                        full_response += event["content"]
                        message_placeholder.markdown(full_response + "▌")
                
                # Fin du streaming
                status.update(label="Réponse terminée", state="complete", expanded=False)
                message_placeholder.markdown(full_response)
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                # SAUVEGARDE ASSISTANT
                save_chat(st.session_state.session_id, st.session_state.messages)
                
                # --- TTS (Synthèse Vocale) ---
                if audio_value:
                    try:
                        tts = gTTS(text=full_response, lang='fr', slow=False)
                        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
                            tts.save(tmp_mp3.name)
                            st.audio(tmp_mp3.name, format="audio/mp3", autoplay=True)
                    except Exception as e:
                        pass # Silent fail for audio to not block chat
                    
            except Exception as e:
                status.update(label="Erreur rencontrée", state="error")
                error_msg = f"Désolé, j'ai rencontré une difficulté : {str(e)}"
                message_placeholder.error(error_msg)

# Footer
st.markdown("""
    <div style="text-align: center; color: #9e9e9e; font-size: 0.8rem; margin-top: 5rem; padding: 2rem;">
    © 2026 Tèwou Agro - L'IA au service de la souveraineté alimentaire. fait par Fadel ADAM
    </div>
    """, unsafe_allow_html=True)
