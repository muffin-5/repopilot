"""
RepoPilot – Vector Store.

Wraps Qdrant for production use, with a complete in-memory fallback
using numpy cosine similarity when Qdrant is not available.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class VectorSearchResult:
    """Single vector search result."""

    chunk_id: str
    score: float
    metadata: dict


class VectorStore:
    """Vector store with Qdrant backend and in-memory numpy fallback."""

    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection: str = "repopilot_chunks",
        qdrant_url: Optional[str] = None,
        collection_name: Optional[str] = None,
    ) -> None:
        """
        Args:
            url: Qdrant server URL.
            collection: Default collection name.
        """
        self.url = qdrant_url or url
        self.collection = collection_name or collection
        self._client = None
        self._use_inmemory = False
        self._inmemory_stores: dict[str, _InMemoryCollection] = {}
        self._connect()

    def _connect(self) -> None:
        """Try to connect to Qdrant; fall back to in-memory store."""
        try:
            from qdrant_client import QdrantClient  # type: ignore

            self._client = QdrantClient(url=self.url, timeout=5)
            # quick health check
            self._client.get_collections()
            logger.info("qdrant_connected", url=self.url)
        except Exception as exc:
            logger.warning("qdrant_unavailable_using_inmemory", error=str(exc))
            self._use_inmemory = True
            self._client = None

    # ── collection management ──────────────────────────────────────────

    def create_collection(self, name: str, dimension: int) -> None:
        """Create (or recreate) a vector collection.

        Args:
            name: Collection name.
            dimension: Vector dimension.
        """
        if self._use_inmemory:
            self._inmemory_stores[name] = _InMemoryCollection(dimension=dimension)
            logger.info("inmemory_collection_created", name=name, dimension=dimension)
            return

        try:
            from qdrant_client.models import Distance, VectorParams  # type: ignore

            self._client.recreate_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )
            logger.info("qdrant_collection_created", name=name, dimension=dimension)
        except Exception as exc:
            logger.error("qdrant_create_collection_failed", error=str(exc))
            self._use_inmemory = True
            self._inmemory_stores[name] = _InMemoryCollection(dimension=dimension)

    def delete_collection(self, name: str) -> None:
        """Delete a collection.

        Args:
            name: Collection name.
        """
        if self._use_inmemory:
            self._inmemory_stores.pop(name, None)
            return

        try:
            self._client.delete_collection(collection_name=name)
            logger.info("qdrant_collection_deleted", name=name)
        except Exception as exc:
            logger.warning("qdrant_delete_failed", error=str(exc))
            self._inmemory_stores.pop(name, None)

    # ── indexing ───────────────────────────────────────────────────────

    def add_chunks(
        self,
        collection: str,
        ids: list[Any],
        vectors: np.ndarray,
        payloads: Optional[list[dict]] = None,
    ) -> int:
        """Insert vectors with metadata into a collection."""
        if payloads is None:
            chunk_dicts = ids
            chunk_ids = [c.get("chunk_id", str(i)) for i, c in enumerate(chunk_dicts)]
            chunk_payloads = chunk_dicts
        else:
            chunk_ids = [str(x) for x in ids]
            chunk_payloads = payloads

        if vectors.shape[0] == 0:
            return 0

        if self._use_inmemory:
            store = self._inmemory_stores.get(collection)
            if store is None:
                store = _InMemoryCollection(dimension=vectors.shape[1])
                self._inmemory_stores[collection] = store
            store.add(chunk_ids, vectors, chunk_payloads)
            return len(chunk_ids)

        try:
            from qdrant_client.models import PointStruct  # type: ignore

            points = [
                PointStruct(
                    id=_str_to_uuid(id_),
                    vector=vec.tolist(),
                    payload=payload,
                )
                for id_, vec, payload in zip(ids, vectors, payloads)
            ]

            batch_size = 100
            for i in range(0, len(points), batch_size):
                self._client.upsert(
                    collection_name=collection,
                    points=points[i: i + batch_size],
                )

            logger.info("vectors_added", collection=collection, count=len(ids))
            return len(ids)
        except Exception as exc:
            logger.error("qdrant_add_failed_falling_back", error=str(exc))
            self._use_inmemory = True
            store = self._inmemory_stores.get(collection)
            if store is None:
                store = _InMemoryCollection(dimension=vectors.shape[1])
                self._inmemory_stores[collection] = store
            store.add(ids, vectors, payloads)
            return len(ids)

    # ── search ─────────────────────────────────────────────────────────

    def search(
        self,
        collection: str,
        query_vector: np.ndarray,
        top_k: int = 10,
    ) -> list[VectorSearchResult]:
        """Search for nearest neighbours.

        Args:
            collection: Collection to search.
            query_vector: 1-D query vector.
            top_k: Number of results.

        Returns:
            Ranked list of ``VectorSearchResult``.
        """
        if self._use_inmemory:
            store = self._inmemory_stores.get(collection)
            if store is None:
                return []
            return store.search(query_vector, top_k)

        try:
            results = self._client.search(
                collection_name=collection,
                query_vector=query_vector.tolist(),
                limit=top_k,
                with_payload=True,
            )
            return [
                VectorSearchResult(
                    chunk_id=str(r.id),
                    score=r.score,
                    metadata=r.payload or {},
                )
                for r in results
            ]
        except Exception as exc:
            logger.error("qdrant_search_failed", error=str(exc))
            store = self._inmemory_stores.get(collection)
            if store:
                return store.search(query_vector, top_k)
            return []

    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists.

        Args:
            name: Collection name.

        Returns:
            True if the collection exists.
        """
        if self._use_inmemory:
            return name in self._inmemory_stores

        try:
            self._client.get_collection(name)
            return True
        except Exception:
            return False

    def collection_count(self, name: str) -> int:
        """Return the number of vectors in a collection.

        Args:
            name: Collection name.

        Returns:
            Vector count.
        """
        if self._use_inmemory:
            store = self._inmemory_stores.get(name)
            return store.count if store else 0

        try:
            info = self._client.get_collection(name)
            return info.points_count or 0
        except Exception:
            return 0


