import pytest
from sentence_transformers import SentenceTransformer


def test_huggingface_local_embedding_dimension() -> None:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    sample_text = "DocuAgent is an agentic RAG document assistant."
    embedding = model.encode(sample_text)

    # all-MiniLM-L6-v2 must produce exactly 384 dimensions
    assert len(embedding) == 384
    assert isinstance(embedding[0].item(), float)
