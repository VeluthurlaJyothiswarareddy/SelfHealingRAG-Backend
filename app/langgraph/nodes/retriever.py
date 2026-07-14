from app.db.client import get_database
from app.services.embedding_service import get_embedding_service
from app.services.vector_search_service import VectorSearchService


async def retriever_node(state: dict) -> dict:
    if state.get("retrieval_scope") == "none":
        return {"retrieved_docs": []}

    db = get_database()
    vector_service = VectorSearchService(db)
    embedding_service = get_embedding_service()

    queries = state.get("retrieval_queries") or [state["question"]]
    embeddings = []
    for q in queries:
        embeddings.append(await embedding_service.embed_query(q))

    docs = await vector_service.search_queries(
        embeddings,
        user_id=state.get("user_id"),
        chat_id=state.get("chat_id"),
        scope=state.get("retrieval_scope", "mixed"),
        exclude_current_chat=state.get("exclude_current_chat", False),
    )
    return {"retrieved_docs": docs}
