"""
Airline Customer Support Agent - Configuration
===============================================
Central configuration for LLM orchestration, model routing, business rules,
and security policies.
"""

from __future__ import annotations

import os
import sys
from typing import Dict
from dotenv import load_dotenv
import litellm

# UTF-8 stdout configuration for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load environment variables
load_dotenv()

# LLM Provider Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
_env_model = os.getenv("LLM_MODEL", "gpt-4o")

# Global LiteLLM Routing
if OPENAI_BASE_URL:
    litellm.api_base = OPENAI_BASE_URL
if OPENAI_API_KEY:
    litellm.api_key = OPENAI_API_KEY

# Determine model with proper provider prefix
if not any(_env_model.startswith(p) for p in ["openai/", "azure/", "anthropic/", "deepseek/", "gemini/"]):
    DEFAULT_MODEL = f"openai/{_env_model}"
else:
    DEFAULT_MODEL = _env_model

VISION_MODEL = os.getenv("VISION_MODEL", "openai/gpt-4o")
MAX_AGENT_ITERATIONS = int(os.getenv("MAX_AGENT_ITERATIONS", "5"))

# Deterministic Business Rules
FARE_CLASS_FEE_PCT: Dict[str, float] = {
    "Flexible": 0.15,
    "Non-flexible": 0.50,
}

# System Persona and Behavioral Constraints
SYSTEM_PROMPT = """You are a bilingual (Bengali/English) airline customer support agent.

RULES:
1. NEVER compute refunds yourself — always call calculate_cancellation_refund.
2. NEVER cancel a ticket without a 4-digit verification token from the user.
3. Mirror the user's language (Bengali -> Bengali, English -> English).
4. Be concise. Confirm PNR before destructive actions.
5. If a tool returns NOT_FOUND, politely ask the user to re-check the PNR.
"""
