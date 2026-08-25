from app.agents.state import AgentState
from app.config import settings
from app.services.llm import generate_rag_answer, get_groq_client
from app.services.retrieval import search_similar_chunks


async def analyze_query_node(state: AgentState) -> dict:
    """Classifies user question as SIMPLE (direct lookup) or COMPLEX (multi-part / comparison)."""
    question = state["question"]

    # Fallback heuristic if API key is not active
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.startswith("gsk_your_") or settings.GROQ_API_KEY.startswith("gsk_dev_"):
        lower_q = question.lower()
        query_type = "COMPLEX" if any(w in lower_q for w in ["compare", "difference", "vs", "versus", "steps"]) else "SIMPLE"
        return {"query_type": query_type}

    try:
        client = get_groq_client()
        prompt = f"""Classify the following question as either 'SIMPLE' or 'COMPLEX'.
- SIMPLE: Direct factual question or definition (e.g., 'What is JWT?').
- COMPLEX: Comparisons, multi-topic, or multi-step questions (e.g., 'Compare JWT vs Session cookies').

Question: "{question}"

Respond with ONLY one word: SIMPLE or COMPLEX."""

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
    """Direct retrieval for SIMPLE queries: fetches top 4 chunks for the question."""
    question = state["question"]
    db = state["db"]

    chunks = await search_similar_chunks(query=question, db=db, top_k=4)
    chunks_data = [
        {
            "content": c.content,
            "page_number": c.page_number,
            "source": c.document.filename if c.document else "Document",
        }
        for c in chunks
    ]
    return {"retrieved_chunks": chunks_data}


async def query_planner_node(state: AgentState) -> dict:
    """Decomposes COMPLEX queries into 2 sub-queries and retrieves chunks for each."""
    question = state["question"]
    db = state["db"]
    sub_queries: list[str] = []

    # 1. Generate sub-queries
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.startswith("gsk_your_") or settings.GROQ_API_KEY.startswith("gsk_dev_"):
        sub_queries = [question, f"Details and comparison regarding {question}"]
    else:
        try:
            client = get_groq_client()
            prompt = f"""Break down this complex question into 2 distinct, focused search sub-queries.
Return ONLY the 2 sub-queries, one per line.

Complex question: "{question}"

Sub-queries:"""

            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            raw_lines = (response.choices[0].message.content or "").strip().split("\n")
            sub_queries = [line.strip().lstrip("123456789.-* ") for line in raw_lines if line.strip()][:2]
        except Exception:
            sub_queries = [question]

    if not sub_queries:
        sub_queries = [question]

    # 2. Search chunks for each sub-query and combine distinct results
    seen_contents: set[str] = set()
    combined_chunks: list[dict] = []

    for sq in sub_queries:
        chunks = await search_similar_chunks(query=sq, db=db, top_k=2)
        for c in chunks:
            if c.content not in seen_contents:
                seen_contents.add(c.content)
                combined_chunks.append({
                    "content": c.content,
                    "page_number": c.page_number,
                    "source": c.document.filename if c.document else "Document",
                })

    return {
        "sub_queries": sub_queries,
        "retrieved_chunks": combined_chunks,
    }


async def evidence_checker_node(state: AgentState) -> dict:
    """Checks if the retrieved chunks provide sufficient evidence to answer the question."""
    retrieved_chunks = state.get("retrieved_chunks", [])
    if not retrieved_chunks:
        return {"evidence_sufficient": False}

    sufficient = len(retrieved_chunks) > 0 and sum(len(c["content"]) for c in retrieved_chunks) > 50
    return {"evidence_sufficient": sufficient}


async def synthesizer_node(state: AgentState) -> dict:
    """Synthesizes final answer with multi-turn memory and appends genuine citations."""
    question = state["question"]
    retrieved_chunks = state.get("retrieved_chunks", [])
    chat_history = state.get("chat_history", [])

    if not retrieved_chunks:
        return {"answer": "No relevant document chunks found in the database to answer this question."}

    # 1. Generate core answer from LLM with conversation history
    chunk_texts = [c["content"] for c in retrieved_chunks]
    base_answer = generate_rag_answer(
        question=question,
        context_chunks=chunk_texts,
        chat_history=chat_history,
    )

    # 2. Build unique, verifiable citations from actual chunks
    unique_sources = []
    seen_citations = set()

    for c in retrieved_chunks:
        source_name = c.get("source", "Document")
        page = c.get("page_number")
        citation_str = f"{source_name} — Page {page}" if page else source_name

        if citation_str not in seen_citations:
            seen_citations.add(citation_str)
            unique_sources.append(citation_str)

    # 3. Append citations section
    citations_text = "\n\nSources:\n" + "\n".join(f"[{i+1}] {s}" for i, s in enumerate(unique_sources))
    full_answer = f"{base_answer}{citations_text}"

    return {"answer": full_answer}
