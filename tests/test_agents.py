import pytest

from app.agents.graph import rag_graph
from app.agents.nodes import analyze_query_node, synthesizer_node
from app.agents.state import AgentState


@pytest.mark.asyncio
async def test_analyze_query_node_simple() -> None:
    state: AgentState = {
        "question": "What is JWT?",
        "query_type": "",
        "retrieved_chunks": [],
        "answer": "",
        "db": None,
    }
    result = await analyze_query_node(state)
    assert result["query_type"] == "SIMPLE"


@pytest.mark.asyncio
async def test_analyze_query_node_complex() -> None:
    state: AgentState = {
        "question": "Compare JWT vs Session cookies for auth",
        "query_type": "",
        "retrieved_chunks": [],
        "answer": "",
        "db": None,
    }
    result = await analyze_query_node(state)
    assert result["query_type"] == "COMPLEX"


@pytest.mark.asyncio
async def test_synthesizer_node_with_empty_chunks() -> None:
    state: AgentState = {
        "question": "What is JWT?",
        "query_type": "SIMPLE",
        "retrieved_chunks": [],
        "answer": "",
        "db": None,
    }
    result = await synthesizer_node(state)
    assert "No relevant document chunks found" in result["answer"]


def test_rag_graph_nodes_exist() -> None:
    # Verify LangGraph compiled state machine contains our 3 nodes
    node_keys = list(rag_graph.nodes.keys())
    assert "analyze_query" in node_keys
    assert "retriever" in node_keys
    assert "synthesizer" in node_keys
