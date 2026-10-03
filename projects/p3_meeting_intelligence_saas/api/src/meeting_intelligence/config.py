"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET_KEY = "dev-secret-key-change-in-production-meeting-intelligence-32char"


class Settings(BaseSettings):
    """Global configuration settings for the Meeting Intelligence API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Project metadata
    PROJECT_NAME: str = "Meeting Intelligence API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./sql_app.db"

    # File uploads (served at /uploads); defaults to api/uploads regardless of CWD
    UPLOAD_DIR: Path = Path(__file__).resolve().parents[2] / "uploads"
    AVATAR_MAX_BYTES: int = 2 * 1024 * 1024  # 2 MB
    AUDIO_MAX_BYTES: int = 50 * 1024 * 1024  # 50 MB

    # Security
    SECRET_KEY: str = DEV_SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
        ]
    )

    # Audio Transcription Providers
    # Local Faster-Whisper
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    # Cloud Deepgram
    DEEPGRAM_API_KEY: str = ""

    # LLM Synthesis (LiteLLM)
    LITELLM_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    @model_validator(mode="after")
    def _require_real_secret_outside_dev(self) -> "Settings":
        """Tokens signed with the public default key could be forged by anyone."""
        if self.ENVIRONMENT not in ("development", "testing") and self.SECRET_KEY == DEV_SECRET_KEY:
            raise ValueError(
                f"SECRET_KEY must be set (not the default) when ENVIRONMENT={self.ENVIRONMENT!r}."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
