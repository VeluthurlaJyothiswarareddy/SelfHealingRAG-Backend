from typing import Any, TypedDict


class GraphState(TypedDict, total=False):
    user_id: str
    chat_id: str
    question: str
    chat_history: list
    uploaded_files: list
    retrieval_scope: str
    retrieval_queries: list
    retrieved_docs: list
    good_context: bool
    answer: str
    critique: dict
    retry_count: int
    confidence: float
    sources: list
    exclude_current_chat: bool
    conversational: bool
    final_verdict: str
