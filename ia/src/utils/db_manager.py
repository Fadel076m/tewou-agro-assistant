import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import uuid
import time
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pool de connexions PostgreSQL
connection_pool = None

def init_db_pool():
    """Initialise le pool de connexions PostgreSQL."""
    global connection_pool
    
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        logger.warning("DATABASE_URL non définie. Utilisation du mode JSON fallback.")
        return None
    
    logger.info("DATABASE_URL détectée. Tentative de connexion PostgreSQL...")
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 10,  # min et max connexions
            database_url
        )
        logger.info("Pool de connexions PostgreSQL initialisé avec succès.")
        
        # Créer les tables si elles n'existent pas
        create_tables()
        return connection_pool
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du pool PostgreSQL: {e}")
        return None

def create_tables():
    """Crée les tables nécessaires si elles n'existent pas."""
    conn = None
    try:
        conn = connection_pool.getconn()
        cursor = conn.cursor()
        
        # Table des sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Index pour optimiser les requêtes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id ON chat_sessions(session_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_updated_at ON chat_sessions(updated_at DESC);
        """)
        
        # Table des messages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_message_session ON chat_messages(session_id);
        """)
        
        conn.commit()
        logger.info("Tables créées avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de la création des tables: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            connection_pool.putconn(conn)

def get_connection():
    """Récupère une connexion du pool."""
    if connection_pool is None:
        init_db_pool()
    
    if connection_pool:
        return connection_pool.getconn()
    return None

def release_connection(conn):
    """Libère une connexion vers le pool."""
    if connection_pool and conn:
        connection_pool.putconn(conn)

def create_new_session():
    """Génère un nouvel ID de session."""
    return str(uuid.uuid4())

def save_chat(session_id, messages, title=None):
    """Sauvegarde ou met à jour une session de chat."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            # Fallback vers JSON si pas de connexion
            from src.utils.chat_manager import save_chat as json_save
            return json_save(session_id, messages, title)
        
        cursor = conn.cursor()
        
        # Vérifier si la session existe
        cursor.execute("SELECT id FROM chat_sessions WHERE session_id = %s", (session_id,))
        session_exists = cursor.fetchone()
        
        if not session_exists:
            # Créer la session
            auto_title = title or "Nouvelle discussion"
            if not title and len(messages) > 0:
                first_user_msg = next((m["content"] for m in messages if m["role"] == "user"), None)
                if first_user_msg:
                    auto_title = (first_user_msg[:30] + '...') if len(first_user_msg) > 30 else first_user_msg
            
            cursor.execute(
                "INSERT INTO chat_sessions (session_id, title) VALUES (%s, %s)",
                (session_id, auto_title)
            )
        else:
            # Mettre à jour le timestamp
            cursor.execute(
                "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = %s",
                (session_id,)
            )
        
        # Supprimer les anciens messages et réinsérer
        cursor.execute("DELETE FROM chat_messages WHERE session_id = %s", (session_id,))
        
        for msg in messages:
            cursor.execute(
                "INSERT INTO chat_messages (session_id, role, content) VALUES (%s, %s, %s)",
                (session_id, msg["role"], msg["content"])
            )
        
        conn.commit()
        logger.info(f"Session {session_id} sauvegardée avec {len(messages)} messages.")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)

def load_all_chats():
    """Charge toutes les sessions de chat."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            # Fallback vers JSON
            from src.utils.chat_manager import load_all_chats as json_load
            return json_load()
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT session_id, title, 
                   EXTRACT(EPOCH FROM created_at) as created_at,
                   EXTRACT(EPOCH FROM updated_at) as updated_at
            FROM chat_sessions
            ORDER BY updated_at DESC
        """)
        
        sessions = cursor.fetchall()
        
        result = {}
        for session in sessions:
            # Charger les messages
            cursor.execute("""
                SELECT role, content 
                FROM chat_messages 
                WHERE session_id = %s 
                ORDER BY created_at
            """, (session['session_id'],))
            
            messages = [{"role": m["role"], "content": m["content"]} for m in cursor.fetchall()]
            
            result[session['session_id']] = {
                "title": session['title'],
                "created_at": session['created_at'],
                "updated_at": session['updated_at'],
                "messages": messages
            }
        
        return result
    except Exception as e:
        logger.error(f"Erreur lors du chargement: {e}")
        return {}
    finally:
        if conn:
            release_connection(conn)

def get_chat(session_id):
    """Récupère une session spécifique."""
    chats = load_all_chats()
    return chats.get(session_id, None)

def delete_chat(session_id):
    """Supprime une session."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            from src.utils.chat_manager import delete_chat as json_delete
            return json_delete(session_id)
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_sessions WHERE session_id = %s", (session_id,))
        conn.commit()
        logger.info(f"Session {session_id} supprimée.")
    except Exception as e:
        logger.error(f"Erreur lors de la suppression: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)

def delete_all_chats():
    """Supprime toutes les sessions de chat."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            # Pour le fallback JSON (on supprime le contenu du fichier)
            import json
            from src.utils.chat_manager import HISTORY_PATH
            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump({}, f)
            return True
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_sessions")
        conn.commit()
        logger.info("Toutes les sessions ont été supprimées.")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la suppression totale: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            release_connection(conn)

# Initialiser le pool au chargement du module
init_db_pool()
