"""
components/sidebar.py — Sidebar avec historique des discussions groupé par date.

Groupes affichés :
  - Aujourd'hui
  - Hier
  - 7 derniers jours
  - Ce mois-ci
  - Plus tôt

Retourne un dict {"soil": str, "location": str} pour paramétrer le chat.
"""
import streamlit as st
from datetime import datetime, timedelta
from config import Config
from src.utils.db_manager import (
    load_all_chats,
    delete_chat,
    delete_all_chats,
    create_new_session,
    sign_out,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

_DATE_GROUPS = [
    ("Aujourd'hui",       0,  1),
    ("Hier",              1,  2),
    ("7 derniers jours",  2,  7),
    ("Ce mois-ci",        7, 30),
    ("Plus tôt",         30, None),
]


def _date_group(timestamp: float) -> str:
    """Retourne l'étiquette de groupe de date pour un timestamp Unix."""
    now = datetime.now()
    age_days = (now - datetime.fromtimestamp(timestamp)).days
    for label, start, end in _DATE_GROUPS:
        if end is None or start <= age_days < end:
            return label
    return "Plus tôt"


def _group_sessions(sessions: dict) -> dict[str, list]:
    """
    Trie et groupe les sessions par plage de date.
    Retourne un dict ordonné {label: [(session_id, data), ...]}
    """
    groups: dict[str, list] = {label: [] for label, *_ in _DATE_GROUPS}

    for s_id, data in sessions.items():
        label = _date_group(data.get("updated_at", 0))
        groups[label].append((s_id, data))

    # Tri interne par updated_at décroissant dans chaque groupe
    for label in groups:
        groups[label].sort(key=lambda x: x[1].get("updated_at", 0), reverse=True)

    return groups


def _session_preview(messages: list) -> str:
    """Retourne un court aperçu (50 chars) du premier message utilisateur."""
    for m in messages:
        if m["role"] == "user":
            content = m["content"].strip()
            return (content[:50] + "…") if len(content) > 50 else content
    return "Discussion vide"


# ── Rendu principal ───────────────────────────────────────────────────────────

def render_sidebar(user) -> dict:
    """
    Affiche la sidebar complète.

    Returns:
        dict avec les clés "soil" et "location" sélectionnées par l'utilisateur.
    """
    with st.sidebar:
        # ── En-tête utilisateur ───────────────────────────────────────────────
        st.markdown(
            f'<div class="sidebar-section-title">👤 {user.email}</div>',
            unsafe_allow_html=True,
        )
        if st.button("🚪 Déconnexion", use_container_width=True, key="logout_btn"):
            sign_out()
            # Nettoyage complet de la session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.divider()

        # ── Actions rapides ───────────────────────────────────────────────────
        col_new, col_del = st.columns([0.8, 0.2])
        with col_new:
            if st.button("➕ Nouveau chat", use_container_width=True, type="primary", key="new_chat_btn"):
                st.session_state.session_id = create_new_session()
                st.session_state.messages = []
                st.rerun()
        with col_del:
            if st.button("🗑️", help="Supprimer tout votre historique", key="del_all_btn"):
                if delete_all_chats(user_id=user.id):
                    st.session_state.session_id = create_new_session()
                    st.session_state.messages = []
                    st.rerun()

        st.divider()

        # ── Configuration du profil agricole ─────────────────────────────────
        with st.expander("⚙️ Mon profil agricole", expanded=False):
            selected_soil = st.selectbox(
                "Type de sol",
                Config.SOIL_TYPES,
                index=Config.SOIL_TYPES.index(
                    st.session_state.get("soil_type", Config.DEFAULT_SOIL)
                ),
                key="soil_selectbox",
            )
            location = st.text_input(
                "Localité",
                value=st.session_state.get("location", Config.DEFAULT_LOCATION),
                key="location_input",
            )
            # Persistance dans session_state
            st.session_state["soil_type"] = selected_soil
            st.session_state["location"] = location

        st.divider()

        # ── Recherche dans l'historique ───────────────────────────────────────
        st.markdown(
            '<div class="sidebar-section-title">🗂️ Historique des discussions</div>',
            unsafe_allow_html=True,
        )
        search_query = st.text_input(
            "🔍 Rechercher…",
            placeholder="Mot-clé dans vos discussions",
            label_visibility="collapsed",
            key="history_search",
        )

        # ── Chargement et filtrage ────────────────────────────────────────────
        all_chats = load_all_chats(user_id=user.id)

        if search_query:
            q = search_query.lower()
            all_chats = {
                s_id: data
                for s_id, data in all_chats.items()
                if q in data.get("title", "").lower()
                or any(q in m["content"].lower() for m in data.get("messages", []))
            }

        grouped = _group_sessions(all_chats)
        total_sessions = sum(len(v) for v in grouped.values())

        # ── Statistiques rapides ──────────────────────────────────────────────
        total_messages = sum(
            len(data.get("messages", [])) for data in all_chats.values()
        )
        col_s, col_m = st.columns(2)
        col_s.metric("Discussions", total_sessions)
        col_m.metric("Messages", total_messages)

        # ── Liste des sessions groupées ───────────────────────────────────────
        with st.container(height=350):
            if total_sessions == 0:
                if search_query:
                    st.caption("Aucun résultat pour cette recherche.")
                else:
                    st.caption("Aucune discussion pour l'instant.")
            else:
                for group_label, _, _ in _DATE_GROUPS:
                    sessions_in_group = grouped.get(group_label, [])
                    if not sessions_in_group:
                        continue

                    # Étiquette de groupe
                    st.markdown(
                        f'<div class="history-date-group">{group_label}</div>',
                        unsafe_allow_html=True,
                    )

                    for s_id, data in sessions_in_group:
                        title = data.get("title", "Discussion sans titre")
                        msgs = data.get("messages", [])
                        msg_count = len(msgs)
                        preview = _session_preview(msgs)

                        is_active = st.session_state.get("session_id") == s_id
                        btn_label = f"{'▶ ' if is_active else ''}📄 {title}"

                        col_btn, col_x = st.columns([0.85, 0.15])
                        with col_btn:
                            help_text = f"{preview}\n{msg_count} message{'s' if msg_count > 1 else ''}"
                            if st.button(
                                btn_label,
                                key=f"hist_{s_id}",
                                use_container_width=True,
                                help=help_text,
                            ):
                                st.session_state.session_id = s_id
                                st.session_state.messages = msgs
                                st.rerun()
                        with col_x:
                            if st.button("✕", key=f"del_{s_id}", help="Supprimer"):
                                delete_chat(s_id)
                                if st.session_state.get("session_id") == s_id:
                                    st.session_state.session_id = create_new_session()
                                    st.session_state.messages = []
                                st.rerun()

        st.divider()

        # ── Diagnostic système ────────────────────────────────────────────────
        with st.expander("🛠️ Diagnostic système"):
            status = Config.check()
            for key, ok in status.items():
                icon = "✅" if ok else "❌"
                st.write(f"{icon} **{key}**")

            from src.build_vectorstore import DB_DIR
            if ok := st.session_state.get("_chroma_ok"):
                st.success("Base vectorielle chargée en mémoire ✅")
            elif not __import__("os").path.exists(DB_DIR):
                st.error(f"chroma_db introuvable : `{DB_DIR}`")
            else:
                st.info(f"chroma_db présent : `{DB_DIR}`")

    # Retourner les valeurs de configuration pour le chat
    return {
        "soil": st.session_state.get("soil_type", Config.DEFAULT_SOIL),
        "location": st.session_state.get("location", Config.DEFAULT_LOCATION),
    }
