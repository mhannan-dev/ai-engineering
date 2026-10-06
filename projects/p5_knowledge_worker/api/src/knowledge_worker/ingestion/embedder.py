"""Dense embeddings with a local multilingual model (fastembed / ONNX, CPU).

multilingual-e5 models are trained with "query: " / "passage: " prefixes and lose accuracy
without them; fastembed does not add them, so this wrapper does.
"""

import os
import shutil
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from knowledge_worker.ingestion.chunker import approx_token_count


class Embedder(Protocol):
    dim: int

    def embed_passages(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...

    def count_tokens(self, text: str) -> int: ...


def materialize_model(model_name: str, cache_dir: Path) -> Path:
    """Download the ONNX model and return a plain directory holding real files.

    The Hugging Face cache stores snapshot files as symlinks into separate blob folders, and
    onnxruntime >= 1.30 refuses to load `model.onnx_data` from outside the model's own folder.
    Hard links (same volume, no extra disk) or copies give it one self-contained directory.
    """
    from fastembed import TextEmbedding
    from huggingface_hub import snapshot_download

    description = next(
        (m for m in TextEmbedding._list_supported_models() if m.model == model_name), None
    )
    if description is None or not description.sources.hf:
        raise ValueError(f"'{model_name}' is not a fastembed model with a Hugging Face source.")

    repo = description.sources.hf
    flat = cache_dir / "flat" / repo.replace("/", "--")
    marker = flat / ".complete"
    if marker.exists():
        return flat

    snapshot = Path(snapshot_download(repo, cache_dir=str(cache_dir)))
    flat.mkdir(parents=True, exist_ok=True)
    for source in snapshot.iterdir():
        target = flat / source.name
        if target.exists():
            continue
        real = os.path.realpath(source)
        try:
            os.link(real, target)
        except OSError:
            shutil.copy2(real, target)
    marker.touch()
    return flat


class FastEmbedEmbedder:
    def __init__(
        self,
        model_name: str,
        cache_dir: str,
        dim: int,
        query_prefix: str = "query: ",
        passage_prefix: str = "passage: ",
        batch_size: int = 16,
    ):
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.dim = dim
        self.query_prefix = query_prefix
        self.passage_prefix = passage_prefix
        self.batch_size = batch_size
        self._model = None
        self._tokenizer = None
        self._lock = threading.Lock()

    def _load(self):
        # Loading takes seconds and ~2 GB RAM, so do it once, on first use, not at import.
        with self._lock:
            if self._model is None:
                from fastembed import TextEmbedding

                path = materialize_model(self.model_name, Path(self.cache_dir))
                self._model = TextEmbedding(
                    self.model_name, cache_dir=self.cache_dir, specific_model_path=str(path)
                )
                self._tokenizer = getattr(getattr(self._model, "model", None), "tokenizer", None)
        return self._model

    def embed_passages(self, texts: Sequence[str]) -> list[list[float]]:
        model = self._load()
        prefixed = [self.passage_prefix + t for t in texts]
        return [v.tolist() for v in model.embed(prefixed, batch_size=self.batch_size)]

    def embed_query(self, text: str) -> list[float]:
        model = self._load()
        return next(iter(model.embed([self.query_prefix + text]))).tolist()

    def count_tokens(self, text: str) -> int:
        self._load()
        if self._tokenizer is None:
            return approx_token_count(text)
        return len(self._tokenizer.encode(self.passage_prefix + text).ids)
