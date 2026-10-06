import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make the src/ package importable when running `alembic` from the api/ folder
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from knowledge_worker.config import get_settings  # noqa: E402
from knowledge_worker.db.models import Base  # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Same DATABASE_URL as the app ('%' escaped for configparser); tests may pass their own.
settings = get_settings()
_url = config.attributes.get("database_url") or settings.DATABASE_URL
if _url.startswith("sqlite"):
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
config.set_main_option("sqlalchemy.url", _url.replace("%", "%%"))

target_metadata = Base.metadata


def include_name(name, type_, parent_names):
    """Only manage this app's tables, in case the database is shared."""
    if type_ == "table":
        return name in target_metadata.tables
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        include_name=include_name,
        render_as_batch=True,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_name=include_name,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
