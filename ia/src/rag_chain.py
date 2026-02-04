import os
import logging
from dotenv import load_dotenv
from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from src.build_vectorstore import get_vectorstore

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def query_rag(question, soil_type="Non spécifié", location="Sénégal", chat_history=None):
    """
    Exécute une requête via la chaîne RAG avec agent de reformulation pour les follow-ups.
    Générateur qui yield des événements de type:
    - {"type": "status", "content": "Message de statut..."}
    - {"type": "chunk", "content": "Texte partiel de la réponse..."}
    """
    if chat_history is None:
        chat_history = []
        
    # --- PHASE 0 : VÉRIFICATIONS ---
    yield {"type": "status", "content": "Vérification de la base de connaissances..."}
    vectorstore = get_vectorstore()
    if not vectorstore:
        yield {"type": "chunk", "content": "Désolé, la base de connaissances n'est pas disponible actuellement."}
        return
        
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = ChatCohere(model="command-r-08-2024")
    
    def format_history(history):
        formatted = ""
        for user_msg, ai_msg in history:
            formatted += f"Utilisateur: {user_msg}\nAssistant: {ai_msg}\n"
        return formatted

    # --- ÉTAPE 1 : CONTEXTUALISATION ---
    # Cette étape transforme une question de suivi (ex: "Et pour l'engrais ?") 
    # en une question autonome compréhensible par le moteur de recherche.
    
    contextualize_template = """
    Étant donné l'historique de la conversation et la question actuelle de l'utilisateur, 
    si la question fait référence à des éléments précédents, reformulez-la en une question autonome 
    qui peut être comprise sans l'historique. Ne répondez pas à la question, reformulez-la simplement.
    Si la question est déjà autonome, renvoyez-la telle quelle.
    
    HISTORIQUE :
    {chat_history}
    
    QUESTION ACTUELLE : {question}
    
    QUESTION AUTONOME REFORMULÉE :
    """
    contextualize_prompt = ChatPromptTemplate.from_template(contextualize_template)
    contextualize_chain = contextualize_prompt | llm | StrOutputParser()
    
    standalone_question = question
    if chat_history:
        yield {"type": "status", "content": "Compréhension du contexte..."}
        standalone_question = contextualize_chain.invoke({
            "chat_history": format_history(chat_history),
            "question": question
        })
        logger.info(f"Question reformulée : {standalone_question}")

    # --- ÉTAPE 2 : RÉPONSE FINALE AVEC RAG ---
    yield {"type": "status", "content": "Recherche d'informations pertinentes..."}
    
    # Prompt système ultra-structuré 
    template = """
    # 🎯 IDENTITÉ ET MANDAT
    Vous êtes **Tèwou Agro-Assistant**, un expert agricole sénégalais virtuel. Votre mission est d'accompagner les agriculteurs avec des conseils pratiques, précis et bienveillants, exclusivement centrés sur l'agriculture au Sénégal.

    # 📜 RÈGLES DE FONCTIONNEMENT
    ## DOMAINE D'EXPERTISE (NON-NÉGOCIABLE)
    - ✅ **SUJETS AUTORISÉS** : Agriculture sénégalaise, cultures locales, sols, climat, météo, saisons, irrigation, fertilisation, protection des cultures, calendriers culturaux
    - ❌ **SUJETS REFUSÉS** : Toute question hors agriculture sénégalaise, politique, économie générale, santé humaine, technologie hors agriculture
    - **RÈGLE D'OR** : Si une question sort de votre domaine, répondez chaleureusement mais fermement : *"Je suis désolé, je suis spécialisé uniquement dans l'agriculture sénégalaise. Je peux vous aider avec des questions sur les cultures, le sol, la météo ou les pratiques agricoles au Sénégal."*

    ## QUALITÉS REQUISES
    - **Praticité** : Toujours donner des conseils applicables immédiatement
    - **Précision** : Utiliser les données contextuelles (sol, localisation)
    - **Empathie** : Comprendre les difficultés des agriculteurs
    - **Clarté** : Expliquer les termes techniques simplement

    # 📊 CONTEXTE UTILISATEUR (PERSONNALISATION)
    **Profil agricole :**
    - 🌱 **Type de sol** : {soil_type}
    - 📍 **Localisation** : {location}

    # 📚 BASE DE CONNAISSANCES (CONTEXTE RÉCUPÉRÉ)
    {context}

    # 💬 HISTORIQUE DE CONVERSATION (POUR RÉFÉRENCE)
    {chat_history}

    # 🎤 QUESTION (CONSOLIDÉE)
    {question}

    # ✨ INSTRUCTIONS DE RÉPONSE
    0. **{introduction_instruction}**
    1. **Accueil chaleureux** (Rapide si ce n'est pas le début)
    2. **Réponse structurée** basée sur le contexte et votre expertise
    3. **Application locale** liée à {soil_type} et {location}
    4. **Citation des sources** (ex: "Selon les données météo...")

    **Commencez maintenant votre réponse :
    """

    prompt = ChatPromptTemplate.from_template(template)
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Détermination de l'instruction de présentation
    intro_text = "Présentez-vous brièvement comme Tèwou Agro-Assistant." if not chat_history else "NE VOUS PRÉSENTEZ PAS. Répondez directement à la question."

    # Pour le streaming, on doit construire la chaîne légèrement différemment pour récupérer les documents si besoin,
    # mais pour simplifier ici on garde la structure et on stream la réponse finale.
    
    # 1. Récupération explicite des docs (pour pouvoir logger ou yield si besoin)
    docs = retriever.invoke(standalone_question)
    formatted_context = format_docs(docs)
    
    yield {"type": "status", "content": "Rédaction de la réponse..."}

    # 2. Chaîne de génération finale
    final_chain = prompt | llm | StrOutputParser()
    
    response_stream = final_chain.stream({
        "context": formatted_context,
        "chat_history": format_history(chat_history),
        "question": question,
        "soil_type": soil_type,
        "location": location,
        "introduction_instruction": intro_text
    })
    
    for chunk in response_stream:
        yield {"type": "chunk", "content": chunk}

if __name__ == "__main__":
    # Quick test
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    
    if args.test:
        print("Test de la chaîne RAG...")
        # Since it's a generator now, we iterate
        for event in query_rag("Quel est le meilleur moment pour semer le mil au Sénégal ?"):
            if event["type"] == "chunk":
                print(event["content"], end="", flush=True)
            elif event["type"] == "status":
                print(f"\n[STATUS: {event['content']}]\n")
        print("\n\nFin du test.")
