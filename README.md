# 🌱 Tèwou Agro-Assistant - IA Agricole au Sénégal

Tèwou est un assistant conversationnel intelligent conçu pour accompagner les agriculteurs sénégalais. Basé sur une architecture **RAG (Retrieval-Augmented Generation)**, il offre des conseils précis sur les cultures, les sols et les pratiques locales en s'appuyant sur une base de connaissances spécialisée.

---

## 🚀 Nouvelles Fonctionnalités Majeures (Février 2026)

### 🔐 Authentification & Comptes Personnels (Nouveau !)
- **Système de Comptes** : Création de compte et connexion sécurisée via **Supabase Auth**.
- **Espace Privé** : Chaque utilisateur dispose de son propre historique de discussion, protégé et persistant.
- **Gestion simplifiée** : Désactivation possible de la confirmation par email pour un accès immédiat.

### 🐘 Persistance sur PostgreSQL (Migration terminée)
- **Stockage Cloud** : Migration complète du stockage JSON local vers une base de données **PostgreSQL** (via Supabase).
- **Fiabilité** : Vos conversations sont sauvegardées en temps réel et accessibles depuis n'importe quel appareil.
- **Contrôle total** : Boutons de suppression individuelle ou de vidage complet de l'historique dans la sidebar.

### 🎨 Expérience Utilisateur "Dark Emerald" 3.0
- **Design Premium** : Interface immersive en mode sombre avec effets de glassmorphisme et animations subtiles.
- **Interaction Intuitive** : Barre de saisie épurée avec fond dégradé vert émeraude.
- **Diagnostic Intégré** : Outils de diagnostic automatique pour faciliter le déploiement sur Streamlit Cloud.
- **Streaming & Statut** : Réponses générées mot à mot avec indicateurs visuels des étapes de réflexion de l'IA.

---

## 📂 Structure du Projet

### 1. [IA & Assistant](ia/)
- **`app.py`** : Interface Streamlit (Login, Chat, Gestion d'état).
- **`src/rag_chain.py`** : Moteur d'intelligence (LangChain, Cohere, Retrieval).
- **`src/build_vectorstore.py`** : Indexation des documents dans ChromaDB.
- **`src/utils/db_manager.py`** : Orchestrateur de la base PostgreSQL et de l'Auth Supabase.
- **`src/utils/metadata.py`** : Gestion des sources et métadonnées documentaires.

### 2. [Web Scrapping](web_scrapping/)
- Outils de collecte automatisée pour enrichir continuellement la base de connaissances agricole.

---

## 🛠️ Stack Technique

- **Frontend** : Streamlit (Python)
- **Intelligence Artificielle** : 
  - LLM : Cohere (Command-R)
  - Embeddings : Multilingual MiniLM (Sentence-Transformers)
  - Vector Store : ChromaDB
- **Backend & Sécurité** : 
  - Base de données : PostgreSQL
  - Authentification : Supabase Auth
- **Orchestration** : LangChain

---

## 💻 Installation & Démarrage

### Pré-requis
Une clé API Cohere et un projet Supabase configuré.

### Installation
```powershell
git clone <votre-repo>
cd projet_assistant_ia
pip install -r requirements.txt
```

### Configuration (.env)
Créez un fichier `.env` dans le dossier `ia/` :
```env
COHERE_API_KEY=votre_cle
DATABASE_URL=votre_url_postgres
SUPABASE_URL=votre_url_projet
SUPABASE_KEY=votre_cle_anon
```

### Lancement
```powershell
cd ia
streamlit run app.py
```

---

## 🌐 Déploiement

Le projet est optimisé pour **Streamlit Community Cloud**. 
⚠️ **Note importante** : Assurez-vous d'ajouter vos clés dans les **Secrets** de l'interface Streamlit (format TOML) pour activer l'authentification en ligne.

---

**Développé pour Tèwou - Propulser l'agriculture sénégalaise par l'IA.**  
Fait par **Fadel ADAM**
