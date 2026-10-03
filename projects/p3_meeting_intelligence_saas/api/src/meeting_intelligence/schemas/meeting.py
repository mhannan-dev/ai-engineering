"""Meeting minutes, action items, and audio upload schemas."""

from enum import StrEnum

from pydantic import BaseModel, Field


class SensitivityLevel(StrEnum):
    """Data sensitivity classification for audio routing."""

    CONFIDENTIAL = "confidential"
    PUBLIC = "public"


class PriorityLevel(StrEnum):
    """Task urgency level."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionItemStatus(StrEnum):
    """Task resolution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ActionItemSchema(BaseModel):
    """Action item detected in meeting discussions."""

    id: str = Field(description="Unique action item identifier.")
    task: str = Field(description="Clear description of the agreed task.")
    assignee: str = Field(description="Responsible person or team.")
    due_date: str = Field(description="Target completion date or timeframe.")
    priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM, description="Task urgency level.")
    status: ActionItemStatus = Field(default=ActionItemStatus.PENDING, description="Current task status.")


class TranscriptionMetadataSchema(BaseModel):
    """Metadata regarding speech-to-text processing engine and execution."""

    engine: str = Field(description="Transcription engine used.")
    sensitivity: SensitivityLevel = Field(description="Sensitivity level applied.")
    duration_seconds: float = Field(description="Audio duration in seconds.")
    confidence_score: float | None = Field(default=None, description="Average confidence score.")
    processed_at: str = Field(description="ISO timestamp of processing.")
    audio_filename: str = Field(description="Original uploaded audio filename.")
    raw_transcript: str = Field(default="", description="Full speech-to-text transcript text.")



class MeetingMinutesSchema(BaseModel):
    """Complete structured synthesis of meeting minutes."""

    id: str = Field(description="Unique meeting minutes ID.")
    meeting_title: str = Field(description="Inferred or extracted meeting title.")
    date: str = Field(description="Meeting date string.")
    executive_summary: str = Field(description="Concise executive synthesis.")
    key_discussion_points: list[str] = Field(default_factory=list, description="Core topics debated.")
    decisions_made: list[str] = Field(default_factory=list, description="Agreed decisions.")
    action_items: list[ActionItemSchema] = Field(default_factory=list, description="Extracted actionable items.")
    transcription_metadata: TranscriptionMetadataSchema = Field(description="Processing audit metadata.")
