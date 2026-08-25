from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import Any
import pypdf

logger = logging.getLogger(__name__)


@dataclass
class ExtractedPage:
    content: str
    page_number: int | None = None


@dataclass
class RawChunk:
    chunk_index: int
    content: str
    page_number: int | None
    metadata: dict[str, Any] = field(default_factory=dict)


def extract_text_from_pdf(file_path: Path) -> list[ExtractedPage]:
    pages: list[ExtractedPage] = []
    try:
        reader = pypdf.PdfReader(str(file_path))
        for idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages.append(ExtractedPage(content=text, page_number=idx))
    except Exception as exc:
        logger.error(f"Failed to extract text from PDF {file_path}: {exc}")
        raise ValueError(f"Could not parse PDF file: {exc}") from exc

    if not pages:
        raise ValueError("PDF file is empty or contains no extractable text.")

    return pages


def extract_text_from_text_file(file_path: Path) -> list[ExtractedPage]:
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()
    except Exception as exc:
        logger.error(f"Failed to read file {file_path}: {exc}")
        raise ValueError(f"Could not read file: {exc}") from exc

    if not content:
        raise ValueError("File is empty.")

    return [ExtractedPage(content=content, page_number=None)]


def extract_document_pages(file_path: Path) -> list[ExtractedPage]:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in (".txt", ".md", ".markdown"):
        return extract_text_from_text_file(file_path)
    else:
        raise ValueError(f"Unsupported file format '{suffix}'. Supported: .pdf, .txt, .md")


def chunk_text(
    text: str,
    page_number: int | None,
    start_index: int,
    source_filename: str,
    chunk_size: int = 600,
    chunk_overlap: int = 100,
) -> tuple[list[RawChunk], int]:
    chunks: list[RawChunk] = []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    current_chunk: list[str] = []
    current_length = 0
    current_idx = start_index

    for para in paragraphs:
        # If single paragraph exceeds chunk size, split by lines or sentences
        if len(para) > chunk_size:
            lines = [line.strip() for line in para.split("\n") if line.strip()]
            for line in lines:
                if current_length + len(line) > chunk_size and current_chunk:
                    chunk_str = "\n".join(current_chunk)
                    chunks.append(
                        RawChunk(
                            chunk_index=current_idx,
                            content=chunk_str,
                            page_number=page_number,
                            metadata={
                                "source": source_filename,
                                "page": page_number,
                                "char_count": len(chunk_str),
                            },
                        )
                    )
                    current_idx += 1
                    # Keep overlap from previous paragraph
                    overlap_chars = 0
                    overlap_items: list[str] = []
                    for item in reversed(current_chunk):
                        if overlap_chars + len(item) <= chunk_overlap:
                            overlap_items.insert(0, item)
                            overlap_chars += len(item)
                        else:
                            break
                    current_chunk = overlap_items
                    current_length = sum(len(x) for x in current_chunk)

                current_chunk.append(line)
                current_length += len(line)
        else:
            if current_length + len(para) > chunk_size and current_chunk:
                chunk_str = "\n\n".join(current_chunk)
                chunks.append(
                    RawChunk(
                        chunk_index=current_idx,
                        content=chunk_str,
                        page_number=page_number,
                        metadata={
                            "source": source_filename,
                            "page": page_number,
                            "char_count": len(chunk_str),
                        },
                    )
                )
                current_idx += 1

                # Retain overlap
                current_chunk = [current_chunk[-1]] if current_chunk else []
                current_length = sum(len(x) for x in current_chunk)

            current_chunk.append(para)
            current_length += len(para)

    # Flush remaining buffer
    if current_chunk:
        chunk_str = "\n\n".join(current_chunk)
        chunks.append(
            RawChunk(
                chunk_index=current_idx,
                content=chunk_str,
                page_number=page_number,
                metadata={
                    "source": source_filename,
                    "page": page_number,
                    "char_count": len(chunk_str),
                },
            )
        )
        current_idx += 1

    return chunks, current_idx


def process_document_chunks(
    file_path: Path,
    source_filename: str,
    chunk_size: int = 600,
    chunk_overlap: int = 100,
) -> list[RawChunk]:
    pages = extract_document_pages(file_path)
    all_chunks: list[RawChunk] = []
    current_index = 0

    for page in pages:
        page_chunks, next_index = chunk_text(
            text=page.content,
            page_number=page.page_number,
            start_index=current_index,
            source_filename=source_filename,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        all_chunks.extend(page_chunks)
        current_index = next_index

    return all_chunks
