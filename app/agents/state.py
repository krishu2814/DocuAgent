from typing import Any, TypedDict


class AgentState(TypedDict):
    question: str
    query_type: str  # "SIMPLE" or "COMPLEX"
    sub_queries: list[str]  # Sub-queries for complex questions
    retrieved_chunks: list[dict[str, Any]]
    evidence_sufficient: bool  # Determined by evidence_checker
    chat_history: list[dict[str, str]]  # Multi-turn conversation memory
    answer: str
    db: Any  # AsyncSession for database search
