from groq import Groq

from app.config import settings


def get_groq_client() -> Groq:
    """Returns the Groq client with the configured API key."""
    return Groq(api_key=settings.GROQ_API_KEY or "dummy_key")


def generate_rag_answer(question: str, context_chunks: list[str]) -> str:
    """Sends retrieved context chunks and user question to Groq LLM to generate an answer."""
    # Check if a real key is present
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.startswith("gsk_your_") or settings.GROQ_API_KEY.startswith("gsk_dev_"):
        return f"[Dev Mode] Retrieved {len(context_chunks)} chunks for question: '{question}'. Set a real GROQ_API_KEY in .env for live LLM responses."

    try:
        client = get_groq_client()
        context_text = "\n\n---\n\n".join(context_chunks)

        prompt = f"""You are a helpful document assistant. Answer the user's question using ONLY the provided context below.
If the context does not have enough information to answer the question, clearly state: "I cannot find sufficient information in the uploaded documents to answer this question."

Context:
{context_text}

Question:
{question}

Answer:"""

        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a concise, factual assistant that answers questions based on documents."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        return f"Failed to generate answer from Groq: {exc}"
