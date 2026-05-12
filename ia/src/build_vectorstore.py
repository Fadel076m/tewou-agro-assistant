import os
import logging
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from src.data_processing import load_documents, split_documents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
# Utilisation de os.path.dirname(os.path.abspath(__file__)) pour garantir le chemin correct
CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
# On remonte de 'src' vers 'ia'
BASE_DIR = os.path.dirname(CURRENT_FILE_DIR)
DB_DIR = os.path.join(BASE_DIR, "chroma_db")
# Model for multilingual support (French/Wolof/etc.)
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def build_vectorstore():
    """
    Builds and persists a Chroma vector store.
    """
    logger.info("Starting to build vector store...")
    
    # Load and split documents
    documents = load_documents()
    if not documents:
        logger.error("No documents found to index.")
        return
        
    chunks = split_documents(documents)
    
    # Initialize embeddings
    logger.info(f"Initializing embedding model: {EMBEDDING_MODEL_NAME}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    # Create and persist Chroma DB
    logger.info(f"Creating vector store in {DB_DIR}...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_DIR
    )
    
    logger.info("Vector store built and persisted successfully.")
    return vectorstore

try:
    import streamlit as st
    cache_decorator = st.cache_resource
except ImportError:
    from functools import lru_cache
    cache_decorator = lru_cache(maxsize=1)

@cache_decorator
def get_vectorstore():
    """
    Loads the existing vector store. Cached to prevent reloading.
    """
    logger.info(f"Recherche de la base vectorielle à: {DB_DIR}")
    
    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        
        # Vérification détaillée du dossier
        if not os.path.exists(DB_DIR):
            logger.error(f"ERREUR CRITIQUE : Le dossier {DB_DIR} n'existe pas.")
            # Diagnostic : Lister le dossier parent pour voir où on est
            parent = os.path.dirname(DB_DIR)
            if os.path.exists(parent):
                logger.info(f"Contenu de {parent} : {os.listdir(parent)}")
            else:
                logger.error(f"Même le dossier parent {parent} est introuvable !")
            return None

        logger.info("Base vectorielle trouvée sur le disque. Chargement...")
        files = os.listdir(DB_DIR)
        logger.info(f"Fichiers détectés dans chroma_db : {files}")
        
        # Vérification qu'on a bien les fichiers essentiels de Chroma
        if not any(".sqlite3" in f or "index" in f for f in files):
            logger.warning("Le dossier chroma_db semble vide ou corrompu.")
            return None

        return Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
        
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la base vectorielle: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

if __name__ == "__main__":
    build_vectorstore()
