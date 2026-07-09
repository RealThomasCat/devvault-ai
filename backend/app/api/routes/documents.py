from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import DocumentUploadResponse
from app.services.document_service import process_uploaded_document


router = APIRouter(prefix="/documents", tags=["documents"])


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