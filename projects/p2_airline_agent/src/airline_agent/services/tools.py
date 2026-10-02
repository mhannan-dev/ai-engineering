# Standalone deterministic tools, tool schemas, and tool registry.
"""Airline business tools callable by LLM tool calling engines.

Implements flight lookup, deterministic refund math, and 2FA-gated cancellations.
Coordinates domain entities and infrastructure audit loggers.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

from ..config.settings import get_settings
from ..domain.business import compute_refund, is_ticket_cancellable, verify_2fa_token
from ..domain.database import find_booking_by_pnr, update_booking_status
from ..infra.audit_log import AuditLoggerProtocol, get_default_audit_logger


def get_flight_details(
    pnr: str,
    logger: AuditLoggerProtocol | None = None,
) -> Dict[str, Any]:
    """Retrieve non-sensitive flight booking details for a given PNR.
    
    Ensures security compliance by redacting verification tokens before returning.
    
    Args:
        pnr: 6-character booking reference.
        logger: Optional audit logger protocol instance.
        
    Returns:
        Dictionary containing booking status and sanitized record.
    """
    audit = logger or get_default_audit_logger()
    clean_pnr = pnr.upper().strip() if pnr else ""
    record = find_booking_by_pnr(clean_pnr)

    if not record:
        audit.log_event("LOOKUP_FAILED", clean_pnr, {"reason": "NOT_FOUND"})
        return {"status": "NOT_FOUND", "pnr": clean_pnr}

    # Redact customer secret verification token
    safe_booking = {k: v for k, v in record.items() if k != "verification_token"}
    audit.log_event("LOOKUP_SUCCESS", clean_pnr, {"flight_no": safe_booking.get("flight_no")})

    return {"status": "OK", "booking": safe_booking}


def calculate_cancellation_refund(
    pnr: str,
    logger: AuditLoggerProtocol | None = None,
) -> Dict[str, Any]:
    """Deterministically compute exact refund amount and cancellation fee.
    
    Zero LLM arithmetic — uses domain compute_refund logic.
    
    Args:
        pnr: 6-character booking reference.
        logger: Optional audit logger protocol instance.
        
    Returns:
        Dictionary detailing refund amounts, fees, and currency.
    """
    audit = logger or get_default_audit_logger()
    clean_pnr = pnr.upper().strip() if pnr else ""
    record = find_booking_by_pnr(clean_pnr)

    if not record:
        audit.log_event("REFUND_CALC_FAILED", clean_pnr, {"reason": "NOT_FOUND"})
        return {"status": "NOT_FOUND", "pnr": clean_pnr}

    if not is_ticket_cancellable(record["status"]):
        audit.log_event("REFUND_CALC_SKIPPED", clean_pnr, {"reason": "ALREADY_CANCELLED"})
        return {
            "status": "ALREADY_CANCELLED",
            "pnr": clean_pnr,
            "message": "This ticket was already cancelled. No refund can be computed.",
        }

    settings = get_settings()
    math_result = compute_refund(
        price_paid=float(record["price_paid"]),
        fare_class=str(record["fare_class"]),
        fee_rules=settings.fare_class_fee_pct,
    )

    payload = {
        "status": "OK",
        "pnr": clean_pnr,
        "fare_class": record["fare_class"],
        "price_paid": record["price_paid"],
        **math_result,
    }
    audit.log_event("REFUND_CALCULATED", clean_pnr, payload)
    return payload


def cancel_ticket_action(
    pnr: str,
    verification_token: str,
    logger: AuditLoggerProtocol | None = None,
) -> Dict[str, Any]:
    """Execute destructive ticket cancellation under 2FA and idempotency guards.
    
    Args:
        pnr: 6-character booking reference.
        verification_token: Customer authorization token.
        logger: Optional audit logger protocol instance.
        
    Returns:
        Dictionary indicating success or refusal status with refund summary.
    """
    audit = logger or get_default_audit_logger()
    clean_pnr = pnr.upper().strip() if pnr else ""
    record = find_booking_by_pnr(clean_pnr)

    if not record:
        audit.log_event("CANCEL_DENIED_NOT_FOUND", clean_pnr, {})
        return {"status": "NOT_FOUND", "pnr": clean_pnr}

    # 1. Idempotency Guard
    if not is_ticket_cancellable(record["status"]):
        audit.log_event("CANCEL_SKIPPED_IDEMPOTENT", clean_pnr, {})
        return {
            "status": "ALREADY_CANCELLED",
            "message": "This ticket was already cancelled. No duplicate refund issued.",
        }

    # 2. 2FA Token Verification Gate
    if not verify_2fa_token(verification_token, str(record.get("verification_token", ""))):
        audit.log_event("CANCEL_DENIED_2FA", clean_pnr, {"supplied_token": "***"})
        return {
            "status": "VERIFICATION_FAILED",
            "message": "Verification token mismatch. Cancellation denied.",
        }

    # 3. Apply state mutation and log success
    refund_info = calculate_cancellation_refund(clean_pnr, logger=audit)
    update_booking_status(clean_pnr, "CANCELLED")
    audit.log_event("CANCEL_SUCCESS", clean_pnr, refund_info)

    return {
        "status": "CANCELLED",
        "pnr": clean_pnr,
        "refund": refund_info,
        "message": (
            f"Ticket {clean_pnr} cancelled. Refund of "
            f"${refund_info.get('refund_amount', 0.0)} will process in 5-7 business days."
        ),
    }


# Tool calling function schemas conforming to OpenAI / LiteLLM standard
TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_flight_details",
            "description": "Fetch flight/booking details for a PNR.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string", "description": "6-character booking reference"}
                },
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
                "properties": {
                    "pnr": {"type": "string", "description": "6-character booking reference"}
                },
                "required": ["pnr"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_ticket_action",
            "description": (
                "Cancel a ticket. REQUIRES a 4-digit verification token from passenger. "
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
    """Safely execute registered tools from raw LLM arguments JSON string.
    
    Args:
        name: Name of tool function matching registry.
        args_json: Raw JSON string emitted by LLM tool caller.
        
    Returns:
        Structured result dictionary.
    """
    fn = TOOL_REGISTRY.get(name)
    if not fn:
        return {"status": "UNKNOWN_TOOL", "name": name}
    try:
        args = json.loads(args_json) if args_json else {}
    except json.JSONDecodeError:
        return {"status": "BAD_ARGS", "raw": args_json}
    try:
        return fn(**args)
    except TypeError as exc:
        return {"status": "ARG_ERROR", "error": str(exc)}
    except Exception as exc:
        return {"status": "TOOL_EXCEPTION", "error": str(exc)}
