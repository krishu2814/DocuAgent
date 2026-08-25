import pytest
from httpx import AsyncClient

from app.services.llm import generate_rag_answer


def test_generate_rag_answer_with_chat_history() -> None:
    chunks = ["JWT stands for JSON Web Token used for stateless auth."]
    history = [
        {"role": "user", "content": "What is JWT?"},
        {"role": "assistant", "content": "JWT is a JSON Web Token."},
    ]
    answer = generate_rag_answer(
        question="Why was it chosen?",
        context_chunks=chunks,
        chat_history=history,
    )
    assert len(answer) > 0


@pytest.mark.asyncio
async def test_chat_empty_question_returns_400(client: AsyncClient) -> None:
    response = await client.post("/chat", json={"question": "   "})
    assert response.status_code == 400
    assert "Question cannot be empty" in response.json()["detail"]
