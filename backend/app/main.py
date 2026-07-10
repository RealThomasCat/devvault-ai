from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes import documents
# TODO: Make route import pattern consistent? (from app.api.routes import documents, health)
from app.core.config import get_settings

# Get config values using the get_settings function.
settings = get_settings()

app = FastAPI(title=settings.app_name)

# Attach all routes from health.py to the FastAPI app with the tag "health".
app.include_router(health_router, tags=["health"])
app.include_router(documents.router)


@app.get("/")
def root() -> dict[str, str]: # This function returns a dictionary where keys are strings and values are strings.
    """
    Return the API welcome message.

    Provides a lightweight root endpoint that confirms the service is running
    and gives clients a simple human-readable entry response.

    Returns:
        A message payload identifying the DevVault AI API.
    """
    return {"message": "Welcome to DevVault AI"}
