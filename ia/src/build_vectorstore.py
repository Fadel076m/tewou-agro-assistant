"""
src/build_vectorstore.py - Construction et chargement du vectorstore ChromaDB.

Usage CLI : cd ia && python -m src.build_vectorstore
"""
import os
import logging

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from config import Config
from src.data_processing import load_documents, split_documents

logger = logging.getLogger(__name__)

DB_DIR = Config.CHROMA_DB_DIR
EMBEDDING_MODEL_NAME = Config.EMBEDDING_MODEL

try:
    import streamlit as st
    _cache = st.cache_resource
except ImportError:
    from functools import lru_cache
    _cache = lru_cache(maxsize=1)


@_cache
def get_vectorstore():
    """
    Charge le vectorstore ChromaDB depuis le disque.
    Mis en cache - ne s'execute qu'une seule fois par session Streamlit.
    """
    logger.info(f"Chargement vectorstore depuis : {DB_DIR}")

    if not os.path.exists(DB_DIR):
        logger.error(f"Dossier chroma_db introuvable : {DB_DIR}")
        parent = os.path.dirname(DB_DIR)
        if os.path.exists(parent):
            logger.info(f"Contenu de {parent} : {os.listdir(parent)}")
        return None

    files = os.listdir(DB_DIR)
    logger.info(f"Fichiers dans chroma_db : {files}")

    if not any(".sqlite3" in f or "index" in f for f in files):
        logger.warning("chroma_db present mais semble vide ou corrompu.")
        return None

    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        vs = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
        logger.info("Vectorstore charge avec succes.")
        try:
            import streamlit as st
            st.session_state["_chroma_ok"] = True
        except Exception:
            pass
        return vs
    except Exception as exc:
        logger.error(f"Erreur chargement vectorstore : {exc}", exc_info=True)
        return None


def build_vectorstore():
    """
    Reconstruit entierement le vectorstore a partir des documents sources.
    A executer localement apres un scraping ou mise a jour des donnees.
    """
    logger.info("Demarrage construction du vectorstore...")

    documents = load_documents()
    if not documents:
        logger.error("Aucun document trouve -- construction annulee.")
        return None

    chunks = split_documents(documents)
    logger.info(f"{len(chunks)} chunks prets a indexer.")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    os.makedirs(DB_DIR, exist_ok=True)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_DIR,
    )
    logger.info(f"Vectorstore construit et sauvegarde dans {DB_DIR}.")
    return vectorstore


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_vectorstore()
