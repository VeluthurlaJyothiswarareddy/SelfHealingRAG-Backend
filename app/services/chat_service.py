from bson import ObjectId

from app.models.helpers import serialize_chat, serialize_message, utcnow
from app.utils.errors import NotFoundError


class ChatService:
    def __init__(self, db):
        self.db = db

    async def create_chat(self, user_id: str, title: str = "New Chat") -> dict:
        now = utcnow()
        doc = {
            "user_id": user_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.db.chats.insert_one(doc)
        doc["_id"] = result.inserted_id
        return serialize_chat(doc)

    async def list_chats(self, user_id: str) -> list[dict]:
        cursor = self.db.chats.find({"user_id": user_id}).sort("updated_at", -1)
        return [serialize_chat(doc) async for doc in cursor]

    async def get_chat(self, chat_id: str) -> dict | None:
        if not ObjectId.is_valid(chat_id):
            return None
        doc = await self.db.chats.find_one({"_id": ObjectId(chat_id)})
        if not doc:
            return None
        return serialize_chat(doc)

    async def get_chat_with_messages(self, chat_id: str) -> dict:
        chat = await self.get_chat(chat_id)
        if not chat:
            raise NotFoundError("Chat not found")

        cursor = self.db.messages.find({"chat_id": chat_id}).sort("created_at", 1)
        messages = [serialize_message(doc) async for doc in cursor]
        return {**chat, "messages": messages}

    async def delete_chat(self, chat_id: str) -> None:
        if not ObjectId.is_valid(chat_id):
            raise NotFoundError("Chat not found")

        result = await self.db.chats.delete_one({"_id": ObjectId(chat_id)})
        if result.deleted_count == 0:
            raise NotFoundError("Chat not found")

        await self.db.messages.delete_many({"chat_id": chat_id})
        docs = self.db.documents.find({"chat_id": chat_id})
        doc_ids = [str(doc["_id"]) async for doc in docs]
        await self.db.documents.delete_many({"chat_id": chat_id})
        if doc_ids:
            await self.db.vector_documents.delete_many({"document_id": {"$in": doc_ids}})

    async def update_chat_title(self, chat_id: str, title: str) -> None:
        await self.db.chats.update_one(
            {"_id": ObjectId(chat_id)},
            {"$set": {"title": title, "updated_at": utcnow()}},
        )

    async def touch_chat(self, chat_id: str) -> None:
        await self.db.chats.update_one(
            {"_id": ObjectId(chat_id)},
            {"$set": {"updated_at": utcnow()}},
        )

    async def get_recent_messages(self, chat_id: str, limit: int = 10) -> list[dict]:
        cursor = (
            self.db.messages.find({"chat_id": chat_id})
            .sort("created_at", -1)
            .limit(limit)
        )
        messages = [doc async for doc in cursor]
        messages.reverse()
        return [
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ]

    async def save_message(
        self,
        chat_id: str,
        role: str,
        content: str,
        sources: list | None = None,
        confidence: float | None = None,
    ) -> dict:
        doc = {
            "chat_id": chat_id,
            "role": role,
            "content": content,
            "sources": sources or [],
            "confidence": confidence,
            "created_at": utcnow(),
        }
        result = await self.db.messages.insert_one(doc)
        doc["_id"] = result.inserted_id
        await self.touch_chat(chat_id)
        return serialize_message(doc)
