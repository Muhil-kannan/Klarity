"""
Application configuration using pydantic-settings.
All values are loaded from environment variables / .env file.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # App
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str
    ALLOWED_HOSTS: list[str] = ["*"]
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # GitHub App
    GITHUB_APP_ID: str
    GITHUB_APP_PRIVATE_KEY: str          # PEM key contents (multiline)
    GITHUB_WEBHOOK_SECRET: str
    GITHUB_CLIENT_ID: str = ""           # For OAuth (dashboard)
    GITHUB_CLIENT_SECRET: str = ""       # For OAuth (dashboard)

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./klarity.db"

    # Redis / ARQ
    REDIS_URL: str = "redis://localhost:6379"

    # Ollama (optional — v0.2+)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_ENABLED: bool = False

    # ChromaDB (optional — v0.2+)
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"             # "json" | "text"

    @field_validator("GITHUB_APP_PRIVATE_KEY")
    @classmethod
    def normalize_private_key(cls, v: str) -> str:
        # Allow newlines stored as \n in .env
        return v.replace("\\n", "\n")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
