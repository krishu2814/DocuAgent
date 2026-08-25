from pathlib import Path
import tempfile
import pytest

from app.services.ingestion import (
    ExtractedPage,
    chunk_text,
    extract_document_pages,
    extract_text_from_text_file,
    process_document_chunks,
)


def test_extract_text_file() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("Hello DocuAgent.\nThis is a sample document.")
        temp_path = Path(f.name)

    try:
        pages = extract_text_from_text_file(temp_path)
        assert len(pages) == 1
        assert "Hello DocuAgent" in pages[0].content
        assert pages[0].page_number is None
    finally:
        temp_path.unlink(missing_ok=True)


def test_extract_markdown_file() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write("# Architecture\n\nDocuAgent uses LangGraph for agentic RAG.")
        temp_path = Path(f.name)

    try:
        pages = extract_document_pages(temp_path)
        assert len(pages) == 1
        assert "DocuAgent uses LangGraph" in pages[0].content
    finally:
        temp_path.unlink(missing_ok=True)


def test_unsupported_format_raises_error() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".xyz", delete=False) as f:
        f.write("Some text")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="Unsupported file format"):
            extract_document_pages(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)


def test_chunking_preserves_metadata_and_overlap() -> None:
    text = (
        "Paragraph 1 is about authentication and JSON Web Tokens in distributed systems.\n\n"
        "Paragraph 2 is about database storage with PostgreSQL and pgvector embeddings.\n\n"
        "Paragraph 3 discusses LangGraph query routing and evaluation loops."
    )

    chunks, next_idx = chunk_text(
        text=text,
        page_number=3,
        start_index=0,
        source_filename="system_design.pdf",
        chunk_size=120,
        chunk_overlap=30,
    )

    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk.page_number == 3
        assert chunk.metadata["source"] == "system_design.pdf"
        assert chunk.metadata["page"] == 3
        assert len(chunk.content) > 0


def test_process_document_chunks_end_to_end() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("Section 1: Setup\n\nSection 2: Agents\n\nSection 3: Testing")
        temp_path = Path(f.name)

    try:
        chunks = process_document_chunks(
            file_path=temp_path,
            source_filename="guide.txt",
            chunk_size=50,
            chunk_overlap=10,
        )
        assert len(chunks) >= 1
        assert chunks[0].metadata["source"] == "guide.txt"
    finally:
        temp_path.unlink(missing_ok=True)
