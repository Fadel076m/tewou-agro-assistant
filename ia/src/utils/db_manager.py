"""
src/utils/db_manager.py — Gestion de la base PostgreSQL et de l'Auth Supabase.

Architecture :
  - get_supabase_client()  : client Supabase (auth)
  - db_connection()        : context manager PostgreSQL (pool)
  - CRUD sessions/messages : save_chat, load_all_chats, delete_chat, …
  - Auth                   : sign_up, sign_in, sign_out
"""
import os
import logging
import uuid
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool as psycopg2_pool
from psycopg2.extras import RealDictCursor
from supabase import create_client, Client
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Client Supabase (singleton) ───────────────────────────────────────────────

_supabase: Client | None = None


def get_supabase_client() -> Client | None:
    """Retourne le client Supabase (lazy init, singleton)."""
    global _supabase
    if _supabase is not None:
        return _supabase

    url = os.getenv("SUPABASE_URL") or _secret("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or _secret("SUPABASE_KEY")

    if url and key:
        try:
            _supabase = create_client(url, key)
            logger.info("Client Supabase initialisé.")
            return _supabase
        except Exception as exc:
            logger.error(f"Supabase init error: {exc}")
    else:
        logger.warning("Clés Supabase manquantes (SUPABASE_URL / SUPABASE_KEY).")
    return None


# ── Pool PostgreSQL ───────────────────────────────────────────────────────────

_pool: psycopg2_pool.SimpleConnectionPool | None = None


def _get_pool() -> psycopg2_pool.SimpleConnectionPool | None:
    """Initialise et retourne le pool de connexions (lazy init, singleton)."""
    global _pool
    if _pool is not None:
        return _pool

    database_url = os.getenv("DATABASE_URL") or _secret("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL non définie — base de données indisponible.")
        return None

    try:
        _pool = psycopg2_pool.SimpleConnectionPool(1, 10, database_url)
        logger.info("Pool PostgreSQL initialisé.")
        _create_tables()
        return _pool
    except Exception as exc:
        logger.error(f"PostgreSQL pool init error: {exc}")
        return None


@contextmanager
def db_connection():
    """
    Context manager pour les connexions PostgreSQL.

    Usage:
        with db_connection() as conn:
            cursor = conn.cursor()
            ...
        # commit automatique à la sortie, rollback en cas d'exception
    """
    current_pool = _get_pool()
    if current_pool is None:
        raise RuntimeError("Base de données non disponible.")

    conn = current_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        current_pool.putconn(conn)


# ── Création des tables ───────────────────────────────────────────────────────

def _create_tables() -> None:
    """Crée les tables nécessaires si elles n'existent pas encore."""
    current_pool = _get_pool()
    if not current_pool:
        return
    conn = current_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id          SERIAL PRIMARY KEY,
                    session_id  VARCHAR(255) UNIQUE NOT NULL,
                    user_id     UUID,
                    title       TEXT,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_session_id  ON chat_sessions(session_id);
                CREATE INDEX IF NOT EXISTS idx_user_id     ON chat_sessions(user_id);
                CREATE INDEX IF NOT EXISTS idx_updated_at  ON chat_sessions(updated_at DESC);
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id          SERIAL PRIMARY KEY,
                    session_id  VARCHAR(255) NOT NULL
                                    REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
                    role        VARCHAR(50)  NOT NULL,
                    content     TEXT         NOT NULL,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_message_session ON chat_messages(session_id);
            """)
        conn.commit()
        logger.info("Tables PostgreSQL vérifiées/créées.")
    except Exception as exc:
        conn.rollback()
        logger.error(f"Erreur création tables : {exc}")
    finally:
        current_pool.putconn(conn)


# ── Auth Supabase ─────────────────────────────────────────────────────────────

def sign_up(email: str, password: str) -> tuple:
    """Crée un compte utilisateur. Retourne (user, error_msg)."""
    client = get_supabase_client()
    if not client:
        return None, "Configuration Supabase manquante."
    try:
        res = client.auth.sign_up({"email": email, "password": password})
        return res.user, None
    except Exception as exc:
        return None, str(exc)


def sign_in(email: str, password: str) -> tuple:
    """Connecte un utilisateur. Retourne (user, error_msg)."""
    client = get_supabase_client()
    if not client:
        return None, "Configuration Supabase manquante."
    try:
        res = client.auth.sign_in_with_password({"email": email, "password": password})
        return res.user, None
    except Exception as exc:
        return None, str(exc)


def sign_out() -> bool:
    """Déconnecte l'utilisateur courant."""
    client = get_supabase_client()
    if client:
        try:
            client.auth.sign_out()
            return True
        except Exception:
            pass
    return False


# ── Gestion des sessions ──────────────────────────────────────────────────────

def create_new_session() -> str:
    """Génère un nouvel UUID de session."""
    return str(uuid.uuid4())


def save_chat(session_id: str, messages: list, user_id=None, title: str | None = None) -> None:
    """
    Sauvegarde ou met à jour une session de chat.
    - Crée la session si elle n'existe pas encore.
    - Génère le titre automatiquement depuis le premier message utilisateur.
    - Remplace tous les messages (approche simple et fiable).
    """
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Vérifier l'existence de la session
                cur.execute(
                    "SELECT id FROM chat_sessions WHERE session_id = %s",
                    (session_id,),
                )
                exists = cur.fetchone()

                if not exists:
                    auto_title = title or _auto_title(messages)
                    cur.execute(
                        "INSERT INTO chat_sessions (session_id, user_id, title) VALUES (%s, %s, %s)",
                        (session_id, user_id, auto_title),
                    )
                else:
                    cur.execute(
                        """UPDATE chat_sessions
                           SET updated_at = CURRENT_TIMESTAMP,
                               user_id    = COALESCE(user_id, %s)
                         WHERE session_id = %s""",
                        (user_id, session_id),
                    )

                # Remplacement des messages
                cur.execute(
                    "DELETE FROM chat_messages WHERE session_id = %s",
                    (session_id,),
                )
                if messages:
                    cur.executemany(
                        "INSERT INTO chat_messages (session_id, role, content) VALUES (%s, %s, %s)",
                        [(session_id, m["role"], m["content"]) for m in messages],
                    )
    except Exception as exc:
        logger.error(f"Erreur save_chat({session_id}): {exc}")


def update_session_title(session_id: str, title: str) -> None:
    """Met à jour le titre d'une session existante."""
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE chat_sessions SET title = %s WHERE session_id = %s",
                    (title, session_id),
                )
    except Exception as exc:
        logger.error(f"Erreur update_session_title: {exc}")


