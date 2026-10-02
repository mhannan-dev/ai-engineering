"""
Airline Customer Support Agent - Deterministic Business Tools
=============================================================
Zero-LLM math arithmetic, 2FA gating, and idempotency protection.
All functions are standalone and 100% testable via pytest.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

from .config import FARE_CLASS_FEE_PCT
from .database import get_booking, record_audit, update_booking_status


def get_flight_details(pnr: str) -> Dict[str, Any]:
    """Return non-sensitive flight details for a PNR.
    Guarantees that verification_token is never leaked to the LLM.
    """
    record = get_booking(pnr)
    if not record:
        return {"status": "NOT_FOUND", "pnr": pnr}

    # Safe projection excluding internal verification secret
    safe_booking = {k: v for k, v in record.items() if k != "verification_token"}
    record_audit("VIEW_FLIGHT_DETAILS", pnr.upper().strip(), {"flight_no": safe_booking.get("flight_no")})
    return {"status": "OK", "booking": safe_booking}


def calculate_cancellation_refund(pnr: str) -> Dict[str, Any]:
    """Deterministic refund calculation engine.
    Ensures that the LLM NEVER performs financial percentage deductions.
    """
    record = get_booking(pnr)
    if not record:
        return {"status": "NOT_FOUND", "pnr": pnr}
    if record["status"] == "CANCELLED":
        return {
            "status": "ALREADY_CANCELLED",
            "pnr": pnr,
            "message": "This ticket was already cancelled. No refund can be computed.",
        }

    fare = record["fare_class"]
    price = record["price_paid"]
    fee_pct = FARE_CLASS_FEE_PCT.get(fare, 0.50)
    fee = round(price * fee_pct, 2)
    refund = round(price - fee, 2)

    result = {
        "status": "OK",
        "pnr": record["pnr"],
        "fare_class": fare,
        "price_paid": price,
        "cancellation_fee_pct": fee_pct,
        "cancellation_fee": fee,
        "refund_amount": refund,
        "currency": "USD",
    }
    record_audit("CALCULATE_REFUND", record["pnr"], result)
    return result


def cancel_ticket_action(pnr: str, verification_token: str) -> Dict[str, Any]:
    """Destructive ticket cancellation action.
    Strictly protected by:
      1. 2FA verification token matching.
      2. Idempotency guard (prevents duplicate refund on re-attempts).
    """
    clean_pnr = pnr.upper().strip()
    record = get_booking(clean_pnr)
    if not record:
        return {"status": "NOT_FOUND", "pnr": clean_pnr}

    # 1. Idempotency guard
    if record["status"] == "CANCELLED":
        record_audit("CANCEL_SKIPPED_IDEMPOTENT", clean_pnr, {})
        return {
            "status": "ALREADY_CANCELLED",
            "message": "This ticket was already cancelled. No duplicate refund issued.",
        }

    # 2. 2FA token gate
    if str(verification_token).strip() != record.get("verification_token"):
        record_audit("CANCEL_DENIED_2FA", clean_pnr, {"supplied_token": "***"})
        return {
            "status": "VERIFICATION_FAILED",
            "message": "Verification token mismatch. Cancellation denied.",
        }

    # 3. Compute final deterministic refund and mutate status
    refund_info = calculate_cancellation_refund(clean_pnr)
    update_booking_status(clean_pnr, "CANCELLED")
    record_audit("CANCEL_SUCCESS", clean_pnr, refund_info)

    return {
        "status": "CANCELLED",
        "pnr": clean_pnr,
        "refund": refund_info,
        "message": f"Ticket {clean_pnr} cancelled. Refund of ${refund_info['refund_amount']} will process in 5-7 business days.",
    }


# ============================================================================
# AGENT TOOL SCHEMAS & REGISTRY
# ============================================================================

TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_flight_details",
            "description": "Fetch flight/booking details for a PNR.",
            "parameters": {
                "type": "object",
                "properties": {"pnr": {"type": "string", "description": "6-character booking reference"}},
                "required": ["pnr"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_cancellation_refund",
            "description": "Compute exact refund and fee for cancelling a PNR.",
            "parameters": {
                "type": "object",
                "properties": {"pnr": {"type": "string", "description": "6-character booking reference"}},
                "required": ["pnr"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_ticket_action",
            "description": (
                "Cancel a ticket. REQUIRES a 4-digit verification token from the passenger. "
                "Only call after user explicitly provides the token."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string", "description": "6-character booking reference"},
                    "verification_token": {"type": "string", "description": "4-digit verification code"},
                },
                "required": ["pnr", "verification_token"],
            },
        },
    },
]

TOOL_REGISTRY: Dict[str, Callable[..., Dict[str, Any]]] = {
    "get_flight_details": get_flight_details,
    "calculate_cancellation_refund": calculate_cancellation_refund,
    "cancel_ticket_action": cancel_ticket_action,
}


def dispatch_tool(name: str, args_json: str) -> Dict[str, Any]:
    """Safely dispatch tool invocations with JSON error handling."""
    fn = TOOL_REGISTRY.get(name)
    if not fn:
        return {"status": "UNKNOWN_TOOL", "name": name}
    try:
        args = json.loads(args_json) if args_json else {}
    except json.JSONDecodeError:
        return {"status": "BAD_ARGS", "raw": args_json}
    try:
        return fn(**args)
    except TypeError as e:
        return {"status": "ARG_ERROR", "error": str(e)}
    except Exception as e:
        return {"status": "TOOL_EXCEPTION", "error": str(e)}
