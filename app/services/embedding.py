from sentence_transformers import SentenceTransformer

# Free local embedding model (384 dimensions)
model = SentenceTransformer("all-MiniLM-L6-v2")


def get_embedding(text: str) -> list[float]:
    """Generate vector embedding for a single text query."""
    return model.encode(text).tolist()


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate vector embeddings for a list of document chunks."""
    if not texts:
        return []
    return model.encode(texts).tolist()
