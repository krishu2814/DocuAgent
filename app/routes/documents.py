from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.schemas.document import DocumentDetailOut, DocumentOut
from app.services.embedding import get_embeddings
from app.services.ingestion import process_file_into_chunks

router = APIRouter(prefix="/documents", tags=["Documents"])

SUPPORTED_TYPES = {".pdf", ".txt", ".md"}


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> Document:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Only {SUPPORTED_TYPES} are allowed.",
        )

    # 1. Save uploaded file locally
    doc_id = str(uuid.uuid4())
    save_path = settings.UPLOAD_DIR / f"{doc_id}_{file.filename}"
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # 2. Extract and chunk text
    chunks_data = process_file_into_chunks(save_path)
    if not chunks_data:
        raise HTTPException(status_code=400, detail="File is empty or has no extractable text.")

    # 3. Generate embeddings
    texts = [c["content"] for c in chunks_data]
    embeddings = get_embeddings(texts)

    # 4. Save document and chunk records
    document = Document(id=doc_id, filename=file.filename, file_path=str(save_path))
    db.add(document)

    for idx, (chunk, embedding) in enumerate(zip(chunks_data, embeddings)):
        db_chunk = DocumentChunk(
            document_id=doc_id,
            chunk_index=idx,
            content=chunk["content"],
            page_number=chunk["page_number"],
            embedding=embedding,
        )
        db.add(db_chunk)

    await db.commit()
    return document


@router.get("", response_model=list[DocumentOut])
async def list_documents(db: AsyncSession = Depends(get_db)) -> list[Document]:
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{document_id}", response_model=DocumentDetailOut)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)) -> Document:
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.chunks))
        .where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)) -> None:
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    Path(doc.file_path).unlink(missing_ok=True)
    await db.delete(doc)
    await db.commit()