# ═══════════════════════════════════════════════════════════════════════════════
# In-memory fallback collection
# ═══════════════════════════════════════════════════════════════════════════════


class _InMemoryCollection:
    """Numpy-based in-memory vector store for a single collection."""

    def __init__(self, dimension: int) -> None:
        self.dimension = dimension
        self.ids: list[str] = []
        self.vectors: np.ndarray = np.empty((0, dimension), dtype=np.float32)
        self.payloads: list[dict] = []

    @property
    def count(self) -> int:
        return len(self.ids)

    def add(self, ids: list[str], vectors: np.ndarray, payloads: list[dict]) -> None:
        """Append vectors to the store."""
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)
        self.ids.extend(ids)
        self.vectors = np.vstack([self.vectors, vectors.astype(np.float32)]) if self.vectors.shape[0] > 0 else vectors.astype(np.float32)
        self.payloads.extend(payloads)

    def search(self, query: np.ndarray, top_k: int = 10) -> list[VectorSearchResult]:
        """Cosine-similarity search against stored vectors."""
        if self.vectors.shape[0] == 0:
            return []

        query = query.astype(np.float32).reshape(1, -1)
        # L2-normalise
        q_norm = np.linalg.norm(query)
        if q_norm > 0:
            query = query / q_norm

        v_norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        v_norms = np.where(v_norms == 0, 1, v_norms)
        normed = self.vectors / v_norms

        scores = (normed @ query.T).flatten()
        k = min(top_k, len(scores))
        if k == 0:
            return []
        top_indices = np.argsort(-scores)[:k]

        return [
            VectorSearchResult(
                chunk_id=self.ids[i],
                score=float(scores[i]),
                metadata=self.payloads[i],
            )
            for i in top_indices
        ]


def _str_to_uuid(s: str) -> str:
    """Convert a string to a deterministic UUID-like hex string for Qdrant."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, s))
