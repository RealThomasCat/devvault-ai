from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """
    Request body for source-cited question answering.
    """

    # Configure Pydantic model to automatically strip whitespace from string fields.
    # ConfigDict is a Pydantic class that allows you to configure model behavior.
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(
        min_length=1,
        max_length=2000,
        description="Question to answer using uploaded document content.",
    )


class ChatCitation(BaseModel):
    """
    One retrieved document chunk returned as a source citation.
    """

    chunk_id: int
    document_id: int
    filename: str
    snippet: str


class ChatResponse(BaseModel):
    """
    Complete response returned by the chat endpoint.
    """

    answer: str
    citations: list[ChatCitation]