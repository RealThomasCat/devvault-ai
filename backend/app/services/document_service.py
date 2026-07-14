from datetime import datetime
from pathlib import Path
from typing import TypedDict, cast

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.document import Document
from app.db.models.document_chunk import DocumentChunk
from app.services.chunking_service import split_text_into_chunks
from app.services.embedding_service import embed_text


ALLOWED_EXTENSIONS = {".md", ".txt"}


class DocumentSummaryData(TypedDict):
    document_id: int
    filename: str
    content_type: str
    created_at: datetime
    chunk_count: int


# Helper function to convert a Document instance and its chunk count into a dictionary suitable for API responses.
def _document_summary(document: Document, chunk_count: int) -> DocumentSummaryData:
    """
    Convert a document row plus its chunk count into an API-ready dictionary.
    """
    return {
        "document_id": document.id,
        "filename": document.filename,
        "content_type": document.content_type,
        "created_at": document.created_at,
        "chunk_count": chunk_count,
    }


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
    Validate, read, chunk, embed, and persist an uploaded text document.

    The uploaded file must be Markdown or TXT containing valid UTF-8 text.
    Each generated chunk is embedded using Ollama and stored together with
    its 768-dimensional embedding.

    Args:
        file: Uploaded document received from the API request.
        db: Active SQLAlchemy session used to persist the document and chunks.

    Returns:
        A dictionary containing the saved document ID, filename, and number
        of chunks created.

    Raises:
        HTTPException: If validation, decoding, chunking, embedding generation,
        or database persistence fails.
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

        # Create a list to hold DocumentChunk instances for each chunk of text.
        chunk_rows: list[DocumentChunk] = []

        # Loop through each chunk of text, generate its embedding, and create a DocumentChunk instance for it.
        for index, chunk in enumerate(chunks):
            embedding = embed_text(chunk)

            chunk_row = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=chunk,
                embedding=embedding,
            )

            chunk_rows.append(chunk_row)

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

    # Handle any other exceptions that may occur during the embedding generation or other operations.
    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to generate document embeddings.",
        ) from exc


def list_documents(db: Session) -> list[DocumentSummaryData]:
    """
    Return all uploaded documents with their chunk counts.
    """
    rows = (
        db.query(Document, func.count(DocumentChunk.id).label("chunk_count"))
        .outerjoin(DocumentChunk, DocumentChunk.document_id == Document.id)
        .group_by(Document.id)
        .order_by(Document.created_at.desc(), Document.id.desc())
        .all()
    )

    return [
        _document_summary(document=document, chunk_count=cast(int, chunk_count))
        for document, chunk_count in rows
    ]


def get_document_by_id(document_id: int, db: Session) -> DocumentSummaryData:
    """
    Return one uploaded document with its chunk count.
    """
    row = (
        db.query(Document, func.count(DocumentChunk.id).label("chunk_count"))
        .outerjoin(DocumentChunk, DocumentChunk.document_id == Document.id)
        .filter(Document.id == document_id)
        .group_by(Document.id)
        .first()
    )

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} was not found.",
        )

    document, chunk_count = row
    return _document_summary(document=document, chunk_count=cast(int, chunk_count))


def delete_document_by_id(document_id: int, db: Session) -> dict:
    """
    Delete one uploaded document and its chunks.
    """
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} was not found.",
        )

    try:
        db.delete(document)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document.",
        ) from exc

    return {
        "document_id": document_id,
        "deleted": True,
        "message": f"Document {document_id} and its chunks were deleted.",
    }
