from app.langgraph.prompts import INSUFFICIENT_MESSAGE
from app.services.llm_service import get_llm_service

CONVERSATIONAL_PHRASES = {
    "hi", "hello", "hey", "thanks", "thank you", "bye", "goodbye",
    "good morning", "good afternoon", "good evening", "how are you",
}


async def intent_router_node(state: dict) -> dict:
    uploaded = state.get("uploaded_files", [])
    history = state.get("chat_history", [])
    question = state["question"].strip()
    question_lower = question.lower()

    # Rule-based routing is more reliable than LLM for common cases.
    if question_lower in CONVERSATIONAL_PHRASES or (
        len(question_lower) < 20 and question_lower.rstrip("!?.") in CONVERSATIONAL_PHRASES
    ):
        return {
            "retrieval_scope": "none",
            "retrieval_queries": [],
            "exclude_current_chat": False,
            "conversational": True,
        }

    if uploaded:
        return {
            "retrieval_scope": "chat_documents",
            "retrieval_queries": [question],
            "exclude_current_chat": False,
            "conversational": False,
        }

    llm = get_llm_service()

    system = """You are an intent router for a RAG assistant.
Classify the user question and choose retrieval scope.

Scopes:
- none: conversational only (greetings, thanks, small talk) - no retrieval needed
- chat_documents: question is about files uploaded in the current chat
- user_documents: question needs user's knowledge but NOT current chat uploads
- global_documents: organization-wide knowledge only
- mixed: compare or synthesize current chat uploads with broader knowledge

Also set exclude_current_chat=true when question is unrelated to current chat uploads.

Return JSON:
{
  "retrieval_scope": "chat_documents|user_documents|global_documents|mixed|none",
  "retrieval_queries": ["primary query", ...],
  "exclude_current_chat": false,
  "conversational": false,
  "reason": "brief reason"
}"""

    user = f"""Question: {question}
Uploaded files in current chat: {uploaded}
Recent chat history: {history[-4:] if history else []}"""

    result = await llm.generate_json(system, user)

    scope = result.get("retrieval_scope", "user_documents")
    queries = result.get("retrieval_queries") or [question]
    if isinstance(queries, str):
        queries = [queries]

    if scope == "none" or result.get("conversational"):
        return {
            "retrieval_scope": "none",
            "retrieval_queries": [],
            "exclude_current_chat": False,
            "conversational": True,
        }

    return {
        "retrieval_scope": scope,
        "retrieval_queries": queries,
        "exclude_current_chat": bool(result.get("exclude_current_chat", False)),
        "conversational": False,
    }
