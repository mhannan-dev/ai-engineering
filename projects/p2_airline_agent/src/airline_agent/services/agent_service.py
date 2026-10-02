# LLM agent reasoning loop and prompt injection sanitization service.
"""Agent orchestration service managing message history, tools, and reasoning loop."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ..config.prompts import INJECTION_PATTERNS
from ..config.settings import get_settings
from ..infra.llm_client import LLMClientProtocol, get_default_llm_client
from .tools import TOOL_SCHEMAS, dispatch_tool


def sanitize_text(text: str) -> str:
    """Strip common prompt-injection vectors from user inputs.
    
    Args:
        text: Raw user or OCR extracted text string.
        
    Returns:
        Sanitized and truncated text string.
    """
    cleaned = INJECTION_PATTERNS.sub("[redacted]", text)
    return cleaned.strip()[:2000]


def execute_agent_loop(
    messages: List[Dict[str, Any]],
    model_name: Optional[str] = None,
    max_iterations: Optional[int] = None,
    client: Optional[LLMClientProtocol] = None,
) -> str:
    """Run the reasoning -> parallel tool dispatching -> observe loop.
    
    Maintains state fidelity by mutating `messages` with tool calls and observations,
    appending only a single final assistant turn without duplicates.
    
    Args:
        messages: Conversation turn dictionary list (mutated in-place).
        model_name: Optional LLM model identifier override.
        max_iterations: Maximum loop iterations guard.
        client: Optional LLM client driver protocol.
        
    Returns:
        Final synthesized text response from the assistant.
    """
    driver = client or get_default_llm_client()
    settings = get_settings()
    limit = max_iterations or settings.max_agent_iterations
    target_model = model_name or settings.default_model

    for _ in range(limit):
        response = driver.complete_with_tools(
            messages=messages,
            tools=TOOL_SCHEMAS,
            model_name=target_model,
        )
        msg = response.choices[0].message
        assistant_entry: Dict[str, Any] = {
            "role": "assistant",
            "content": msg.content or "",
        }

        tool_calls = getattr(msg, "tool_calls", None)

        # Base case: Final answer reached (no tools needed)
        if not tool_calls:
            messages.append(assistant_entry)
            return msg.content or "(no response)"

        # Record assistant tool call intention in history
        assistant_entry["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in tool_calls
        ]
        messages.append(assistant_entry)

        # PARALLEL DISPATCH: execute each tool call independently
        for tc in tool_calls:
            result = dispatch_tool(tc.function.name, tc.function.arguments)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": tc.function.name,
                "content": json.dumps(result),
            })

    return "I'm having trouble completing that request. Please try again or contact support."


def get_system_prompt() -> str:
    """Return the system persona prompt template."""
    from ..config.prompts import SYSTEM_PROMPT
    return SYSTEM_PROMPT


def get_audit_records(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve audit log records through infrastructure abstraction."""
    from ..infra.audit_log import get_default_audit_logger
    return get_default_audit_logger().get_entries(limit)


def get_active_model_info() -> Dict[str, str | None]:
    """Retrieve active model name and API base URL for UI display."""
    settings = get_settings()
    return {
        "model": settings.default_model,
        "base_url": settings.openai_base_url,
    }

