"""LLM client abstraction using LiteLLM + Instructor with testable fake."""

import os
from collections.abc import Iterator
from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol):
    """Protocol for LLM generation with structured output and text streaming."""

    def generate_structured(
        self,
        messages: list[dict[str, str]],
        response_model: type[T],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> T: ...

    def stream_text(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> Iterator[str]: ...


class LiteLLMClient:
    """Production LLM client utilizing LiteLLM and Instructor."""

    def __init__(
        self,
        model: str = "deepseek/deepseek-chat",
        api_key: str | None = None,
        api_base: str | None = None,
    ):
        # Load integrations during container startup, before request workers use them. Importing
        # lazily inside requests lets concurrent workers deadlock on LiteLLM's circular imports.
        import instructor
        import litellm

        self._instructor = instructor
        self._instructor_mode = instructor.Mode
        self._litellm = litellm
        self.model = model
        self.api_key = api_key
        self.api_base = api_base

    def _configure_env(self) -> None:
        if self.api_key:
            if "deepseek" in self.model:
                os.environ["DEEPSEEK_API_KEY"] = self.api_key
            else:
                os.environ["OPENAI_API_KEY"] = self.api_key
        if self.api_base and not self.model.startswith("deepseek/"):
            os.environ["OPENAI_BASE_URL"] = self.api_base

    def generate_structured(
        self,
        messages: list[dict[str, str]],
        response_model: type[T],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> T:
        self._configure_env()

        # DeepSeek and open-weights models are most reliable with Markdown JSON mode
        if "deepseek" in self.model:
            client = self._instructor.from_litellm(
                self._litellm.completion, mode=self._instructor_mode.MD_JSON
            )
        else:
            client = self._instructor.from_litellm(self._litellm.completion)

        kwargs: dict = {
            "model": self.model,
            "response_model": response_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout": 30.0,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base and not self.model.startswith("deepseek/"):
            kwargs["api_base"] = self.api_base

        return client.chat.completions.create(**kwargs)

    def stream_text(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> Iterator[str]:
        self._configure_env()

        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "timeout": 30.0,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base and not self.model.startswith("deepseek/"):
            kwargs["api_base"] = self.api_base

        response = self._litellm.completion(**kwargs)
        for part in response:
            choices = part.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                content = delta.get("content")
                if content:
                    yield content


class FakeLLMClient:
    """Deterministic, offline LLM client for tests."""

    def __init__(self, canned_response: BaseModel | None = None):
        self.canned_response = canned_response

    def generate_structured(
        self,
        messages: list[dict[str, str]],
        response_model: type[T],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> T:
        if self.canned_response is not None:
            if isinstance(self.canned_response, response_model):
                return self.canned_response
            # Attempt to convert or construct
            return response_model.model_validate(self.canned_response.model_dump())

        # Synthesize a default structured answer
        from knowledge_worker.schemas.generation import Citation, StructuredAnswer

        user_content = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"), ""
        )

        return response_model.model_validate(
            StructuredAnswer(
                answer=f"Verified factual answer for: {user_content[:40]} [sample.pdf, Page 1].",
                citations=[Citation(document_filename="sample.pdf", page=1)],
                is_abstention=False,
            ).model_dump()
        )

    def stream_text(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> Iterator[str]:
        if self.canned_response and hasattr(self.canned_response, "answer"):
            text = self.canned_response.answer
        else:
            text = "Here is the streamed factual answer [sample.pdf, Page 1]."

        words = text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
