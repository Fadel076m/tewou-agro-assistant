# 🌱 Tèwou Agro-Assistant

**Tèwou Agro-Assistant** est un assistant conversationnel intelligent (IA) conçu pour accompagner les agriculteurs sénégalais. Il utilise une architecture **RAG (Retrieval-Augmented Generation)** pour fournir des conseils agricoles personnalisés, fiables et contextualisés en fonction du type de sol, de la localisation et des données météorologiques.

---

## 🚀 Fonctionnalités Clés

- **Assistant IA Multilingue** : Répond aux questions en français et en wolof.
- **Scraping Automatisé** : Collecte systématique de données depuis des sources officielles (Banque Mondiale, FAO, Géo Sénégal, sites météo et actualités).
- **Raisonnement Contextualisé** : Adaptation des conseils au type de sol (Dior, Deck, etc.) et à la région spécifiée.
- **Base de Connaissances Dynamique** : Indexation de PDF, rapports et articles web dans une base vectorielle sémantique.
- **Interface Intuitive** : Application web moderne réalisée avec Streamlit.

---

## 📂 Structure du Projet

```text
├── data_collection/           # Dossier racine des données collectées
│   ├── raw_pdfs/              # PDF originaux téléchargés
│   ├── extracted_text/        # Texte brut extrait et nettoyé des PDF
│   ├── web_content/           # Contenu des sites web (JSON)
│   ├── structured_data/       # Données SIG et tableaux (CSV, GeoJSON)
│   ├── logs/                  # Historique des opérations de scraping
│   └── metadata.json          # Index central de tous les documents
├── chroma_db/                 # Base de données vectorielle (ChromaDB)
├── src/                       # Code source Python
│   ├── scrapers/              # Modules de collecte par domaine (Stats, Geo, Meteo, News)
│   ├── utils/                 # Utilitaires (Nettoyage, PDF, Métadonnées)
│   ├── crawler.py             # Classe de base pour le web scraping
│   ├── data_processing.py     # Chargement et découpage des documents
│   ├── build_vectorstore.py   # Génération des embeddings et de la DB
│   └── rag_chain.py           # Logique de la chaîne RAG LangChain
├── app.py                     # Interface utilisateur Streamlit (Point d'entrée)
├── .env                       # Fichier de configuration des clés API
├── .venv/                     # Environnement virtuel Python
└── README.md                  # Documentation du projet
```

---

## 🛠️ Installation et Configuration

### 1. Prérequis
- Python 3.10 ou supérieur.
- Une clé API [Cohere](https://dashboard.cohere.com/api-keys).

### 2. Installation de l'environnement
L'environnement virtuel a déjà été créé. Pour l'activer :
```powershell
.venv\Scripts\Activate.ps1
```

### 3. Installation des dépendances
Si nécessaire, réinstallez les packages :
```powershell
pip install -r requirements.txt
# Ou manuellement :
pip install requests beautifulsoup4 selenium pandas pymupdf langdetect lxml webdriver-manager langchain langchain-community langchain-cohere chromadb sentence-transformers streamlit python-dotenv
```

### 4. Configuration des clés API
Éditez le fichier `.env` à la racine et ajoutez votre clé Cohere :
```text
COHERE_API_KEY=votre_cle_api_ici
```

---

## 📖 Utilisation

### Phase 1 : Collecte des données (Scraping)
Pour lancer une collecte de test (rapide) :
```powershell
$env:PYTHONPATH="."
python src/main.py --test
```
Pour une collecte complète :
```powershell
python src/main.py
```

### Phase 2 : Construction de la base vectorielle (IA)
Pour indexer les documents collectés dans la base de données sémantique :
```powershell
python src/build_vectorstore.py
```

### Phase 3 : Lancement de l'Assistant
Démarrez l'interface utilisateur Streamlit :
```powershell
streamlit run app.py
```

---

## 🧠 Détails Techniques

- **LLM** : Utilise le modèle `command-r-08-2024` de Cohere pour sa compréhension avancée du français.
- **Embeddings** : Modèle multilingue `paraphrase-multilingual-MiniLM-L12-v2` (Hugging Face) pour une recherche sémantique précise.
- **Vector Store** : **ChromaDB** pour un stockage local performant et léger.
- **Orchestration** : **LangChain** pour lier la recherche documentaire à la génération de texte.

---

## 📋 Prochaines Étapes
- Intégration d'une API de météo en temps réel (ex: OpenWeatherMap).
- Ajout d'une mémoire de conversation pour gérer les suivis de questions.
- Expansion de la base de données avec des guides culturels spécifiques par région.

---
**Développé pour Tèwou - Propulser l'agriculture sénégalaise par l'IA.**
