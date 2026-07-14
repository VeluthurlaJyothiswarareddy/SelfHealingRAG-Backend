from app.langgraph.graph import run_rag_workflow
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService
from app.services.llm_service import get_llm_service


class MessageService:
    def __init__(self, db):
        self.db = db
        self.chat_service = ChatService(db)
        self.document_service = DocumentService(db)

    async def send_message(self, chat_id: str, user_id: str, content: str) -> dict:
        chat = await self.chat_service.get_chat(chat_id)
        if not chat or chat["user_id"] != user_id:
            from app.utils.errors import NotFoundError
            raise NotFoundError("Chat not found")

        await self.chat_service.save_message(chat_id, "user", content)

        history = await self.chat_service.get_recent_messages(chat_id, limit=10)
        uploaded_files = await self.document_service.get_uploaded_filenames(chat_id)

        initial_state = {
            "user_id": user_id,
            "chat_id": chat_id,
            "question": content,
            "chat_history": history,
            "uploaded_files": uploaded_files,
            "retry_count": 0,
            "retrieved_docs": [],
            "sources": [],
        }

        result = await run_rag_workflow(initial_state)

        answer = result.get("answer", "I don't have enough information to answer this confidently.")
        sources = result.get("sources", [])
        confidence = float(result.get("confidence", 0))
        verdict = result.get("final_verdict") or result.get("critique", {}).get("verdict", "FAIL")
        scope = result.get("retrieval_scope", "none")

        await self.chat_service.save_message(
            chat_id,
            "assistant",
            answer,
            sources=sources,
            confidence=confidence,
        )

        messages = await self.chat_service.get_recent_messages(chat_id, limit=2)
        if len(messages) <= 2 and chat.get("title") == "New Chat":
            llm = get_llm_service()
            title = await llm.generate(
                "Generate a short chat title (max 6 words) for this conversation. Return title only.",
                f"User: {content}\nAssistant: {answer[:200]}",
            )
            await self.chat_service.update_chat_title(chat_id, title.strip().strip('"'))

        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "critic_verdict": verdict,
            "retrieval_scope": scope,
        }
