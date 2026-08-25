from datetime import datetime
from pydantic import BaseModel


class ChunkOut(BaseModel):
    id: str
    chunk_index: int
    content: str
    page_number: int | None = None


class DocumentOut(BaseModel):
    id: str
    filename: str
    created_at: datetime


class DocumentDetailOut(DocumentOut):
    chunks: list[ChunkOut] = []
