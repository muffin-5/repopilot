"""
RepoPilot Backend - Core Configuration Module.

Manages all application settings using pydantic-settings, loading values
from environment variables and .env files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM & Gemini ───────────────────────────────────────────────────
    LLM_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-3.5-flash-lite"
    LLM_BASE_URL: str = ""

    # ── Embedding ──────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ── Qdrant ─────────────────────────────────────────────────────────
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "repopilot_chunks"

    # ── Chunking ───────────────────────────────────────────────────────
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64

    # ── Retrieval ──────────────────────────────────────────────────────
    TOP_K: int = 10
    BM25_WEIGHT: float = 0.4
    VECTOR_WEIGHT: float = 0.6
    USE_RERANKER: bool = False

    # ── Application ────────────────────────────────────────────────────
    APP_NAME: str = "RepoPilot"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    MAX_REPO_SIZE_MB: int = 500
    DATA_DIR: str = "./data"

    @property
    def app_name(self) -> str:
        return self.APP_NAME

    @property
    def app_env(self) -> str:
        return self.APP_ENV

    @property
    def is_gemini(self) -> bool:
        return (
            bool(self.GEMINI_API_KEY)
            or self.LLM_MODEL.lower().startswith("gemini")
            or self.LLM_API_KEY.startswith("AIza")
        )

    @property
    def gemini_api_key(self) -> str:
        return self.GEMINI_API_KEY

    @property
    def llm_api_key(self) -> str:
        return self.GEMINI_API_KEY or self.LLM_API_KEY

    @property
    def llm_model(self) -> str:
        if self.GEMINI_API_KEY and not self.LLM_MODEL.lower().startswith("gemini"):
            return "gemini-1.5-flash"
        return self.LLM_MODEL

    @property
    def llm_base_url(self) -> str:
        if self.LLM_BASE_URL:
            return self.LLM_BASE_URL
        if self.is_gemini:
            return "https://generativelanguage.googleapis.com/v1beta/openai/"
        return "https://api.openai.com/v1"

    @property
    def embedding_model(self) -> str:
        return self.EMBEDDING_MODEL

    @property
    def qdrant_url(self) -> str:
        return self.QDRANT_URL

    @property
    def qdrant_collection(self) -> str:
        return self.QDRANT_COLLECTION

    @property
    def chunk_size(self) -> int:
        return self.CHUNK_SIZE

    @property
    def chunk_overlap(self) -> int:
        return self.CHUNK_OVERLAP

    @property
    def top_k(self) -> int:
        return self.TOP_K

    @property
    def bm25_weight(self) -> float:
        return self.BM25_WEIGHT

    @property
    def vector_weight(self) -> float:
        return self.VECTOR_WEIGHT

    @property
    def use_reranker(self) -> bool:
        return self.USE_RERANKER

    @property
    def log_level(self) -> str:
        return self.LOG_LEVEL

    @property
    def cors_origins(self) -> List[str]:
        return self.CORS_ORIGINS

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list) -> list:
        """Parse CORS_ORIGINS from JSON string or list."""
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def data_path(self) -> Path:
        """Return the resolved data directory path, creating it if needed."""
        p = Path(self.DATA_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def repos_path(self) -> Path:
        """Return the path where cloned repos are stored."""
        p = self.data_path / "repos"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def metadata_path(self) -> Path:
        """Return the path to the repos metadata JSON file."""
        return self.data_path / "repos_metadata.json"

    @property
    def eval_results_path(self) -> Path:
        """Return the path to evaluation results directory."""
        p = self.data_path / "eval_results"
        p.mkdir(parents=True, exist_ok=True)
        return p


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
