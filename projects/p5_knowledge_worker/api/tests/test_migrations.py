from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

API_DIR = Path(__file__).resolve().parents[1]


def test_upgrade_and_downgrade_on_fresh_sqlite(tmp_path):
    url = f"sqlite:///{(tmp_path / 'm.db').as_posix()}"
    config = Config(str(API_DIR / "alembic.ini"))
    config.attributes["database_url"] = url

    command.upgrade(config, "head")
    assert {"documents", "chunks"} <= set(inspect(create_engine(url)).get_table_names())

    command.check(config)  # models and migrations agree

    command.downgrade(config, "base")
    assert "documents" not in inspect(create_engine(url)).get_table_names()
