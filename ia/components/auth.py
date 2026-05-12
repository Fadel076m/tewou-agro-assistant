"""
components/auth.py — Page d'authentification (Login / Inscription)
"""
import streamlit as st
from config import Config
from src.utils.db_manager import sign_in, sign_up, get_supabase_client


def show_auth_page() -> None:
    """Affiche la page de connexion / création de compte."""
    st.markdown("""
    <div class="header-container">
        <div class="agro-orb">🌱</div>
        <h1>Accès Tèwou Agro</h1>
        <p style="font-size:1.2rem;opacity:.8;margin-top:1rem;">
            Connectez-vous pour accéder à votre assistant personnalisé
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Diagnostic si Supabase non configuré ─────────────────────────────────
    if not get_supabase_client():
        status = Config.check()
        with st.expander("🛠️ Diagnostic de connexion (Problème détecté)", expanded=True):
            st.error("L'application ne trouve pas vos clés Supabase.")
            st.info("Ajoutez `SUPABASE_URL` et `SUPABASE_KEY` dans les **Secrets** de Streamlit Cloud.")
            st.write("**État des variables :**")
            for k, v in status.items():
                icon = "✅" if v else "❌"
                st.write(f"- **{k}** : {icon}")
        return

    # ── Formulaires centrés ───────────────────────────────────────────────────
    _, col, _ = st.columns([1, 2, 1])
    with col:
        tab_login, tab_signup = st.tabs(["🔑 Connexion", "📝 Créer un compte"])

        # Connexion
        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email", placeholder="vous@exemple.com")
                password = st.text_input("Mot de passe", type="password")
                submitted = st.form_submit_button(
                    "Se connecter", use_container_width=True, type="primary"
                )
                if submitted:
                    if not email or not password:
                        st.warning("Veuillez remplir tous les champs.")
                    else:
                        with st.spinner("Connexion en cours..."):
                            user, error = sign_in(email, password)
                        if error:
                            st.error(f"❌ {error}")
                        else:
                            st.session_state.user = user
                            st.success("✅ Connexion réussie !")
                            st.rerun()

        # Inscription
        with tab_signup:
            st.info("Un email de confirmation peut vous être envoyé selon la configuration Supabase.")
            with st.form("signup_form", clear_on_submit=True):
                new_email = st.text_input("Email", placeholder="vous@exemple.com", key="su_email")
                new_password = st.text_input("Mot de passe", type="password", key="su_pw")
                confirm_password = st.text_input("Confirmer le mot de passe", type="password", key="su_cpw")
                submitted_signup = st.form_submit_button(
                    "Créer mon compte", use_container_width=True
                )
                if submitted_signup:
                    if not new_email or not new_password:
                        st.warning("Veuillez remplir tous les champs.")
                    elif new_password != confirm_password:
                        st.error("❌ Les mots de passe ne correspondent pas.")
                    elif len(new_password) < 6:
                        st.error("❌ Le mot de passe doit faire au moins 6 caractères.")
                    else:
                        with st.spinner("Création du compte..."):
                            user, error = sign_up(new_email, new_password)
                        if error:
                            st.error(f"❌ {error}")
                        else:
                            st.success(
                                "✅ Compte créé ! Connectez-vous via l'onglet **Connexion**."
                            )
