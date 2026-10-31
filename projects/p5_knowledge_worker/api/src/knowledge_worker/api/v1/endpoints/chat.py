import logging
from collections.abc import Iterator
from typing import Annotated, Any

from fastapi import APIRouter, Query, Response, status
from fastapi.responses import StreamingResponse

from knowledge_worker.api.deps import (
    ConversationServiceDep,
    CurrentUserIdDep,
    GeneratorDep,
    SettingsDep,
)
from knowledge_worker.config import Settings
from knowledge_worker.core.exceptions import AppException
from knowledge_worker.db.session import SessionLocal
from knowledge_worker.schemas.conversation import (
    ConversationDetail,
    ConversationOut,
    ConversationPage,
)
from knowledge_worker.schemas.generation import ChatRequest, ChatResponse
from knowledge_worker.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)
router = APIRouter()

# Sent instead of the exception text, which can hold keys, model names and server paths.
GENERIC_STREAM_ERROR = "Something went wrong while answering. Please try again."

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _history(
    request: ChatRequest, user_id: str, conversations: ConversationService, settings: Settings
) -> list[tuple[str, str]]:
    """Recent turns used to rewrite a follow-up. Loading them also checks that the
    conversation is this user's, so an unknown id is a 404 before any LLM call."""
    if request.conversation_id is None:
        return []
    return conversations.recent_turns(user_id, request.conversation_id, settings.CHAT_HISTORY_TURNS)


@router.post("", response_model=ChatResponse, summary="Generate faithful answer with citations")
def chat_answer(
    request: ChatRequest,
    user_id: CurrentUserIdDep,
    generator: GeneratorDep,
    conversations: ConversationServiceDep,
    settings: SettingsDep,
) -> ChatResponse:
    """Generate a fully grounded answer with bracketed citations and abstention check."""
    history = _history(request, user_id, conversations, settings)
    try:
        response = generator.generate(user_id=user_id, request=request, history=history)
    except AppException:
        # The handler returns only the safe message; the chained cause goes to the log.
        logger.exception("Chat answer failed")
        raise
    # Any other error reaches the app's catch-all middleware, which logs it and returns a
    # generic 500.
    conversation = conversations.save_turn(
        user_id,
        request.conversation_id,
        request.query,
        response.answer,
        citations=[c.model_dump() for c in response.citations],
        sources=[s.model_dump() for s in response.sources],
        validation=response.validation.model_dump(),
        is_abstention=response.is_abstention,
    )
    return response.model_copy(update={"conversation_id": conversation.id})


def _save_streamed_turn(
    user_id: str, request: ChatRequest, done: dict[str, Any], sources: list[dict[str, Any]]
) -> dict[str, str] | None:
    """Persist a finished streamed answer. The stream outlives the request's DB session, so
    this opens its own. Saving must never cost the user the answer they already received."""
    try:
        with SessionLocal() as db:
            conversation = ConversationService(db).save_turn(
                user_id,
                request.conversation_id,
                request.query,
                done.get("answer", ""),
                citations=done.get("citations"),
                sources=sources,
                validation=done.get("validation"),
                is_abstention=bool(done.get("is_abstention")),
            )
            return {"id": conversation.id, "title": conversation.title}
    except Exception:
        logger.exception("Could not save the chat turn")
        return None


def _sse_events(
    generator, user_id: str, request: ChatRequest, history: list[tuple[str, str]]
) -> Iterator[str]:
    sources: list[dict[str, Any]] = []
    try:
        for event in generator.stream_events(user_id=user_id, request=request, history=history):
            if event["event"] == "sources":
                sources = event["data"].get("sources", [])
            elif event["event"] == "done":
                # Saved only when the answer is complete, then announced before `done` so the
                # client knows which conversation to continue.
                saved = _save_streamed_turn(user_id, request, event["data"], sources)
                if saved is not None:
                    yield generator.format_sse({"event": "conversation", "data": saved})
            yield generator.format_sse(event)
    except AppException as exc:
        logger.exception("Chat stream failed")
        yield generator.format_sse({"event": "error", "data": {"error": exc.message}})
    except Exception:
        logger.exception("Chat stream failed")
        yield generator.format_sse({"event": "error", "data": {"error": GENERIC_STREAM_ERROR}})


# There is deliberately no GET variant for EventSource: EventSource cannot send the
# Authorization header, and passing the token in the query string would leak it into server
# logs, proxy logs and browser history. Browsers read this POST stream with fetch().
@router.post("/stream", summary="Stream faithful answer tokens and citation validation via SSE")
def chat_stream(
    request: ChatRequest,
    user_id: CurrentUserIdDep,
    generator: GeneratorDep,
    conversations: ConversationServiceDep,
    settings: SettingsDep,
) -> StreamingResponse:
    """Stream answer generation as Server-Sent Events (SSE).

    Events: `status`, `sources`, `token`, `validation`, `conversation` (the saved
    conversation's id and title), `done`, or `error`. With a `conversation_id`, a follow-up
    is rewritten into a standalone question first; `sources.normalized_query` shows it.
    """
    # Loaded before streaming starts, so an unknown id is a plain 404, not a stream error.
    history = _history(request, user_id, conversations, settings)
    return StreamingResponse(
        _sse_events(generator, user_id, request, history),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


@router.get("/conversations", response_model=ConversationPage, summary="List saved conversations")
def list_conversations(
    user_id: CurrentUserIdDep,
    conversations: ConversationServiceDep,
    limit: Limit = 50,
    offset: Offset = 0,
) -> ConversationPage:
    """Most recently active first."""
    items, total = conversations.list_conversations(user_id, limit, offset)
    return ConversationPage(
        items=[ConversationOut.model_validate(c) for c in items], total=total, limit=limit, offset=offset
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail,
    summary="A conversation with its messages",
)
def get_conversation(
    conversation_id: str, user_id: CurrentUserIdDep, conversations: ConversationServiceDep
) -> ConversationDetail:
    return ConversationDetail.model_validate(
        conversations.get(user_id, conversation_id, with_messages=True)
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation and its messages",
)
def delete_conversation(
    conversation_id: str, user_id: CurrentUserIdDep, conversations: ConversationServiceDep
) -> Response:
    conversations.delete(user_id, conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
