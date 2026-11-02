"""
RepoPilot – BM25 Lexical Search Module.

Provides BM25Okapi-based sparse retrieval tailored for source code:
  • Code-aware tokenisation (camelCase, snake_case, identifiers).
  • In-memory index per repository with serialization capability.
  • Return ranked results with score and provenance metadata.
"""

from __future__ import annotations

import math
import pickle
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# Tokenization regex for code: splits identifiers, numbers, operators
_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+|[^\s\w]")
_CAMEL_RE = re.compile(r"([a-z])([A-Z])")


def tokenize_code(text: str) -> list[str]:
    """Tokenize source code into searchable terms.

    Splits camelCase, snake_case, and keeps symbols to support exact code lookups.
    """
    # Split camelCase: "getUserById" -> "get User By Id"
    expanded = _CAMEL_RE.sub(r"\1 \2", text)
    # Split snake_case: "get_user_by_id" -> "get user by id"
    expanded = expanded.replace("_", " ")

    tokens = []
    for match in _IDENTIFIER_RE.finditer(expanded.lower()):
        token = match.group().strip()
        if len(token) > 1 or token.isalnum():
            tokens.append(token)
    return tokens


@dataclass
class BM25SearchResult:
    """A single result from BM25 search."""

    chunk_id: str
    score: float
    metadata: dict[str, Any]


class BM25Search:
    """In-memory BM25 index with fallback implementation."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.corpus_chunks: list[dict[str, Any]] = []
        self.tokenized_corpus: list[list[str]] = []
        self.doc_lengths: list[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self._bm25_okapi: Any = None
        self._use_rank_bm25 = False

        # Attempt to import rank-bm25
        try:
            from rank_bm25 import BM25Okapi
            self._bm25_cls = BM25Okapi
            self._use_rank_bm25 = True
        except ImportError:
            logger.warning("rank_bm25_not_found_using_fallback")
            self._use_rank_bm25 = False

    def build_index(self, chunks: list[dict[str, Any]]) -> None:
        """Build BM25 index from chunk dictionaries.

        Each chunk dict should contain at least:
          - chunk_id: str
          - content: str
          - (optional metadata fields)
        """
        self.corpus_chunks = chunks
        self.tokenized_corpus = [tokenize_code(c.get("content", "")) for c in chunks]
        self.doc_lengths = [len(doc) for doc in self.tokenized_corpus]
        total_len = sum(self.doc_lengths)
        num_docs = len(chunks)

        if num_docs == 0:
            self.avg_doc_len = 0.0
            return

        self.avg_doc_len = total_len / num_docs

        if self._use_rank_bm25 and num_docs > 0:
            self._bm25_okapi = self._bm25_cls(self.tokenized_corpus)
        else:
            # Fallback pure-python BM25
            self.doc_freqs = {}
            for doc in self.tokenized_corpus:
                seen = set(doc)
                for term in seen:
                    self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

            self.idf = {}
            for term, freq in self.doc_freqs.items():
                self.idf[term] = math.log((num_docs - freq + 0.5) / (freq + 0.5) + 1.0)

        logger.info("bm25_index_built", chunk_count=num_docs)

    def search(self, query: str, top_k: int = 10) -> list[BM25SearchResult]:
        """Search the BM25 index for matching code chunks."""
        if not self.corpus_chunks:
            return []

        query_tokens = tokenize_code(query)
        if not query_tokens:
            return []

        if self._use_rank_bm25 and self._bm25_okapi is not None:
            raw_scores = self._bm25_okapi.get_scores(query_tokens)
            indexed_scores = list(enumerate(raw_scores))
        else:
            indexed_scores = []
            for idx, doc in enumerate(self.tokenized_corpus):
                score = 0.0
                doc_len = self.doc_lengths[idx]
                term_counts: dict[str, int] = {}
                for t in doc:
                    term_counts[t] = term_counts.get(t, 0) + 1

                for q in query_tokens:
                    if q not in term_counts:
                        continue
                    tf = term_counts[q]
                    idf = self.idf.get(q, 0.0)
                    denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
                    score += idf * (tf * (self.k1 + 1.0)) / denom
                indexed_scores.append((idx, score))

        # Sort descending by score
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        top_results = indexed_scores[:top_k]

        results = []
        for idx, score in top_results:
            if score <= 0.0 and len(top_results) > 1:
                continue
            chunk = self.corpus_chunks[idx]
            results.append(
                BM25SearchResult(
                    chunk_id=chunk.get("chunk_id", str(idx)),
                    score=float(score),
                    metadata=chunk,
                )
            )
        return results

    def save(self, file_path: str | Path) -> None:
        """Serialize index to disk."""
        data = {
            "corpus_chunks": self.corpus_chunks,
            "tokenized_corpus": self.tokenized_corpus,
            "doc_lengths": self.doc_lengths,
            "avg_doc_len": self.avg_doc_len,
            "doc_freqs": self.doc_freqs,
            "idf": self.idf,
        }
        with open(file_path, "wb") as f:
            pickle.dump(data, f)

    def load(self, file_path: str | Path) -> None:
        """Load serialized index from disk."""
        with open(file_path, "rb") as f:
            data = pickle.load(f)
        self.corpus_chunks = data["corpus_chunks"]
        self.tokenized_corpus = data["tokenized_corpus"]
        self.doc_lengths = data["doc_lengths"]
        self.avg_doc_len = data["avg_doc_len"]
        self.doc_freqs = data.get("doc_freqs", {})
        self.idf = data.get("idf", {})
        if self._use_rank_bm25 and len(self.tokenized_corpus) > 0:
            self._bm25_okapi = self._bm25_cls(self.tokenized_corpus)
