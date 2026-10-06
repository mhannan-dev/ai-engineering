"""Database engine and session dependency."""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from knowledge_worker.config import get_settings


def make_engine(url: str) -> Engine:
    is_sqlite = url.startswith("sqlite")
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False} if is_sqlite else {},
        pool_pre_ping=not is_sqlite,
    )
    if is_sqlite:
        # SQLite ignores ON DELETE CASCADE unless foreign keys are enabled per connection
        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

    return engine


_settings = get_settings()
if _settings.DATABASE_URL.startswith("sqlite"):
    _settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
engine = make_engine(_settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

# Schema is managed by Alembic: run `uv run alembic upgrade head`


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
