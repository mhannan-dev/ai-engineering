# Unit tests for service layer business tools and audit logging.
"""Unit tests verifying tool execution, 2FA gating, and audit trail."""

from airline_agent.domain.database import reset_database
from airline_agent.infra.audit_log import InMemoryAuditLogger
from airline_agent.services.tools import (
    calculate_cancellation_refund,
    cancel_ticket_action,
    dispatch_tool,
    get_flight_details,
)


def setup_function() -> None:
    """Reset database state before each test execution."""
    reset_database()


def test_get_flight_details_redacts_token() -> None:
    """Verify that flight details lookup never leaks verification_token."""
    logger = InMemoryAuditLogger()
    result = get_flight_details("ABC123", logger=logger)
    assert result["status"] == "OK"
    assert "verification_token" not in result["booking"]
    assert result["booking"]["name"] == "Rahim Uddin"
    assert len(logger.get_entries()) == 1


def test_cancellation_denied_with_wrong_token() -> None:
    """Verify that wrong token rejects cancellation without mutating status."""
    logger = InMemoryAuditLogger()
    result = cancel_ticket_action("ABC123", verification_token="0000", logger=logger)
    assert result["status"] == "VERIFICATION_FAILED"

    # Verify status in database remains CONFIRMED
    flight = get_flight_details("ABC123", logger=logger)
    assert flight["booking"]["status"] == "CONFIRMED"


def test_cancellation_success_and_idempotency() -> None:
    """Verify valid token succeeds and subsequent call is blocked by idempotency."""
    logger = InMemoryAuditLogger()
    first_attempt = cancel_ticket_action("ABC123", verification_token="7788", logger=logger)
    assert first_attempt["status"] == "CANCELLED"
    assert first_attempt["refund"]["refund_amount"] == 722.50

    # Repeat attempt (idempotency check)
    second_attempt = cancel_ticket_action("ABC123", verification_token="7788", logger=logger)
    assert second_attempt["status"] == "ALREADY_CANCELLED"


def test_dispatch_tool_dispatcher() -> None:
    """Verify JSON argument parsing and dispatching."""
    res = dispatch_tool("get_flight_details", '{"pnr": "XYZ789"}')
    assert res["status"] == "OK"
    assert res["booking"]["pnr"] == "XYZ789"
