"""Saved chat history: turns are stored when an answer completes, and stay private."""

import json

from knowledge_worker.services.conversation_service import make_title
from tests.test_auth import auth_client, bearer, register  # noqa: F401  (fixture + helpers)
from tests.test_chat_api import seeded_client  # noqa: F401  (fixture)
from tests.test_chat_errors import ExplodingLLM

ASK = {"query": "How many days of annual leave do employees receive?", "top_k": 2, "threshold": 0.1}


def stream(client, payload, headers=None) -> list[tuple[str, dict]]:
    """POST /chat/stream and parse the SSE body into (event, data) pairs."""
    body = client.post("/api/v1/chat/stream", json=payload, headers=headers or {}).text
    events = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def conversation_event(events) -> dict:
    return next(data for name, data in events if name == "conversation")


class TestStreamSavesHistory:
    def test_first_question_creates_a_conversation(self, seeded_client):  # noqa: F811
        events = stream(seeded_client, ASK)
        names = [name for name, _ in events]
        assert names.index("conversation") == names.index("done") - 1
        saved = conversation_event(events)
        assert saved["title"] == ASK["query"]

        detail = seeded_client.get(f"/api/v1/chat/conversations/{saved['id']}").json()
        assert [m["role"] for m in detail["messages"]] == ["user", "assistant"]
        assert detail["messages"][0]["content"] == ASK["query"]
        answer = detail["messages"][1]
        assert answer["content"]
        assert answer["sources"], "sources are stored with the answer"
        assert answer["validation"] is not None

    def test_follow_up_appends_to_the_same_conversation(self, seeded_client):  # noqa: F811
        first = conversation_event(stream(seeded_client, ASK))
        second = conversation_event(
            stream(seeded_client, {**ASK, "query": "And sick leave?", "conversation_id": first["id"]})
        )
        assert second["id"] == first["id"]
        assert second["title"] == first["title"]  # the title stays the first question

        messages = seeded_client.get(f"/api/v1/chat/conversations/{first['id']}").json()["messages"]
        assert [(m["role"], m["content"]) for m in messages][::2] == [
            ("user", ASK["query"]),
            ("user", "And sick leave?"),
        ]
        assert len(messages) == 4

    def test_abstention_is_saved_too(self, seeded_client):  # noqa: F811
        events = stream(seeded_client, {**ASK, "query": "telescope astrophysics", "threshold": 0.99})
        saved = conversation_event(events)
        answer = seeded_client.get(f"/api/v1/chat/conversations/{saved['id']}").json()["messages"][1]
        assert answer["is_abstention"] is True

    def test_failed_answer_saves_nothing(self, seeded_client, container):  # noqa: F811
        container.generator.llm_client = ExplodingLLM()
        events = stream(seeded_client, ASK)
        assert "conversation" not in [name for name, _ in events]
        assert seeded_client.get("/api/v1/chat/conversations").json()["total"] == 0

    def test_unknown_conversation_is_404_before_streaming(self, seeded_client):  # noqa: F811
        response = seeded_client.post(
            "/api/v1/chat/stream", json={**ASK, "conversation_id": "does-not-exist"}
        )
        assert response.status_code == 404
        assert response.json()["error"] == "NotFoundError"


class TestNonStreamingChat:
    def test_saves_and_returns_the_conversation_id(self, seeded_client):  # noqa: F811
        body = seeded_client.post("/api/v1/chat", json=ASK).json()
        assert body["conversation_id"]
        detail = seeded_client.get(f"/api/v1/chat/conversations/{body['conversation_id']}").json()
        assert len(detail["messages"]) == 2


class TestConversationApi:
    def test_list_is_most_recent_first(self, seeded_client):  # noqa: F811
        older = conversation_event(stream(seeded_client, {**ASK, "query": "first topic"}))
        newer = conversation_event(stream(seeded_client, {**ASK, "query": "second topic"}))
        stream(seeded_client, {**ASK, "query": "back to the first", "conversation_id": older["id"]})

        page = seeded_client.get("/api/v1/chat/conversations").json()
        assert page["total"] == 2
        assert [c["id"] for c in page["items"]] == [older["id"], newer["id"]]

    def test_delete_removes_the_conversation_and_messages(self, seeded_client):  # noqa: F811
        saved = conversation_event(stream(seeded_client, ASK))
        assert seeded_client.delete(f"/api/v1/chat/conversations/{saved['id']}").status_code == 204
        assert seeded_client.get(f"/api/v1/chat/conversations/{saved['id']}").status_code == 404
        assert seeded_client.delete(f"/api/v1/chat/conversations/{saved['id']}").status_code == 404

    def test_users_cannot_see_or_continue_each_others_conversations(self, auth_client):  # noqa: F811
        rahim = bearer(register(auth_client).json()["access_token"])
        karim = bearer(
            register(auth_client, email="karim@example.com", name="Karim").json()["access_token"]
        )
        saved = conversation_event(stream(auth_client, {**ASK, "threshold": 0.99}, headers=karim))

        assert auth_client.get("/api/v1/chat/conversations", headers=rahim).json()["total"] == 0
        url = f"/api/v1/chat/conversations/{saved['id']}"
        assert auth_client.get(url, headers=rahim).status_code == 404
        assert auth_client.delete(url, headers=rahim).status_code == 404
        hijack = auth_client.post(
            "/api/v1/chat/stream", json={**ASK, "conversation_id": saved["id"]}, headers=rahim
        )
        assert hijack.status_code == 404
        assert auth_client.get(url, headers=karim).status_code == 200


class TestTitle:
    def test_short_question_is_kept(self):
        assert make_title("  How many\n days?  ") == "How many days?"

    def test_long_question_is_cut_at_a_word(self):
        title = make_title("word " * 40)
        assert len(title) <= 81 and title.endswith("…") and not title.endswith(" …")
