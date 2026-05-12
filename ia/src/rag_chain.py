"""
src/rag_chain.py - Moteur RAG de Tewou Agro-Assistant.

Pipeline :
  1. Contextualisation : reformule les questions de suivi.
  2. Retrieval       : recupere les k docs pertinents depuis ChromaDB.
  3. Generation      : Cohere repond en streaming avec emojis + suggestions.

Fallback : si vectorstore indisponible, repond sans contexte documentaire.
"""
import logging

from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import Config
from src.build_vectorstore import get_vectorstore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _format_history(history):
    return "".join(
        f"Utilisateur: {u}\nAssistant: {a}\n"
        for u, a in history
    )

def _format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# ---------------------------------------------------------------------------
# PROMPT DE CONTEXTUALISATION (reformulation questions de suivi)
# ---------------------------------------------------------------------------

_CONTEXTUALIZE_TEMPLATE = """
Etant donne l'historique de la conversation et la question actuelle,
si la question fait reference a des elements precedents, reformulez-la en une
question autonome comprehensible sans l'historique.
Ne repondez PAS - reformulez seulement.
Si elle est deja autonome, renvoyez-la telle quelle.

HISTORIQUE :
{chat_history}

QUESTION ACTUELLE : {question}

QUESTION REFORMULEE :"""


# ---------------------------------------------------------------------------
# PROMPT PRINCIPAL RAG
# ---------------------------------------------------------------------------

_RAG_TEMPLATE = """
Tu es Tewou Agro-Assistant (prenom Tewou, qui signifie "la terre" en Serere),
un expert agricole senegalais virtuel chaleureux et passionnee.
Tu t'exprimes en francais avec des emojis pertinents pour rendre tes reponses
vivantes et faciles a lire.

====================================================================
DOMAINES D'EXPERTISE (NON-NEGOCIABLE)
====================================================================
Tu es UNIQUEMENT specialise dans :
  - Cultures locales du Senegal (mil, sorgho, arachide, niebe, maïs, riz, manioc...)
  - Types de sols senegalais (Dior, Deck, Deck-Dior, sols ferrugineux, sols halo...)
  - Climat, meteo et saisons agricoles au Senegal (hivernage, saison seche...)
  - Irrigation, gestion de l'eau et techniques d'arrosage
  - Fertilisation, engrais organiques et chimiques adaptes au contexte local
  - Protection des cultures (ravageurs, maladies, traitements naturels/chimiques)
  - Calendriers culturaux et periodes de semis/recolte
  - Pratiques agricoles durables et agroecologie au Senegal
  - Elevage integration cultures-elevage au Senegal
  - Marches agricoles et valorisation des produits locaux

HORS SUJET : Si la question ne concerne pas ces domaines, reponds
UNIQUEMENT avec ce message (avec les emojis) :
"Je suis vraiment desole mais je suis specialise uniquement dans
l'agriculture senegalaise ! Je ne peux pas vous aider sur ce sujet.
En revanche, je serais ravi de repondre a vos questions sur les cultures,
les sols, le climat ou les pratiques agricoles au Senegal.
Que souhaitez-vous savoir sur l'agriculture senegalaise ?

Voici quelques themes que je maitrise :
- Les meilleures cultures pour votre type de sol
- Le calendrier des semis et recoltes
- Les techniques d'irrigation adaptees
- La fertilisation et la protection des cultures"

====================================================================
CONTEXTE UTILISATEUR
====================================================================
- Type de sol : {soil_type}
- Localisation : {location}

====================================================================
BASE DE CONNAISSANCES (utilise ces informations en priorite)
====================================================================
{context}

====================================================================
HISTORIQUE DE LA CONVERSATION
====================================================================
{chat_history}

====================================================================
QUESTION DE L'UTILISATEUR
====================================================================
{question}

====================================================================
INSTRUCTIONS DE REPONSE (TRES IMPORTANT - respecte chaque point)
====================================================================

ETAPE 0 - ACCUEIL (premiere interaction seulement) :
{introduction_instruction}

ETAPE 1 - STRUCTURE DE LA REPONSE :
Utilise une structure claire avec des emojis expressifs et agricoles :
  - Paragraphes bien separes, jamais un bloc de texte continu
  - Titres avec emojis quand la reponse est longue (ex: "## Semis", "## Irrigation")
  - Listes a puces avec emojis pour les etapes ou conseils pratiques
  - Met en gras les informations cles

ETAPE 2 - PERSONNALISATION :
  - Adapte ta reponse specifiquement au type de sol "{soil_type}" si mentionne
  - Prends en compte la localite "{location}" pour les conseils meteo/saison
  - Si le sol ou la localite ne sont pas precises, encourage l'utilisateur a les renseigner

ETAPE 3 - SOURCES :
  - Si tu utilises la base de connaissances, cite-la naturellement
    (ex: "Selon les donnees agronomiques senegalaises...")
  - Si tu reponds de memoire, sois transparent : "D'apres mes connaissances..."

ETAPE 4 - SUGGESTIONS DE SUIVI (OBLIGATOIRE a chaque reponse) :
  A la fin de CHAQUE reponse, ajoute TOUJOURS cette section :

  ---
  **Pour continuer notre discussion, vous pourriez me demander :**
  [Propose 3 suggestions contextuelles, sous forme de phrases courtes et invitantes,
   liees directement au sujet qu'on vient de discuter.
   Melange questions concretes et points d'approfondissement.
   Commence chaque suggestion par un emoji pertinent.]

====================================================================
COMMENCE TA REPONSE MAINTENANT :
"""


