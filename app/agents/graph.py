from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.nodes import (
    analyze_query_node,
    retriever_node,
    synthesizer_node,
)
from app.agents.state import AgentState


def build_rag_graph():
    """Builds the LangGraph state machine for simple agentic RAG."""
    workflow = StateGraph(AgentState)

    # 1. Add nodes
    workflow.add_node("analyze_query", analyze_query_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("synthesizer", synthesizer_node)

    # 2. Define execution flow
    workflow.set_entry_point("analyze_query")
    workflow.add_edge("analyze_query", "retriever")
    workflow.add_edge("retriever", "synthesizer")
    workflow.add_edge("synthesizer", END)

    return workflow.compile()


# Compiled LangGraph instance
rag_graph = build_rag_graph()


async def run_agent_workflow(question: str, db: AsyncSession) -> dict:
    """Runs the LangGraph workflow on a user question and returns the final state."""
    initial_state: AgentState = {
        "question": question,
        "query_type": "SIMPLE",
        "retrieved_chunks": [],
        "answer": "",
        "db": db,
    }
    final_state = await rag_graph.ainvoke(initial_state)
    return final_state
