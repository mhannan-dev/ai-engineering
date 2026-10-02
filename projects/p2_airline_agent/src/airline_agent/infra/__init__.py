# Package marker for infrastructure layer.
"""Infrastructure layer isolating external SDKs, LLM drivers, and audit sinks."""

from .audit_log import AuditLoggerProtocol, InMemoryAuditLogger, get_default_audit_logger
from .llm_client import LLMClientProtocol, LiteLLMClient, get_default_llm_client

__all__ = [
    "LLMClientProtocol",
    "LiteLLMClient",
    "get_default_llm_client",
    "AuditLoggerProtocol",
    "InMemoryAuditLogger",
    "get_default_audit_logger",
]
