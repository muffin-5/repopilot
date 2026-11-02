"""
RepoPilot – Hybrid Search Module.

Combines dense vector retrieval (semantic) and BM25 sparse retrieval (lexical)
using Reciprocal Rank Fusion (RRF) and weighted linear combination.
Supports optional cross-encoder reranking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import structlog

from app.retrieval.bm25_search import BM25Search
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import VectorStore

logger = structlog.get_logger(__name__)


@dataclass
class RetrievedChunk:
    """Represents a retrieved chunk with combined score and metadata."""

    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    chunk_type: str
    score: float
    vector_score: float = 0.0
    bm25_score: float = 0.0
    rank: int = 0
    language: str = "text"
    metadata: dict[str, Any] = field(default_factory=dict)


class HybridRetriever:
    """Orchestrates BM25 + Dense Vector Search + Reranking."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        bm25_weight: float = 0.4,
        vector_weight: float = 0.6,
        rrf_k: int = 60,
        use_reranker: bool = False,
    ) -> None:
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.rrf_k = rrf_k
        self.use_reranker = use_reranker
        self._bm25_indices: dict[str, BM25Search] = {}
        self._reranker: Any = None

        if self.use_reranker:
            try:
                from sentence_transformers import CrossEncoder
                self._reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
                logger.info("cross_encoder_reranker_loaded")
            except Exception as e:
                logger.warning("reranker_load_failed", error=str(e))
                self._reranker = None

    def get_or_create_bm25(self, repo_id: str) -> BM25Search:
        """Get or create the BM25 search instance for a repository."""
        if repo_id not in self._bm25_indices:
            self._bm25_indices[repo_id] = BM25Search()
        return self._bm25_indices[repo_id]

    def index_repo_chunks(self, repo_id: str, chunks: list[dict[str, Any]]) -> None:
        """Build both Vector Store collection and BM25 index for repository chunks."""
        if not chunks:
            logger.warning("no_chunks_to_index", repo_id=repo_id)
            return

        # 1. Build BM25 index
        bm25 = self.get_or_create_bm25(repo_id)
        bm25.build_index(chunks)

        # 2. Embed chunks and insert into vector store
        texts = [c.get("content", "") for c in chunks]
        embeddings = self.embedding_service.embed_batch(texts)

        # Ensure collection exists and insert
        self.vector_store.create_collection(repo_id, dimension=embeddings.shape[1])
        self.vector_store.add_chunks(repo_id, chunks, embeddings)

        logger.info("indexed_repo_chunks", repo_id=repo_id, count=len(chunks))

    def search_vector_only(self, repo_id: str, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        """Baseline A / B: Pure dense vector search."""
        query_vec = self.embedding_service.embed(query)
        v_results = self.vector_store.search(repo_id, query_vec, top_k=top_k)

        results = []
        for rank, res in enumerate(v_results, start=1):
            meta = res.metadata or {}
            results.append(
                RetrievedChunk(
                    chunk_id=res.chunk_id,
                    file_path=meta.get("file_path", "unknown"),
                    start_line=meta.get("start_line", 1),
                    end_line=meta.get("end_line", 1),
                    content=meta.get("content", ""),
                    chunk_type=meta.get("chunk_type", "code"),
                    score=float(res.score),
                    vector_score=float(res.score),
                    bm25_score=0.0,
                    rank=rank,
                    language=meta.get("language", "text"),
                    metadata=meta,
                )
            )
        return results

    def search_bm25_only(self, repo_id: str, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        """Sparse lexical-only search."""
        bm25 = self._bm25_indices.get(repo_id)
        if not bm25:
            return []

        bm25_results = bm25.search(query, top_k=top_k)
        results = []
        for rank, res in enumerate(bm25_results, start=1):
            meta = res.metadata or {}
            results.append(
                RetrievedChunk(
                    chunk_id=res.chunk_id,
                    file_path=meta.get("file_path", "unknown"),
                    start_line=meta.get("start_line", 1),
                    end_line=meta.get("end_line", 1),
                    content=meta.get("content", ""),
                    chunk_type=meta.get("chunk_type", "code"),
                    score=float(res.score),
                    vector_score=0.0,
                    bm25_score=float(res.score),
                    rank=rank,
                    language=meta.get("language", "text"),
                    metadata=meta,
                )
            )
        return results

    def search_hybrid(
        self,
        repo_id: str,
        query: str,
        top_k: int = 10,
        candidates_k: int = 25,
    ) -> list[RetrievedChunk]:
        """Proposed System: Hybrid dense + sparse search with Reciprocal Rank Fusion."""
        # 1. Retrieve candidates from both sources
        v_results = self.search_vector_only(repo_id, query, top_k=candidates_k)
        b_results = self.search_bm25_only(repo_id, query, top_k=candidates_k)

        # 2. Combine via Reciprocal Rank Fusion (RRF)
        # RRF_score(d) = sum( weight / (k + rank) )
        combined_scores: dict[str, float] = {}
        chunk_map: dict[str, RetrievedChunk] = {}

        for rank, item in enumerate(v_results, start=1):
            rrf_score = self.vector_weight * (1.0 / (self.rrf_k + rank))
            combined_scores[item.chunk_id] = combined_scores.get(item.chunk_id, 0.0) + rrf_score
            chunk_map[item.chunk_id] = item

        for rank, item in enumerate(b_results, start=1):
            rrf_score = self.bm25_weight * (1.0 / (self.rrf_k + rank))
            combined_scores[item.chunk_id] = combined_scores.get(item.chunk_id, 0.0) + rrf_score
            if item.chunk_id in chunk_map:
                chunk_map[item.chunk_id].bm25_score = item.bm25_score
            else:
                chunk_map[item.chunk_id] = item

        # Sort by combined RRF score descending
        sorted_ids = sorted(combined_scores.keys(), key=lambda cid: combined_scores[cid], reverse=True)

        hybrid_candidates: list[RetrievedChunk] = []
        for rank, cid in enumerate(sorted_ids[:candidates_k], start=1):
            chunk = chunk_map[cid]
            chunk.score = combined_scores[cid]
            chunk.rank = rank
            hybrid_candidates.append(chunk)

        # 3. Optional Reranking with CrossEncoder
        if self._reranker is not None and hybrid_candidates:
            pairs = [[query, c.content] for c in hybrid_candidates]
            try:
                rerank_scores = self._reranker.predict(pairs)
                for c, s in zip(hybrid_candidates, rerank_scores):
                    c.score = float(s)
                hybrid_candidates.sort(key=lambda x: x.score, reverse=True)
                for rank, c in enumerate(hybrid_candidates, start=1):
                    c.rank = rank
            except Exception as e:
                logger.error("reranking_execution_failed", error=str(e))

        return hybrid_candidates[:top_k]

    def search(
        self,
        repo_id: str,
        query: str,
        mode: str = "hybrid",
        top_k: int = 10,
    ) -> list[RetrievedChunk]:
        """Unified dispatch method supporting vector, bm25, or hybrid search."""
        mode_lower = mode.lower()
        if mode_lower == "vector":
            return self.search_vector_only(repo_id, query, top_k=top_k)
        elif mode_lower == "bm25":
            return self.search_bm25_only(repo_id, query, top_k=top_k)
        else:
            return self.search_hybrid(repo_id, query, top_k=top_k)
