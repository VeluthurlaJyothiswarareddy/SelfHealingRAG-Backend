from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId


def serialize_user(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "email": doc["email"],
        "created_at": doc["created_at"],
    }


def serialize_chat(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "user_id": doc["user_id"],
        "title": doc["title"],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


def serialize_message(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "chat_id": doc["chat_id"],
        "role": doc["role"],
        "content": doc["content"],
        "sources": doc.get("sources", []),
        "confidence": doc.get("confidence"),
        "created_at": doc["created_at"],
    }


def serialize_document(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "user_id": doc.get("user_id"),
        "chat_id": doc.get("chat_id"),
        "file_name": doc["file_name"],
        "file_type": doc["file_type"],
        "upload_time": doc["upload_time"],
    }


def new_object_id() -> ObjectId:
    return ObjectId()


def utcnow() -> datetime:
    return datetime.utcnow()
