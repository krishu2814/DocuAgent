from groq import Groq

from app.config import settings


def get_groq_client() -> Groq:
    """Returns the Groq client with the configured API key."""
    return Groq(api_key=settings.GROQ_API_KEY or "dummy_key")


def generate_rag_answer(
    question: str,
    context_chunks: list[str],
    chat_history: list[dict] | None = None,
) -> str:
    """Sends retrieved context chunks, conversation history, and question to Groq LLM."""
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.startswith("gsk_your_") or settings.GROQ_API_KEY.startswith("gsk_dev_"):
        return f"[Dev Mode] Retrieved {len(context_chunks)} chunks for question: '{question}'. Set a real GROQ_API_KEY in .env for live LLM responses."

    try:
        client = get_groq_client()
        context_text = "\n\n---\n\n".join(context_chunks)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a factual, concise document assistant. "
                    "Answer the user's question using ONLY the provided document context. "
                    "If the context does not contain the answer, clearly state: "
                    "'I cannot find sufficient information in the uploaded documents to answer this question.'"
                ),
            }
        ]

        # Append recent conversation history for multi-turn context (last 4 messages)
        if chat_history:
            for msg in chat_history[-4:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        user_prompt = f"""Context from uploaded documents:
{context_text}

Question:
{question}"""

        messages.append({"role": "user", "content": user_prompt})

        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        return f"Failed to generate answer from Groq: {exc}"
