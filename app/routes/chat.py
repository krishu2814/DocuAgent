from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse, SourceChunk
from app.services.llm import generate_rag_answer
from app.services.retrieval import search_similar_chunks

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat_with_documents(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Basic RAG: Retrieves relevant chunks using pgvector and generates an answer with Groq."""
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Search for relevant document chunks
    chunks = await search_similar_chunks(query=question, db=db, top_k=4)

    if not chunks:
        return ChatResponse(
            question=question,
            answer="No documents found in the database. Please upload a document first.",
            sources=[],
        )

    # 2. Send chunks to LLM
    chunk_texts = [c.content for c in chunks]
    answer = generate_rag_answer(question=question, context_chunks=chunk_texts)

    # 3. Format source chunks
    sources = [SourceChunk(content=c.content, page_number=c.page_number) for c in chunks]

    return ChatResponse(
        question=question,
        answer=answer,
        sources=sources,
    )
