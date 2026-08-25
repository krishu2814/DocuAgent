from typing import Any, TypedDict


class AgentState(TypedDict):
    question: str
    query_type: str  # "SIMPLE" or "COMPLEX"
    sub_queries: list[str]  # Sub-questions generated for COMPLEX queries
    retrieved_chunks: list[dict[str, Any]]
    evidence_sufficient: bool  # Determined by evidence_checker
    answer: str
    db: Any  # AsyncSession for database search
