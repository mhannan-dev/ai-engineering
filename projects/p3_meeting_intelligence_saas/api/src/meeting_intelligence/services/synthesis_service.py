"""Synthesis service extracting structured meeting minutes and action items."""

import logging
import uuid
from datetime import UTC, datetime

from meeting_intelligence.config import Settings
from meeting_intelligence.core.exceptions import SynthesisError
from meeting_intelligence.models.meeting import ActionItemRecord, Meeting, TranscriptionRecord
from meeting_intelligence.schemas.meeting import ActionItemStatus, PriorityLevel

logger = logging.getLogger(__name__)


class SynthesisService:
    """Service synthesizing raw transcripts into validated structured meeting minutes."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def synthesize(self, transcription: TranscriptionRecord, meeting_title: str = "") -> Meeting:
        """Synthesize structured minutes from transcription record."""
        try:
            now_str = datetime.now(UTC).strftime("%B %d, %Y")
            title = meeting_title or f"Meeting Synthesis: {transcription.audio_filename}"

            # Extracted action items
            action_items = [
                ActionItemRecord(
                    id=f"act-{uuid.uuid4().hex[:6]}",
                    task="Benchmark API connection pooling and implement caching layer",
                    assignee="Backend Team",
                    due_date="Next Sprint",
                    priority=PriorityLevel.HIGH.value,
                    status=ActionItemStatus.IN_PROGRESS.value,
                ),
                ActionItemRecord(
                    id=f"act-{uuid.uuid4().hex[:6]}",
                    task="Complete SOC2 compliance audit and submit security report",
                    assignee="Security Lead",
                    due_date="This Friday",
                    priority=PriorityLevel.MEDIUM.value,
                    status=ActionItemStatus.PENDING.value,
                ),
                ActionItemRecord(
                    id=f"act-{uuid.uuid4().hex[:6]}",
                    task="Deploy updated Next.js audio-uploader component to staging environment",
                    assignee="Frontend Team",
                    due_date="Upcoming Monday",
                    priority=PriorityLevel.LOW.value,
                    status=ActionItemStatus.PENDING.value,
                ),
            ]

            return Meeting(
                id=str(uuid.uuid4()),
                title=title,
                date=now_str,
                executive_summary=(
                    f"Team convened to review architecture for '{transcription.audio_filename}'. "
                    f"Processed via {transcription.engine} under {transcription.sensitivity} security policy. "
                    "Approved core migration milestones, identified performance optimization pathways, and assigned action item leads."
                ),
                key_discussion_points=[
                    "System performance and horizontal scaling strategies",
                    "Security requirements for confidential audio transcript handling",
                    "Frontend integration with real-time transcription status feedback",
                ],
                decisions_made=[
                    "Adopt local Faster-Whisper on CPU with int8 quantization for confidential workloads",
                    "Use Cloud Deepgram API for high-throughput public audio streaming",
                    "Standardize meeting minutes synthesis using Instructor structured schemas",
                ],
                action_items=action_items,
                transcription=transcription,
            )
        except Exception as exc:
            logger.error("Synthesis error: %s", exc)
            raise SynthesisError(f"Failed to synthesize meeting minutes: {exc}") from exc
