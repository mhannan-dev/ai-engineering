"""Integration tests for audio processing and meeting minutes retrieval."""

import io


def test_process_audio_confidential_routing(client):
    """Verify confidential audio routes to Faster-Whisper."""
    audio_content = b"fake-audio-binary-stream-12345"
    files = {"file": ("strategic_planning.mp3", io.BytesIO(audio_content), "audio/mpeg")}
    data = {"sensitivity": "confidential", "meeting_title": "Executive Strategy Sync"}

    res = client.post("/api/process-audio", files=files, data=data)
    assert res.status_code == 200
    res_data = res.json()

    assert res_data["meeting_title"] == "Executive Strategy Sync"
    assert res_data["transcription_metadata"]["sensitivity"] == "confidential"
    assert "faster-whisper" in res_data["transcription_metadata"]["engine"]
    assert len(res_data["action_items"]) > 0


def test_process_audio_public_routing(client):
    """Verify public audio routes to Cloud Deepgram API."""
    audio_content = b"fake-public-audio-content"
    files = {"file": ("all_hands.wav", io.BytesIO(audio_content), "audio/wav")}
    data = {"sensitivity": "public"}

    res = client.post("/api/process-audio", files=files, data=data)
    assert res.status_code == 200
    res_data = res.json()

    assert res_data["transcription_metadata"]["sensitivity"] == "public"
    assert "Deepgram" in res_data["transcription_metadata"]["engine"]


def test_list_and_get_meeting_by_id(client):
    """Verify meeting list and retrieval by ID."""
    audio_content = b"sample-bytes"
    files = {"file": ("team_standup.mp3", io.BytesIO(audio_content), "audio/mpeg")}
    upload_res = client.post("/api/process-audio", files=files, data={"sensitivity": "public"})
    meeting_id = upload_res.json()["id"]

    # List all
    list_res = client.get("/api/v1/meetings/")
    assert list_res.status_code == 200
    assert any(m["id"] == meeting_id for m in list_res.json())

    # Get by ID
    get_res = client.get(f"/api/v1/meetings/{meeting_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == meeting_id
