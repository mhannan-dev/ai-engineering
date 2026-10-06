"""Per-user BM25 index (bm25s) saved to disk.

bm25s cannot add or remove documents from an existing index, so the user's index is rebuilt
from the chunks table whenever a document is indexed or deleted. That takes well under a second
for tens of thousands of chunks, which is fine at this scale.
"""

import json
import shutil
import threading
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import bm25s

from knowledge_worker.text.tokenizer import tokenize


@dataclass(frozen=True)
class SparseHit:
    chunk_id: str
    score: float


class SparseIndex:
    def __init__(self, root: Path):
        self._root = root
        self._locks: defaultdict[str, threading.Lock] = defaultdict(threading.Lock)
        self._cache: dict[str, tuple[bm25s.BM25, list[str]]] = {}

    def _dir(self, user_id: str) -> Path:
        return self._root / user_id

    def rebuild(self, user_id: str, chunks: Sequence[tuple[str, str]]) -> None:
        """Replace the user's index with `chunks` = [(chunk_id, text), ...]."""
        with self._locks[user_id]:
            target = self._dir(user_id)
            self._cache.pop(user_id, None)
            if not chunks:
                shutil.rmtree(target, ignore_errors=True)
                return
            ids = [cid for cid, _ in chunks]
            # Keep empty token lists: bm25s maps them to a placeholder so row i stays chunk i.
            corpus = [tokenize(text) for _, text in chunks]
            retriever = bm25s.BM25()
            retriever.index(corpus, show_progress=False)

            staging = target.with_name(target.name + ".tmp")
            shutil.rmtree(staging, ignore_errors=True)
            retriever.save(str(staging))
            (staging / "chunk_ids.json").write_text(json.dumps(ids), encoding="utf-8")
            shutil.rmtree(target, ignore_errors=True)
            staging.rename(target)
            self._cache[user_id] = (retriever, ids)

    def _get(self, user_id: str) -> tuple[bm25s.BM25, list[str]] | None:
        with self._locks[user_id]:
            if user_id not in self._cache:
                target = self._dir(user_id)
                if not (target / "chunk_ids.json").exists():
                    return None
                ids = json.loads((target / "chunk_ids.json").read_text(encoding="utf-8"))
                self._cache[user_id] = (bm25s.BM25.load(str(target)), ids)
            return self._cache[user_id]

    def search(self, user_id: str, query: str, limit: int) -> list[SparseHit]:
        loaded = self._get(user_id)
        tokens = tokenize(query)
        if loaded is None or not tokens:
            return []
        retriever, ids = loaded
        scores = retriever.get_scores(tokens)
        ranked = sorted(range(len(ids)), key=lambda i: scores[i], reverse=True)[:limit]
        return [SparseHit(ids[i], float(scores[i])) for i in ranked if scores[i] > 0]
