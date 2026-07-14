import logging
import math
from typing import Any

from app.config import get_settings
from app.utils.errors import VectorSearchError

logger = logging.getLogger(__name__)


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorSearchService:
    def __init__(self, db):
        self.db = db
        self.settings = get_settings()

    def _build_filter(self, scope: str, user_id: str | None, chat_id: str | None, exclude_chat: bool = False) -> dict:
        if scope == "chat_documents":
            return {"user_id": user_id, "chat_id": chat_id}
        if scope == "user_documents":
            if exclude_chat and chat_id:
                return {"user_id": user_id, "chat_id": {"$ne": chat_id}}
            return {"user_id": user_id}
        if scope == "global_documents":
            return {"user_id": None}
        return {}

    async def _search_scope(
        self,
        query_embedding: list[float],
        scope: str,
        user_id: str | None,
        chat_id: str | None,
        top_k: int,
        exclude_chat: bool = False,
    ) -> list[dict[str, Any]]:
        filter_query = self._build_filter(scope, user_id, chat_id, exclude_chat)
        if scope == "global_documents":
            filter_query = {"user_id": None}

        pipeline = [
            {
                "$vectorSearch": {
                    "index": self.settings.vector_index_name,
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": top_k * 10,
                    "limit": top_k,
                    "filter": filter_query if filter_query else None,
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "chunk_text": 1,
                    "source_file": 1,
                    "metadata": 1,
                    "chunk_number": 1,
                    "document_id": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]

        if filter_query:
            pipeline[0]["$vectorSearch"]["filter"] = filter_query
        else:
            del pipeline[0]["$vectorSearch"]["filter"]

        try:
            results = []
            async for doc in self.db.vector_documents.aggregate(pipeline):
                results.append(
                    {
                        "chunk_id": str(doc["_id"]),
                        "chunk_text": doc.get("chunk_text", ""),
                        "source_file": doc.get("source_file", "unknown"),
                        "metadata": doc.get("metadata", {}),
                        "chunk_number": doc.get("chunk_number", 0),
                        "document_id": doc.get("document_id"),
                        "similarity_score": float(doc.get("score", 0.0)),
                        "scope": scope,
                    }
                )

            if not results and filter_query:
                logger.warning(
                    "Atlas vector search returned 0 results for scope=%s; using in-memory fallback",
                    scope,
                )
                results = await self._fallback_search(query_embedding, filter_query, top_k, scope)

            return results
        except Exception as exc:
            logger.warning(
                "Atlas vector search failed for scope %s (%s); using in-memory fallback",
                scope,
                exc,
            )
            if filter_query:
                return await self._fallback_search(query_embedding, filter_query, top_k, scope)
            raise VectorSearchError(str(exc)) from exc

    async def _fallback_search(
        self,
        query_embedding: list[float],
        filter_query: dict,
        top_k: int,
        scope: str,
    ) -> list[dict[str, Any]]:
        """Fallback when Atlas Vector Search index is missing or returns no results."""
        results: list[dict[str, Any]] = []
        async for doc in self.db.vector_documents.find(filter_query):
            embedding = doc.get("embedding")
            if not embedding:
                continue
            score = _cosine_similarity(query_embedding, embedding)
            results.append(
                {
                    "chunk_id": str(doc["_id"]),
                    "chunk_text": doc.get("chunk_text", ""),
                    "source_file": doc.get("source_file", "unknown"),
                    "metadata": doc.get("metadata", {}),
                    "chunk_number": doc.get("chunk_number", 0),
                    "document_id": doc.get("document_id"),
                    "similarity_score": score,
                    "scope": scope,
                }
            )
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

    async def search(
        self,
        query_embedding: list[float],
        *,
        user_id: str | None,
        chat_id: str | None,
        scope: str,
        top_k: int | None = None,
        exclude_current_chat: bool = False,
    ) -> list[dict[str, Any]]:
        k = top_k or self.settings.top_k

        if scope == "none":
            return []

        if scope == "mixed":
            scopes = ["chat_documents", "user_documents", "global_documents"]
            all_results: list[dict[str, Any]] = []
            for s in scopes:
                exclude = exclude_current_chat and s == "user_documents"
                all_results.extend(
                    await self._search_scope(query_embedding, s, user_id, chat_id, k, exclude_chat=exclude)
                )
            return self._merge_and_rerank(all_results, k)

        if scope == "user_documents" and exclude_current_chat:
            results = await self._search_scope(
                query_embedding, scope, user_id, chat_id, k, exclude_chat=True
            )
            if not results:
                results = await self._search_scope(
                    query_embedding, "global_documents", user_id, chat_id, k
                )
            return self._merge_and_rerank(results, k)

        if scope in {"chat_documents", "user_documents", "global_documents"}:
            results = await self._search_scope(query_embedding, scope, user_id, chat_id, k)
            if not results and scope == "chat_documents":
                user_results = await self._search_scope(
                    query_embedding, "user_documents", user_id, chat_id, k, exclude_chat=False
                )
                global_results = await self._search_scope(
                    query_embedding, "global_documents", user_id, chat_id, k
                )
                return self._merge_and_rerank(user_results + global_results, k)
            if not results and scope == "user_documents":
                results = await self._search_scope(
                    query_embedding, "global_documents", user_id, chat_id, k
                )
            return self._merge_and_rerank(results, k)

        return []

    def _merge_and_rerank(self, results: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        seen: set[str] = set()
        merged: list[dict[str, Any]] = []
        for item in sorted(results, key=lambda x: x.get("similarity_score", 0), reverse=True):
            chunk_id = item.get("chunk_id")
            if chunk_id in seen:
                continue
            seen.add(chunk_id)
            merged.append(item)
            if len(merged) >= top_k:
                break
        return merged

    async def search_queries(
        self,
        query_embeddings: list[list[float]],
        *,
        user_id: str | None,
        chat_id: str | None,
        scope: str,
        top_k: int | None = None,
        exclude_current_chat: bool = False,
    ) -> list[dict[str, Any]]:
        all_results: list[dict[str, Any]] = []
        for embedding in query_embeddings:
            all_results.extend(
                await self.search(
                    embedding,
                    user_id=user_id,
                    chat_id=chat_id,
                    scope=scope,
                    top_k=top_k,
                    exclude_current_chat=exclude_current_chat,
                )
            )
        return self._merge_and_rerank(all_results, top_k or self.settings.top_k)
