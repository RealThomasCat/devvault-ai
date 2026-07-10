from functools import lru_cache

# BaseSettings is used for config classes that read from environment variables and .env files.
# SettingsConfigDict is used to configure the behavior of the BaseSettings class.
from pydantic_settings import BaseSettings, SettingsConfigDict


# Create a Settings class that inherits from BaseSettings to define the configuration for the application.
class Settings(BaseSettings):
    app_name: str = "DevVault AI" # Default "DevVault AI" if APP_NAME is not set in the environment variables.
    app_env: str = "local"
    database_url: str # Required field, no default, must be set in the environment variables or .env file.

    ollama_base_url: str = "http://localhost:11434"
    ollama_embed_model: str = "embeddinggemma"

    # Tell Pydantic to read config from .env file and ignore any extra fields that are not defined in the Settings class.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache # Cache the results of the get_settings function to avoid reloading the settings multiple times.
def get_settings() -> Settings:
    """
    Load and cache application settings.

    Settings are read from environment variables and the configured `.env` file
    once per process. Subsequent calls reuse the cached instance so route
    handlers and infrastructure modules share a consistent configuration view.

    Returns:
        The validated application settings instance.
    """
    return Settings() # pyright: ignore[reportCallIssue]
