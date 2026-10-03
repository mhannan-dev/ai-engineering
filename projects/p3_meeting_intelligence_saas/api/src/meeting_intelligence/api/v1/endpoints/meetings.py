"""Meeting minutes, audio processing, and action items endpoints."""


from fastapi import APIRouter, File, Form, Query, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from meeting_intelligence.api.deps import (
    CurrentUserDep,
    DatabaseDep,
    SettingsDep,
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
        raw_transcript=trans.raw_transcript,
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
    current_user: CurrentUserDep,
    settings: SettingsDep,
    file: UploadFile = File(..., description="Audio file recording (.mp3 / .wav)"),
    sensitivity: SensitivityLevel = Form(
        default=SensitivityLevel.CONFIDENTIAL,
        description="Routing policy: 'confidential' routes to local Faster-Whisper, 'public' to Cloud Deepgram.",
    ),
    meeting_title: str | None = Form(default=None, description="Optional custom title for the meeting."),
    language: str | None = Form(default=None, description="Optional audio language: 'bn' for Bengali, 'en' for English, or None for auto."),
    transcription_service: TranscriptionServiceDep = None,  # type: ignore[assignment]
    synthesis_service: SynthesisServiceDep = None,          # type: ignore[assignment]
    db: DatabaseDep = None,                                # type: ignore[assignment]
) -> MeetingMinutesSchema:
    """Handle audio upload, routing, transcription, and synthesis."""
    if not file.filename:
        raise AudioProcessingError("Uploaded file has no filename.")

    # Bounded read to protect against OOM / memory exhaustion (BackendRule Rule 4 & 5)
    content = await file.read(settings.AUDIO_MAX_BYTES + 1)
    if len(content) > settings.AUDIO_MAX_BYTES:
        max_mb = settings.AUDIO_MAX_BYTES // (1024 * 1024)
        raise AudioProcessingError(f"Uploaded audio file exceeds the maximum allowed size of {max_mb} MB.")
    if not content:
        raise AudioProcessingError("Uploaded audio file is empty.")

    # 1. Transcribe audio via hybrid routing
    transcription = await transcription_service.transcribe(
        audio_bytes=content,
        filename=file.filename,
        sensitivity=sensitivity,
        language=language,
    )

    # 2. Synthesize structured minutes via LLM
    meeting = await synthesis_service.synthesize(
        transcription=transcription,
        meeting_title=meeting_title or file.filename.rsplit(".", 1)[0].replace("_", " ").title(),
    )

    # 3. Persist record, owned by the caller (sync DB call kept off the event loop)
    meeting.user_id = current_user.id
    await run_in_threadpool(db.meetings.create, meeting)

    return _to_schema(meeting)


@router.get(
    "/",
    response_model=list[MeetingMinutesSchema],
    summary="List my processed meetings",
    description="Retrieve the caller's previously processed meeting minutes (newest first).",
)
def list_meetings(
    current_user: CurrentUserDep,
    db: DatabaseDep,
    limit: int = Query(default=50, ge=1, le=100, description="Page size (max 100)."),
    offset: int = Query(default=0, ge=0, description="Number of meetings to skip."),
) -> list[MeetingMinutesSchema]:
    """List the caller's meeting records, newest first."""
    return [_to_schema(m) for m in db.meetings.list_by_user(current_user.id, limit=limit, offset=offset)]


@router.get(
    "/{meeting_id}",
    response_model=MeetingMinutesSchema,
    summary="Get meeting minutes by ID",
    description="Retrieve single meeting minutes by ID.",
)
def get_meeting(meeting_id: str, current_user: CurrentUserDep, db: DatabaseDep) -> MeetingMinutesSchema:
    """Get one of the caller's meeting minutes records."""
    meeting = db.meetings.get_by_id(meeting_id)
    # 404 (not 403) for other users' meetings, so IDs can't be probed
    if not meeting or meeting.user_id != current_user.id:
        raise NotFoundError(f"Meeting with ID {meeting_id} was not found.")
    return _to_schema(meeting)
