# Immutable audit logging infrastructure with Protocol abstraction.
"""Audit log infrastructure providing append-only persistence.

Complies with enterprise compliance requirements for tracking all customer-facing
and destructive financial operations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Protocol


class AuditLoggerProtocol(Protocol):
    """Protocol interface for event auditing and compliance logging."""

    def log_event(self, action: str, pnr: str, detail: Dict[str, Any]) -> None:
        """Append an audit entry to the audit log sink."""
        ...

    def get_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent audit entries."""
        ...


class InMemoryAuditLogger:
    """Thread-safe append-only in-memory implementation of AuditLoggerProtocol."""

    def __init__(self) -> None:
        self._records: List[Dict[str, Any]] = []

    def log_event(self, action: str, pnr: str, detail: Dict[str, Any]) -> None:
        """Record an immutable timestamped event."""
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "pnr": pnr.upper().strip() if pnr else "UNKNOWN",
            "detail": detail,
        }
        self._records.append(entry)

    def get_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent audit records up to limit."""
        return list(self._records[-limit:])

    def clear(self) -> None:
        """Clear all audit records (primarily for testing fixtures)."""
        self._records.clear()


# Default singleton instance
_DEFAULT_LOGGER = InMemoryAuditLogger()


def get_default_audit_logger() -> InMemoryAuditLogger:
    """Return singleton audit logger instance."""
    return _DEFAULT_LOGGER
