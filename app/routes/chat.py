from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import run_agent_workflow
from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse, SourceChunk

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat_with_documents(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Agentic RAG endpoint powered by a LangGraph state machine workflow."""
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Run LangGraph workflow
    final_state = await run_agent_workflow(question=question, db=db)

    # 2. Extract source chunks
    sources = [
        SourceChunk(content=c["content"], page_number=c.get("page_number"))
        for c in final_state.get("retrieved_chunks", [])
    ]

    return ChatResponse(
        question=question,
        answer=final_state.get("answer", "No answer could be generated."),
        sources=sources,
    )
