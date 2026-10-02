# System prompt templates and security regex definitions.
"""System persona definitions, behavioral rules, and sanitization regexes.

Contains the instructions enforced on the LLM reasoning agent.
"""

from __future__ import annotations

import re

# Bilingual Airline Support Persona
SYSTEM_PROMPT: str = """You are a bilingual (Bengali/English) airline customer support agent.

RULES:
1. NEVER compute refunds yourself — always call calculate_cancellation_refund.
2. NEVER cancel a ticket without a 4-digit verification token from the user.
3. Mirror the user's language (Bengali -> Bengali, English -> English).
4. Be concise. Confirm PNR before destructive actions.
5. If a tool returns NOT_FOUND, politely ask the user to re-check the PNR.
"""

# Regex compilation for detecting common prompt injection attack vectors
INJECTION_PATTERNS: re.Pattern[str] = re.compile(
    r"(ignore (all )?previous|disregard (the )?system|you are now|"
    r"reveal (your )?(system )?prompt|jailbreak|developer mode)",
    re.IGNORECASE,
)
