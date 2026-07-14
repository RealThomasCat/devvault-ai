from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentSummary,
    DocumentUploadResponse,
)
from app.services.document_service import (
    delete_document_by_id,
    get_document_by_id,
    list_documents,
    process_uploaded_document,
)


router = APIRouter(prefix="/documents", tags=["documents"])


# List Documents Endpoint
@router.get("", response_model=DocumentListResponse)
def get_documents(
    db: Annotated[Session, Depends(get_db)],
) -> DocumentListResponse:
    """
    List uploaded documents with their metadata and chunk counts.
    """
    documents = [
        DocumentSummary(**document)
        for document in list_documents(db=db)
    ]

    return DocumentListResponse(documents=documents)


# Get Document by ID Endpoint
@router.get("/{document_id}", response_model=DocumentSummary)
def get_document(
    document_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> DocumentSummary:
    """
    Return one uploaded document by ID.
    """
    document = get_document_by_id(document_id=document_id, db=db)

    return DocumentSummary(**document)


# Delete Document Endpoint
@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
def delete_document(
    document_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> DocumentDeleteResponse:
    """
    Delete one uploaded document and its chunks.
    """
    result = delete_document_by_id(document_id=document_id, db=db)

    return DocumentDeleteResponse(**result)


# Upload Document Endpoint
@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    # "file" is expected to be an uploaded file.
    # UploadFile tells Python/FastAPI the value is a file upload object.
    # File(...) tells FastAPI to read it from multipart form-data and make it required.
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentUploadResponse:
    """
    Upload a supported text document and persist its extracted chunks.

    Accepts a multipart file upload, delegates validation and persistence to the
    document service, and returns metadata for the saved document. Only Markdown
    and plain text uploads are supported.

    Args:
        file: Required uploaded file from multipart form data.
        db: Request-scoped SQLAlchemy session provided by dependency injection.

    Returns:
        Metadata for the saved document, including its ID, filename, and chunk
        count.
    """
    result = await process_uploaded_document(file=file, db=db)

    # Return a DocumentUploadResponse object with the result data (** unpacks the dictionary into keyword arguments).
    return DocumentUploadResponse(**result)
