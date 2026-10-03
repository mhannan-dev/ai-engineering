"""Unit tests for TranscriptionService routing and validation."""

import asyncio
import time
from types import SimpleNamespace

import pytest

from meeting_intelligence.config import Settings
from meeting_intelligence.core.exceptions import AudioProcessingError
from meeting_intelligence.schemas.meeting import SensitivityLevel
from meeting_intelligence.services.transcription_service import TranscriptionService


@pytest.mark.asyncio
async def test_transcribe_empty_bytes_raises():
    """Verify empty audio bytes trigger AudioProcessingError."""
    settings = Settings()
    service = TranscriptionService(settings)

    with pytest.raises(AudioProcessingError):
        await service.transcribe(b"", "empty.mp3", SensitivityLevel.CONFIDENTIAL)


@pytest.mark.asyncio
async def test_transcribe_routes_confidential():
    """Verify confidential sensitivity selects local faster-whisper engine."""
    settings = Settings()
    service = TranscriptionService(settings)

    result = await service.transcribe(b"valid-audio-data", "secret_sync.mp3", SensitivityLevel.CONFIDENTIAL)
    assert result.sensitivity == "confidential"
    assert "faster-whisper" in result.engine


@pytest.mark.asyncio
async def test_whisper_model_is_loaded_once(monkeypatch):
    """Verify the model is created once and reused across requests."""
    import faster_whisper

    created = []

    class CountingModel:
        def __init__(self, *args, **kwargs):
            created.append(args)

        def transcribe(self, audio, **kwargs):
            return iter([SimpleNamespace(text="hi")]), SimpleNamespace(duration=1.0)

    monkeypatch.setattr(faster_whisper, "WhisperModel", CountingModel)
    service = TranscriptionService(Settings())
    for _ in range(3):
        await service.transcribe(b"audio", "a.mp3", SensitivityLevel.CONFIDENTIAL)

    assert len(created) == 1


@pytest.mark.asyncio
async def test_local_transcription_does_not_block_event_loop(monkeypatch):
    """Verify inference runs off the event loop: other coroutines keep running meanwhile."""
    import faster_whisper

    class SlowModel:
        def __init__(self, *args, **kwargs):
            pass

        def transcribe(self, audio, **kwargs):
            time.sleep(0.5)  # simulates CPU-bound inference
            return iter([SimpleNamespace(text="done")]), SimpleNamespace(duration=1.0)

    monkeypatch.setattr(faster_whisper, "WhisperModel", SlowModel)
    ticks = 0

    async def ticker():
        nonlocal ticks
        for _ in range(20):
            await asyncio.sleep(0.05)
            ticks += 1

    async def transcribe_and_count_ticks():
        await TranscriptionService(Settings()).transcribe(b"audio", "slow.mp3", SensitivityLevel.CONFIDENTIAL)
        return ticks

    ticks_during_inference, _ = await asyncio.gather(transcribe_and_count_ticks(), ticker())
    # A blocked loop would leave the ticker at 0 until the 0.5s inference finished
    assert ticks_during_inference >= 3


@pytest.mark.asyncio
async def test_transcribe_routes_public():
    """Verify public sensitivity selects Deepgram engine."""
    settings = Settings()
    service = TranscriptionService(settings)

    result = await service.transcribe(b"valid-audio-data", "public_webinar.mp3", SensitivityLevel.PUBLIC)
    assert result.sensitivity == "public"
    assert "Deepgram" in result.engine
