# Configuration settings loaded from environment variables with strong typing.
"""Application runtime settings and environment variables management.

Loads LLM keys, base URLs, model identifiers, and execution limits.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict
from dotenv import load_dotenv

# UTF-8 stdout configuration for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure .env is parsed
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Immutable application settings container.
    
    Attributes:
        openai_api_key: Secret API key for OpenAI or DeepSeek.
        openai_base_url: Custom API endpoint (e.g. DeepSeek, vLLM).
        default_model: Primary model used for agent reasoning and tool calling.
        vision_model: Multi-modal vision model for OCR extraction.
        max_agent_iterations: Guard limit for tool reasoning loop.
        fare_class_fee_pct: Fee percentages mapped by fare tier.
    """
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_base_url: str | None = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL"))
    default_model: str = field(
        default_factory=lambda: (
            f"openai/{m}" if not any(
                (m := os.getenv("LLM_MODEL", "gpt-4o")).startswith(p)
                for p in ["openai/", "azure/", "anthropic/", "deepseek/", "gemini/"]
            ) else os.getenv("LLM_MODEL", "gpt-4o")
        )
    )
    vision_model: str = field(default_factory=lambda: os.getenv("VISION_MODEL", "openai/gpt-4o"))
    max_agent_iterations: int = field(
        default_factory=lambda: int(os.getenv("MAX_AGENT_ITERATIONS", "5"))
    )
    fare_class_fee_pct: Dict[str, float] = field(
        default_factory=lambda: {
            "Flexible": 0.15,
            "Non-flexible": 0.50,
        }
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached singleton instance of Settings."""
    return Settings()
