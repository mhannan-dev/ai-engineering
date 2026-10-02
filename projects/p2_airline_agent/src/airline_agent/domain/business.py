# Pure domain business rules and deterministic arithmetic.
"""Deterministic business logic for airline ticketing.

Handles fee calculations, 2FA verification rules, and idempotency status checks.
No external dependencies.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

# Default fee percentages according to airline policy
DEFAULT_FARE_RULES: Dict[str, float] = {
    "Flexible": 0.15,
    "Non-flexible": 0.50,
}


def compute_refund(
    price_paid: float,
    fare_class: str,
    fee_rules: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Deterministically compute cancellation fee and refundable balance.
    
    Zero LLM arithmetic — calculated via exact floating-point rounding.
    
    Args:
        price_paid: Gross ticket purchase price.
        fare_class: Ticket fare category ('Flexible' or 'Non-flexible').
        fee_rules: Optional fee mapping table; falls back to DEFAULT_FARE_RULES.
        
    Returns:
        Dictionary containing fee percentage, fee amount, and refund amount.
    """
    rules = fee_rules if fee_rules is not None else DEFAULT_FARE_RULES
    fee_pct = rules.get(fare_class, 0.50)
    cancellation_fee = round(price_paid * fee_pct, 2)
    refund_amount = round(max(0.0, price_paid - cancellation_fee), 2)

    return {
        "cancellation_fee_pct": fee_pct,
        "cancellation_fee": cancellation_fee,
        "refund_amount": refund_amount,
        "currency": "USD",
    }


def verify_2fa_token(provided_token: str, expected_token: str) -> bool:
    """Validate customer-supplied 2FA authorization token against stored secret.
    
    Args:
        provided_token: Token string supplied by the user.
        expected_token: Secret token registered on the booking record.
        
    Returns:
        True if tokens match exactly (trimmed), False otherwise.
    """
    if not provided_token or not expected_token:
        return False
    return str(provided_token).strip() == str(expected_token).strip()


def is_ticket_cancellable(current_status: str) -> bool:
    """Check if the ticket is currently in a cancellable state.
    
    Args:
        current_status: Current booking status ('CONFIRMED', 'CANCELLED', etc.)
        
    Returns:
        True if status is CONFIRMED, False if already CANCELLED or invalid.
    """
    return current_status.upper().strip() == "CONFIRMED"
