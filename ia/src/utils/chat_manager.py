import json
import os
import time
import uuid

# Chemin du fichier de stockage
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "chat_history.json")

def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

def load_all_chats():
    """Charge tour l'historique des discussions."""
    _ensure_data_dir()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur chargement historique: {e}")
        return {}

def save_chat(session_id, messages, title=None):
    """Sauvegarde ou met à jour une discussion."""
    _ensure_data_dir()
    chats = load_all_chats()
    
    if session_id not in chats:
        chats[session_id] = {
            "created_at": time.time(),
            "title": title or "Nouvelle discussion",
            "messages": []
        }
    
    # Mise à jour
    chats[session_id]["updated_at"] = time.time()
    chats[session_id]["messages"] = messages
    
    # Si le titre n'est pas défini et qu'on a un message utilisateur, l'utiliser comme titre
    if chats[session_id]["title"] == "Nouvelle discussion" and len(messages) > 0:
        first_user_msg = next((m["content"] for m in messages if m["role"] == "user"), None)
        if first_user_msg:
            # Tronquer le titre
            chats[session_id]["title"] = (first_user_msg[:30] + '...') if len(first_user_msg) > 30 else first_user_msg

    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(chats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur sauvegarde historique: {e}")

def delete_chat(session_id):
    """Supprime une discussion."""
    chats = load_all_chats()
    if session_id in chats:
        del chats[session_id]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(chats, f, ensure_ascii=False, indent=2)

def get_chat(session_id):
    """Récupère une discussion spécifique."""
    chats = load_all_chats()
    return chats.get(session_id, None)

def create_new_session():
    """Génère un nouvel ID de session."""
    return str(uuid.uuid4())
