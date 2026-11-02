"""
RepoPilot – Embedding Service.

Wraps sentence-transformers (``all-MiniLM-L6-v2`` by default) with
scikit-learn TF-IDF fallback, and a pure Python/NumPy hash vectorizer fallback
for zero-dependency runtime resilience.
"""

from __future__ import annotations

import hashlib
import re
from typing import List, Union

import numpy as np
import structlog

logger = structlog.get_logger(__name__)

_WORD_RE = re.compile(r"\b\w+\b")


class EmbeddingService:
    """Compute dense vector embeddings for text chunks."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None
        self._tfidf = None
        self._use_tfidf = False
        self._use_hashing = False
        self._dimension: int = 384
        self._load_model()

    def _load_model(self) -> None:
        """Try to load sentence-transformers; fall back to TF-IDF or NumPy hashing."""
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer(self.model_name)
            test = self._model.encode(["test"], show_progress_bar=False)
            self._dimension = test.shape[1]
            logger.info("embedding_model_loaded", model=self.model_name, dimension=self._dimension)
        except Exception as exc:
            logger.warning("sentence_transformers_unavailable_trying_tfidf", error=str(exc))
            self._init_tfidf_fallback()

    def _init_tfidf_fallback(self) -> None:
        """Initialise scikit-learn TF-IDF, or fall back to pure NumPy hashing."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore

            self._tfidf = TfidfVectorizer(max_features=384)
            self._dimension = 384
            self._tfidf_fitted = False
            self._use_tfidf = True
            logger.info("tfidf_fallback_initialised", dimension=self._dimension)
        except Exception as exc:
            logger.warning("sklearn_unavailable_using_numpy_hashing", error=str(exc))
            self._use_hashing = True
            self._dimension = 384

    @property
    def dimension(self) -> int:
        """Return the embedding vector dimension."""
        return self._dimension

    def embed(self, texts: Union[str, list[str]]) -> np.ndarray:
        """Embed text(s) into an (N, D) numpy array, or (D,) if single string."""
        single_input = isinstance(texts, str)
        text_list = [texts] if single_input else list(texts)

        if not text_list:
            res = np.empty((0, self.dimension), dtype=np.float32)
            return res[0] if single_input else res

        if self._model is not None:
            vecs = self._embed_transformer(text_list)
        elif self._use_tfidf and self._tfidf is not None:
            vecs = self._embed_tfidf(text_list)
        else:
            vecs = self._embed_hashing(text_list)

        return vecs[0] if single_input else vecs

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Batch embedding interface."""
        return self.embed(texts)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string into a 1-D numpy vector."""
        return self.embed(query)

    def _embed_transformer(self, texts: list[str]) -> np.ndarray:
        try:
            embeddings = self._model.encode(
                texts,
                show_progress_bar=False,
                batch_size=64,
                normalize_embeddings=True,
            )
            return np.asarray(embeddings, dtype=np.float32)
        except Exception as exc:
            logger.error("transformer_embed_failed", error=str(exc))
            return self._embed_hashing(texts)

    def _embed_tfidf(self, texts: list[str]) -> np.ndarray:
        assert self._tfidf is not None
        if not self._tfidf_fitted:
            self._tfidf.fit(texts)
            self._tfidf_fitted = True

        try:
            matrix = self._tfidf.transform(texts).toarray().astype(np.float32)
        except Exception:
            self._tfidf.fit(texts)
            matrix = self._tfidf.transform(texts).toarray().astype(np.float32)

        d = self._dimension
        if matrix.shape[1] < d:
            pad = np.zeros((matrix.shape[0], d - matrix.shape[1]), dtype=np.float32)
            matrix = np.hstack([matrix, pad])
        elif matrix.shape[1] > d:
            matrix = matrix[:, :d]

        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return matrix / norms

    def _embed_hashing(self, texts: list[str]) -> np.ndarray:
        """Deterministic pure NumPy feature hashing vectorizer."""
        d = self._dimension
        matrix = np.zeros((len(texts), d), dtype=np.float32)

        for row_idx, text in enumerate(texts):
            tokens = _WORD_RE.findall(text.lower())
            if not tokens:
                continue
            for tok in tokens:
                h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
                idx = h % d
                sign = 1.0 if (h // d) % 2 == 0 else -1.0
                matrix[row_idx, idx] += sign

        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return matrix / norms
