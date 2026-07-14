from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime


class ChatCreate(BaseModel):
    user_id: str
    title: Optional[str] = "New Chat"


class ChatResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    id: str
    chat_id: str
    role: str
    content: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: Optional[float] = None
    created_at: datetime


class ChatDetailResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]


class SendMessageRequest(BaseModel):
    user_id: str
    content: str


class SourceItem(BaseModel):
    source_file: str
    chunk_id: str
    score: float
    chunk_text: Optional[str] = None


class MessageReplyResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    confidence: float
    critic_verdict: str
    retrieval_scope: str


class DocumentResponse(BaseModel):
    id: str
    user_id: Optional[str]
    chat_id: Optional[str]
    file_name: str
    file_type: str
    upload_time: datetime
