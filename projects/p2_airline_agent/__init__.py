"""
Airline Customer Support Agent Package
======================================
Production-grade multi-modal airline support agent.
"""

from .agent import execute_agent_loop, sanitize_text
from .config import DEFAULT_MODEL, SYSTEM_PROMPT
from .database import DATABASE, get_audit_log
from .models import BoardingPassSchema
from .tools import (
    calculate_cancellation_refund,
    cancel_ticket_action,
    get_flight_details,
)
from .vision import parse_boarding_pass_vision

__all__ = [
    "DEFAULT_MODEL",
    "SYSTEM_PROMPT",
    "DATABASE",
    "get_audit_log",
    "BoardingPassSchema",
    "get_flight_details",
    "calculate_cancellation_refund",
    "cancel_ticket_action",
    "parse_boarding_pass_vision",
    "execute_agent_loop",
    "sanitize_text",
]
