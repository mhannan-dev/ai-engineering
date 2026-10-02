# Package marker for core domain layer.
"""Domain layer containing pure enterprise business logic and models.

Strictly independent of all infrastructure, UI, and third-party dependencies (except Pydantic).
"""

from .business import compute_refund, is_ticket_cancellable, verify_2fa_token
from .database import (
    DATABASE,
    find_booking_by_pnr,
    get_all_bookings,
    reset_database,
    update_booking_status,
)
from .models import (
    BoardingPassSchema,
    BookingRecord,
    CancellationOutcome,
    RefundCalculation,
)

__all__ = [
    "BoardingPassSchema",
    "BookingRecord",
    "RefundCalculation",
    "CancellationOutcome",
    "DATABASE",
    "find_booking_by_pnr",
    "update_booking_status",
    "get_all_bookings",
    "reset_database",
    "compute_refund",
    "verify_2fa_token",
    "is_ticket_cancellable",
]
