"""Alembic migrations must build the schema from scratch and match the ORM models."""

from pathlib import Path

from alembic import command
from alembic.config import Config

API_DIR = Path(__file__).resolve().parents[1]


def _config(tmp_path: Path) -> Config:
    cfg = Config(str(API_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_DIR / "migrations"))
    cfg.attributes["database_url"] = f"sqlite:///{(tmp_path / 'migrations.db').as_posix()}"
    return cfg


def test_upgrade_head_matches_models(tmp_path):
    cfg = _config(tmp_path)
    command.upgrade(cfg, "head")
    command.check(cfg)  # raises if models have changes with no migration


def test_downgrade_to_base_and_back(tmp_path):
    cfg = _config(tmp_path)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
