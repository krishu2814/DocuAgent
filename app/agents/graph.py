from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.nodes import (
    analyze_query_node,
    evidence_checker_node,
    query_planner_node,
    retriever_node,
    synthesizer_node,
)
from app.agents.state import AgentState


def route_by_query_type(state: AgentState) -> str:
    """Routes execution: SIMPLE goes to retriever, COMPLEX goes to query_planner."""
    if state.get("query_type") == "COMPLEX":
        return "query_planner"
    return "retriever"


def build_rag_graph():
    """Builds the 5-node LangGraph state machine with conditional routing."""
    workflow = StateGraph(AgentState)

    # 1. Register nodes
    workflow.add_node("analyze_query", analyze_query_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("query_planner", query_planner_node)
    workflow.add_node("evidence_checker", evidence_checker_node)
    workflow.add_node("synthesizer", synthesizer_node)

    # 2. Set entry point
    workflow.set_entry_point("analyze_query")

    # 3. Add conditional edge from analyzer
    workflow.add_conditional_edges(
        "analyze_query",
        route_by_query_type,
        {
            "retriever": "retriever",
            "query_planner": "query_planner",
        },
    )

    # 4. Simple branch flow
    workflow.add_edge("retriever", "synthesizer")

    # 5. Complex branch flow
    workflow.add_edge("query_planner", "evidence_checker")
    workflow.add_edge("evidence_checker", "synthesizer")

    # 6. Exit
    workflow.add_edge("synthesizer", END)

    return workflow.compile()


# Compiled LangGraph state machine
rag_graph = build_rag_graph()


async def run_agent_workflow(
    question: str,
    db: AsyncSession,
    chat_history: list[dict] | None = None,
) -> dict:
    """Executes the LangGraph state machine on a user question with conversation history."""
    initial_state: AgentState = {
        "question": question,
        "query_type": "SIMPLE",
        "sub_queries": [],
        "retrieved_chunks": [],
        "evidence_sufficient": True,
        "chat_history": chat_history or [],
        "answer": "",
        "db": db,
    }
    final_state = await rag_graph.ainvoke(initial_state)
    return final_state
