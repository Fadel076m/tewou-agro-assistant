"""
config.py — Configuration centralisée de Tèwou Agro-Assistant
Source unique de vérité pour toutes les constantes, chemins et clés d'API.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration globale de l'application."""

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME = "Tèwou Agro-Assistant"
    APP_ICON = "🌱"
    APP_VERSION = "3.1"

    # ── Chemins absolus ───────────────────────────────────────────────────────
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    LOGO_PATH = os.path.join(STATIC_DIR, "logo.png")
    # Fallback logo à la racine de ia/
    LOGO_FALLBACK_PATH = os.path.join(BASE_DIR, "logo.png")

    # ── Clés d'API (chargées depuis .env ; complétées par st.secrets au runtime)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "")

    # ── Modèles IA ────────────────────────────────────────────────────────────
    EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    LLM_MODEL = "command-r-08-2024"
    RAG_K = 3  # Nombre de documents récupérés par le retriever

    # ── Traitement des documents ──────────────────────────────────────────────
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 100

    # ── Interface utilisateur ─────────────────────────────────────────────────
    SOIL_TYPES = [
        "Sols sablonneux (Dior)",
        "Sols sablo-argileux (Deck)",
        "Sols argileux (Deck-Dior)",
        "Sols ferrugineux tropicaux",
        "Sols halomorphes (Salés)",
        "Non spécifié",
    ]
    DEFAULT_SOIL = "Non spécifié"
    DEFAULT_LOCATION = "Sénégal"

    # ── PostgreSQL ────────────────────────────────────────────────────────────
    DB_POOL_MIN = 1
    DB_POOL_MAX = 10

    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def init_from_streamlit_secrets(cls) -> None:
        """
        Complète les clés manquantes depuis st.secrets (Streamlit Cloud).
        À appeler une seule fois au démarrage, après l'import de streamlit.
        """
        try:
            import streamlit as st
            secrets = getattr(st, "secrets", {})
            for key in ("SUPABASE_URL", "SUPABASE_KEY", "DATABASE_URL", "COHERE_API_KEY"):
                if not getattr(cls, key) and key in secrets:
                    setattr(cls, key, secrets[key])
        except Exception:
            pass

    @classmethod
    def check(cls) -> dict[str, bool]:
        """
        Diagnostic : retourne l'état des clés et ressources critiques.
        Utile pour l'expander 'Diagnostic Système' dans la sidebar.
        """
        logo_exists = os.path.exists(cls.LOGO_PATH) or os.path.exists(cls.LOGO_FALLBACK_PATH)
        return {
            "SUPABASE_URL": bool(cls.SUPABASE_URL),
            "SUPABASE_KEY": bool(cls.SUPABASE_KEY),
            "DATABASE_URL": bool(cls.DATABASE_URL),
            "COHERE_API_KEY": bool(cls.COHERE_API_KEY),
            "Chroma DB": os.path.exists(cls.CHROMA_DB_DIR),
            "Logo": logo_exists,
        }

    @classmethod
    def get_logo_b64(cls) -> str | None:
        """Retourne le logo encodé en base64 (None si introuvable)."""
        import base64
        for path in (cls.LOGO_PATH, cls.LOGO_FALLBACK_PATH):
            if os.path.exists(path):
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
        return None
