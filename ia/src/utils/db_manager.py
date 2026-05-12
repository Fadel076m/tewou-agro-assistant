"""
src/utils/db_manager.py - Gestion PostgreSQL + Auth Supabase.

Strategie de persistance :
  - session_state : cache rapide en memoire pour la session courante
  - PostgreSQL    : stockage persistant entre sessions

Cycle de vie :
  CONNEXION   -> warm_cache_from_db(user_id)  : DB -> cache
  UTILISATION -> save_chat()                  : cache + DB en meme temps
  DECONNEXION -> sync_cache_to_db()           : cache -> DB (filet de securite)
"""
import os
import logging
import uuid
import time
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool as psycopg2_pool
from psycopg2.extras import RealDictCursor
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_CACHE_KEY = "_tewou_chat_cache"

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _secret(key):
    try:
        import streamlit as st
        return st.secrets.get(key, "") if hasattr(st, "secrets") else ""
    except Exception:
        return ""

def _get_env(key):
    return os.getenv(key, "") or _secret(key)

# ---------------------------------------------------------------------------
# CLIENT SUPABASE (singleton)
# ---------------------------------------------------------------------------

_supabase = None

def get_supabase_client():
    global _supabase
    if _supabase is not None:
        return _supabase
    url = _get_env("SUPABASE_URL")
    key = _get_env("SUPABASE_KEY")
    if url and key:
        try:
            _supabase = create_client(url, key)
            logger.info("Client Supabase initialise.")
        except Exception as exc:
            logger.error(f"Supabase init error: {exc}")
    else:
        logger.warning("Cles Supabase manquantes.")
    return _supabase

# ---------------------------------------------------------------------------
# POOL POSTGRESQL
# ---------------------------------------------------------------------------

_pool = None
_pool_failed = False

def _get_pool():
    global _pool, _pool_failed
    if _pool is not None:
        return _pool
    if _pool_failed:
        return None

    database_url = _get_env("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL non definie - mode cache uniquement.")
        _pool_failed = True
        return None

    # Supabase requiert sslmode=require
    if "supabase" in database_url and "sslmode" not in database_url:
        sep = "&" if "?" in database_url else "?"
        database_url += f"{sep}sslmode=require"

    try:
        _pool = psycopg2_pool.SimpleConnectionPool(1, 10, database_url)
        logger.info("Pool PostgreSQL initialise.")
        _create_tables()
    except Exception as exc:
        logger.error(f"PostgreSQL pool init error: {exc}")
        _pool_failed = True
        _pool = None
    return _pool


@contextmanager
def db_connection():
    """Context manager PostgreSQL - commit auto, rollback en cas d'erreur."""
    current_pool = _get_pool()
    if current_pool is None:
        raise RuntimeError("Base de donnees non disponible.")
    conn = current_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        current_pool.putconn(conn)

# ---------------------------------------------------------------------------
# CREATION DES TABLES
# ---------------------------------------------------------------------------

def _create_tables():
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
                    user_id     TEXT,
                    title       TEXT,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_session_id ON chat_sessions(session_id);
                CREATE INDEX IF NOT EXISTS idx_user_id    ON chat_sessions(user_id);
                CREATE INDEX IF NOT EXISTS idx_updated_at ON chat_sessions(updated_at DESC);
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
        logger.info("Tables PostgreSQL verifiees/creees.")
    except Exception as exc:
        conn.rollback()
        logger.error(f"Erreur creation tables : {exc}")
    finally:
        current_pool.putconn(conn)

# ---------------------------------------------------------------------------
# CACHE SESSION_STATE (Niveau 1 - toujours disponible)
# ---------------------------------------------------------------------------

def _cache_save(session_id, messages, user_id=None, title=None):
    """Sauvegarde dans le cache session_state."""
    try:
        import streamlit as st
        if _CACHE_KEY not in st.session_state:
            st.session_state[_CACHE_KEY] = {}
        cache = st.session_state[_CACHE_KEY]
        uid = str(user_id) if user_id else None
        now = time.time()
        if session_id not in cache:
            cache[session_id] = {
                "title":      title or _auto_title(messages),
                "created_at": now,
                "updated_at": now,
                "messages":   list(messages),
                "user_id":    uid,
            }
        else:
            cache[session_id]["updated_at"] = now
            cache[session_id]["messages"] = list(messages)
            if uid:
                cache[session_id]["user_id"] = uid
    except Exception as exc:
        logger.warning(f"Cache save error: {exc}")


