from datetime import datetime
from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = None


class SourceChunk(BaseModel):
    content: str
    page_number: int | None = None
    source: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    question: str
    answer: str
    sources: list[SourceChunk] = []


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime


class ConversationOut(BaseModel):
    id: str
    created_at: datetime
    messages: list[MessageOut] = []
