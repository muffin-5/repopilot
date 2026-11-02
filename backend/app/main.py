"""
RepoPilot – FastAPI Main Application.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.api.agent import router as agent_router
from app.api.chat import router as chat_router
from app.api.evaluation import router as eval_router
from app.api.repos import router as repos_router
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown tasks."""
    settings = get_settings()
    logger.info(
        "repopilot_startup",
        app_name=settings.app_name,
        env=settings.app_env,
        qdrant_url=settings.qdrant_url,
    )
    yield
    logger.info("repopilot_shutdown")


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="RepoPilot API",
        description="Autonomous AI Software Engineering Agent with AST Hybrid RAG & Verification",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS configuration
    origins = settings.cors_origins
    if "*" not in origins:
        origins.extend(["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Routers
    app.include_router(repos_router)
    app.include_router(chat_router)
    app.include_router(agent_router)
    app.include_router(eval_router)

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Service health check."""
        return {"status": "ok", "app": settings.app_name, "version": "1.0.0"}

    @app.get("/", tags=["Root"])
    async def root() -> dict[str, str]:
        """Root API metadata."""
        return {
            "name": "RepoPilot API",
            "docs": "/docs",
            "health": "/health",
            "description": "AI Software Engineering Agent API",
        }

    return app


app = create_app()
