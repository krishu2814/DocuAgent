from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import DocumentChunk
from app.services.embedding import get_embedding


async def search_similar_chunks(
    query: str,
    db: AsyncSession,
    top_k: int = 4,
) -> list[DocumentChunk]:
    """Finds the most relevant document chunks for a question using pgvector cosine distance."""
    # 1. Convert question into a 384-dimensional vector
    query_vector = get_embedding(query)

    # 2. Query database for chunks closest to the question vector
    statement = (
        select(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        .limit(top_k)
    )
    result = await db.execute(statement)
    return list(result.scalars().all())