def _cache_load(user_id=None):
    """Charge depuis le cache session_state."""
    try:
        import streamlit as st
        cache = st.session_state.get(_CACHE_KEY, {})
        if user_id:
            uid = str(user_id)
            return {k: v for k, v in cache.items() if v.get("user_id") == uid}
        return dict(cache)
    except Exception:
        return {}

# ---------------------------------------------------------------------------
# PERSISTANCE DB - fonctions internes
# ---------------------------------------------------------------------------

def _save_to_db(session_id, messages, user_id=None, title=None):
    """Sauvegarde une session dans PostgreSQL (fonction interne)."""
    uid = str(user_id) if user_id else None
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM chat_sessions WHERE session_id = %s",
                (session_id,)
            )
            if not cur.fetchone():
                auto_title = title or _auto_title(messages)
                cur.execute(
                    "INSERT INTO chat_sessions (session_id, user_id, title)"
                    " VALUES (%s, %s, %s)",
                    (session_id, uid, auto_title)
                )
            else:
                cur.execute(
                    "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP,"
                    " user_id = COALESCE(user_id, %s) WHERE session_id = %s",
                    (uid, session_id)
                )
            cur.execute(
                "DELETE FROM chat_messages WHERE session_id = %s",
                (session_id,)
            )
            if messages:
                cur.executemany(
                    "INSERT INTO chat_messages (session_id, role, content)"
                    " VALUES (%s, %s, %s)",
                    [(session_id, m["role"], m["content"]) for m in messages]
                )


def _load_from_db(user_id=None):
    """Charge toutes les sessions depuis PostgreSQL (fonction interne)."""
    uid = str(user_id) if user_id else None
    result = {}
    with db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if uid:
                cur.execute(
                    "SELECT session_id, title,"
                    " EXTRACT(EPOCH FROM created_at) AS created_at,"
                    " EXTRACT(EPOCH FROM updated_at) AS updated_at"
                    " FROM chat_sessions WHERE user_id = %s"
                    " ORDER BY updated_at DESC",
                    (uid,)
                )
            else:
                cur.execute(
                    "SELECT session_id, title,"
                    " EXTRACT(EPOCH FROM created_at) AS created_at,"
                    " EXTRACT(EPOCH FROM updated_at) AS updated_at"
                    " FROM chat_sessions ORDER BY updated_at DESC"
                )
            sessions = cur.fetchall()
            for session in sessions:
                cur.execute(
                    "SELECT role, content FROM chat_messages"
                    " WHERE session_id = %s ORDER BY created_at",
                    (session["session_id"],)
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

# ---------------------------------------------------------------------------
# SYNCHRONISATION CACHE <-> DB (appels explicites)
# ---------------------------------------------------------------------------

def sync_cache_to_db():
    """
    Pousse TOUTES les sessions du cache session_state vers PostgreSQL.

    A appeler AVANT la deconnexion pour garantir la persistance.
    Retourne le nombre de sessions sauvegardees.
    """
    try:
        import streamlit as st
        cache = st.session_state.get(_CACHE_KEY, {})
        if not cache:
            logger.info("sync_cache_to_db : cache vide, rien a synchroniser.")
            return 0

        saved = 0
        for session_id, data in cache.items():
            messages = data.get("messages", [])
            user_id = data.get("user_id")
            title = data.get("title")
            if not messages:
                continue
            try:
                _save_to_db(session_id, messages, user_id, title)
                saved += 1
            except Exception as exc:
                logger.warning(f"sync: echec pour {session_id[:8]}... : {exc}")

        logger.info(f"sync_cache_to_db : {saved}/{len(cache)} sessions synchronisees.")
        return saved
    except Exception as exc:
        logger.error(f"sync_cache_to_db global error: {exc}")
        return 0


def warm_cache_from_db(user_id):
    """
    Charge les sessions depuis PostgreSQL dans le cache session_state.

    A appeler APRES connexion pour restaurer l'historique de l'utilisateur.
    Retourne le nombre de sessions restaurees.
    """
    try:
        db_chats = _load_from_db(user_id)
        if not db_chats:
            logger.info("warm_cache_from_db : aucune session en base pour cet utilisateur.")
            return 0

        import streamlit as st
        if _CACHE_KEY not in st.session_state:
            st.session_state[_CACHE_KEY] = {}

        cache = st.session_state[_CACHE_KEY]
        uid = str(user_id)
        restored = 0
        for s_id, data in db_chats.items():
            if s_id not in cache:
                cache[s_id] = {**data, "user_id": uid}
                restored += 1

        logger.info(f"warm_cache_from_db : {restored} sessions restaurees depuis la DB.")
        return restored
    except Exception as exc:
        logger.warning(f"warm_cache_from_db error: {exc}")
        return 0

# ---------------------------------------------------------------------------
# AUTH SUPABASE
# ---------------------------------------------------------------------------

def sign_up(email, password):
    client = get_supabase_client()
    if not client:
        return None, "Configuration Supabase manquante."
    try:
        res = client.auth.sign_up({"email": email, "password": password})
        return res.user, None
    except Exception as exc:
        return None, str(exc)


def sign_in(email, password):
    client = get_supabase_client()
    if not client:
        return None, "Configuration Supabase manquante."
    try:
        res = client.auth.sign_in_with_password({"email": email, "password": password})
        return res.user, None
    except Exception as exc:
        return None, str(exc)


def sign_out():
    client = get_supabase_client()
    if client:
        try:
            client.auth.sign_out()
            return True
        except Exception:
            pass
    return False

# ---------------------------------------------------------------------------
# GESTION DES SESSIONS
# ---------------------------------------------------------------------------

def create_new_session():
    return str(uuid.uuid4())


def save_chat(session_id, messages, user_id=None, title=None):
    """
    Sauvegarde a deux niveaux :
      1. Cache session_state (immediat, infaillible)
      2. PostgreSQL (persistant, best-effort)
    """
    _cache_save(session_id, messages, user_id, title)
    try:
        _save_to_db(session_id, messages, user_id, title)
    except Exception as exc:
        logger.warning(f"DB save echoue pour {session_id[:8]}... (cache conserve) : {exc}")


def load_all_chats(user_id=None):
    """
    Charge toutes les sessions. Fusionne DB + cache.
    Si DB indisponible, retourne uniquement le cache.
    """
    uid = str(user_id) if user_id else None
    db_chats = {}
    try:
        db_chats = _load_from_db(uid)
    except Exception as exc:
        logger.warning(f"DB load echoue, fallback cache : {exc}")

    cache = _cache_load(uid)
    merged = dict(db_chats)
    for s_id, data in cache.items():
        if s_id not in merged and len(data.get("messages", [])) > 0:
            merged[s_id] = {k: v for k, v in data.items() if k != "user_id"}
    return merged


def delete_chat(session_id):
    """Supprime du cache ET de la DB."""
    try:
        import streamlit as st
        st.session_state.get(_CACHE_KEY, {}).pop(session_id, None)
    except Exception:
        pass
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM chat_sessions WHERE session_id = %s",
                    (session_id,)
                )
    except Exception as exc:
        logger.warning(f"DB delete echoue (supprime du cache) : {exc}")
    return True


