"""
components/sidebar.py - Sidebar avec historique des discussions groupe par date.

Groupes: Aujourd'hui / Hier / 7 derniers jours / Ce mois-ci / Plus tot
Retourne dict {"soil": str, "location": str} pour parametrer le chat.
"""
import streamlit as st
from datetime import datetime
from config import Config
from src.utils.db_manager import (
    load_all_chats,
    delete_chat,
    delete_all_chats,
    create_new_session,
    sign_out,
    db_status,
)

# ---------------------------------------------------------------------------
# HELPERS - GROUPEMENT PAR DATE
# ---------------------------------------------------------------------------

_DATE_GROUPS = [
    ("Aujourd'hui",      0,  1),
    ("Hier",             1,  2),
    ("7 derniers jours", 2,  7),
    ("Ce mois-ci",       7, 30),
    ("Plus tot",        30, None),
]


def _date_group(timestamp):
    """Retourne l'etiquette de groupe de date pour un timestamp Unix."""
    now = datetime.now()
    age_days = (now - datetime.fromtimestamp(timestamp)).days
    for label, start, end in _DATE_GROUPS:
        if end is None or start <= age_days < end:
            return label
    return "Plus tot"


def _group_sessions(sessions):
    """Trie et groupe les sessions par plage de date."""
    groups = {label: [] for label, *_ in _DATE_GROUPS}
    for s_id, data in sessions.items():
        label = _date_group(data.get("updated_at", 0))
        groups[label].append((s_id, data))
    # Tri interne par updated_at decroissant
    for label in groups:
        groups[label].sort(key=lambda x: x[1].get("updated_at", 0), reverse=True)
    return groups


def _session_preview(messages):
    """Apercu court (60 chars) du premier message utilisateur."""
    for m in messages:
        if m["role"] == "user":
            content = m["content"].strip()
            return (content[:60] + "...") if len(content) > 60 else content
    return "Discussion vide"


# ---------------------------------------------------------------------------
# RENDU PRINCIPAL
# ---------------------------------------------------------------------------

def render_sidebar(user):
    """
    Affiche la sidebar complete.
    Returns: dict {"soil": str, "location": str}
    """
    with st.sidebar:

        # -- En-tete utilisateur -------------------------------------------
        st.markdown(
            f'<div class="sidebar-section-title">Utilisateur : {user.email}</div>',
            unsafe_allow_html=True,
        )
        if st.button("Deconnexion", use_container_width=True, key="logout_btn"):
            sign_out()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.divider()

        # -- Actions rapides -----------------------------------------------
        col_new, col_del = st.columns([0.8, 0.2])
        with col_new:
            if st.button(
                "+ Nouveau chat",
                use_container_width=True,
                type="primary",
                key="new_chat_btn",
            ):
                st.session_state.session_id = create_new_session()
                st.session_state.messages = []
                st.rerun()
        with col_del:
            if st.button(
                "X",
                help="Supprimer tout votre historique",
                key="del_all_btn",
            ):
                if delete_all_chats(user_id=user.id):
                    st.session_state.session_id = create_new_session()
                    st.session_state.messages = []
                    st.rerun()

        st.divider()

        # -- Configuration profil agricole ---------------------------------
        with st.expander("Mon profil agricole", expanded=False):
            current_soil = st.session_state.get("soil_type", Config.DEFAULT_SOIL)
            soil_index = (
                Config.SOIL_TYPES.index(current_soil)
                if current_soil in Config.SOIL_TYPES
                else len(Config.SOIL_TYPES) - 1
            )
            selected_soil = st.selectbox(
                "Type de sol",
                Config.SOIL_TYPES,
                index=soil_index,
                key="soil_selectbox",
            )
            location = st.text_input(
                "Localite",
                value=st.session_state.get("location", Config.DEFAULT_LOCATION),
                key="location_input",
            )
            st.session_state["soil_type"] = selected_soil
            st.session_state["location"] = location

        st.divider()

        # -- Historique des discussions ------------------------------------
        st.markdown(
            '<div class="sidebar-section-title">Historique des discussions</div>',
            unsafe_allow_html=True,
        )
        search_query = st.text_input(
            "Rechercher",
            placeholder="Mot-cle dans vos discussions",
            label_visibility="collapsed",
            key="history_search",
        )

        # Chargement et filtrage
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
        total_messages = sum(
            len(data.get("messages", [])) for data in all_chats.values()
        )

        # Statistiques
        col_s, col_m = st.columns(2)
        col_s.metric("Discussions", total_sessions)
        col_m.metric("Messages", total_messages)

        # Liste des sessions groupees par date
        with st.container(height=350):
            if total_sessions == 0:
                if search_query:
                    st.caption("Aucun resultat pour cette recherche.")
                else:
                    st.caption("Aucune discussion pour l'instant.")
            else:
                for group_label, _, _ in _DATE_GROUPS:
                    sessions_in_group = grouped.get(group_label, [])
                    if not sessions_in_group:
                        continue

                    # Etiquette de groupe
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

                        prefix = "[>] " if is_active else ""
                        btn_label = f"{prefix}{title}"
                        help_text = f"{preview} | {msg_count} msg"

                        col_btn, col_x = st.columns([0.85, 0.15])
                        with col_btn:
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
                            if st.button("x", key=f"del_{s_id}", help="Supprimer"):
                                delete_chat(s_id)
                                if st.session_state.get("session_id") == s_id:
                                    st.session_state.session_id = create_new_session()
                                    st.session_state.messages = []
                                st.rerun()

        st.divider()

        # -- Diagnostic systeme --------------------------------------------
        with st.expander("Diagnostic systeme"):
            cfg = Config.check()
            db_info = db_status()
            import os

            st.markdown("**Configuration**")
            for key, ok in cfg.items():
                icon = "OK" if ok else "MANQUANT"
                st.write(f"[{icon}] {key}")

            st.markdown("**Stockage**")
            pg_ok = db_info["postgresql"]
            pg_label = "connecte" if pg_ok else "non dispo (mode cache actif)"
            st.write(f"[{'OK' if pg_ok else '!'}] PostgreSQL : {pg_label}")
            st.write(f"[i] Sessions en cache : {db_info['cache_sessions']}")

            st.markdown("**Vectorstore**")
            from src.build_vectorstore import DB_DIR
            if st.session_state.get("_chroma_ok"):
                st.write("[OK] Base vectorielle chargee")
            elif not os.path.exists(DB_DIR):
                st.write(f"[!] chroma_db introuvable : {DB_DIR}")
            else:
                st.write("[i] chroma_db present (en attente de chargement)")

    return {
        "soil": st.session_state.get("soil_type", Config.DEFAULT_SOIL),
        "location": st.session_state.get("location", Config.DEFAULT_LOCATION),
    }
