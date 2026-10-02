# Pure domain models and Pydantic v2 schemas.
"""Domain models and value objects for airline ticketing.

Defines PNR extraction schema, booking records, and refund structures.
Strictly free of third-party dependencies except Pydantic.
"""

from __future__ import annotations

import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BoardingPassSchema(BaseModel):
    """Strict schema for multi-modal boarding pass OCR extraction.
    
    Attributes:
        pnr: 5 to 6 alphanumeric booking reference.
        passenger_name: Full passenger name printed on boarding pass.
        flight_number: Airline flight code (e.g. BG-401).
        seat_number: Assigned seat number (e.g. 12A).
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    pnr: str = Field(..., description="6-character alphanumeric booking reference")
    passenger_name: str = Field(..., description="Full passenger name as printed on ticket")
    flight_number: str = Field(..., description="Flight code, e.g. BG-401")
    seat_number: str = Field(..., description="Seat designation, e.g. 12A")

    @field_validator("pnr")
    @classmethod
    def validate_and_clean_pnr(cls, value: str) -> str:
        """Sanitize and validate booking reference format."""
        cleaned = re.sub(r"[^A-Za-z0-9]", "", value).upper()
        if len(cleaned) < 5:
            raise ValueError("PNR must be at least 5 alphanumeric characters")
        return cleaned


class BookingRecord(BaseModel):
    """In-memory domain representation of an airline passenger booking."""
    model_config = ConfigDict(frozen=True)

    pnr: str
    name: str
    flight_no: str
    route: str
    departure: str
    fare_class: Literal["Flexible", "Non-flexible"]
    price_paid: float
    status: Literal["CONFIRMED", "CANCELLED"]
    verification_token: str


class RefundCalculation(BaseModel):
    """Immutable domain representation of a refund calculation."""
    model_config = ConfigDict(frozen=True)

    status: str
    pnr: str
    fare_class: str
    price_paid: float
    cancellation_fee_pct: float
    cancellation_fee: float
    refund_amount: float
    currency: str = "USD"


class CancellationOutcome(BaseModel):
    """Immutable result structure for ticket cancellation operations."""
    model_config = ConfigDict(frozen=True)

    status: str
    pnr: str
    message: str
    refund: RefundCalculation | None = None
