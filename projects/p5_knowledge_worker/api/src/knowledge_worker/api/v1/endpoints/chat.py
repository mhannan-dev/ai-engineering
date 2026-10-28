import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from knowledge_worker.api.deps import CurrentUserIdDep, GeneratorDep
from knowledge_worker.schemas.generation import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse, summary="Generate faithful answer with citations")
def chat_answer(
    request: ChatRequest,
    user_id: CurrentUserIdDep,
    generator: GeneratorDep,
) -> ChatResponse:
    """Generate a fully grounded answer with bracketed citations and abstention check."""
    try:
        return generator.generate(user_id=user_id, request=request)
    except Exception as exc:
        logger.exception("Error in chat_answer: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/stream", summary="Stream faithful answer tokens and citation validation via SSE")
def chat_stream_post(
    request: ChatRequest,
    user_id: CurrentUserIdDep,
    generator: GeneratorDep,
) -> StreamingResponse:
    """Stream answer generation as Server-Sent Events (SSE)."""
    def event_generator():
        try:
            for event in generator.stream_events(user_id=user_id, request=request):
                yield generator.format_sse(event)
        except Exception as exc:
            logger.exception("Error in chat_stream_post: %s", exc)
            err_sse = generator.format_sse({"event": "error", "data": {"error": str(exc)}})
            yield err_sse

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/stream", summary="Stream faithful answer via GET SSE (browser EventSource friendly)")
def chat_stream_get(
    user_id: CurrentUserIdDep,
    generator: GeneratorDep,
    query: str = Query(..., min_length=1, max_length=1000),
    top_k: int = Query(default=5, ge=1, le=20),
    threshold: float | None = Query(default=None),
) -> StreamingResponse:
    """GET endpoint for browser EventSource SSE streaming."""
    request = ChatRequest(query=query, top_k=top_k, threshold=threshold)

    def event_generator():
        try:
            for event in generator.stream_events(user_id=user_id, request=request):
                yield generator.format_sse(event)
        except Exception as exc:
            logger.exception("Error in chat_stream_get: %s", exc)
            yield generator.format_sse({"event": "error", "data": {"error": str(exc)}})
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
