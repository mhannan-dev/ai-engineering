# Package marker for configuration layer.
"""Configuration layer for settings and prompt definitions."""

from .prompts import INJECTION_PATTERNS, SYSTEM_PROMPT
from .settings import Settings, get_settings

__all__ = ["Settings", "get_settings", "SYSTEM_PROMPT", "INJECTION_PATTERNS"]
