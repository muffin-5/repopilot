"""
RepoPilot – FastAPI Dependencies and Service Registry.

Manages application lifecycle and singleton service instances with proper
dependency injection.
"""

from __future__ import annotations

from typing import Optional

import structlog

from app.agents.bug_agent import BugInvestigationAgent
from app.core.config import Settings, get_settings
from app.evaluation.benchmark import BenchmarkRunner
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.hybrid_search import HybridRetriever
from app.retrieval.vector_store import VectorStore
from app.services.chat_service import ChatService
from app.services.llm_service import LLMService
from app.services.repo_service import RepoService

logger = structlog.get_logger(__name__)

# Global singletons
_settings: Optional[Settings] = None
_embeddings: Optional[EmbeddingService] = None
_vector_store: Optional[VectorStore] = None
_retriever: Optional[HybridRetriever] = None
_llm_service: Optional[LLMService] = None
_repo_service: Optional[RepoService] = None
_chat_service: Optional[ChatService] = None
_bug_agent: Optional[BugInvestigationAgent] = None
_benchmark_runner: Optional[BenchmarkRunner] = None


def get_app_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings


def get_embedding_service() -> EmbeddingService:
    global _embeddings
    if _embeddings is None:
        settings = get_app_settings()
        _embeddings = EmbeddingService(model_name=settings.embedding_model)
    return _embeddings


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        settings = get_app_settings()
        _vector_store = VectorStore(
            qdrant_url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
        )
    return _vector_store


def get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        settings = get_app_settings()
        _retriever = HybridRetriever(
            vector_store=get_vector_store(),
            embedding_service=get_embedding_service(),
            bm25_weight=settings.bm25_weight,
            vector_weight=settings.vector_weight,
            use_reranker=settings.use_reranker,
        )
    return _retriever


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        settings = get_app_settings()
        _llm_service = LLMService(settings=settings)
    return _llm_service


def get_repo_service() -> RepoService:
    global _repo_service
    if _repo_service is None:
        settings = get_app_settings()
        _repo_service = RepoService(
            settings=settings,
            retriever=get_retriever(),
        )
    return _repo_service


def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        settings = get_app_settings()
        _chat_service = ChatService(
            settings=settings,
            retriever=get_retriever(),
            llm_service=get_llm_service(),
            repo_service=get_repo_service(),
        )
    return _chat_service


def get_bug_agent() -> BugInvestigationAgent:
    global _bug_agent
    if _bug_agent is None:
        settings = get_app_settings()
        _bug_agent = BugInvestigationAgent(
            settings=settings,
            retriever=get_retriever(),
            llm_service=get_llm_service(),
        )
    return _bug_agent


def get_benchmark_runner() -> BenchmarkRunner:
    global _benchmark_runner
    if _benchmark_runner is None:
        settings = get_app_settings()
        _benchmark_runner = BenchmarkRunner(
            settings=settings,
            retriever=get_retriever(),
            chat_service=get_chat_service(),
        )
    return _benchmark_runner
