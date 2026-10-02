"""Meeting minutes, audio processing, and action items endpoints."""


from fastapi import APIRouter, File, Form, UploadFile, status

from meeting_intelligence.api.deps import (
    DatabaseDep,
    SynthesisServiceDep,
    TranscriptionServiceDep,
)
from meeting_intelligence.core.exceptions import AudioProcessingError, NotFoundError
from meeting_intelligence.models.meeting import Meeting, TranscriptionRecord
from meeting_intelligence.schemas.meeting import (
    ActionItemSchema,
    MeetingMinutesSchema,
    SensitivityLevel,
    TranscriptionMetadataSchema,
)

router = APIRouter()


def _to_schema(meeting: Meeting) -> MeetingMinutesSchema:
    """Map domain Meeting model to MeetingMinutesSchema."""
    action_items_schemas = [
        ActionItemSchema(
            id=item.id,
            task=item.task,
            assignee=item.assignee,
            due_date=item.due_date,
            priority=item.priority,  # type: ignore[arg-type]
            status=item.status,      # type: ignore[arg-type]
        )
        for item in meeting.action_items
    ]

    trans = meeting.transcription or TranscriptionRecord(
        audio_filename="unknown",
        sensitivity=SensitivityLevel.PUBLIC.value,
        engine="Unknown",
        duration_seconds=0.0,
        raw_transcript="",
    )

    metadata_schema = TranscriptionMetadataSchema(
        engine=trans.engine,
        sensitivity=SensitivityLevel(trans.sensitivity),
        duration_seconds=trans.duration_seconds,
        confidence_score=trans.confidence_score,
        processed_at=trans.processed_at.isoformat(),
        audio_filename=trans.audio_filename,
    )

    return MeetingMinutesSchema(
        id=meeting.id,
        meeting_title=meeting.title,
        date=meeting.date,
        executive_summary=meeting.executive_summary,
        key_discussion_points=meeting.key_discussion_points,
        decisions_made=meeting.decisions_made,
        action_items=action_items_schemas,
        transcription_metadata=metadata_schema,
    )


@router.post(
    "/process-audio",
    response_model=MeetingMinutesSchema,
    status_code=status.HTTP_200_OK,
    summary="Process audio upload",
    description="Upload an audio file (.mp3 / .wav) with sensitivity routing to generate structured meeting minutes.",
)
async def process_audio(
    file: UploadFile = File(..., description="Audio file recording (.mp3 / .wav)"),
    sensitivity: SensitivityLevel = Form(
        default=SensitivityLevel.CONFIDENTIAL,
        description="Routing policy: 'confidential' routes to local Faster-Whisper, 'public' to Cloud Deepgram.",
    ),
    meeting_title: str | None = Form(default=None, description="Optional custom title for the meeting."),
    transcription_service: TranscriptionServiceDep = None,  # type: ignore[assignment]
    synthesis_service: SynthesisServiceDep = None,          # type: ignore[assignment]
    db: DatabaseDep = None,                                # type: ignore[assignment]
) -> MeetingMinutesSchema:
    """Handle audio upload, routing, transcription, and synthesis."""
    if not file.filename:
        raise AudioProcessingError("Uploaded file has no filename.")

    content = await file.read()
    if not content:
        raise AudioProcessingError("Uploaded audio file is empty.")

    # 1. Transcribe audio via hybrid routing
    transcription = await transcription_service.transcribe(
        audio_bytes=content,
        filename=file.filename,
        sensitivity=sensitivity,
    )

    # 2. Synthesize structured minutes via LLM
    meeting = await synthesis_service.synthesize(
        transcription=transcription,
        meeting_title=meeting_title or file.filename.rsplit(".", 1)[0].replace("_", " ").title(),
    )

    # 3. Persist record in repository
    db.meetings.create(meeting)

    return _to_schema(meeting)


@router.get(
    "/",
    response_model=list[MeetingMinutesSchema],
    summary="List all processed meetings",
    description="Retrieve all previously processed meeting minutes.",
)
async def list_meetings(db: DatabaseDep) -> list[MeetingMinutesSchema]:
    """List meeting records."""
    return [_to_schema(m) for m in db.meetings.list_all()]


@router.get(
    "/{meeting_id}",
    response_model=MeetingMinutesSchema,
    summary="Get meeting minutes by ID",
    description="Retrieve single meeting minutes by ID.",
)
async def get_meeting(meeting_id: str, db: DatabaseDep) -> MeetingMinutesSchema:
    """Get single meeting minutes record."""
    meeting = db.meetings.get_by_id(meeting_id)
    if not meeting:
        raise NotFoundError(f"Meeting with ID {meeting_id} was not found.")
    return _to_schema(meeting)
