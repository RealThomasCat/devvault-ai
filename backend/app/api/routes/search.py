from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.search import SearchRequest, SearchResponse
from app.services.retrieval_service import search_document_chunks


router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search_documents(
    request: SearchRequest,
    db: Annotated[Session, Depends(get_db)],
) -> SearchResponse:
    """
    Search uploaded document chunks using vector similarity.
    """

    results = search_document_chunks(
        query=request.query,
        top_k=request.top_k,
        db=db,
    )

    return SearchResponse(results=results)