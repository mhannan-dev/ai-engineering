"""Root entrypoint: `uv run fastapi dev main.py`."""

import sys
from pathlib import Path

SRC_DIR = str(Path(__file__).resolve().parent / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from knowledge_worker.main import app, create_app  # noqa: E402

__all__ = ["app", "create_app"]
