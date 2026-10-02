# Low-level LLM and Vision SDK wrapper with Protocol abstraction.
"""LLM driver infrastructure isolating LiteLLM, Instructor, and PIL.

Wraps model invocation, tool calling, and multi-modal base64 processing.
"""

from __future__ import annotations

import base64
import io
from typing import Any, Dict, List, Protocol, Type, TypeVar
import instructor
import litellm
from PIL import Image
from pydantic import BaseModel

from ..config.settings import Settings, get_settings

T = TypeVar("T", bound=BaseModel)


class LLMClientProtocol(Protocol):
    """Protocol interface defining LLM completion and vision extraction capabilities."""

    def complete_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        model_name: str | None = None,
        temperature: float = 0.2,
    ) -> Any:
        """Execute a chat completion request with structured tool calling."""
        ...

    def extract_structured_vision(
        self,
        image_bytes: bytes,
        response_model: Type[T],
        prompt: str,
        model_name: str | None = None,
        max_retries: int = 2,
    ) -> T:
        """Extract typed Pydantic models from image inputs using vision models."""
        ...

    def verify_image(self, image_bytes: bytes) -> bool:
        """Validate whether byte payload represents a legitimate image format."""
        ...


class LiteLLMClient:
    """Concrete LLM client implementation wrapping LiteLLM and Instructor."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._configure_litellm()
        self._instructor_client = instructor.from_litellm(litellm.completion)

    def _configure_litellm(self) -> None:
        """Apply global credentials and endpoint overrides to LiteLLM."""
        if self._settings.openai_base_url:
            litellm.api_base = self._settings.openai_base_url
        if self._settings.openai_api_key:
            litellm.api_key = self._settings.openai_api_key

    def complete_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        model_name: str | None = None,
        temperature: float = 0.2,
    ) -> Any:
        """Invoke litellm.completion with tool schema configuration."""
        target_model = model_name or self._settings.default_model
        kwargs: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": temperature,
        }
        if self._settings.openai_base_url:
            kwargs["api_base"] = self._settings.openai_base_url
        if self._settings.openai_api_key:
            kwargs["api_key"] = self._settings.openai_api_key

        return litellm.completion(**kwargs)

    def extract_structured_vision(
        self,
        image_bytes: bytes,
        response_model: Type[T],
        prompt: str,
        model_name: str | None = None,
        max_retries: int = 2,
    ) -> T:
        """Encode image to base64 and invoke Instructor vision client."""
        b64_str = base64.b64encode(image_bytes).decode("utf-8")
        target_model = model_name or self._settings.vision_model

        # Fallback to vision_model if default model is a text-only endpoint (e.g. deepseek-chat)
        if "deepseek" in (target_model or "").lower():
            target_model = self._settings.vision_model

        return self._instructor_client.chat.completions.create(  # type: ignore[no-any-return]
            model=target_model,
            response_model=response_model,
            max_retries=max_retries,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_str}"}},
                ],
            }],
        )

    def verify_image(self, image_bytes: bytes) -> bool:
        """Verify image integrity using Pillow (PIL)."""
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.verify()
            return True
        except Exception:
            return False


# Singleton default client
_DEFAULT_CLIENT: LiteLLMClient | None = None


def get_default_llm_client() -> LiteLLMClient:
    """Return or initialize global LiteLLMClient instance."""
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None:
        _DEFAULT_CLIENT = LiteLLMClient()
    return _DEFAULT_CLIENT