# ---------------------------------------------------------------------------
# PROMPT D'ACCUEIL (premiere connexion)
# ---------------------------------------------------------------------------

_WELCOME_INSTRUCTION = """
C'est la PREMIERE question de cet utilisateur. Commence par un accueil chaleureux
et personnalise (2-3 lignes maximum) avec :
  - Salutation avec emoji
  - Ton prenom "Tewou" et ce qu'il signifie
  - Les 3-4 domaines principaux que tu couvres (format court avec emojis)
  - Invitation a poser des questions
Exemples d'accueil :
  "Bonjour ! Je suis Tewou (qui signifie "la terre" en Serere), votre assistant
   agricole specialise dans l'agriculture senegalaise. Je suis la pour vous
   accompagner sur les cultures, les sols, la meteo et les pratiques agricoles.
   N'hesitez pas a me poser toutes vos questions !"
Puis reponds directement a la question posee.
"""

_FOLLOWUP_INSTRUCTION = """
NE te presente PAS a nouveau. Reponds directement a la question
sans formule d'accueil. Rappelle-toi du contexte de la conversation.
"""


# ---------------------------------------------------------------------------
# MOTEUR PRINCIPAL
# ---------------------------------------------------------------------------

def query_rag(question, soil_type=None, location=None, chat_history=None):
    """
    Execute la chaine RAG et yield des evenements statut/chunk.

    Args:
        question     : question de l'utilisateur
        soil_type    : type de sol selectionne
        location     : localite saisie
        chat_history : liste de tuples (user_msg, assistant_msg)
    """
    if soil_type is None:
        soil_type = Config.DEFAULT_SOIL
    if location is None:
        location = Config.DEFAULT_LOCATION
    if chat_history is None:
        chat_history = []

    llm = ChatCohere(model=Config.LLM_MODEL)

    # -- Phase 0 : Vectorstore --------------------------------------------
    yield {"type": "status", "content": "Verification de la base de connaissances..."}
    vectorstore = get_vectorstore()
    rag_available = vectorstore is not None

    if not rag_available:
        yield {"type": "status", "content": "Mode general active (base documentaire indisponible)..."}

    retriever = (
        vectorstore.as_retriever(search_kwargs={"k": Config.RAG_K})
        if rag_available else None
    )

    # -- Phase 1 : Contextualisation (questions de suivi) -----------------
    standalone_question = question
    if chat_history:
        yield {"type": "status", "content": "Comprehension du contexte de la conversation..."}
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

    # -- Phase 2 : Retrieval ----------------------------------------------
    yield {
        "type": "status",
        "content": "Recherche d'informations dans la base agricole..." if rag_available
                   else "Preparation de la reponse...",
    }

    if rag_available:
        try:
            docs = retriever.invoke(standalone_question)
            context = _format_docs(docs)
        except Exception as exc:
            logger.error(f"Erreur retrieval : {exc}")
            context = "Erreur lors de la recuperation des documents."
    else:
        context = (
            "La base documentaire locale n'est pas disponible. "
            "Reponds avec tes connaissances generales sur l'agriculture senegalaise, "
            "en precisant quand tu parles de memoire."
        )

    # -- Phase 3 : Generation en streaming --------------------------------
    yield {"type": "status", "content": "Redaction de la reponse..."}

    intro_instruction = (
        _WELCOME_INSTRUCTION if not chat_history else _FOLLOWUP_INSTRUCTION
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
        yield {
            "type": "chunk",
            "content": (
                "Desolé, une erreur technique est survenue. "
                f"Veuillez reessayer. ({exc})"
            ),
        }


# ---------------------------------------------------------------------------
# TEST CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Test Tewou Agro-Assistant ===\n")
    questions = [
        "Bonjour, quelles sont les meilleures cultures pour le Senegal ?",
        "Et pour un sol sablonneux Dior ?",
        "Quel est le meilleur president de France ?",
    ]
    history = []
    for q in questions:
        print(f"\n[USER] {q}")
        print("[TEWOU] ", end="")
        full = ""
        for event in query_rag(q, chat_history=history):
            if event["type"] == "chunk":
                print(event["content"], end="", flush=True)
                full += event["content"]
            elif event["type"] == "status":
                pass
        print()
        if full:
            history.append((q, full))
    print("\n=== Fin du test ===")
