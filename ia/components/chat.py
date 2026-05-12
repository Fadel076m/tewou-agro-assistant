"""
components/chat.py — Interface de chat (header + messages + saisie + streaming).
"""
import streamlit as st
from config import Config
from src.rag_chain import query_rag
from src.utils.db_manager import save_chat, create_new_session


# ── Header ────────────────────────────────────────────────────────────────────

def render_chat_header() -> None:
    """Affiche le header glassmorphism avec logo et titre."""
    logo_b64 = Config.get_logo_b64()
    logo_html = (
        f'<center><img src="data:image/png;base64,{logo_b64}" '
        f'width="320" style="margin-bottom:1.5rem;'
        f'filter:drop-shadow(0 0 15px rgba(129,199,132,.4));"></center>'
    ) if logo_b64 else ""

    st.markdown(f"""
    <div class="header-container">
        {logo_html}
        <div class="agro-orb">🌱</div>
        <h1>{Config.APP_NAME}</h1>
        <p style="font-size:1.2rem;opacity:.8;margin-top:1rem;">
            Votre compagnon agricole intelligent pour le Sénégal
        </p>
    </div>
    """, unsafe_allow_html=True)


# ── Messages ──────────────────────────────────────────────────────────────────

def _render_messages(messages: list) -> None:
    """Affiche tous les messages de la conversation courante."""
    for message in messages:
        avatar = "🧑‍🌾" if message["role"] == "user" else "🌱"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])


# ── Réponse en streaming ──────────────────────────────────────────────────────

def _stream_response(
    question: str,
    history: list[tuple[str, str]],
    soil_type: str,
    location: str,
) -> str:
    """
    Affiche la réponse en streaming et retourne le texte complet.
    Gère les statuts intermédiaires via st.status.
    """
    full_response = ""

    with st.chat_message("assistant", avatar="🌱"):
        placeholder = st.empty()

        with st.status("Analyse de votre demande…", expanded=True) as status_box:
            try:
                stream = query_rag(
                    question,
                    soil_type=soil_type,
                    location=location,
                    chat_history=history,
                )
                for event in stream:
                    if event["type"] == "status":
                        status_box.update(label=event["content"], state="running")
                    elif event["type"] == "chunk":
                        full_response += event["content"]
                        placeholder.markdown(full_response + "▌")

                status_box.update(label="✅ Réponse terminée", state="complete", expanded=False)
                placeholder.markdown(full_response)

            except Exception as exc:
                status_box.update(label="❌ Erreur rencontrée", state="error")
                full_response = f"Désolé, une erreur est survenue : {exc}"
                placeholder.error(full_response)

    return full_response


# ── Composant principal ───────────────────────────────────────────────────────

def render_chat(user, session_id: str, messages: list, soil_type: str, location: str) -> None:
    """
    Affiche la zone de chat complète (historique + saisie + streaming).

    Args:
        user:       Objet utilisateur Supabase (user.id, user.email).
        session_id: UUID de la session courante.
        messages:   Liste de messages {"role": str, "content": str}.
        soil_type:  Type de sol sélectionné dans la sidebar.
        location:   Localité saisie dans la sidebar.
    """
    render_chat_header()

    # Affichage de l'historique courant
    _render_messages(messages)

    # Saisie utilisateur
    user_input = st.chat_input("Posez votre question agricole ici…")

    if not user_input:
        return

    # ── Affichage du message utilisateur ─────────────────────────────────────
    with st.chat_message("user", avatar="🧑‍🌾"):
        st.markdown(user_input)

    messages.append({"role": "user", "content": user_input})
    st.session_state.messages = messages

    # Sauvegarde immédiate (question posée)
    save_chat(session_id, messages, user_id=user.id)

    # ── Construction de l'historique (paires user/assistant) ─────────────────
    # On ne prend que les échanges complets (user + assistant)
    history: list[tuple[str, str]] = []
    user_msgs = [m for m in messages if m["role"] == "user"]
    asst_msgs = [m for m in messages if m["role"] == "assistant"]
    for u, a in zip(user_msgs[:-1], asst_msgs):  # exclure la dernière question
        history.append((u["content"], a["content"]))

    # ── Streaming de la réponse ───────────────────────────────────────────────
    full_response = _stream_response(user_input, history, soil_type, location)

    if full_response:
        messages.append({"role": "assistant", "content": full_response})
        st.session_state.messages = messages
        # Sauvegarde finale (réponse incluse)
        save_chat(session_id, messages, user_id=user.id)


# ── Footer ────────────────────────────────────────────────────────────────────

def render_footer() -> None:
    st.markdown("""
    <div style="text-align:center;color:#9e9e9e;font-size:.8rem;margin-top:5rem;padding:2rem;">
        © 2026 Tèwou Agro — L'IA au service de la souveraineté alimentaire.<br>
        Fait par <strong>Fadel ADAM</strong>
    </div>
    """, unsafe_allow_html=True)
