from pathlib import Path
import pypdf


def extract_pages(file_path: Path) -> list[dict]:
    """Extracts text page-by-page from PDF, or entire content for TXT/MD."""
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        pages = []
        reader = pypdf.PdfReader(str(file_path))
        for page_idx, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append({"text": text, "page": page_idx})
        return pages

    elif suffix in (".txt", ".md"):
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()
        return [{"text": content, "page": None}] if content else []

    else:
        raise ValueError(f"Unsupported file format: {suffix}. Only PDF, TXT, and MD are supported.")


def split_text_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Splits a string into overlapping chunks using a simple sliding window."""
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def process_file_into_chunks(file_path: Path) -> list[dict]:
    """Extracts text from a file and splits it into chunks with page metadata."""
    pages = extract_pages(file_path)
    all_chunks = []

    for page_data in pages:
        text = page_data["text"]
        page_num = page_data["page"]

        chunks = split_text_into_chunks(text, chunk_size=500, overlap=50)
        for chunk in chunks:
            all_chunks.append({
                "content": chunk,
                "page_number": page_num,
            })

    return all_chunks
