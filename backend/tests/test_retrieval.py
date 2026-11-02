"""
Unit tests for BM25, Vector Store, and Hybrid Retrieval.
"""

from __future__ import annotations

import pytest
from app.retrieval.bm25_search import BM25Search
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.hybrid_search import HybridRetriever
from app.retrieval.vector_store import VectorStore


def test_bm25_search_scoring() -> None:
    bm25 = BM25Search()
    chunks = [
        {"chunk_id": "c1", "content": "def authenticate_user(username, password): pass", "file_path": "auth.py"},
        {"chunk_id": "c2", "content": "def database_connect(host, port): pass", "file_path": "db.py"},
        {"chunk_id": "c3", "content": "def render_template(template_name): pass", "file_path": "views.py"},
    ]
    bm25.build_index(chunks)

    results = bm25.search("authenticate user", top_k=2)
    assert len(results) > 0
    assert results[0].chunk_id == "c1"
    assert "auth.py" in results[0].metadata["file_path"]


def test_vector_store_in_memory() -> None:
    store = VectorStore(qdrant_url="http://non-existent-host:6333")
    store.create_collection("test_repo", dimension=3)

    import numpy as np
    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ])
    chunks = [
        {"chunk_id": "1", "content": "chunk one"},
        {"chunk_id": "2", "content": "chunk two"},
        {"chunk_id": "3", "content": "chunk three"},
    ]
    store.add_chunks("test_repo", chunks, embeddings)

    query_vec = np.array([0.9, 0.1, 0.0])
    search_res = store.search("test_repo", query_vec, top_k=2)
    assert len(search_res) == 2
    assert search_res[0].chunk_id == "1"


def test_hybrid_retriever() -> None:
    store = VectorStore(qdrant_url="http://non-existent-host:6333")
    embeddings = EmbeddingService()
    retriever = HybridRetriever(
        vector_store=store,
        embedding_service=embeddings,
        bm25_weight=0.5,
        vector_weight=0.5,
    )

    chunks = [
        {
            "chunk_id": "c_jwt",
            "content": "def verify_jwt_token(token): return jwt.decode(token)",
            "file_path": "app/security.py",
            "start_line": 10,
            "end_line": 20,
            "chunk_type": "function",
        },
        {
            "chunk_id": "c_db",
            "content": "def get_db_session(): return SessionLocal()",
            "file_path": "app/database.py",
            "start_line": 30,
            "end_line": 40,
            "chunk_type": "function",
        },
    ]

    retriever.index_repo_chunks("sample_repo", chunks)
    results = retriever.search("sample_repo", "jwt token security", mode="hybrid", top_k=2)

    assert len(results) > 0
    assert results[0].file_path == "app/security.py"
