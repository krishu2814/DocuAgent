import pytest

from app.agents.graph import rag_graph, route_by_query_type
from app.agents.nodes import (
    analyze_query_node,
    evidence_checker_node,
    query_planner_node,
    synthesizer_node,
)
from app.agents.state import AgentState


@pytest.mark.asyncio
async def test_analyze_query_node_simple() -> None:
    state: AgentState = {
        "question": "What is JWT?",
        "query_type": "",
        "sub_queries": [],
        "retrieved_chunks": [],
        "evidence_sufficient": True,
        "chat_history": [],
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
        "sub_queries": [],
        "retrieved_chunks": [],
        "evidence_sufficient": True,
        "chat_history": [],
        "answer": "",
        "db": None,
    }
    result = await analyze_query_node(state)
    assert result["query_type"] == "COMPLEX"


@pytest.mark.asyncio
async def test_evidence_checker_node() -> None:
    empty_state: AgentState = {
        "question": "What is JWT?",
        "query_type": "SIMPLE",
        "sub_queries": [],
        "retrieved_chunks": [],
        "evidence_sufficient": False,
        "chat_history": [],
        "answer": "",
        "db": None,
    }
    empty_result = await evidence_checker_node(empty_state)
    assert empty_result["evidence_sufficient"] is False

    valid_state: AgentState = {
        "question": "What is JWT?",
        "query_type": "SIMPLE",
        "sub_queries": [],
        "retrieved_chunks": [{"content": "JWT is a JSON Web Token used for authentication." * 2}],
        "evidence_sufficient": False,
        "chat_history": [],
        "answer": "",
        "db": None,
    }
    valid_result = await evidence_checker_node(valid_state)
    assert valid_result["evidence_sufficient"] is True


@pytest.mark.asyncio
async def test_synthesizer_appends_citations() -> None:
    state: AgentState = {
        "question": "How does auth work?",
        "query_type": "SIMPLE",
        "sub_queries": [],
        "retrieved_chunks": [
            {
                "content": "Tokens are signed with a private key.",
                "source": "auth_spec.pdf",
                "page_number": 4,
            }
        ],
        "evidence_sufficient": True,
        "chat_history": [],
        "answer": "",
        "db": None,
    }
    result = await synthesizer_node(state)
    assert "Sources:" in result["answer"]
    assert "auth_spec.pdf — Page 4" in result["answer"]


def test_route_by_query_type() -> None:
    simple_state: AgentState = {"query_type": "SIMPLE", "question": "", "sub_queries": [], "retrieved_chunks": [], "evidence_sufficient": True, "chat_history": [], "answer": "", "db": None}
    complex_state: AgentState = {"query_type": "COMPLEX", "question": "", "sub_queries": [], "retrieved_chunks": [], "evidence_sufficient": True, "chat_history": [], "answer": "", "db": None}

    assert route_by_query_type(simple_state) == "retriever"
    assert route_by_query_type(complex_state) == "query_planner"


def test_rag_graph_all_5_nodes_exist() -> None:
    node_keys = list(rag_graph.nodes.keys())
    assert "analyze_query" in node_keys
    assert "retriever" in node_keys
    assert "query_planner" in node_keys
    assert "evidence_checker" in node_keys
    assert "synthesizer" in node_keys
