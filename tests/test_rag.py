import pytest
from httpx import AsyncClient

from app.services.llm import generate_rag_answer


def test_generate_rag_answer_fallback_mode() -> None:
    chunks = ["JWT stands for JSON Web Token used for stateless auth."]
    answer = generate_rag_answer(question="What is JWT?", context_chunks=chunks)
    assert len(answer) > 0
    assert "Context provided" in answer or "JWT" in answer


@pytest.mark.asyncio
async def test_chat_empty_question_returns_400(client: AsyncClient) -> None:
    response = await client.post("/chat", json={"question": "   "})
    assert response.status_code == 400
    assert "Question cannot be empty" in response.json()["detail"]
