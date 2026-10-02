"""
Multi-Modal Airline Customer Support Agent - Application Entry Point
====================================================================
Primary entry point delegating to modularized app lifecycle.

Run:  python -m streamlit run projects/p2_airline_agent/airline_main_agent.py
      OR
      streamlit run projects/p2_airline_agent/airline_main_agent.py
"""

from __future__ import annotations

try:
    from .app import run_app
except ImportError:
    from app import run_app

if __name__ == "__main__":
    run_app()
else:
    # When executed directly via `streamlit run airline_main_agent.py`
    run_app()