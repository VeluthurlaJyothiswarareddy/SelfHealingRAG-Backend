from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Depends

from app.db.client import get_database
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService
from app.utils.errors import NotFoundError, UnauthorizedError


async def get_db() -> AsyncIOMotorDatabase:
    return get_database()


async def get_user_or_404(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")
    return user


async def verify_chat_owner(chat_id: str, user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    chat_service = ChatService(db)
    chat = await chat_service.get_chat(chat_id)
    if not chat:
        raise NotFoundError("Chat not found")
    if chat["user_id"] != user_id:
        raise UnauthorizedError("You do not have access to this chat")
    return chat
