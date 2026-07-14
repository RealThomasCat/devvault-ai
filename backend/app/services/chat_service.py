from urllib import response

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.ollama_client import ollama_client
from app.schemas.chat import ChatCitation, ChatResponse
from app.schemas.search import SearchResult
from app.services.retrieval_service import search_document_chunks


settings = get_settings()


# Number of document chunks retrieved for each chat question.
CHAT_TOP_K = 5

# Maximum number of characters to include in the snippet for each citation.
CITATION_SNIPPET_LENGTH = 300


# Fixed fallback message used when retrieved context cannot answer the question.
NO_CONTEXT_ANSWER = (
    "The uploaded documents do not contain enough information "
    "to answer this question."
)


# Prompt for the chat model to follow when answering questions using the retrieved document context.
SYSTEM_PROMPT = """
You answer questions using only the supplied document context.

Your primary task is to identify relevant information in the context and
answer the user's question.

Rules:
1. Use only facts explicitly stated in the context.
2. You may combine explicit facts from multiple sources.
3. Do not add likely benefits, explanations, or technical assumptions unless
   they are directly stated in the context.
4. Do not mention source numbers, chunk IDs, document IDs, or filenames.
5. Only conclude that there is insufficient information when none of the
   supplied context is relevant to the question.
6. Give a direct and concise answer.
""".strip()


# Function to build the context from retrieved document chunks.
def build_context(results: list[SearchResult]) -> str:
    """
    Convert retrieved document chunks into labeled text context.

    Each chunk is given source metadata so the chat model can distinguish
    between the retrieved documents and chunks.
    """

    # List to hold the labeled context sections for each retrieved chunk.
    context_sections: list[str] = []

    # Add each retrieved chunk to the context sections with its source metadata.
    for source_number, result in enumerate(results, start=1):
        section = (
            f"[Source {source_number}]\n"
            f"Filename: {result.filename}\n"
            f"Document ID: {result.document_id}\n"
            f"Chunk ID: {result.chunk_id}\n"
            f"Content:\n{result.content}"
        )

        context_sections.append(section)

    # Join all context sections into a single string with double newlines between sections.
    return "\n\n".join(context_sections)


# Function to generate an answer using the configured Ollama chat model.
def generate_answer(
    question: str,
    context: str,
) -> str:
    """
    Generate an answer using the configured Ollama chat model.

    The system message defines grounding rules. The user message contains
    the retrieved document context and the user's question.
    """

    user_prompt = (
        f"Document context:\n"
        f"{context}\n\n"
        f"Question:\n"
        f"{question}"
    )

    response = ollama_client.chat(
        model=settings.ollama_chat_model,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    answer = response.message.content

    if answer is None:
        raise RuntimeError("Ollama returned no chat response content.")

    cleaned_answer = answer.strip()

    if not cleaned_answer:
        raise RuntimeError("Ollama returned an empty chat response.")

    return cleaned_answer


# Function to create a shortened citation snippet from full chunk content.
def create_snippet(
    content: str,
    max_length: int = CITATION_SNIPPET_LENGTH,
) -> str:
    """
    Create a shortened citation snippet from full chunk content.
    """

    cleaned_content = content.strip()

    if len(cleaned_content) <= max_length:
        return cleaned_content

    return cleaned_content[:max_length].rstrip() + "..."


# Function to build a list of ChatCitation objects from retrieved SearchResult objects.
def build_citations(results: list[SearchResult]) -> list[ChatCitation]:
    """
    Convert retrieved search results into user-facing citation objects.
    """

    # Create and return a list of ChatCitation objects, each containing metadata and a snippet for the corresponding SearchResult.
    return [
        ChatCitation(
            chunk_id=result.chunk_id,
            document_id=result.document_id,
            filename=result.filename,
            snippet=create_snippet(result.content),
        )
        for result in results
    ]



# Function to answer a question using the RAG flow.
def answer_question(
    question: str,
    db: Session,
) -> tuple[str, list[SearchResult]]:
    """
    Run the basic RAG question-answering flow.

    Flow:
    - retrieve relevant chunks
    - return fallback when no chunks exist
    - build context from retrieved chunks
    - generate a grounded answer through Ollama
    - return the answer and the original retrieved sources
    """

    # Retrieve relevant document chunks from the database using the question using retrieval_service.
    results = search_document_chunks(
        query=question,
        top_k=CHAT_TOP_K,
        db=db,
    )

    if not results:
        return NO_CONTEXT_ANSWER, []

    # Build the context from the retrieved document chunks to provide to the chat model.
    context = build_context(results)

    # Generate an answer using the chat model with the provided question and context.
    answer = generate_answer(
        question=question,
        context=context,
    )

    # Return the generated answer and the original retrieved document chunks for reference.
    return answer, results


# Function to create a complete ChatResponse object from a question and database session.
def create_chat_response(
    question: str,
    db: Session,
) -> ChatResponse:
    """
    Run the RAG flow and convert the result into the API response model.
    """

    # Run the RAG flow to get the answer and the retrieved document chunks.
    answer, results = answer_question(
        question=question,
        db=db,
    )

    if answer == NO_CONTEXT_ANSWER:
        return ChatResponse(
            answer=answer,
            citations=[],
        )

    # Build the list of citations from the retrieved document chunks.
    citations = build_citations(results)

    # Return the complete ChatResponse object containing the answer and the citations.
    return ChatResponse(
        answer=answer,
        citations=citations,
    )