"""
src/rag_chain.py - Moteur RAG de Tewou Agro-Assistant.

Pipeline :
  1. Contextualisation : reformule les questions de suivi en questions autonomes.
  2. Retrieval : recupere les k documents les plus pertinents depuis ChromaDB.
  3. Generation : Cohere genere la reponse en streaming avec le contexte recupere.

Fallback : si le vectorstore est indisponible, repond sans contexte documentaire.

Yields des evenements :
  {"type": "status", "content": str}  -- etape en cours
  {"type": "chunk",  "content": str}  -- morceau de la reponse finale
"""
import logging

from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import Config
from src.build_vectorstore import get_vectorstore

logger = logging.getLogger(__name__)


def _format_history(history):
    return "".join(
        f"Utilisateur: {u}\nAssistant: {a}\n"
        for u, a in history
    )


def _format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


_CONTEXTUALIZE_TEMPLATE = """
Etant donne l'historique de la conversation et la question actuelle,
si la question fait reference a des elements precedents, reformulez-la en une
question autonome comprehensible sans l'historique.
Ne repondez PAS a la question -- reformulez-la seulement.
Si elle est deja autonome, renvoyez-la telle quelle.

HISTORIQUE :
{chat_history}

QUESTION ACTUELLE : {question}

QUESTION REFORMULEE :"""

_RAG_TEMPLATE = """
# IDENTITE ET MANDAT
Vous etes Tewou Agro-Assistant, un expert agricole senegalais virtuel.
Votre mission est d'accompagner les agriculteurs avec des conseils pratiques,
precis et bienveillants, exclusivement centres sur l'agriculture au Senegal.

# REGLES
## Domaine d'expertise
- AUTORISE : Agriculture senegalaise, cultures locales, sols, climat, irrigation,
  fertilisation, protection des cultures, calendriers culturaux.
- REFUSE : politique, economie generale, sante humaine, technologie non agricole.
  Repondre : "Je suis specialise dans l'agriculture senegalaise. Je peux vous
  aider sur les cultures, le sol, la meteo ou les pratiques agricoles."

# CONTEXTE UTILISATEUR
- Type de sol : {soil_type}
- Localisation : {location}

# BASE DE CONNAISSANCES
{context}

# HISTORIQUE
{chat_history}

# QUESTION
{question}

# INSTRUCTIONS
0. {introduction_instruction}
1. Accueil chaleureux (bref si ce n'est pas le debut).
2. Reponse structuree basee sur le contexte et votre expertise.
3. Application locale liee a {soil_type} et {location}.
4. Citez les sources si pertinent.

Repondez maintenant :"""


def query_rag(question, soil_type=None, location=None, chat_history=None):
    """
    Execute la chaine RAG et yield des evenements de statut/chunk.

    Args:
        question:     Question de l'utilisateur.
        soil_type:    Type de sol (depuis Config.SOIL_TYPES).
        location:     Localite (ex: "Thies").
        chat_history: Liste de tuples (user_msg, assistant_msg).
    """
    if soil_type is None:
        soil_type = Config.DEFAULT_SOIL
    if location is None:
        location = Config.DEFAULT_LOCATION
    if chat_history is None:
        chat_history = []

    llm = ChatCohere(model=Config.LLM_MODEL)

    # Phase 0 : Vectorstore
    yield {"type": "status", "content": "Verification de la base de connaissances..."}
    vectorstore = get_vectorstore()
    rag_available = vectorstore is not None

    if not rag_available:
        logger.warning("Vectorstore indisponible -- mode degrade sans RAG.")
        yield {"type": "status", "content": "Base documentaire indisponible, mode general active..."}

    retriever = (
        vectorstore.as_retriever(search_kwargs={"k": Config.RAG_K})
        if rag_available else None
    )

    # Phase 1 : Contextualisation (questions de suivi)
    standalone_question = question
    if chat_history:
        yield {"type": "status", "content": "Comprehension du contexte..."}
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
            logger.info(f"Question reformulee : {standalone_question}")
        except Exception as exc:
            logger.warning(f"Contextualisation echouee, question originale conservee : {exc}")

    # Phase 2 : Retrieval
    if rag_available:
        yield {"type": "status", "content": "Recherche d'informations pertinentes..."}
    else:
        yield {"type": "status", "content": "Generation de la reponse..."}

    if rag_available:
        try:
            docs = retriever.invoke(standalone_question)
            context = _format_docs(docs)
        except Exception as exc:
            logger.error(f"Erreur retrieval : {exc}")
            context = "Erreur lors de la recuperation des documents."
    else:
        context = (
            "Base documentaire non disponible. "
            "Repondez avec vos connaissances generales sur l'agriculture senegalaise."
        )

    # Phase 3 : Generation en streaming
    yield {"type": "status", "content": "Redaction de la reponse..."}

    intro_instruction = (
        "Presentez-vous brievement comme Tewou Agro-Assistant."
        if not chat_history
        else "NE vous presentez PAS. Repondez directement a la question."
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
        logger.error(f"Erreur generation : {exc}")
        yield {"type": "chunk", "content": f"\nErreur lors de la generation : {exc}"}


if __name__ == "__main__":
    print("Test de la chaine RAG...\n")
    for event in query_rag("Quel est le meilleur moment pour semer le mil au Senegal ?"):
        if event["type"] == "chunk":
            print(event["content"], end="", flush=True)
        elif event["type"] == "status":
            print(f"\n[STATUS] {event['content']}")
    print("\n\nFin du test.")
