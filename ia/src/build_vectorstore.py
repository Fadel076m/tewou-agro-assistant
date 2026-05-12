"""
src/build_vectorstore.py — Construction et chargement du vectorstore ChromaDB.

Usage CLI :
    cd ia && python -m src.build_vectorstore

La fonction get_vectorstore() est décorée @st.cache_resource pour n'être
chargée qu'une seule fois par instance Streamlit (évite de recharger
le modèle d'embedding à chaque requête).
"""
import os
import logging

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from config import Config
from src.data_processing import load_documents, split_documents

logger = logging.getLogger(__name__)

# Alias publics utilisés par d'autres modules (ex: sidebar diagnostics)
DB_DIR = Config.CHROMA_DB_DIR
EMBEDDING_MODEL_NAME = Config.EMBEDDING_MODEL


# ── Cache Streamlit (ou lru_cache en dehors de Streamlit) ────────────────────
try:
    import streamlit as st
    _cache = st.cache_resource
except ImportError:
    from functools import lru_cache
    _cache = lru_cache(maxsize=1)


@_cache
def get_vectorstore() -> Chroma | None:
    """
    Charge le vectorstore ChromaDB depuis le disque.
    Résultat mis en cache — ne s'exécute qu'une seule fois par session Streamlit.

    Returns:
        Instance Chroma prête à l'emploi, ou None si la base est introuvable.
    """
    logger.info(f"Chargement du vectorstore depuis : {DB_DIR}")

    if not os.path.exists(DB_DIR):
        logger.error(f"Dossier chroma_db introuvable : {DB_DIR}")
        _log_parent_dir()
        return None

    files = os.listdir(DB_DIR)
    logger.info(f"Fichiers dans chroma_db : {files}")

    if not any(".sqlite3" in f or "index" in f for f in files):
        logger.warning("chroma_db présent mais semble vide ou corrompu.")
        return None

    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        vs = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
        logger.info("Vectorstore chargé avec succès.")
        # Marquer dans session_state pour le diagnostic sidebar
        try:
            import streamlit as st
            st.session_state["_chroma_ok"] = True
        except Exception:
            pass
        return vs
    except Exception as exc:
        logger.error(f"Erreur chargement vectorstore : {exc}", exc_info=True)
        return None


def build_vectorstore() -> Chroma | None:
    """
    Reconstruit entièrement le vectorstore à partir des documents sources.
    À exécuter localement après un scraping ou mise à jour des données.
    """
    logger.info("Démarrage de la construction du vectorstore…")

    documents = load_documents()
    if not documents:
        logger.error("Aucun document trouvé — construction annulée.")
        return None

    chunks = split_documents(documents)
    logger.info(f"{len(chunks)} chunks prêts à indexer.")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    os.makedirs(DB_DIR, exist_ok=True)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_DIR,
    )
    logger.info(f"Vectorstore construit et sauvegardé dans {DB_DIR}.")
    return vectorstore


# ── Helpers privés ────────────────────────────────────────────────────────────

def _log_parent_dir() -> None:
    parent = os.path.dirname(DB_DIR)
    if os.path.exists(parent):
        logger.info(f"Contenu de {parent} : {os.listdir(parent)}")
    else:
        logger.error(f"Le dossier parent {parent} est également introuvable.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_vectorstore()
