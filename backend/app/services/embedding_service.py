from app.core.config import get_settings
from app.integrations.ollama_client import ollama_client


settings = get_settings()


def embed_text(text: str) -> list[float]:
    """
    Generate one embedding vector for the supplied text.
    """

    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError("Text cannot be empty when generating an embedding.")

    # Call the Ollama client to generate embeddings for the cleaned text using the specified model.
    response = ollama_client.embed(
        model=settings.ollama_embed_model,
        input=cleaned_text,
    )

    if not response.embeddings:
        raise RuntimeError("Ollama returned no embeddings.")

    # Ollama returns embeddings as a Sequence[float], not necessarily a Python list.
    # Convert the first (and only) embedding into a regular list of floats before returning it.
    return list(response.embeddings[0])