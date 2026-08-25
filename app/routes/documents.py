import logging
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.services.embedding import embed_texts
from app.services.ingestion import process_document_chunks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file_ext}'. Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    # Save uploaded file to disk with unique prefix to prevent collisions
    doc_id = uuid.uuid4()
    safe_filename = f"{doc_id}_{Path(file.filename).name}"
    file_path = settings.UPLOAD_DIR / safe_filename

    try:
        content = await file.read()
        file_size = len(content)
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as exc:
        logger.error(f"Failed to save uploaded file {file.filename}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write uploaded file to disk: {exc}",
        ) from exc

    # Create Document record
    document = Document(
        id=doc_id,
        filename=file.filename,
        file_type=file_ext,
        file_path=str(file_path),
        file_size=file_size,
        status="PROCESSING",
    )
    db.add(document)
    await db.flush()

    try:
        # Extract and chunk
        raw_chunks = process_document_chunks(
            file_path=file_path,
            source_filename=file.filename,
        )

        if not raw_chunks:
            raise ValueError("Document yielded no chunks after processing.")

        # Batch generate embeddings
        chunk_texts = [c.content for c in raw_chunks]
        embeddings = embed_texts(chunk_texts)

        # Store chunks in pgvector
        for chunk, embedding in zip(raw_chunks, embeddings):
            db_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_number=chunk.page_number,
                embedding=embedding,
                metadata_=chunk.metadata,
            )
            db.add(db_chunk)

        document.status = "COMPLETED"
        document.chunk_count = len(raw_chunks)
        await db.commit()
        await db.refresh(document)

        return DocumentUploadResponse(
            message=f"Successfully ingested '{file.filename}' into {len(raw_chunks)} chunks.",
            document=DocumentResponse.model_validate(document),
        )

    except Exception as exc:
        logger.error(f"Failed to ingest document '{file.filename}': {exc}", exc_info=True)
        document.status = "FAILED"
        document.error_message = str(exc)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document ingestion failed: {exc}",
        ) from exc


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
) -> list[DocumentResponse]:
    result = await db.execute(
        select(Document).order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.chunks))
        .where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found.",
        )
    return DocumentDetailResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found.",
        )

    # Remove file on disk if exists
    try:
        Path(document.file_path).unlink(missing_ok=True)
    except Exception as exc:
        logger.warning(f"Could not remove local file {document.file_path}: {exc}")

    await db.delete(document)
    await db.commit()