def delete_all_chats(user_id=None):
    """Supprime toutes les sessions du cache ET de la DB."""
    uid = str(user_id) if user_id else None
    try:
        import streamlit as st
        cache = st.session_state.get(_CACHE_KEY, {})
        if uid:
            for k in [k for k, v in cache.items() if v.get("user_id") == uid]:
                del cache[k]
        else:
            st.session_state[_CACHE_KEY] = {}
    except Exception:
        pass
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                if uid:
                    cur.execute("DELETE FROM chat_sessions WHERE user_id = %s", (uid,))
                else:
                    cur.execute("DELETE FROM chat_sessions")
    except Exception as exc:
        logger.warning(f"DB delete_all echoue : {exc}")
    return True


def update_session_title(session_id, title):
    try:
        import streamlit as st
        cache = st.session_state.get(_CACHE_KEY, {})
        if session_id in cache:
            cache[session_id]["title"] = title
    except Exception:
        pass
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE chat_sessions SET title = %s WHERE session_id = %s",
                    (title, session_id)
                )
    except Exception as exc:
        logger.warning(f"DB update_title echoue : {exc}")


def db_status():
    pool_ok = _get_pool() is not None
    try:
        import streamlit as st
        cache_count = len(st.session_state.get(_CACHE_KEY, {}))
    except Exception:
        cache_count = 0
    return {"postgresql": pool_ok, "cache_sessions": cache_count}

# ---------------------------------------------------------------------------
# HELPERS PRIVES
# ---------------------------------------------------------------------------

def _auto_title(messages):
    for m in messages:
        if m.get("role") == "user":
            content = m["content"].strip()
            return (content[:40] + "...") if len(content) > 40 else content
    return "Nouvelle discussion"

# ---------------------------------------------------------------------------
# INITIALISATION
# ---------------------------------------------------------------------------
get_supabase_client()
_get_pool()
