from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    """
    Request body for semantic vector search.
    """

    # Remove leading and trailing whitespace from string fields before validation.
    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(
        min_length=1,
        max_length=2000,
        description="Text used to search for semantically related document chunks.",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of matching chunks to return.",
    )


class SearchResult(BaseModel):
    """
    One document chunk returned by vector search.
    """

    chunk_id: int
    document_id: int
    filename: str
    content: str
    distance: float


class SearchResponse(BaseModel):
    """
    Complete response returned by the search endpoint.
    """

    results: list[SearchResult]