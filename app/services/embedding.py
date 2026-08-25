from functools import lru_cache
from fastembed import TextEmbedding

# Model produces 384-dimensional embeddings (100% compatible with pgvector Vector(384))
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> TextEmbedding:
    """Lazy-loads the lightweight ONNX embedding model (<30MB RAM footprint)."""
    return TextEmbedding(model_name=MODEL_NAME)


def get_embedding(text: str) -> list[float]:
    """Generate vector embedding for a single text query."""
    model = get_embedding_model()
    embeddings = list(model.embed([text]))
    return embeddings[0].tolist()


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate vector embeddings for a list of document chunks."""
    if not texts:
        return []
    model = get_embedding_model()
    embeddings = list(model.embed(texts))
    return [e.tolist() for e in embeddings]
