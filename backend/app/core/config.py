from functools import lru_cache

# BaseSettings is used for config classes that read from environment variables and .env files.
# SettingsConfigDict is used to configure the behavior of the BaseSettings class.
from pydantic_settings import BaseSettings, SettingsConfigDict


# Create a Settings class that inherits from BaseSettings to define the configuration for the application.
class Settings(BaseSettings):
    app_name: str = "DevVault AI" # Default "DevVault AI" if APP_NAME is not set in the environment variables.
    app_env: str = "local"
    database_url: str # Required field, no default, must be set in the environment variables or .env file.

    # Tell Pydantic to read config from .env file and ignore any extra fields that are not defined in the Settings class.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache # Cache the results of the get_settings function to avoid reloading the settings multiple times.
def get_settings() -> Settings:
    return Settings() # pyright: ignore[reportCallIssue]