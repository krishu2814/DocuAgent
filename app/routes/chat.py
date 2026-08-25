from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.graph import run_agent_workflow
from app.database import get_db
from app.models.conversation import Conversation, Message
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationOut,
    SourceChunk,
)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat_with_documents(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Agentic RAG endpoint with conversation memory and verifiable citations."""
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Retrieve or create conversation session
    chat_history: list[dict[str, str]] = []
    conversation: Conversation | None = None

    if request.conversation_id:
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == request.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            chat_history = [
                {"role": m.role, "content": m.content}
                for m in conversation.messages
            ]

    if not conversation:
        conversation = Conversation()
        db.add(conversation)
        await db.flush()

    # 2. Execute LangGraph workflow with conversation memory
    final_state = await run_agent_workflow(
        question=question,
        db=db,
        chat_history=chat_history,
    )

    answer = final_state.get("answer", "No answer could be generated.")
    sources = [
        SourceChunk(
            content=c["content"],
            page_number=c.get("page_number"),
            source=c.get("source"),
        )
        for c in final_state.get("retrieved_chunks", [])
    ]

    # 3. Persist user and assistant messages in PostgreSQL
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=question,
    )
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
    )
    db.add(user_msg)
    db.add(assistant_msg)
    await db.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        question=question,
        answer=answer,
        sources=sources,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    """Retrieves conversation history and past messages."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation
