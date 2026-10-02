# Unit tests for Pydantic v2 schemas and PNR sanitization rules.
"""Unit tests verifying domain model validation."""

import pytest
from pydantic import ValidationError
from airline_agent.domain.models import BoardingPassSchema, BookingRecord


def test_boarding_pass_valid_pnr() -> None:
    """Test valid PNR formats are cleaned and upper-cased."""
    bp = BoardingPassSchema(
        pnr="abc123",
        passenger_name="Rahim Uddin",
        flight_number="BG-401",
        seat_number="12A",
    )
    assert bp.pnr == "ABC123"
    assert bp.passenger_name == "Rahim Uddin"


def test_boarding_pass_short_pnr_fails() -> None:
    """Test that PNRs shorter than 5 characters trigger ValidationError."""
    with pytest.raises(ValidationError):
        BoardingPassSchema(
            pnr="ab1",
            passenger_name="Test Passenger",
            flight_number="BG-101",
            seat_number="1A",
        )


def test_booking_record_model() -> None:
    """Test immutable BookingRecord instantiation."""
    record = BookingRecord(
        pnr="ABC123",
        name="Rahim Uddin",
        flight_no="BG-401",
        route="DAC -> LHR",
        departure="2025-03-15T22:30:00Z",
        fare_class="Flexible",
        price_paid=850.00,
        status="CONFIRMED",
        verification_token="7788",
    )
    assert record.pnr == "ABC123"
    assert record.fare_class == "Flexible"
