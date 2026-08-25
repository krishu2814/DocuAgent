from app.agents.state import AgentState
from app.config import settings
from app.services.llm import generate_rag_answer, get_groq_client
from app.services.retrieval import search_similar_chunks


async def analyze_query_node(state: AgentState) -> dict:
    """Classifies the user question as SIMPLE (direct lookup) or COMPLEX (requires decomposition)."""
    question = state["question"]

    # Fallback heuristic if API key is not active
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.startswith("gsk_your_") or settings.GROQ_API_KEY.startswith("gsk_dev_"):
        lower_q = question.lower()
        query_type = "COMPLEX" if any(w in lower_q for w in ["compare", "difference", "vs", "versus", "steps"]) else "SIMPLE"
        return {"query_type": query_type}

    try:
        client = get_groq_client()
        prompt = f"""Classify the following question into either 'SIMPLE' or 'COMPLEX'.
- SIMPLE: Direct factual lookup, definitions, single topic questions (e.g., 'What is JWT?').
- COMPLEX: Comparisons, multi-part questions, tradeoffs, or multi-topic questions (e.g., 'Compare OAuth vs JWT').

Question: "{question}"

Respond with ONLY the single word: SIMPLE or COMPLEX."""

        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        classification = (response.choices[0].message.content or "SIMPLE").strip().upper()
        query_type = "COMPLEX" if "COMPLEX" in classification else "SIMPLE"
        return {"query_type": query_type}
    except Exception:
        return {"query_type": "SIMPLE"}


async def retriever_node(state: AgentState) -> dict:
    """Retrieves the top 4 most relevant chunks from pgvector for the question."""
    question = state["question"]
    db = state["db"]

    chunks = await search_similar_chunks(query=question, db=db, top_k=4)
    chunks_data = [
        {"content": c.content, "page_number": c.page_number}
        for c in chunks
    ]
    return {"retrieved_chunks": chunks_data}


async def synthesizer_node(state: AgentState) -> dict:
    """Synthesizes the final answer using retrieved chunks and Groq LLM."""
    question = state["question"]
    retrieved_chunks = state.get("retrieved_chunks", [])

    if not retrieved_chunks:
        return {"answer": "No relevant document chunks found to answer this question."}

    chunk_texts = [c["content"] for c in retrieved_chunks]
    answer = generate_rag_answer(question=question, context_chunks=chunk_texts)
    return {"answer": answer}
