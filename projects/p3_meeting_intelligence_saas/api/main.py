"""Root application entrypoint delegating to layered package factory."""

import sys
from pathlib import Path

# Ensure src/ is always discoverable in sys.path
SRC_DIR = str(Path(__file__).resolve().parent / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from meeting_intelligence.main import app, create_app  # noqa: E402

__all__ = ["app", "create_app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
