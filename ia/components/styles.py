"""
components/styles.py — Thème Dark Emerald de Tèwou Agro-Assistant
Tout le CSS est centralisé ici. Modifier ce fichier pour changer l'apparence globale.
"""
import streamlit as st


def apply_global_styles() -> None:
    """Injecte le CSS global dans l'application Streamlit."""
    st.markdown(_CSS, unsafe_allow_html=True)


_CSS = """
<style>
/* ── Fonts ─────────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

/* ── Background global ──────────────────────────────────────────────────── */
.stApp {
    background: radial-gradient(circle at top right, #0a2e1a 0%, #000000 100%);
    color: #e0e0e0;
    font-family: 'Inter', sans-serif;
}

/* ── Animations ─────────────────────────────────────────────────────────── */
@keyframes pulse-glow {
    0%   { box-shadow: 0 0 20px rgba(46,125,50,.4); transform: scale(1);    }
    50%  { box-shadow: 0 0 50px rgba(46,125,50,.6); transform: scale(1.02); }
    100% { box-shadow: 0 0 20px rgba(46,125,50,.4); transform: scale(1);    }
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0);   }
}

/* ── Header glassmorphism ───────────────────────────────────────────────── */
.header-container {
    background: rgba(255,255,255,.03);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 24px;
    padding: 3rem 1rem;
    text-align: center;
    margin-bottom: 2rem;
    animation: fadeIn .6s ease;
}

/* ── Agro Orb ───────────────────────────────────────────────────────────── */
.agro-orb {
    width: 120px; height: 120px;
    background: radial-gradient(circle, #4caf50 0%, #1b5e20 100%);
    border-radius: 50%;
    margin: 0 auto 1.5rem;
    animation: pulse-glow 3s infinite ease-in-out;
    display: flex; align-items: center; justify-content: center;
    font-size: 3rem;
    filter: drop-shadow(0 0 15px #4caf50);
}

/* ── Sidebar ────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: radial-gradient(circle at top left, #0a2e1a 0%, #000000 100%);
    border-right: 1px solid rgba(255,255,255,.1);
}
.sidebar-section-title {
    color: #81c784;
    font-weight: 800;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-size: 0.75rem;
    margin: 1rem 0 0.5rem;
    opacity: .85;
}
/* Groupes de date dans l'historique */
.history-date-group {
    color: #66bb6a;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .08em;
    margin: 0.8rem 0 0.3rem;
    padding-left: 4px;
    border-left: 2px solid #4caf50;
}
/* Badge nombre de messages */
.msg-badge {
    display: inline-block;
    background: rgba(76,175,80,.2);
    color: #81c784;
    font-size: 0.65rem;
    border-radius: 8px;
    padding: 1px 6px;
    margin-left: 4px;
    vertical-align: middle;
}

/* ── Messages de chat ───────────────────────────────────────────────────── */
.stChatMessage {
    background: rgba(255,255,255,.03) !important;
    border: 1px solid rgba(255,255,255,.05);
    border-radius: 16px !important;
    padding: 1.2rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(5px);
    animation: fadeIn .3s ease;
}

/* ── Barre de saisie ────────────────────────────────────────────────────── */
.stChatInputContainer {
    padding-bottom: 2.5rem;
    padding-top: 1rem;
    background: linear-gradient(to top, #1b5e20 0%, #0a2e1a 100%) !important;
    border-top: 1px solid #4caf50;
}
.stChatInputContainer > div,
[data-testid="stAudioInput"] > div {
    background: transparent !important;
}

/* ── Inputs texte ───────────────────────────────────────────────────────── */
.stTextInput > div > div > input {
    background: rgba(255,255,255,.05) !important;
    border: 1px solid rgba(255,255,255,.1) !important;
    color: white !important;
    border-radius: 12px;
}

/* ── Titre principal ────────────────────────────────────────────────────── */
h1 {
    background: linear-gradient(90deg, #ffffff, #81c784);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 3.5rem !important;
    margin-bottom: 0px;
}

/* ── Texte markdown ─────────────────────────────────────────────────────── */
.stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div {
    color: #FFFFFF !important;
}

/* ── Boutons ────────────────────────────────────────────────────────────── */
div.stButton > button[kind="primary"] {
    background-color: #4caf50 !important;
    border-color: #4caf50 !important;
    color: white !important;
    border-radius: 10px;
    transition: background-color .2s;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #388e3c !important;
}
div.stButton > button[kind="secondary"] {
    background-color: rgba(255,255,255,.05);
    color: #e0e0e0;
    border: none;
    text-align: left;
    display: block;
    width: 100%;
    margin-bottom: 0.4rem;
    border-radius: 8px;
    transition: background-color .15s;
}
div.stButton > button[kind="secondary"]:hover {
    background-color: rgba(76,175,80,.15);
}

/* ── Labels sidebar ─────────────────────────────────────────────────────── */
.stTextInput label, .stSelectbox label {
    color: #FFFFFF !important;
    font-weight: 600;
}
.streamlit-expanderHeader {
    color: #FFFFFF !important;
    background-color: transparent !important;
    font-weight: 600;
}

/* ── Scrollbar ──────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: rgba(0,0,0,.1); }
::-webkit-scrollbar-thumb { background: rgba(46,125,50,.3); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(76,175,80,.5); }
</style>
"""
