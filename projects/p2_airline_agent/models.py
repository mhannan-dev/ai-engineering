"""
Airline Customer Support Agent - Pydantic Data Models
=====================================================
Strict Pydantic v2 schemas for structured vision extraction, booking records,
and deterministic business outputs.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class BoardingPassSchema(BaseModel):
    """Strict schema for multi-modal boarding pass OCR extraction."""
    pnr: str = Field(..., description="6-character alphanumeric PNR / booking reference")
    passenger_name: str = Field(..., description="Full passenger name as printed on ticket")
    flight_number: str = Field(..., description="Flight code, e.g. BG-401")
    seat_number: str = Field(..., description="Seat designation, e.g. 12A")

    @field_validator("pnr")
    @classmethod
    def _clean_pnr(cls, v: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9]", "", v).upper()
        if len(cleaned) < 5:
            raise ValueError("PNR must be at least 5 alphanumeric characters")
        return cleaned


class BookingRecord(BaseModel):
    """Flight booking record structure."""
    pnr: str
    name: str
    flight_no: str
    route: str
    departure: str
    fare_class: Literal["Flexible", "Non-flexible"]
    price_paid: float
    status: Literal["CONFIRMED", "CANCELLED"]


class RefundCalculation(BaseModel):
    """Deterministic refund calculation breakdown."""
    status: str
    pnr: str
    fare_class: str
    price_paid: float
    cancellation_fee_pct: float
    cancellation_fee: float
    refund_amount: float
    currency: str = "USD"
