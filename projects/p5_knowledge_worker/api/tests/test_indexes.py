from qdrant_client import QdrantClient

from knowledge_worker.ingestion.sparse_index import SparseIndex
from knowledge_worker.ingestion.vector_store import VectorPoint, VectorStore

CHUNKS = [
    ("c1", "কর্মীরা বছরে ২০ দিন বার্ষিক ছুটি পাবেন।"),
    ("c2", "Remote work is allowed two days per week."),
    ("c3", "The cafeteria opens at 9am on weekdays."),
]


class TestSparseIndex:
    def test_bangla_query_matches_inflected_form(self, tmp_path):
        index = SparseIndex(tmp_path)
        index.rebuild("u1", CHUNKS)
        hits = index.search("u1", "ছুটির নিয়ম কী?", limit=5)  # "ছুটির" vs indexed "ছুটি"
        assert [h.chunk_id for h in hits] == ["c1"]

    def test_english_query_and_digits(self, tmp_path):
        index = SparseIndex(tmp_path)
        index.rebuild("u1", CHUNKS)
        assert [h.chunk_id for h in index.search("u1", "working remotely", 5)] == ["c2"]
        assert index.search("u1", "২০ days", 5)[0].chunk_id == "c1"

    def test_persists_and_reloads(self, tmp_path):
        SparseIndex(tmp_path).rebuild("u1", CHUNKS)
        assert SparseIndex(tmp_path).search("u1", "cafeteria", 5)[0].chunk_id == "c3"

    def test_users_are_isolated_and_empty_rebuild_clears(self, tmp_path):
        index = SparseIndex(tmp_path)
        index.rebuild("u1", CHUNKS)
        assert index.search("u2", "cafeteria", 5) == []
        index.rebuild("u1", [])
        assert index.search("u1", "cafeteria", 5) == []
        assert not (tmp_path / "u1").exists()

    def test_no_matching_terms_returns_nothing(self, tmp_path):
        index = SparseIndex(tmp_path)
        index.rebuild("u1", CHUNKS)
        assert index.search("u1", "the and of", 5) == []  # stopwords only


class TestVectorStore:
    def test_search_is_scoped_to_user_and_delete_by_document(self):
        store = VectorStore(QdrantClient(":memory:"), "t", 2)
        store.ensure_collection()
        a = "00000000-0000-0000-0000-00000000000a"
        b = "00000000-0000-0000-0000-00000000000b"
        store.upsert([VectorPoint(a, "d1", "u1", [1.0, 0.0]), VectorPoint(b, "d2", "u2", [1.0, 0.0])])
        assert [h.chunk_id for h in store.search("u1", [1.0, 0.0], 10)] == [a]
        store.delete_document("u1", "d1")
        assert store.count("u1") == 0 and store.count("u2") == 1

    def test_dimension_mismatch_is_reported(self):
        client = QdrantClient(":memory:")
        VectorStore(client, "t", 2).ensure_collection()
        try:
            VectorStore(client, "t", 3).ensure_collection()
        except RuntimeError as exc:
            assert "re-indexing" in str(exc)
        else:
            raise AssertionError("expected a dimension mismatch error")
