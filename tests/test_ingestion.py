from pathlib import Path
import tempfile
import pytest

from app.services.ingestion import (
    extract_pages,
    process_file_into_chunks,
    split_text_into_chunks,
)


def test_extract_text_file() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("Hello DocuAgent. Simple RAG assistant.")
        temp_path = Path(f.name)

    try:
        pages = extract_pages(temp_path)
        assert len(pages) == 1
        assert "Hello DocuAgent" in pages[0]["text"]
        assert pages[0]["page"] is None
    finally:
        temp_path.unlink(missing_ok=True)


def test_extract_markdown_file() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write("# LangGraph\n\nDocuAgent uses LangGraph for agentic workflow.")
        temp_path = Path(f.name)

    try:
        pages = extract_pages(temp_path)
        assert len(pages) == 1
        assert "DocuAgent uses LangGraph" in pages[0]["text"]
    finally:
        temp_path.unlink(missing_ok=True)


def test_unsupported_file_format_raises_error() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".exe", delete=False) as f:
        f.write("test")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="Unsupported file format"):
            extract_pages(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)


def test_split_text_into_chunks() -> None:
    text = "A" * 1200
    chunks = split_text_into_chunks(text, chunk_size=500, overlap=50)
    assert len(chunks) == 3


def test_process_file_into_chunks() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("Section 1: Authentication with JWT tokens.\n\nSection 2: PostgreSQL and pgvector.")
        temp_path = Path(f.name)

    try:
        chunks = process_file_into_chunks(temp_path)
        assert len(chunks) >= 1
        assert "content" in chunks[0]
        assert "page_number" in chunks[0]
    finally:
        temp_path.unlink(missing_ok=True)
