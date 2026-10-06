"""Document upload and management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Query, Response, UploadFile, status

from knowledge_worker.api.deps import CurrentUserIdDep, DocumentServiceDep, SettingsDep
from knowledge_worker.core.exceptions import FileTooLargeError
from knowledge_worker.schemas.document import ChunkPage, DocumentOut, DocumentPage

router = APIRouter()

Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


@router.post(
    "",
    response_model=DocumentOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a document",
    description="Stores the file and queues it for indexing. Poll GET /documents/{id} for status.",
)
async def upload_document(
    file: UploadFile, user_id: CurrentUserIdDep, service: DocumentServiceDep, settings: SettingsDep
) -> DocumentOut:
    data = await file.read(settings.UPLOAD_MAX_BYTES + 1)
    if len(data) > settings.UPLOAD_MAX_BYTES:
        raise FileTooLargeError(f"Files can be at most {settings.UPLOAD_MAX_BYTES // 2**20} MB.")
    doc = service.upload(user_id, file.filename or "document", data)
    return DocumentOut.model_validate(doc)


@router.get("", response_model=DocumentPage, summary="List documents")
def list_documents(
    user_id: CurrentUserIdDep, service: DocumentServiceDep, limit: Limit = 50, offset: Offset = 0
) -> DocumentPage:
    items, total = service.list_documents(user_id, limit, offset)
    return DocumentPage(
        items=[DocumentOut.model_validate(d) for d in items], total=total, limit=limit, offset=offset
    )


@router.get("/{document_id}", response_model=DocumentOut, summary="Get a document")
def get_document(
    document_id: str, user_id: CurrentUserIdDep, service: DocumentServiceDep
) -> DocumentOut:
    return DocumentOut.model_validate(service.get(user_id, document_id))


@router.get(
    "/{document_id}/chunks",
    response_model=ChunkPage,
    summary="List a document's chunks",
    description="The passages that retrieval searches over, with page and heading.",
)
def list_chunks(
    document_id: str,
    user_id: CurrentUserIdDep,
    service: DocumentServiceDep,
    limit: Limit = 50,
    offset: Offset = 0,
) -> ChunkPage:
    items, total = service.list_chunks(user_id, document_id, limit, offset)
    return ChunkPage(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/{document_id}/reindex",
    response_model=DocumentOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Re-index a document",
)
def reindex_document(
    document_id: str, user_id: CurrentUserIdDep, service: DocumentServiceDep
) -> DocumentOut:
    return DocumentOut.model_validate(service.reindex(user_id, document_id))


@router.delete(
    "/{document_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a document"
)
def delete_document(
    document_id: str, user_id: CurrentUserIdDep, service: DocumentServiceDep
) -> Response:
    service.delete(user_id, document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
