from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import get_db, get_user_or_404, verify_chat_owner
from app.schemas import (
    ChatCreate,
    ChatDetailResponse,
    ChatResponse,
    MessageReplyResponse,
    SendMessageRequest,
)
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService
from app.services.message_service import MessageService

router = APIRouter()


@router.post("/create", response_model=ChatResponse)
async def create_chat(payload: ChatCreate, db=Depends(get_db)):
    await get_user_or_404(payload.user_id, db)
    service = ChatService(db)
    return await service.create_chat(payload.user_id, payload.title or "New Chat")


@router.get("/list/{user_id}", response_model=list[ChatResponse])
async def list_chats(user_id: str, db=Depends(get_db)):
    await get_user_or_404(user_id, db)
    service = ChatService(db)
    return await service.list_chats(user_id)


@router.get("/{chat_id}", response_model=ChatDetailResponse)
async def get_chat(chat_id: str, user_id: str, db=Depends(get_db)):
    await verify_chat_owner(chat_id, user_id, db)
    service = ChatService(db)
    return await service.get_chat_with_messages(chat_id)


@router.delete("/{chat_id}")
async def delete_chat(chat_id: str, user_id: str, db=Depends(get_db)):
    await verify_chat_owner(chat_id, user_id, db)
    service = ChatService(db)
    await service.delete_chat(chat_id)
    return {"detail": "Chat deleted"}


@router.post("/{chat_id}/message", response_model=MessageReplyResponse)
async def send_message(chat_id: str, payload: SendMessageRequest, db=Depends(get_db)):
    await verify_chat_owner(chat_id, payload.user_id, db)
    service = MessageService(db)
    return await service.send_message(chat_id, payload.user_id, payload.content)


@router.post("/{chat_id}/upload")
async def upload_document(
    chat_id: str,
    user_id: str = Form(...),
    file: UploadFile = File(...),
    db=Depends(get_db),
):
    await verify_chat_owner(chat_id, user_id, db)
    content = await file.read()
    service = DocumentService(db)
    doc = await service.process_upload(file.filename, content, user_id, chat_id)
    return doc
