"""
Airline Customer Support Agent - Database & Audit Store
========================================================
In-memory mock transactional database and append-only audit trail.
Easily swappable with SQLite or PostgreSQL in production.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# Mock airline bookings database
DATABASE: Dict[str, Dict[str, Any]] = {
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
        "status": "CANCELLED",  # Already cancelled for idempotency testing
        "verification_token": "1111",
    },
}

# Immutable append-only audit log
AUDIT_LOG: List[Dict[str, Any]] = []


def record_audit(action: str, pnr: str, detail: Dict[str, Any]) -> None:
    """Record a timestamped event into the immutable audit trail."""
    AUDIT_LOG.append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "pnr": pnr,
        "detail": detail,
    })


def get_audit_log() -> List[Dict[str, Any]]:
    """Return a shallow copy of the audit log."""
    return list(AUDIT_LOG)


def get_booking(pnr: str) -> Optional[Dict[str, Any]]:
    """Retrieve raw booking record by PNR."""
    return DATABASE.get(pnr.upper().strip())


def update_booking_status(pnr: str, new_status: str) -> bool:
    """Update status of an existing booking."""
    record = DATABASE.get(pnr.upper().strip())
    if record:
        record["status"] = new_status
        return True
    return False
