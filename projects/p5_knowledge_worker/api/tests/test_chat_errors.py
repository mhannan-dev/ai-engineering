"""Step 1: LLM failures must not leak internal details to the client.

When the LLM call fails (bad key, timeout, provider outage), the user gets a short, generic
message in the standard error shape, and the full exception goes to the server log instead.
"""

import logging

import pytest

from tests.test_chat_api import seeded_client  # noqa: F401  (fixture)

# Looks like what provider errors really contain: a key fragment, a path, a model name.
SECRET_ERROR = "AuthenticationError: invalid key sk-SECRET123 for deepseek-chat at C:\\internal\\llm.py"
SECRETS = ["sk-SECRET123", "C:\\internal", "AuthenticationError", "deepseek-chat"]

ASK = {"query": "How many days of annual leave do employees receive?", "top_k": 2, "threshold": 0.1}


class ExplodingLLM:
    """An LLM client whose every call fails like a real provider error."""

    def generate_structured(self, *args, **kwargs):
        raise RuntimeError(SECRET_ERROR)

    def stream_text(self, *args, **kwargs):
        raise RuntimeError(SECRET_ERROR)
        yield  # makes this a generator, like the real client


@pytest.fixture
def broken_llm(container):
    container.generator.llm_client = ExplodingLLM()
    return container


def assert_no_secrets(text: str):
    for secret in SECRETS:
        assert secret not in text, f"leaked {secret!r} to the client"


class TestChatEndpoint:
    def test_returns_502_in_the_standard_error_shape(self, seeded_client, broken_llm):  # noqa: F811
        response = seeded_client.post("/api/v1/chat", json=ASK)
        assert response.status_code == 502
        body = response.json()
        assert set(body) == {"error", "message", "details"}
        assert body["error"] == "LLMUnavailableError"
        assert body["message"]  # a human-readable sentence, not empty

    def test_does_not_leak_the_exception_text(self, seeded_client, broken_llm):  # noqa: F811
        response = seeded_client.post("/api/v1/chat", json=ASK)
        assert_no_secrets(response.text)

    def test_logs_the_real_error_for_operators(self, seeded_client, broken_llm, caplog):  # noqa: F811
        with caplog.at_level(logging.ERROR):
            seeded_client.post("/api/v1/chat", json=ASK)
        assert SECRET_ERROR in caplog.text


class TestChatStream:
    def test_sends_a_generic_error_event(self, seeded_client, broken_llm):  # noqa: F811
        response = seeded_client.post("/api/v1/chat/stream", json=ASK)
        assert response.status_code == 200  # the stream had already started
        assert "event: error" in response.text
        assert_no_secrets(response.text)

    def test_logs_the_real_error_for_operators(self, seeded_client, broken_llm, caplog):  # noqa: F811
        with caplog.at_level(logging.ERROR):
            seeded_client.post("/api/v1/chat/stream", json=ASK)
        assert SECRET_ERROR in caplog.text

    def test_sources_still_arrive_before_the_error(self, seeded_client, broken_llm):  # noqa: F811
        # Retrieval worked, so the user can still see what was found.
        body = seeded_client.post("/api/v1/chat/stream", json=ASK).text
        assert body.index("event: sources") < body.index("event: error")
