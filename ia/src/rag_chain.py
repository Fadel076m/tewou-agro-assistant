"""
src/rag_chain.py — Moteur RAG de Tèwou Agro-Assistant.

Pipeline :
  1. Contextualisation : reformule les questions de suivi en questions autonomes.
  2. Retrieval : récupère les k documents les plus pertinents depuis ChromaDB.
  3. Génération : Cohere génère la réponse en streaming avec le contexte récupéré.

Fallback : si le vectorstore est indisponible, répond sans contexte documentaire.

Yields des événements :
  {"type": "status", "content": str}   — étape en cours
  {"type": "chunk",  "content": str}   — morceau de la réponse finale
"""
import logging
from typing import Generator

from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import Config
from src.build_vectorstore import get_vectorstore

logger = logging.getLogger(__name__)

Event = dict[str, str]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_history(history: list[tuple[str, str]]) -> str:
    """Formate l'historique de conversation pour le prompt."""
    return "".join(
        f"Utilisateur: {u}\nAssistant: {a}\n"
        for u, a in history
    )


def _format_docs(docs) -> str:
    """Concatène le contenu des documents récupérés."""
    return "\n\n".join(doc.page_content for doc in docs)


# ── Prompts ───────────────────────────────────────────────────────────────────

_CONTEXTUALIZE_TEMPLATE = """
Étant donné l'historique de la conversation et la question actuelle,
si la question fait référence à des éléments précédents, reformulez-la en une
question autonome compréhensible sans l'historique.
Ne répondez PAS à la question — reformulez-la seulement.
Si elle est déjà autonome, renvoyez-la telle quelle.

HISTORIQUE :
{chat_history}

QUESTION ACTUELLE : {question}

QUESTION REFORMULÉE :"""

_RAG_TEMPLATE = """
# 🎯 IDENTITÉ ET MANDAT
Vous êtes **Tèwou Agro-Assistant**, un expert agricole sénégalais virtuel.
Votre mission est d'accompagner les agriculteurs avec des conseils pratiques,
précis et bienveillants, exclusivement centrés sur l'agriculture au Sénégal.

# 📜 RÈGLES
## Domaine d'expertise
- ✅ Agriculture sénégalaise, cultures locales, sols, climat, irrigation,
     fertilisation, protection des cultures, calendriers culturaux.
- ❌ Hors-sujet : politique, économie générale, santé humaine, technologie
     non agricole. → Répondre poliment : *"Je suis spécialisé dans l'agriculture
     sénégalaise. Je peux vous aider sur les cultures, le sol, la météo ou les
     pratiques agricoles."*

# 📊 CONTEXTE UTILISATEUR
- 🌱 **Type de sol** : {soil_type}
- 📍 **Localisation** : {location}

# 📚 BASE DE CONNAISSANCES
{context}

# 💬 HISTORIQUE
{chat_history}

# 🎤 QUESTION
{question}

# ✨ INSTRUCTIONS DE RÉPONSE
0. {introduction_instruction}
1. Accueil chaleureux (bref si ce n'est pas le début).
2. Réponse structurée basée sur le contexte et votre expertise.
3. Application locale liée à {soil_type} et {location}.
4. Citez les sources si pertinent (ex : "Selon les données FAO…").

**Répondez maintenant :**"""


# ── Moteur principal ──────────────────────────────────────────────────────────

def query_rag(
    question: str,
    soil_type: str = Config.DEFAULT_SOIL,
    location: str = Config.DEFAULT_LOCATION,
    chat_history: list[tuple[str, str]] | None = None,
) -> Generator[Event, None, None]:
    """
    Exécute la chaîne RAG et yield des événements de statut/chunk.

    Args:
        question:     Question de l'utilisateur.
        soil_type:    Type de sol (depuis Config.SOIL_TYPES).
        location:     Localité (ex: "Thiès").
        chat_history: Liste de tuples (user_msg, assistant_msg).
    """
    if chat_history is None:
        chat_history = []

    llm = ChatCohere(model=Config.LLM_MODEL)

    # ── Phase 0 : Vectorstore ──────────────────────────────────────────────────
    yield {"type": "status", "content": "Vérification de la base de connaissances…"}
    vectorstore = get_vectorstore()
    rag_available = vectorstore is not None

    if not rag_available:
        logger.warning("Vectorstore indisponible — mode dégradé sans RAG.")
        yield {"type": "status", "content": "⚠️ Base documentaire indisponible, mode général activé…"}

    retriever = vectorstore.as_retriever(search_kwargs={"k": Config.RAG_K}) if rag_available else None

    # ── Phase 1 : Contextualisation (questions de suivi) ──────────────────────
    standalone_question = question
    if chat_history:
        yield {"type": "status", "content": "Compréhension du contexte…"}
        try:
            ctx_chain = (
                ChatPromptTemplate.from_template(_CONTEXTUALIZE_TEMPLATE)
                | llm
                | StrOutputParser()
            )
            standalone_question = ctx_chain.invoke({
                "chat_history": _format_history(chat_history),
                "question": question,
            })
            logger.info(f"Question reformulée : {standalone_question}")
        except Exception as exc:
            logger.warning(f"Contextualisation échouée, question originale conservée : {exc}")

    # ── Phase 2 : Retrieval ────────────────────────────────────────────────────
    yield {
        "type": "status",
        "content": "Recherche d'informations pertinentes…" if rag_available else "Génération de la réponse…",
    }

    if rag_available:
        try:
            docs = retriever.invoke(standalone_question)
            context = _format_docs(docs)
        except Exception as exc:
            logger.error(f"Erreur retrieval : {exc}")
            context = "⚠️ Erreur lors de la récupération des documents."
    else:
        context = (
            "⚠️ Base documentaire non disponible. "
            "Répondez avec vos connaissances générales sur l'agriculture sénégalaise."
        )

    # ── Phase 3 : Génération en streaming ─────────────────────────────────────
    yield {"type": "status", "content": "Rédaction de la réponse…"}

    intro_instruction = (
        "Présentez-vous brièvement comme Tèwou Agro-Assistant."
        if not chat_history
        else "NE vous présentez PAS. Répondez directement à la question."
    )

    final_chain = (
        ChatPromptTemplate.from_template(_RAG_TEMPLATE)
        | llm
        | StrOutputParser()
    )

    try:
        for chunk in final_chain.stream({
            "context": context,
            "chat_history": _format_history(chat_history),
            "question": question,
            "soil_type": soil_type,
            "location": location,
            "introduction_instruction": intro_instruction,
        }):
            yield {"type": "chunk", "content": chunk}
    except Exception as exc:
        logger.error(f"Erreur génération : {exc}")
        yield {"type": "chunk", "content": f"\n\n⚠️ Erreur lors de la génération : {exc}"}


# ── Test rapide en CLI ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Test de la chaîne RAG…\n")
    for event in query_rag("Quel est le meilleur moment pour semer le mil au Sénégal ?"):
        if event["type"] == "chunk":
            print(event["content"], end="", flush=True)
        elif event["type"] == "status":
            print(f"\n[STATUS] {event['content']}")
    print("\n\nFin du test.")
