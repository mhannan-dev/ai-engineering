"""Meeting, Transcription, and ActionItem domain models."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class ActionItemRecord:
    """Action item domain record."""

    task: str
    assignee: str
    due_date: str
    priority: str = "medium"  # high, medium, low
    status: str = "pending"   # pending, in_progress, completed
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class TranscriptionRecord:
    """Transcription metadata and raw text output."""

    audio_filename: str
    sensitivity: str  # confidential | public
    engine: str
    duration_seconds: float
    raw_transcript: str
    confidence_score: float | None = None
    processed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Meeting:
    """Meeting domain entity containing minutes and action items."""

    title: str
    date: str
    executive_summary: str
    key_discussion_points: list[str] = field(default_factory=list)
    decisions_made: list[str] = field(default_factory=list)
    action_items: list[ActionItemRecord] = field(default_factory=list)
    transcription: TranscriptionRecord | None = None
    user_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
