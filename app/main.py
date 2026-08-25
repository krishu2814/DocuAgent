from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import settings
from app.database import init_db
from app.routes.chat import router as chat_router
from app.routes.documents import router as documents_router

logger = logging.getLogger("docuagent.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    try:
        await init_db()
        logger.info("Database initialized with pgvector extension.")
    except Exception as exc:
        logger.warning(f"Database auto-initialization skipped or deferred: {exc}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Agentic RAG Document Assistant with LangGraph, PostgreSQL & pgvector",
    version="1.0.0",
    docs_url="/docs" if settings.is_dev else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    project: str
    environment: str


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        project=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
    )


# Mount API Routers First
app.include_router(documents_router)
app.include_router(chat_router)

# Mount Static Frontend if present
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
