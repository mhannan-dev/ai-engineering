import builtins
from types import SimpleNamespace

from pydantic import BaseModel

from knowledge_worker.generation.llm import LiteLLMClient


class SampleResponse(BaseModel):
    value: int


def test_litellm_imports_are_complete_before_request_methods(monkeypatch):
    client = LiteLLMClient()
    expected = SampleResponse(value=42)
    monkeypatch.setattr(
        client._instructor,
        "from_litellm",
        lambda *_args, **_kwargs: SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=lambda **_kwargs: expected)
            )
        ),
    )
    monkeypatch.setattr(
        client._litellm,
        "completion",
        lambda **_kwargs: iter([{"choices": [{"delta": {"content": "hello"}}]}]),
    )
    original_import = builtins.__import__

    def reject_litellm_imports(name, *args, **kwargs):
        if name.split(".", maxsplit=1)[0] in {"instructor", "litellm"}:
            raise AssertionError(f"LLM dependency imported during request: {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", reject_litellm_imports)

    structured = client.generate_structured([], SampleResponse)
    streamed = list(client.stream_text([]))

    assert structured == expected
    assert streamed == ["hello"]
