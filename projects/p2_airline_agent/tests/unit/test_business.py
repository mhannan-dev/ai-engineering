# Unit tests for domain business logic and deterministic refund calculation.
"""Unit tests verifying deterministic refund calculations and 2FA guards."""

from __future__ import annotations

import pytest
from airline_agent.domain.business import (
    compute_refund,
    is_ticket_cancellable,
    verify_2fa_token,
)


def test_compute_refund_flexible_fare() -> None:
    """Test Case 1: Flexible ticket incurs 15% cancellation fee and 85% refund."""
    result = compute_refund(price_paid=850.00, fare_class="Flexible")
    assert result["cancellation_fee_pct"] == 0.15
    assert result["cancellation_fee"] == 127.50
    assert result["refund_amount"] == 722.50
    assert result["currency"] == "USD"


def test_compute_refund_non_flexible_fare() -> None:
    """Test Case 2: Non-flexible ticket incurs 50% cancellation fee and 50% refund."""
    result = compute_refund(price_paid=420.00, fare_class="Non-flexible")
    assert result["cancellation_fee_pct"] == 0.50
    assert result["cancellation_fee"] == 210.00
    assert result["refund_amount"] == 210.00


def test_compute_refund_zero_price_paid() -> None:
    """Test Case 3: Zero dollar complimentary ticket produces zero fee and refund."""
    result = compute_refund(price_paid=0.00, fare_class="Flexible")
    assert result["cancellation_fee"] == 0.00
    assert result["refund_amount"] == 0.00


def test_compute_refund_custom_fee_rules_override() -> None:
    """Test Case 4: Custom fee rule table overrides default airline percentages."""
    custom_rules = {"First Class": 0.05, "Promo": 0.90}
    result = compute_refund(price_paid=1000.00, fare_class="First Class", fee_rules=custom_rules)
    assert result["cancellation_fee_pct"] == 0.05
    assert result["cancellation_fee"] == 50.00
    assert result["refund_amount"] == 950.00


def test_verify_2fa_and_cancellable_status() -> None:
    """Test Case 5: 2FA token matching rules and status idempotency validation."""
    assert verify_2fa_token("7788", "7788") is True
    assert verify_2fa_token(" 7788 ", "7788") is True
    assert verify_2fa_token("wrong", "7788") is False
    assert verify_2fa_token("", "7788") is False
    assert verify_2fa_token("7788", "") is False

    assert is_ticket_cancellable("CONFIRMED") is True
    assert is_ticket_cancellable("confirmed") is True
    assert is_ticket_cancellable("CANCELLED") is False
    assert is_ticket_cancellable("PENDING") is False
