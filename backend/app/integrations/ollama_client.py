from ollama import Client

from app.core.config import get_settings


settings = get_settings()

# Initialize the Ollama client with the base URL from the settings.
ollama_client = Client(
    host=settings.ollama_base_url,
)