from datetime import datetime
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chunk_index: int
    content: str
    page_number: int | None = None
    metadata: dict[str, Any] = {}
    created_at: datetime


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    error_message: str | None = None
    created_at: datetime


class DocumentDetailResponse(DocumentResponse):
    chunks: list[ChunkResponse] = []


class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentResponse
