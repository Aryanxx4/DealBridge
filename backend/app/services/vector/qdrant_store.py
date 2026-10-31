"""Qdrant access for the two knowledge collections.

Every search goes through `retrievable_filter()` so that only approved, ACTIVE knowledge is returned (R4).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient, models

from app.core.config import get_settings
from app.core.errors import VectorDBUnavailable

log = logging.getLogger("dealbridge.qdrant")

PAYLOAD_INDEXES = ("knowledge_id", "category", "source_type", "approval_status", "validity_status", "source_document")


@dataclass
class Hit:
    id: str
    score: float
    payload: dict[str, Any]
    collection: str  # OFFICIAL | RESOLVED


def retrievable_filter() -> models.Filter:
    """The mandatory retrieval filter: approval_status = approved AND validity_status = ACTIVE."""
    return models.Filter(
        must=[
            models.FieldCondition(key="approval_status", match=models.MatchValue(value="approved")),
            models.FieldCondition(key="validity_status", match=models.MatchValue(value="ACTIVE")),
        ]
    )


class QdrantStore:
    def __init__(self, url: str, api_key: str | None, official: str, resolved: str, dimension: int):
        self.client = QdrantClient(url=url, api_key=api_key or None, timeout=10, check_compatibility=False)
        self.official = official
        self.resolved = resolved
        self.dimension = dimension

    def collection_for(self, kind: str) -> str:
        return self.official if kind == "OFFICIAL" else self.resolved

    # ---- lifecycle ------------------------------------------------------
    def ping(self) -> bool:
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False

    def _wrap(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except VectorDBUnavailable:
            raise
        except Exception as exc:
            log.error("qdrant call failed", extra={"error": type(exc).__name__})
            raise VectorDBUnavailable() from exc

    def create_collection(self, name: str, recreate: bool = False) -> bool:
        """Create the collection and payload indexes if missing. Returns True if created."""
        exists = self._wrap(self.client.collection_exists, name)
        if exists and recreate:
            self._wrap(self.client.delete_collection, name)
            exists = False
        created = False
        if not exists:
            self._wrap(
                self.client.create_collection,
                collection_name=name,
                vectors_config=models.VectorParams(size=self.dimension, distance=models.Distance.COSINE),
            )
            created = True
        for field in PAYLOAD_INDEXES:
            self._wrap(
                self.client.create_payload_index,
                collection_name=name,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
        return created

    def init_collections(self, recreate_official: bool = False, recreate_resolved: bool = False) -> dict[str, bool]:
        return {
            self.official: self.create_collection(self.official, recreate_official),
            self.resolved: self.create_collection(self.resolved, recreate_resolved),
        }

    def collection_config(self, name: str) -> tuple[int, str] | None:
        """(vector size, distance) or None if the collection is missing."""
        if not self._wrap(self.client.collection_exists, name):
            return None
        info = self._wrap(self.client.get_collection, name)
        vp = info.config.params.vectors
        return int(vp.size), str(vp.distance.value if hasattr(vp.distance, "value") else vp.distance)

    def count(self, name: str, only_retrievable: bool = False) -> int:
        flt = retrievable_filter() if only_retrievable else None
        return int(self._wrap(self.client.count, name, count_filter=flt, exact=True).count)

    # ---- writes ---------------------------------------------------------
    def upsert(self, name: str, points: list[tuple[str, list[float], dict]]) -> int:
        if not points:
            return 0
        self._wrap(
            self.client.upsert,
            collection_name=name,
            points=[models.PointStruct(id=pid, vector=vec, payload=payload) for pid, vec, payload in points],
            wait=True,
        )
        return len(points)

    def delete(self, name: str, ids: list[str]) -> int:
        if not ids:
            return 0
        self._wrap(self.client.delete, collection_name=name, points_selector=models.PointIdsList(points=ids), wait=True)
        return len(ids)

    def set_payload(self, name: str, ids: list[str], payload: dict) -> None:
        self._wrap(self.client.set_payload, collection_name=name, payload=payload, points=ids, wait=True)

    def retrieve(self, name: str, ids: list[str]) -> list[dict]:
        recs = self._wrap(self.client.retrieve, collection_name=name, ids=ids, with_payload=True)
        return [{"id": str(r.id), "payload": r.payload or {}} for r in recs]

    def scroll_all(self, name: str, with_payload: bool = True) -> list[dict]:
        out, offset = [], None
        while True:
            recs, offset = self._wrap(self.client.scroll, collection_name=name, limit=256, offset=offset, with_payload=with_payload)
            out.extend({"id": str(r.id), "payload": r.payload or {}} for r in recs)
            if offset is None:
                return out

    # ---- search ---------------------------------------------------------
    def search(self, kind: str, vector: list[float], limit: int) -> list[Hit]:
        """Search one collection with the mandatory approved+ACTIVE filter."""
        name = self.collection_for(kind)
        res = self._wrap(
            self.client.query_points,
            collection_name=name,
            query=vector,
            limit=limit,
            query_filter=retrievable_filter(),
            with_payload=True,
        )
        return [Hit(id=str(p.id), score=float(p.score), payload=p.payload or {}, collection=kind) for p in res.points]


_store: QdrantStore | None = None


def get_store() -> QdrantStore:
    global _store
    if _store is None:
        s = get_settings()
        _store = QdrantStore(
            s.QDRANT_URL, s.QDRANT_API_KEY, s.QDRANT_OFFICIAL_COLLECTION, s.QDRANT_RESOLVED_COLLECTION, s.EMBEDDING_DIMENSION
        )
    return _store


def set_store(store: QdrantStore | None) -> None:
    """Test hook."""
    global _store
    _store = store
