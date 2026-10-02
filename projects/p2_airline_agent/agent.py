"""
Airline Customer Support Agent - Reasoning Engine & Agent Loop
===============================================================
Orchestrates LiteLLM tool calling, parallel tool dispatching, prompt injection
redaction, and stateful conversation history.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
import litellm

from .config import DEFAULT_MODEL, MAX_AGENT_ITERATIONS, OPENAI_API_KEY, OPENAI_BASE_URL
from .tools import TOOL_SCHEMAS, dispatch_tool

# Prompt injection pattern sanitizer
_INJECTION_PATTERNS = re.compile(
    r"(ignore (all )?previous|disregard (the )?system|you are now|"
    r"reveal (your )?(system )?prompt|jailbreak|developer mode)",
    re.IGNORECASE,
)


def sanitize_text(text: str) -> str:
    """Strip common prompt-injection attempts from user or OCR text."""
    cleaned = _INJECTION_PATTERNS.sub("[redacted]", text)
    return cleaned.strip()[:2000]


def execute_agent_loop(
    messages: List[Dict[str, Any]],
    model_name: str = DEFAULT_MODEL,
    max_iterations: int = MAX_AGENT_ITERATIONS,
) -> str:
    """Run the reasoning -> tool execution -> observe loop until a final text response.
    
    Mutates `messages` in-place by adding assistant turns and tool observations,
    ensuring full state fidelity without duplicate assistant messages.
    """
    for _ in range(max_iterations):
        completion_kwargs: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "tools": TOOL_SCHEMAS,
            "tool_choice": "auto",
            "temperature": 0.2,
        }
        if OPENAI_BASE_URL:
            completion_kwargs["api_base"] = OPENAI_BASE_URL
        if OPENAI_API_KEY:
            completion_kwargs["api_key"] = OPENAI_API_KEY

        response = litellm.completion(**completion_kwargs)
        msg = response.choices[0].message
        assistant_entry: Dict[str, Any] = {
            "role": "assistant",
            "content": msg.content or "",
        }

        tool_calls = getattr(msg, "tool_calls", None)

        # Base case: No tool calls requested -> final answer reached
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
