# Package execution entry point for python -m airline_agent.
"""Main execution CLI dispatcher for airline_agent."""

from __future__ import annotations

import sys
from .ui.app import main

if __name__ == "__main__":
    if "streamlit" in sys.modules:
        main()
    else:
        import subprocess
        from pathlib import Path

        app_path = Path(__file__).parent / "ui" / "app.py"
        subprocess.run(["streamlit", "run", str(app_path)], check=True)
