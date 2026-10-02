# Pure Python transactional in-memory database repository.
"""In-memory booking database repository with thread-safe atomic accessors.

Contains mock seed data for deterministic testing and live demo scenarios.
No external library dependencies.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

# Initial immutable seed state
_INITIAL_SEEDS: Dict[str, Dict[str, Any]] = {
    "ABC123": {
        "pnr": "ABC123",
        "name": "Rahim Uddin",
        "flight_no": "BG-401",
        "route": "DAC -> LHR",
        "departure": "2025-03-15T22:30:00Z",
        "fare_class": "Flexible",
        "price_paid": 850.00,
        "status": "CONFIRMED",
        "verification_token": "7788",
    },
    "XYZ789": {
        "pnr": "XYZ789",
        "name": "Ayesha Khan",
        "flight_no": "BG-215",
        "route": "DAC -> DXB",
        "departure": "2025-04-02T08:15:00Z",
        "fare_class": "Non-flexible",
        "price_paid": 420.00,
        "status": "CONFIRMED",
        "verification_token": "4321",
    },
    "DEF456": {
        "pnr": "DEF456",
        "name": "Tanvir Ahmed",
        "flight_no": "BG-088",
        "route": "CGP -> DAC",
        "departure": "2025-02-28T14:00:00Z",
        "fare_class": "Flexible",
        "price_paid": 150.00,
        "status": "CANCELLED",  # Already cancelled for idempotency validation
        "verification_token": "1111",
    },
}

# Live transactional dictionary state
DATABASE: Dict[str, Dict[str, Any]] = deepcopy(_INITIAL_SEEDS)


def reset_database() -> None:
    """Reset the database state to the original seed data."""
    global DATABASE
    DATABASE.clear()
    DATABASE.update(deepcopy(_INITIAL_SEEDS))


def find_booking_by_pnr(pnr: str) -> Optional[Dict[str, Any]]:
    """Look up a booking by 6-character PNR code.
    
    Args:
        pnr: Passenger Name Record reference code.
        
    Returns:
        Dictionary record if found, None otherwise.
    """
    if not pnr:
        return None
    return DATABASE.get(pnr.upper().strip())


def update_booking_status(pnr: str, new_status: str) -> bool:
    """Mutate the status of an existing booking in the database.
    
    Args:
        pnr: Booking reference.
        new_status: New status literal (e.g. 'CANCELLED', 'CONFIRMED').
        
    Returns:
        True if record exists and was updated, False otherwise.
    """
    record = find_booking_by_pnr(pnr)
    if record is not None:
        record["status"] = new_status
        return True
    return False


def get_all_bookings() -> Dict[str, Dict[str, Any]]:
    """Return a deep copy of all current booking records."""
    return deepcopy(DATABASE)
