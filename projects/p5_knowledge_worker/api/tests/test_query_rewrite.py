"""Follow-up questions are rewritten into standalone ones before retrieval."""

import pytest

from knowledge_worker.generation.prompts import build_rewrite_prompt
from knowledge_worker.generation.rewriter import QueryRewriter, StandaloneQuestion
from tests.test_auth import auth_client, bearer, register  # noqa: F401  (fixture + helpers)
from tests.test_chat_api import seeded_client  # noqa: F401  (fixture)
from tests.test_conversations import ASK, conversation_event, stream


class RecordingLLM:
    """Returns a fixed rewrite and remembers the prompts it was given."""

    def __init__(self, answer="How many days of sick leave do employees get?", error=None):
        self.answer = answer
        self.error = error
        self.calls: list[list[dict[str, str]]] = []

    def generate_structured(self, messages, response_model, temperature=0.0, max_tokens=1500):
        self.calls.append(messages)
        if self.error:
            raise self.error
        assert response_model is StandaloneQuestion
        return StandaloneQuestion(question=self.answer)


HISTORY = [("How many days of annual leave do I get?", "You get 20 days [hr.md, 1. Annual leave].")]


class TestRewriter:
    def test_first_message_needs_no_llm_call(self):
        llm = RecordingLLM()
        assert QueryRewriter(llm).rewrite([], "How many days of annual leave?") == "How many days of annual leave?"
        assert llm.calls == []

    def test_follow_up_is_rewritten_using_the_history(self):
        llm = RecordingLLM(answer="  How many days of sick leave\n do employees get?  ")
        rewritten = QueryRewriter(llm).rewrite(HISTORY, "And sick leave?")
        assert rewritten == "How many days of sick leave do employees get?"  # whitespace tidied
        prompt = llm.calls[0][-1]["content"]
        assert "User: How many days of annual leave do I get?" in prompt
        assert "Assistant: You get 20 days" in prompt
        assert prompt.rstrip().endswith("Latest message: And sick leave?\n\nStandalone question:")

    def test_system_prompt_keeps_the_question_language(self):
        llm = RecordingLLM()
        QueryRewriter(llm).rewrite(HISTORY, "আর অসুস্থতার ছুটি?")
        assert "Bangla stays Bangla" in llm.calls[0][0]["content"]

    @pytest.mark.parametrize(
        "llm",
        [RecordingLLM(error=RuntimeError("provider down")), RecordingLLM(answer="   "), RecordingLLM(answer="x" * 1001)],
        ids=["llm-error", "empty", "too-long"],
    )
    def test_falls_back_to_the_original_question(self, llm):
        assert QueryRewriter(llm).rewrite(HISTORY, "And sick leave?") == "And sick leave?"


class TestRewritePrompt:
    def test_turns_are_oldest_first(self):
        prompt = build_rewrite_prompt([("q1", "a1"), ("q2", "a2")], "q3")
        assert prompt.index("User: q1") < prompt.index("User: q2") < prompt.index("Latest message: q3")

    def test_long_answers_are_cut(self):
        prompt = build_rewrite_prompt([("q", "word " * 500)], "next", max_answer_chars=50)
        answer_line = next(line for line in prompt.splitlines() if line.startswith("Assistant:"))
        assert len(answer_line) < 70 and answer_line.endswith("…")


class FakeRewriter:
    """Stands in for the LLM rewrite and records the history each call received."""

    def __init__(self, rewrites: dict[str, str]):
        self.rewrites = rewrites
        self.histories: list[list[tuple[str, str]]] = []

    def rewrite(self, history, question):
        self.histories.append(list(history))
        return self.rewrites.get(question, question) if history else question


class TestFollowUpInChat:
    def test_follow_up_searches_with_the_rewritten_question(self, seeded_client, container):  # noqa: F811
        rewriter = FakeRewriter({"And how long is it?": ASK["query"]})
        container.generator.rewriter = rewriter

        first = conversation_event(stream(seeded_client, ASK))
        events = stream(seeded_client, {**ASK, "query": "And how long is it?", "conversation_id": first["id"]})

        # The first message had no history; the follow-up got the first turn.
        assert rewriter.histories[0] == []
        assert [q for q, _ in rewriter.histories[1]] == [ASK["query"]]
        assert rewriter.histories[1][0][1], "the previous answer is part of the history"

        sources = next(data for name, data in events if name == "sources")
        assert sources["query"] == "And how long is it?"  # what the user typed
        assert sources["normalized_query"] == ASK["query"]  # what was searched
        assert sources["sources"], "the rewritten question finds passages"

        # History keeps the user's own words, not the rewrite.
        messages = seeded_client.get(f"/api/v1/chat/conversations/{first['id']}").json()["messages"]
        assert messages[2]["content"] == "And how long is it?"

    def test_only_the_last_n_turns_are_used(self, seeded_client, container, monkeypatch):  # noqa: F811
        # Settings are a cached singleton shared by all tests, so restore it afterwards.
        monkeypatch.setattr(container.settings, "CHAT_HISTORY_TURNS", 2)
        rewriter = FakeRewriter({})
        container.generator.rewriter = rewriter
        conversation = conversation_event(stream(seeded_client, {**ASK, "query": "turn one"}))
        for text in ("turn two", "turn three", "turn four"):
            stream(seeded_client, {**ASK, "query": text, "conversation_id": conversation["id"]})
        assert [q for q, _ in rewriter.histories[-1]] == ["turn two", "turn three"]


class TestRecentTurns:
    def test_other_users_conversation_is_404(self, auth_client):  # noqa: F811
        rahim = bearer(register(auth_client).json()["access_token"])
        karim = bearer(register(auth_client, email="karim@example.com", name="Karim").json()["access_token"])
        saved = conversation_event(stream(auth_client, {**ASK, "threshold": 0.99}, headers=karim))
        response = auth_client.post(
            "/api/v1/chat", json={**ASK, "conversation_id": saved["id"]}, headers=rahim
        )
        assert response.status_code == 404
