from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class SourceChunk(BaseModel):
    content: str
    page_number: int | None = None


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceChunk] = []
