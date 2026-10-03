"""Integration tests for audio processing and meeting minutes retrieval."""

import io


def _upload(client, headers, filename="team_standup.mp3", sensitivity="public", title=None):
    files = {"file": (filename, io.BytesIO(b"fake-audio-binary-stream-12345"), "audio/mpeg")}
    data = {"sensitivity": sensitivity, **({"meeting_title": title} if title else {})}
    return client.post("/api/process-audio", files=files, data=data, headers=headers)


def test_process_audio_confidential_routing(client, auth_headers):
    """Verify confidential audio routes to Faster-Whisper."""
    res = _upload(client, auth_headers, "strategic_planning.mp3", "confidential", "Executive Strategy Sync")
    assert res.status_code == 200
    res_data = res.json()

    assert res_data["meeting_title"] == "Executive Strategy Sync"
    assert res_data["transcription_metadata"]["sensitivity"] == "confidential"
    assert "faster-whisper" in res_data["transcription_metadata"]["engine"]
    assert len(res_data["action_items"]) > 0


def test_process_audio_public_routing(client, auth_headers):
    """Verify public audio routes to Cloud Deepgram API."""
    res = _upload(client, auth_headers, "all_hands.wav", "public")
    assert res.status_code == 200
    res_data = res.json()

    assert res_data["transcription_metadata"]["sensitivity"] == "public"
    assert "Deepgram" in res_data["transcription_metadata"]["engine"]


def test_list_and_get_meeting_by_id(client, auth_headers):
    """Verify meeting list and retrieval by ID."""
    meeting_id = _upload(client, auth_headers).json()["id"]

    list_res = client.get("/api/v1/meetings/", headers=auth_headers)
    assert list_res.status_code == 200
    assert [m["id"] for m in list_res.json()] == [meeting_id]

    get_res = client.get(f"/api/v1/meetings/{meeting_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == meeting_id


def test_list_meetings_is_paginated(client, auth_headers):
    """Verify limit/offset paging and the 100-item cap."""
    ids = [_upload(client, auth_headers, f"m{i}.mp3").json()["id"] for i in range(3)]

    page1 = client.get("/api/v1/meetings/?limit=2", headers=auth_headers).json()
    page2 = client.get("/api/v1/meetings/?limit=2&offset=2", headers=auth_headers).json()
    assert len(page1) == 2 and len(page2) == 1
    assert {m["id"] for m in page1 + page2} == set(ids)
    assert client.get("/api/v1/meetings/?limit=101", headers=auth_headers).status_code == 422


def test_undecodable_audio_returns_clear_422(client, auth_headers, monkeypatch):
    """Verify a corrupt/non-audio upload is reported as a client error, not a server fault."""
    import av
    import faster_whisper

    class BrokenAudioModel:
        def __init__(self, *args, **kwargs):
            pass

        def transcribe(self, audio, **kwargs):
            raise av.error.InvalidDataError(1094995529, "Invalid data found when processing input")

    monkeypatch.setattr(faster_whisper, "WhisperModel", BrokenAudioModel)
    res = _upload(client, auth_headers, "notes.mp3", "confidential")
    assert res.status_code == 422
    assert "valid MP3, WAV or M4A" in res.json()["message"]
    assert "ffmpeg" not in res.json()["message"]


def test_meetings_require_authentication(client):
    """Verify upload, list and get all reject anonymous callers."""
    assert _upload(client, headers={}).status_code == 401
    assert client.get("/api/v1/meetings/").status_code == 401
    assert client.get("/api/v1/meetings/some-id").status_code == 401


def test_meetings_are_private_to_their_owner(client, auth_headers, make_user):
    """Verify one user cannot list or fetch another user's meetings."""
    meeting_id = _upload(client, auth_headers).json()["id"]
    mallory = make_user("mallory@example.com", "Mallory")

    assert client.get("/api/v1/meetings/", headers=mallory).json() == []
    assert client.get(f"/api/v1/meetings/{meeting_id}", headers=mallory).status_code == 404
