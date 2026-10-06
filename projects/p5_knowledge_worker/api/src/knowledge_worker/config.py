"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

API_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = API_DIR.parent / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=API_DIR / ".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    PROJECT_NAME: str = "Enterprise Knowledge Worker API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = f"sqlite:///{(DATA_DIR / 'knowledge_worker.db').as_posix()}"

    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # Until auth lands (Phase 6) every request acts as this user. All rows and vectors already
    # carry user_id, so switching to real users only changes the dependency in api/deps.py.
    LOCAL_USER_ID: str = "local"

    # Storage
    DATA_DIR: Path = DATA_DIR
    UPLOAD_MAX_BYTES: int = 25 * 1024 * 1024  # 25 MB

    # Dense retrieval
    QDRANT_URL: str = ""  # empty = embedded Qdrant stored under DATA_DIR/qdrant
    QDRANT_COLLECTION: str = "chunks_e5_large"
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"
    EMBEDDING_DIM: int = 1024
    EMBEDDING_QUERY_PREFIX: str = "query: "
    EMBEDDING_PASSAGE_PREFIX: str = "passage: "

    # Chunking (e5 accepts 512 tokens; leave room for the prefix and heading)
    CHUNK_MAX_TOKENS: int = 400
    CHUNK_OVERLAP_TOKENS: int = 60

    @property
    def upload_dir(self) -> Path:
        return self.DATA_DIR / "uploads"

    @property
    def qdrant_path(self) -> Path:
        return self.DATA_DIR / "qdrant"

    @property
    def bm25_dir(self) -> Path:
        return self.DATA_DIR / "bm25"

    @property
    def model_cache_dir(self) -> Path:
        return self.DATA_DIR / "models"

    @property
    def is_local(self) -> bool:
        """Return True if running in local or development environment."""
        return self.ENVIRONMENT.strip().lower() in {"development", "local", "dev"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
