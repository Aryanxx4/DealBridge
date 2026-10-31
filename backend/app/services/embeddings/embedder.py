"""Local embedding model wrapper (fastembed, BAAI/bge-small-en-v1.5, 384 dims).

fastembed's TextEmbedding exposes `passage_embed` (documents; for BGE models it embeds the text as-is)
and `query_embed` (questions; for BGE models it prepends the BGE query instruction). Both were
confirmed present in the installed fastembed package (see test_embedder_methods_exist).
"""

from __future__ import annotations

import logging
import threading

import numpy as np

from app.core.config import get_settings
from app.core.errors import EmbeddingUnavailable

log = logging.getLogger("dealbridge.embedder")

BATCH_SIZE = 32


class Embedder:
    def __init__(self, model_name: str, dimension: int, cache_dir: str):
        self.model_name = model_name
        self.dimension = dimension
        self.cache_dir = cache_dir
        self._model = None
        self._lock = threading.Lock()
        self.load_error: str | None = None

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        with self._lock:
            if self._model is not None:
                return
            try:
                from fastembed import TextEmbedding

                self._model = TextEmbedding(model_name=self.model_name, cache_dir=self.cache_dir)
                self.load_error = None
                log.info("embedding model loaded", extra={"model": self.model_name})
            except Exception as exc:  # download or runtime failure
                self.load_error = f"{type(exc).__name__}: {exc}"[:300]
                log.error("embedding model failed to load", extra={"model": self.model_name, "error": self.load_error})
                raise EmbeddingUnavailable(f"Embedding model could not be loaded: {self.load_error}") from exc

    def _ensure(self):
        if self._model is None:
            self.load()
        return self._model

    def _check(self, vectors: list[np.ndarray]) -> list[list[float]]:
        out = []
        for v in vectors:
            if len(v) != self.dimension:
                raise EmbeddingUnavailable(f"Embedding dimension {len(v)} does not match EMBEDDING_DIMENSION={self.dimension}.")
            out.append([float(x) for x in v])
        return out

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._ensure()
        try:
            vectors = list(model.passage_embed(texts, batch_size=BATCH_SIZE))
        except EmbeddingUnavailable:
            raise
        except Exception as exc:
            raise EmbeddingUnavailable(f"Embedding failed: {type(exc).__name__}") from exc
        return self._check(vectors)

    def embed_query(self, text: str) -> list[float]:
        model = self._ensure()
        try:
            vectors = list(model.query_embed([text]))
        except Exception as exc:
            raise EmbeddingUnavailable(f"Embedding failed: {type(exc).__name__}") from exc
        return self._check(vectors)[0]


_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        s = get_settings()
        s.fastembed_cache_dir.mkdir(parents=True, exist_ok=True)
        _embedder = Embedder(s.EMBEDDING_MODEL, s.EMBEDDING_DIMENSION, str(s.fastembed_cache_dir))
    return _embedder


def set_embedder(embedder: Embedder | None) -> None:
    """Test hook."""
    global _embedder
    _embedder = embedder


def cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    return float(va @ vb / denom) if denom else 0.0
