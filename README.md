# DocuAgent — Agentic RAG Document Assistant

<div align="center">

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://docuagent-30lj.onrender.com)
[![API Docs](https://img.shields.io/badge/Interactive%20Docs-Swagger%20UI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://docuagent-30lj.onrender.com/docs)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Groq](https://img.shields.io/badge/Groq-Fast%20LLM-F05A28?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20Workflow-FF6F00?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain.com)

<br/>

**DocuAgent** is a production-ready **Agentic RAG (Retrieval-Augmented Generation)** document intelligence platform. It features **query decomposition**, **pgvector semantic similarity search**, **sub-second ONNX embeddings**, **multi-turn conversation memory**, and **grounded page-level citations**.

[🚀 Open Live App](https://docuagent-30lj.onrender.com) • [📖 Interactive API Docs](https://docuagent-30lj.onrender.com/docs) • [🛠️ Architecture](#-system-architecture)

</div>

---

## 🌟 Key Highlights

- **🌐 Live Production Deployment**: Hosted on Render with serverless Neon PostgreSQL + `pgvector`.
- **🧠 5-Node LangGraph Agentic Pipeline**: Analyzes user intent, routes queries (Simple vs. Complex), decomposes multi-part questions, and verifies retrieved evidence before synthesis.
- **⚡ Sub-Second ONNX Embeddings**: Uses lightweight FastEmbed (`all-MiniLM-L6-v2`, 384 dimensions) with <30MB RAM footprint for fast, cost-free local vectorization.
- **📚 Grounded Page-Level Citations**: Every answer links directly to the exact source document and page number (`[1] filename.pdf — Page 4`).
- **💬 Multi-Turn Conversation Memory**: Maintains dialogue context across turns via relational message history.
- **🎨 Modern Embedded UI**: Pure Vanilla HTML5/CSS/JS single-page dashboard with real-time markdown rendering and source badge inspection.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Client["User Interface & API"]
        UI["Modern Web Client (Vanilla JS/CSS)"]
        API["FastAPI 0.115+ REST Backend"]
        UI <--> API
    end

    subgraph Ingestion["Document Ingestion Pipeline"]
        Upload["Document Upload (.pdf, .md, .txt)"] --> Parser["pypdf & Text Extractors"]
        Parser --> Chunker["Character-Aware Chunker (1000 chars, 200 overlap)"]
        Chunker --> FastEmbed["FastEmbed ONNX (384-dim Dense Vectors)"]
        FastEmbed --> DBInsert["pgvector Vector(384) Storage"]
    end

    subgraph LangGraph["Agentic RAG StateGraph"]
        Q["User Query"] --> Analyzer{"1. Query Analyzer Node"}
        
        Analyzer -->|"SIMPLE (Direct lookup)"| Retriever["2. Retriever Node (Top 4 Chunks)"]
        Analyzer -->|"COMPLEX (Comparison / Multi-part)"| Planner["3. Query Planner (Decomposes into 2 Sub-queries)"]
        
        Planner --> MultiSearch["Sub-query Semantic Search"]
        MultiSearch --> Evidence{"4. Evidence Checker Node"}
        
        Evidence -->|"Sufficient"| Synthesizer["5. Synthesizer Node"]
        Evidence -->|"Insufficient"| Fallback["Graceful Fallback Response"]
        
        Retriever --> Synthesizer
        Synthesizer --> Groq["Groq Cloud LLM (groq/compound-mini)"]
        Groq --> Output["Grounded Response + Memory + Citations"]
    end

    API --> Ingestion
    API --> LangGraph
    DBInsert --> Postgres[("PostgreSQL 16 + pgvector")]
    Retriever <--> Postgres
    MultiSearch <--> Postgres
```

---

## 🔬 Why Agentic RAG over Naive RAG?

| Feature | Naive RAG | DocuAgent (Agentic RAG) |
| :--- | :--- | :--- |
| **Simple Queries** | Single vector search | Routed to direct retriever (sub-100ms) |
| **Comparative Queries** | Often retrieves only one side of the topic | Decomposed into 2 focused sub-queries for balanced retrieval |
| **Hallucination Prevention** | None (sends raw chunks directly to LLM) | **Evidence Checker Node** validates retrieved context quality |
| **Citations** | LLM-generated (prone to hallucinated sources) | **System-Enforced** from actual database chunk metadata |
| **Multi-turn Dialogue** | Stateless | **Relational Conversation Memory** stored in PostgreSQL |

---

## 🚀 Live Demo & API Usage

**Live App URL**: [https://docuagent-30lj.onrender.com](https://docuagent-30lj.onrender.com)  
**Interactive Swagger Docs**: [https://docuagent-30lj.onrender.com/docs](https://docuagent-30lj.onrender.com/docs)

### 1. Health Check
```bash
curl https://docuagent-30lj.onrender.com/health
```

### 2. Upload Document (PDF / TXT / Markdown)
```bash
curl -X POST https://docuagent-30lj.onrender.com/documents/upload \
  -F "file=@architecture_spec.pdf"
```

### 3. Ask a Question with Citations
```bash
curl -X POST https://docuagent-30lj.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What encryption standards and authentication protocols are used?"
  }'
```

**Response:**
```json
{
  "conversation_id": "8edd5fa3-dcbb-4b6c-a4f1-72069cb26608",
  "question": "What encryption standards and authentication protocols are used?",
  "answer": "The system enforces AES-GCM-256 encryption at rest, TLS 1.3 in transit, and JWT signed tokens for authentication.\n\nSources:\n[1] architecture_spec.pdf — Page 3",
  "sources": [
    {
      "content": "All customer records are encrypted at rest using AES-GCM-256 and in transit using TLS 1.3...",
      "page_number": 3,
      "source": "architecture_spec.pdf"
    }
  ]
}
```

### 4. Multi-Turn Follow-Up (Conversational Memory)
```bash
curl -X POST https://docuagent-30lj.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "8edd5fa3-dcbb-4b6c-a4f1-72069cb26608",
    "question": "How long are customer transaction logs retained under this policy?"
  }'
```

---

## 💻 Local Development Setup

### Prerequisites
- Python 3.12+
- Docker & Docker Compose (or local PostgreSQL with pgvector)
- A free [Groq API Key](https://console.groq.com/keys)

### Option A: Running with Docker Compose
```bash
# 1. Clone the repository
git clone https://github.com/krishu2814/DocuAgent.git
cd DocuAgent

# 2. Setup environment variables
cp .env.example .env
# Set GROQ_API_KEY=gsk_... in .env

# 3. Launch database and API
docker compose up --build
```
The app will be running at `http://localhost:8000`.

---

### Option B: Running Locally with Virtualenv
```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start local pgvector instance
docker run -d --name docuagent-db -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=docuagent \
  pgvector/pgvector:pg16

# 4. Start development server
uvicorn app.main:app --reload --port 8000
```

---

## ⚙️ Environment Variables

| Variable | Description | Required in Production | Default |
| :--- | :--- | :---: | :--- |
| `DATABASE_URL` | PostgreSQL connection string with pgvector | **Yes** | `postgresql+asyncpg://postgres:postgres@localhost:5432/docuagent` |
| `GROQ_API_KEY` | Groq API Key for fast LLM answers | **Yes** | `""` |
| `GROQ_MODEL` | Active Groq LLM model | No | `groq/compound-mini` |
| `ENVIRONMENT` | Environment mode (`production` / `development`) | No | `development` |
| `FRONTEND_URL` | Allowed CORS origin for decoupled frontend | No | `""` (Allows all / same-origin) |

---

## 🧪 Testing & Verification

DocuAgent includes a comprehensive **21-test pytest suite** covering units, async database connections, text extraction, ONNX embeddings, LangGraph routing, memory persistence, and end-to-end RAG workflows:

```bash
pytest -v
```

```text
============================= test session starts ==============================
collected 21 items

tests/test_agents.py::test_analyze_query_node_simple PASSED              [  4%]
tests/test_agents.py::test_analyze_query_node_complex PASSED             [  9%]
tests/test_agents.py::test_evidence_checker_node PASSED                  [ 14%]
tests/test_agents.py::test_synthesizer_appends_citations PASSED          [ 19%]
tests/test_agents.py::test_route_by_query_type PASSED                    [ 23%]
tests/test_agents.py::test_rag_graph_all_5_nodes_exist PASSED            [ 28%]
tests/test_config.py::test_settings_defaults PASSED                      [ 33%]
tests/test_config.py::test_settings_production_cors PASSED               [ 38%]
tests/test_document_routes.py::test_upload_unsupported_file_type_returns_400 PASSED [ 42%]
tests/test_document_routes.py::test_get_nonexistent_document_returns_404 PASSED [ 47%]
tests/test_embeddings_smoke.py::test_huggingface_local_embedding_dimension PASSED [ 52%]
tests/test_embeddings_smoke.py::test_batch_embeddings_dimension PASSED   [ 57%]
tests/test_health.py::test_health_check PASSED                           [ 61%]
tests/test_health.py::test_frontend_home_page PASSED                     [ 66%]
tests/test_ingestion.py::test_extract_text_file PASSED                   [ 71%]
tests/test_ingestion.py::test_extract_markdown_file PASSED               [ 76%]
tests/test_ingestion.py::test_unsupported_file_format_raises_error PASSED [ 80%]
tests/test_ingestion.py::test_split_text_into_chunks PASSED              [ 85%]
tests/test_ingestion.py::test_process_file_into_chunks PASSED            [ 90%]
tests/test_rag.py::test_generate_rag_answer_with_chat_history PASSED     [ 95%]
tests/test_rag.py::test_chat_empty_question_returns_400 PASSED           [100%]

============================== 21 passed in 1.62s ==============================
```

---

## 📁 Repository Structure

```text
DocuAgent/
├── app/
│   ├── main.py              # FastAPI app, lifespan, CORS & static frontend mounting
│   ├── config.py            # Pydantic Settings for environment variables
│   ├── database.py          # SQLAlchemy async engine, cloud URL normalizer & Base
│   │
│   ├── models/              # Relational & Vector Models
│   │   ├── document.py      # Document model (id, filename, file_path, created_at)
│   │   ├── chunk.py         # DocumentChunk model (content, page_number, Vector(384))
│   │   └── conversation.py  # Conversation & Message models for conversational memory
│   │
│   ├── routes/              # FastAPI REST Endpoints
│   │   ├── documents.py     # POST /documents/upload, GET /documents, DELETE /documents/{id}
│   │   └── chat.py          # POST /chat, GET /chat/conversations/{id}
│   │
│   ├── services/            # Core Services
│   │   ├── ingestion.py     # Multi-format document parser & chunking
│   │   ├── embedding.py     # FastEmbed ONNX local vector generation (<30MB RAM)
│   │   ├── retrieval.py     # pgvector cosine similarity search
│   │   └── llm.py           # Groq LLM integration with resilient multi-model fallback
│   │
│   └── agents/              # LangGraph Agentic RAG
│       ├── state.py         # AgentState TypedDict definition
│       ├── nodes.py         # 5 LangGraph agent nodes
│       └── graph.py         # StateGraph assembly & conditional routing
│
├── frontend/                # Lightweight Embedded Frontend
│   ├── index.html           # Semantic Single-Page Dashboard
│   ├── styles.css           # Modern Clean Design System
│   └── app.js               # Reactive Chat, Upload & Document Management
│
├── tests/                   # Complete Pytest Test Suite
├── Dockerfile               # Production Docker container with pre-baked ONNX cache
├── docker-compose.yml       # Local multi-service orchestration
├── requirements.txt         # Pinned production dependencies
├── .env.example             # Example environment variable template
└── README.md
```

---

## 📄 License
MIT License. Created by [Krishu Kumar](https://github.com/krishu2814). Free to use for personal, academic, and portfolio purposes.
