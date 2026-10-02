# Public API entry exports for the airline_agent package.
"""Airline Customer Support Agent package.

Clean Architecture layered implementation conforming to enterprise production standards.
"""

from .domain.models import BoardingPassSchema, BookingRecord, RefundCalculation
from .services.agent_service import execute_agent_loop, sanitize_text
from .services.tools import (
    calculate_cancellation_refund,
    cancel_ticket_action,
    get_flight_details,
)
from .services.vision_service import parse_boarding_pass_vision

__version__ = "0.2.0"

__all__ = [
    "execute_agent_loop",
    "parse_boarding_pass_vision",
    "get_flight_details",
    "calculate_cancellation_refund",
    "cancel_ticket_action",
    "sanitize_text",
    "BoardingPassSchema",
    "BookingRecord",
    "RefundCalculation",
]
