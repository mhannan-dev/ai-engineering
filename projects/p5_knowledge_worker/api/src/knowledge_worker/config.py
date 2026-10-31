"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

API_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = API_DIR.parent / "data"
DEV_SECRET_KEY = "dev-secret-key-change-in-production-knowledge-worker"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Later files win, so the shared repo-root .env comes first and api/.env overrides it.
        env_file=(API_DIR.parents[2] / ".env", API_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    PROJECT_NAME: str = "Enterprise Knowledge Worker API"
    PROJECT_DESCRIPTION: str = (
        "Hybrid-search RAG over your own English and Bangla documents: dense vectors + BM25, "
        "fused with Reciprocal Rank Fusion, reranked, and answered with page-level citations."
    )
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = f"sqlite:///{(DATA_DIR / 'knowledge_worker.db').as_posix()}"

    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # Auth (Phase 6): signed bearer tokens, ported from P3. With AUTH_ENABLED=false every request
    # acts as LOCAL_USER_ID, which is handy for local experiments and the test suite.
    AUTH_ENABLED: bool = True
    SECRET_KEY: str = DEV_SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    # Brute-force protection for POST /auth/login (failed attempts per sliding window)
    LOGIN_MAX_FAILURES: int = 5  # per client IP + email
    LOGIN_MAX_FAILURES_PER_IP: int = 20  # per client IP, across all emails
    LOGIN_WINDOW_SECONDS: int = 15 * 60
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

    # Reranking (Phase 3)
    RERANKER_MODEL: str = "jinaai/jina-reranker-v2-base-multilingual"
    RERANKER_THRESHOLD: float = 0.25
    RERANKER_CANDIDATE_LIMIT: int = 20

    # Generation (Phase 4)
    LLM_MODEL: str = "deepseek/deepseek-chat"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 1500
    # Follow-up questions are rewritten using this many recent turns (0 turns rewriting off)
    CHAT_HISTORY_TURNS: int = 3

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

    @model_validator(mode="after")
    def _require_real_secret_outside_dev(self) -> "Settings":
        env = self.ENVIRONMENT.strip().lower()
        if env not in {"development", "local", "dev", "testing"} and self.SECRET_KEY == DEV_SECRET_KEY:
            raise ValueError(f"SECRET_KEY must be set (not the default) when ENVIRONMENT={env!r}.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
