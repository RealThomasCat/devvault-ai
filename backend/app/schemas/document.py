from datetime import datetime

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    chunk_count: int


class DocumentSummary(BaseModel):
    document_id: int
    filename: str
    content_type: str
    created_at: datetime
    chunk_count: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]


class DocumentDeleteResponse(BaseModel):
    document_id: int
    deleted: bool
    message: str
