import os
import logging
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from src.data_processing import load_documents, split_documents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        if os.path.exists(DB_DIR):
            logger.info("Base vectorielle trouvée sur le disque. Chargement...")
            # Vérifier que c'est bien une base Chroma (contient index ou sqlite)
            files = os.listdir(DB_DIR)
            logger.info(f"Fichiers dans {DB_DIR}: {files}")
            return Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
        else:
            logger.warning(f"Répertoire de la base vectorielle non trouvé à: {DB_DIR}")
            # Diagnostic : Lister le contenu du dossier parent
            parent = os.path.dirname(DB_DIR)
            if os.path.exists(parent):
                logger.info(f"Contenu de {parent}: {os.listdir(parent)}")
            return None
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la base vectorielle: {e}")
        return None

if __name__ == "__main__":
    build_vectorstore()