def load_all_chats(user_id=None) -> dict:
    """
    Charge toutes les sessions d'un utilisateur avec leurs messages.

    Returns:
        {session_id: {"title": str, "created_at": float, "updated_at": float, "messages": list}}
    """
    try:
        with db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if user_id:
                    cur.execute(
                        """SELECT session_id, title,
                                  EXTRACT(EPOCH FROM created_at) AS created_at,
                                  EXTRACT(EPOCH FROM updated_at) AS updated_at
                             FROM chat_sessions
                            WHERE user_id = %s
                            ORDER BY updated_at DESC""",
                        (user_id,),
                    )
                else:
                    cur.execute(
                        """SELECT session_id, title,
                                  EXTRACT(EPOCH FROM created_at) AS created_at,
                                  EXTRACT(EPOCH FROM updated_at) AS updated_at
                             FROM chat_sessions
                            ORDER BY updated_at DESC"""
                    )

                sessions = cur.fetchall()
                result = {}

                for session in sessions:
                    cur.execute(
                        """SELECT role, content
                             FROM chat_messages
                            WHERE session_id = %s
                            ORDER BY created_at""",
                        (session["session_id"],),
                    )
                    result[session["session_id"]] = {
                        "title":      session["title"] or "Discussion sans titre",
                        "created_at": float(session["created_at"] or 0),
                        "updated_at": float(session["updated_at"] or 0),
                        "messages":   [
                            {"role": m["role"], "content": m["content"]}
                            for m in cur.fetchall()
                        ],
                    }
                return result
    except Exception as exc:
        logger.error(f"Erreur load_all_chats: {exc}")
        return {}


def delete_chat(session_id: str) -> bool:
    """Supprime une session et ses messages (CASCADE)."""
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM chat_sessions WHERE session_id = %s",
                    (session_id,),
                )
        return True
    except Exception as exc:
        logger.error(f"Erreur delete_chat: {exc}")
        return False


def delete_all_chats(user_id=None) -> bool:
    """Supprime toutes les sessions (d'un utilisateur si user_id fourni)."""
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                if user_id:
                    cur.execute(
                        "DELETE FROM chat_sessions WHERE user_id = %s",
                        (user_id,),
                    )
                else:
                    cur.execute("DELETE FROM chat_sessions")
        return True
    except Exception as exc:
        logger.error(f"Erreur delete_all_chats: {exc}")
        return False


# ── Helpers privés ────────────────────────────────────────────────────────────

def _secret(key: str) -> str:
    """Lit une clé depuis st.secrets (Streamlit Cloud)."""
    try:
        return st.secrets.get(key, "") if hasattr(st, "secrets") else ""
    except Exception:
        return ""


def _auto_title(messages: list) -> str:
    """Génère un titre automatique à partir du premier message utilisateur."""
    for m in messages:
        if m.get("role") == "user":
            content = m["content"].strip()
            return (content[:40] + "…") if len(content) > 40 else content
    return "Nouvelle discussion"


# ── Initialisation au chargement ──────────────────────────────────────────────
get_supabase_client()
_get_pool()
