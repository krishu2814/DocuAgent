from app.services.embedding import get_embedding, get_embeddings


def test_huggingface_local_embedding_dimension() -> None:
    sample_text = "DocuAgent is an agentic RAG document assistant."
    embedding = get_embedding(sample_text)

    # all-MiniLM-L6-v2 must produce exactly 384 dimensions
    assert len(embedding) == 384
    assert isinstance(embedding[0], float)


def test_batch_embeddings_dimension() -> None:
    texts = ["First chunk text.", "Second chunk text."]
    embeddings = get_embeddings(texts)

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384
