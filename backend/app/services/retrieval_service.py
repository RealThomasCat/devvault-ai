from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.document import Document
from app.db.models.document_chunk import DocumentChunk
from app.schemas.search import SearchResult
from app.services.embedding_service import embed_text


def search_document_chunks(
    query: str,
    top_k: int,
    db: Session,
) -> list[SearchResult]:
    """
    Embed a search query and return the nearest document chunks.
    """

    query_embedding = embed_text(query)

    # Define the cosine-distance expression.
    # This computes the cosine distance between the query embedding and each document chunk's embedding.
    distance = DocumentChunk.embedding.cosine_distance(
        query_embedding
    ).label("distance")

    # Build the SQLAlchemy query to retrieve the nearest document chunks.
    statement = (
         # Select the chunk ID as chunk_id, document ID, filename, content, and the computed distance.
        select(
            DocumentChunk.id.label("chunk_id"),
            DocumentChunk.document_id,
            Document.filename,
            DocumentChunk.content,
            distance,
        )
        .select_from(DocumentChunk)
        # Join chunks with their corresponding documents to get the filename.
        .join(
            Document,
            Document.id == DocumentChunk.document_id,
        )
        .where(DocumentChunk.embedding.is_not(None))
        # Sort by distance and limit the number of results to top_k.
        .order_by(distance)
        .limit(top_k)
    )

    # Execute the query and fetch all results.
    rows = db.execute(statement).all()

    # Return a list of SearchResult objects constructed from the query results.
    return [
        SearchResult(
            chunk_id=row.chunk_id,
            document_id=row.document_id,
            filename=row.filename,
            content=row.content,
            distance=float(row.distance),
        )
        for row in rows
    ]