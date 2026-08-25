from app.agents.state import AgentState
from app.config import settings
from app.services.llm import generate_rag_answer, get_groq_client
from app.services.retrieval import search_similar_chunks


async def analyze_query_node(state: AgentState) -> dict:
    """Classifies user question as SIMPLE (direct lookup) or COMPLEX (multi-part / comparison)."""
    question = state["question"]
    lower_q = question.lower()
    fallback_type = (
        "COMPLEX"
        if any(w in lower_q for w in ["compare", "difference", "vs", "versus", "steps", "summarise", "summarize"])
        else "SIMPLE"
    )

    # Fallback heuristic if API key is not a real production key
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.startswith("gsk_your_") or settings.GROQ_API_KEY.startswith("gsk_dev_"):
        return {"query_type": fallback_type}

    try:
        client = get_groq_client()
        prompt = f"""Classify the following question as either 'SIMPLE' or 'COMPLEX'.
- SIMPLE: Direct factual question or definition (e.g., 'What is JWT?').
- COMPLEX: Comparisons, multi-topic, or multi-step questions (e.g., 'Compare JWT vs Session cookies').

Question: "{question}"

Respond with ONLY one word: SIMPLE or COMPLEX."""

        model_to_use = settings.GROQ_MODEL
        if "8192" in model_to_use:
            model_to_use = "llama-3.1-8b-instant"

        response = client.chat.completions.create(
            model=model_to_use,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        classification = (response.choices[0].message.content or "").strip().upper()
        query_type = "COMPLEX" if "COMPLEX" in classification else "SIMPLE"
        return {"query_type": query_type}
    except Exception:
        return {"query_type": fallback_type}


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
    """Decomposes a COMPLEX question into 2 focused sub-queries and retrieves chunks for both."""
    question = state["question"]
    db = state["db"]

    # Generate 2 sub-queries using Groq or fallback rule
    sub_queries = [
        f"Key concepts and definitions in: {question}",
        f"Tradeoffs and details in: {question}",
    ]

    if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("gsk_your_") and not settings.GROQ_API_KEY.startswith("gsk_dev_"):
        try:
            client = get_groq_client()
            prompt = f"""Break the following complex user question into exactly 2 distinct search queries.
User question: "{question}"

Format: Return exactly 2 lines, each line containing one search query."""
            model_to_use = settings.GROQ_MODEL
            if "8192" in model_to_use:
                model_to_use = "llama-3.1-8b-instant"

            response = client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            lines = [
                line.strip().lstrip("1234567890.- ")
                for line in (response.choices[0].message.content or "").split("\n")
                if line.strip()
            ]
            if len(lines) >= 2:
                sub_queries = lines[:2]
        except Exception:
            pass

    # Retrieve chunks for each sub-query
    all_chunks_data = []
    seen_contents = set()

    for sub_q in sub_queries:
        sub_chunks = await search_similar_chunks(query=sub_q, db=db, top_k=3)
        for c in sub_chunks:
            if c.content not in seen_contents:
                seen_contents.add(c.content)
                all_chunks_data.append(
                    {
                        "content": c.content,
                        "page_number": c.page_number,
                        "source": c.document.filename if c.document else "Document",
                    }
                )

    return {
        "sub_queries": sub_queries,
        "retrieved_chunks": all_chunks_data,
    }


async def evidence_checker_node(state: AgentState) -> dict:
    """Evaluates whether retrieved chunks contain sufficient evidence."""
    retrieved_chunks = state.get("retrieved_chunks", [])
    if not retrieved_chunks:
        return {"evidence_sufficient": False}

    total_chars = sum(len(c["content"]) for c in retrieved_chunks)
    is_sufficient = total_chars >= 50
    return {"evidence_sufficient": is_sufficient}


async def synthesizer_node(state: AgentState) -> dict:
    """Synthesizes the final grounded answer with citations and multi-turn chat history."""
    question = state["question"]
    retrieved_chunks = state.get("retrieved_chunks", [])
    evidence_sufficient = state.get("evidence_sufficient", True)
    chat_history = state.get("chat_history", [])

    if not evidence_sufficient or not retrieved_chunks:
        return {
            "answer": "I could not find enough relevant information in the uploaded documents to answer your question."
        }

    raw_text_chunks = [c["content"] for c in retrieved_chunks]
    base_answer = generate_rag_answer(
        question=question,
        context_chunks=raw_text_chunks,
        chat_history=chat_history,
    )

    # Format grounded citations from retrieved chunks
    citation_lines = []
    seen_citations = set()

    for chunk in retrieved_chunks:
        source_name = chunk.get("source") or "Document"
        page_num = chunk.get("page_number")
        citation_label = f"{source_name} — Page {page_num}" if page_num else source_name

        if citation_label not in seen_citations:
            seen_citations.add(citation_label)
            citation_lines.append(f"[{len(seen_citations)}] {citation_label}")

    if citation_lines:
        citations_section = "\n\nSources:\n" + "\n".join(citation_lines)
        final_answer = f"{base_answer}{citations_section}"
    else:
        final_answer = base_answer

    return {"answer": final_answer}
