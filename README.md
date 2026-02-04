# 🌱 Tèwou Agro-Assistant - Projet IA & Web Scrapping

Ce projet est un assistant conversationnel intelligent conçu pour accompagner les agriculteurs sénégalais. Il utilise une architecture **RAG (Retrieval-Augmented Generation)** avancée, une interface vocale naturelle et un design ergonomique optimisé sur le thème "Dark Emerald".

## ✨ Nouvelles Fonctionnalités (Février 2026)

### 🎨 Interface "Dark Emerald" (Design Premium)
- **Thème Visuel** : Dégradé Vert Sombre / Noir (`#0a2e1a` -> `#000000`) pour une identité forte et apaisante.
- **Lisibilité Maximale** : Textes et labels en Blanc pur (`#FFFFFF`) pour un contraste parfait.
- **Sidebar Unifiée** : Fond assorti au thème principal (dégradé continu).
- **Icônes Personnalisées** : 🧑‍🌾 (Utilisateur) et 🌱 (Assistant Tèwou).
- **Layout Ergonomique** : Barre de saisie fixée en bas avec fond vert dégradé, microphone intégré.
- **Bouton "Nouveau Chat"** : Couleur verte pour cohérence visuelle.

### 🎙️ Interaction Vocale & Multimodale
- **Speech-to-Text (STT)** : Posez vos questions à la voix via le bouton microphone dédié.
- **Text-to-Speech (TTS)** : L'assistant lit ses réponses à haute voix UNIQUEMENT si vous utilisez le micro.
- **Mode Hybride** : Basculez fluidement entre saisie texte (silencieux) et vocal (parlé).

### ⚡ Performance & Intelligence
- **Streaming en Temps Réel** : Les réponses s'affichent mot à mot pour une meilleure réactivité.
- **Indicateurs de Statut** : Visualisation des étapes (Reformulation, Recherche, Rédaction).
- **Vitesse Optimisée** : Mise en cache (`st.cache_resource`) du modèle vectoriel.
- **Mémoire Contextuelle** : Gestion des questions de suivi (ex: "Et pour l'engrais ?") grâce à une reformulation intelligente.
- **Recherche Affinée** : Recherche vectorielle optimisée (`k=3`) pour plus de pertinence.
- **Introduction Smart** : L'assistant ne se présente qu'au tout premier message.

### 💾 Persistance des Conversations
- **Sauvegarde Automatique** : Toutes les conversations sont enregistrées dans `ia/data/chat_history.json`.
- **Historique Cliquable** : Retrouvez et rechargez vos anciennes discussions depuis la sidebar.
- **Recherche Intelligente** : Filtrez vos conversations par mots-clés (titre ou contenu).
- **Titres Automatiques** : Chaque conversation reçoit un titre basé sur la première question.

---

## 📂 Structure du Projet

### 1. [IA & Assistant](ia/)
Le cœur de l'application :
- **`app.py`** : Interface Streamlit principale (UI/UX, Gestion d'état, CSS).
- **`src/rag_chain.py`** : Moteur d'intelligence (LangChain, Cohere, Prompts dynamiques, Streaming).
- **`src/build_vectorstore.py`** : Gestion de la base de données ChromaDB (avec caching).
- **`src/utils/chat_manager.py`** : Gestion de la persistance des conversations (JSON).
- **`src/utils/metadata.py`** : Extraction des métadonnées des documents.

### 2. [Web Scrapping](web_scrapping/)
Outils d'alimentation de la base de connaissances :
- **`main.py`** : Orchestrateur de la collecte de données.
- **`data_collection/`** : Documents PDF et JSON indexés.

### 3. Fichiers de Configuration
- **`requirements.txt`** : Dépendances Python pour le déploiement.
- **`.streamlit/config.toml`** : Configuration Streamlit (thème, serveur).
- **`.gitignore`** : Fichiers à exclure du versioning.
- **`.env.example`** : Template pour les variables d'environnement.

---

## 🚀 Démarrage Rapide

### Installation
```powershell
# Cloner le projet
git clone <votre-repo>
cd projet_assistant_ia

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et ajouter votre COHERE_API_KEY
```

### Lancer l'Assistant
```powershell
cd ia
streamlit run app.py
```

L'application sera accessible sur `http://localhost:8501`

---

## 🌐 Déploiement

### Option 1 : Streamlit Community Cloud (Recommandé - Gratuit)
1. Créer un compte sur [share.streamlit.io](https://share.streamlit.io)
2. Connecter votre repository GitHub
3. Configurer les secrets :
   - `COHERE_API_KEY` : Votre clé API Cohere
4. Déployer en un clic !

### Option 2 : Hugging Face Spaces
1. Créer un compte sur [huggingface.co](https://huggingface.co)
2. Créer un nouveau Space (type: Streamlit)
3. Uploader votre code
4. Configurer les variables d'environnement dans Settings

### Option 3 : Render / Railway
1. Connecter votre repo GitHub
2. Configurer la commande de démarrage : `streamlit run ia/app.py`
3. Ajouter les variables d'environnement

### ⚠️ Notes de Déploiement
- **ChromaDB** : Le dossier `ia/chroma_db/` doit être inclus ou régénéré au démarrage.
- **Secrets** : Ne jamais pousser `.env` dans Git ! Utilisez les systèmes de secrets de chaque plateforme.
- **Audio** : Les fonctionnalités STT/TTS peuvent nécessiter des permissions spéciales selon la plateforme.
- **Persistance** : Pour la production, envisagez une vraie base de données (PostgreSQL) au lieu de `chat_history.json`.

---

## 📋 Changelog

### Version 2.0 (Février 2026)
- ✅ Streaming des réponses en temps réel
- ✅ Indicateurs de statut visuels
- ✅ Persistance des conversations (JSON)
- ✅ Recherche dans l'historique
- ✅ Interface "Dark Emerald" complète
- ✅ Bouton "Nouveau Chat" vert
- ✅ Optimisation de la barre de saisie (fond vert transparent)
- ✅ Fichiers de déploiement (requirements.txt, config.toml, .gitignore)

### Version 1.0 (Janvier 2026)
- ✅ Interface vocale (STT/TTS)
- ✅ RAG avec ChromaDB et Cohere
- ✅ Gestion des questions de suivi
- ✅ Design "Dark Emerald" initial

---

## 🛠️ Technologies Utilisées

- **Frontend** : Streamlit
- **LLM** : Cohere (command-r-08-2024)
- **Embeddings** : sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
- **Vector Store** : ChromaDB
- **Framework** : LangChain
- **Audio** : SpeechRecognition, gTTS
- **Scraping** : BeautifulSoup4, Requests

---

**Développé pour Tèwou - Propulser l'agriculture sénégalaise par l'IA.**  
Fait par **Fadel ADAM**
