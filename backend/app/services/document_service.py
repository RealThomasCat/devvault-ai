from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.document import Document
from app.db.models.document_chunk import DocumentChunk
from app.services.chunking_service import split_text_into_chunks


ALLOWED_EXTENSIONS = {".md", ".txt"}


def validate_file_extension(filename: str | None) -> str:
    """
    Validate uploaded file extension.

    Returns the normalized extension if valid.
    Raises HTTPException if invalid.
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .md and .txt files are supported.",
        )

    return extension


def get_content_type_from_extension(extension: str) -> str:
    """
    Convert file extension into a simple content type value for our DB.

    We are not depending on the browser-provided MIME type because it can be
    missing or inconsistent across clients.
    """
    if extension == ".md":
        return "text/markdown"

    if extension == ".txt":
        return "text/plain"

    return "text/plain"


async def read_uploaded_file_as_text(file: UploadFile) -> str:
    """
    Read uploaded file bytes and decode them as UTF-8 text.
    """
    file_bytes = await file.read()

    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be valid UTF-8 text.",
        ) from exc

    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    return text


async def process_uploaded_document(file: UploadFile, db: Session) -> dict:
    """
    Validate, parse, chunk, and persist an uploaded text document.

    The uploaded file must be a supported plain-text document type. The file is
    read as UTF-8 text, normalized through the chunking pipeline, and stored as
    one document record with one or more associated chunk records.

    Args:
        file: Uploaded document received from the API request.
        db: Active SQLAlchemy session used to persist the document and chunks.

    Returns:
        A dictionary containing the saved document ID, original filename, and
        number of chunks created.

    Raises:
        HTTPException: If the file extension is unsupported, the file cannot be
        decoded as UTF-8, the file is empty, no chunks are produced, or database
        persistence fails.
    """
    extension = validate_file_extension(file.filename)
    content_type = get_content_type_from_extension(extension)

    text = await read_uploaded_file_as_text(file)
    chunks = split_text_into_chunks(text)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file did not produce any chunks.",
        )

    try:
        # Create a new Document instance with the uploaded file's metadata and add it to the database session.
        document = Document(
            filename=file.filename,
            content_type=content_type,
            source_type="upload",
        )

        # Add the document to the database session. This prepares it for insertion into the database.
        db.add(document)

        # flush sends the INSERT to the database without committing the transaction.
        # This gives us document.id so chunk rows can reference it.
        db.flush()

        # Create DocumentChunk instances for each chunk of text and add them to the database session.
        chunk_rows = [
            DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=chunk,
            )
            for index, chunk in enumerate(chunks)
        ]

        db.add_all(chunk_rows) # Add all chunk rows to the database session in one go.
        db.commit() # Commit the transaction to save the document and its chunks to the database.
        db.refresh(document) # Refresh the document instance to get the latest state from the database, including any auto-generated fields like id.

        # Return a dictionary containing the document ID, filename, and the number of chunks created.
        return {
            "document_id": document.id,
            "filename": document.filename,
            "chunk_count": len(chunk_rows),
        }

    # Handle any SQLAlchemy errors that occur during the database operations.
    # If an error occurs, roll back the transaction and raise an HTTPException with a 500 status code.
    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded document.",
        ) from exc