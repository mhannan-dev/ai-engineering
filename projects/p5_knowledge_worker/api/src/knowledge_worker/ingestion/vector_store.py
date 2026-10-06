"""Qdrant wrapper. Every point carries user_id, and every query filters on it."""

from collections.abc import Sequence
from dataclasses import dataclass

from qdrant_client import QdrantClient, models


@dataclass(frozen=True)
class VectorPoint:
    chunk_id: str
    document_id: str
    user_id: str
    vector: list[float]


@dataclass(frozen=True)
class VectorHit:
    chunk_id: str
    score: float


class VectorStore:
    def __init__(self, client: QdrantClient, collection: str, dim: int, remote: bool = False):
        self._client = client
        self._collection = collection
        self._dim = dim
        self._remote = remote

    @classmethod
    def connect(cls, url: str, path: str, collection: str, dim: int) -> "VectorStore":
        """Use a Qdrant server when `url` is set, otherwise embedded local storage at `path`."""
        client = QdrantClient(url=url) if url else QdrantClient(path=path)
        store = cls(client, collection, dim, remote=bool(url))
        store.ensure_collection()
        return store

    def ensure_collection(self) -> None:
        if self._client.collection_exists(self._collection):
            size = self._client.get_collection(self._collection).config.params.vectors.size
            if size != self._dim:
                raise RuntimeError(
                    f"Qdrant collection '{self._collection}' has dimension {size}, but the "
                    f"embedding model produces {self._dim}. Changing EMBEDDING_MODEL requires a "
                    "new QDRANT_COLLECTION and re-indexing all documents."
                )
            return
        self._client.create_collection(
            self._collection,
            vectors_config=models.VectorParams(size=self._dim, distance=models.Distance.COSINE),
        )
        if not self._remote:
            return  # embedded Qdrant scans payloads and ignores indexes
        for field in ("user_id", "document_id"):
            self._client.create_payload_index(
                self._collection, field, field_schema=models.PayloadSchemaType.KEYWORD
            )

    def upsert(self, points: Sequence[VectorPoint], batch_size: int = 128) -> None:
        for start in range(0, len(points), batch_size):
            self._client.upsert(
                self._collection,
                points=[
                    models.PointStruct(
                        id=p.chunk_id,
                        vector=p.vector,
                        payload={"user_id": p.user_id, "document_id": p.document_id},
                    )
                    for p in points[start : start + batch_size]
                ],
            )

    def delete_document(self, user_id: str, document_id: str) -> None:
        self._client.delete(
            self._collection,
            points_selector=models.FilterSelector(filter=self._filter(user_id, document_id)),
        )

    def search(self, user_id: str, vector: list[float], limit: int) -> list[VectorHit]:
        result = self._client.query_points(
            self._collection, query=vector, query_filter=self._filter(user_id), limit=limit
        )
        return [VectorHit(chunk_id=str(p.id), score=p.score) for p in result.points]

    def count(self, user_id: str) -> int:
        return self._client.count(self._collection, count_filter=self._filter(user_id)).count

    def close(self) -> None:
        self._client.close()

    @staticmethod
    def _filter(user_id: str, document_id: str | None = None) -> models.Filter:
        must = [models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
        if document_id:
            must.append(
                models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id))
            )
        return models.Filter(must=must)
