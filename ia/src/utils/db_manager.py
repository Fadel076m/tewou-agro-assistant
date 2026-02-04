import os
import logging
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import uuid
import time
from datetime import datetime
from supabase import create_client, Client
import streamlit as st
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement (.env)
load_dotenv()

# --- CONFIGURATION SUPABASE ---

def get_supabase_client():
    """Initialise et retourne le client Supabase."""
    global supabase
    if supabase is not None:
        return supabase
    
    # 1. Tentative via variables d'environnement (local .env ou injected secrets)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    # 2. Fallback via st.secrets (Propre à Streamlit Cloud)
    if not url or not key:
        try:
            url = url or st.secrets.get("SUPABASE_URL")
            key = key or st.secrets.get("SUPABASE_KEY")
        except:
            pass
            
    if url and key:
        try:
            supabase = create_client(url, key)
            logger.info("Client Supabase initialisé avec succès.")
            return supabase
        except Exception as e:
            logger.error(f"Erreur initialisation client Supabase: {e}")
    else:
        logger.warning(f"SUPABASE_URL ou SUPABASE_KEY manquante. URL: {'OK' if url else 'MISSING'}, KEY: {'OK' if key else 'MISSING'}")
    return None

# Tentative d'initialisation au chargement
get_supabase_client()

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
        
        # Table des sessions (avec user_id optionnel pour compatibilité)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                user_id UUID,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Index pour optimiser les requêtes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id ON chat_sessions(session_id);
            CREATE INDEX IF NOT EXISTS idx_user_id ON chat_sessions(user_id);
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

# --- FONCTIONS AUTHENTIFICATION ---

def sign_up(email, password):
    """Créer un compte utilisateur."""
    client = get_supabase_client()
    if not client:
        return None, "Configuration Supabase manquante (URL/KEY)."
    try:
        res = client.auth.sign_up({"email": email, "password": password})
        return res.user, None
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    """Se connecter."""
    client = get_supabase_client()
    if not client:
        return None, "Configuration Supabase manquante (URL/KEY)."
    try:
        res = client.auth.sign_in_with_password({"email": email, "password": password})
        return res.user, None
    except Exception as e:
        return None, str(e)

def sign_out():
    """Se déconnecter."""
    client = get_supabase_client()
    if client:
        try:
            client.auth.sign_out()
            return True
        except:
            pass
    return False

# --- GESTION DES CHATS ---

def create_new_session():
    """Génère un nouvel ID de session."""
    return str(uuid.uuid4())

def save_chat(session_id, messages, user_id=None, title=None):
    """Sauvegarde ou met à jour une session de chat."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return None
        
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
                "INSERT INTO chat_sessions (session_id, user_id, title) VALUES (%s, %s, %s)",
                (session_id, user_id, auto_title)
            )
        else:
            # Mettre à jour le timestamp et potentiellement le user_id si manquant
            cursor.execute(
                "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP, user_id = COALESCE(user_id, %s) WHERE session_id = %s",
                (user_id, session_id)
            )
        
        # Supprimer les anciens messages et réinsérer
        cursor.execute("DELETE FROM chat_messages WHERE session_id = %s", (session_id,))
        
        for msg in messages:
            cursor.execute(
                "INSERT INTO chat_messages (session_id, role, content) VALUES (%s, %s, %s)",
                (session_id, msg["role"], msg["content"])
            )
        
        conn.commit()
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)

def load_all_chats(user_id=None):
    """Charge toutes les sessions de chat filtrées par utilisateur."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if user_id:
            cursor.execute("""
                SELECT session_id, title, 
                       EXTRACT(EPOCH FROM created_at) as created_at,
                       EXTRACT(EPOCH FROM updated_at) as updated_at
                FROM chat_sessions
                WHERE user_id = %s OR user_id IS NULL
                ORDER BY updated_at DESC
            """, (user_id,))
        else:
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

def delete_chat(session_id):
    """Supprime une session."""
    conn = None
    try:
        conn = get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_sessions WHERE session_id = %s", (session_id,))
        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
    finally:
        if conn: release_connection(conn)

def delete_all_chats(user_id=None):
    """Supprime toutes les sessions de chat (d'un utilisateur)."""
    conn = None
    try:
        conn = get_connection()
        if not conn: return False
        cursor = conn.cursor()
        if user_id:
            cursor.execute("DELETE FROM chat_sessions WHERE user_id = %s", (user_id,))
        else:
            cursor.execute("DELETE FROM chat_sessions")
        conn.commit()
        return True
    except Exception as e:
        if conn: conn.rollback()
        return False
    finally:
        if conn: release_connection(conn)

init_db_pool()

