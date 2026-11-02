"""
RepoPilot – Chat API Router.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from app.core.dependencies import get_chat_service, get_repo_service
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.repo_service import RepoService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
    repo_service: RepoService = Depends(get_repo_service),
) -> ChatResponse:
    """Ask a question about an indexed codebase with citations and quality tracking."""
    repo = repo_service.get_repo_status(request.repo_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{request.repo_id}' not found.",
        )

    try:
        return chat_service.answer_question(
            repo_id=request.repo_id,
            question=request.question,
            retrieval_mode=request.retrieval_mode,
        )
    except Exception as e:
        logger.error("chat_generation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}",
        )


@router.get("/history/{repo_id}")
async def get_chat_history(
    repo_id: str,
    chat_service: ChatService = Depends(get_chat_service),
) -> dict[str, Any]:
    """Retrieve conversation history for a given repository."""
    history = chat_service.get_history(repo_id)
    return {"repo_id": repo_id, "messages": history}
