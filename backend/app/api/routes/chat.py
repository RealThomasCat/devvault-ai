from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import create_chat_response


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ChatResponse:
    """
    Answer a question using retrieved document chunks and return citations.
    """

    return create_chat_response(
        question=request.question,
        db=db,
    )