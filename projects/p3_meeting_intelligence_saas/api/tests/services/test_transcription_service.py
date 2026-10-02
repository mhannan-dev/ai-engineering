"""Unit tests for TranscriptionService routing and validation."""

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
async def test_transcribe_routes_public():
    """Verify public sensitivity selects Deepgram engine."""
    settings = Settings()
    service = TranscriptionService(settings)

    result = await service.transcribe(b"valid-audio-data", "public_webinar.mp3", SensitivityLevel.PUBLIC)
    assert result.sensitivity == "public"
    assert "Deepgram" in result.engine
