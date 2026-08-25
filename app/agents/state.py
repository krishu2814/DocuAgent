from typing import Any, TypedDict


class AgentState(TypedDict):
    question: str
    query_type: str  # "SIMPLE" or "COMPLEX"
    retrieved_chunks: list[dict[str, Any]]
    answer: str
    db: Any  # AsyncSession for database vector search
