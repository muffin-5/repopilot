"""
RepoPilot – Repositories API Router.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from app.core.dependencies import get_repo_service
from app.models.schemas import RepoIngestRequest, RepoIngestResponse, RepoStatus
from app.services.repo_service import RepoService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/repos", tags=["Repositories"])


@router.post("/ingest", response_model=RepoIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_repository(
    request: RepoIngestRequest,
    repo_service: RepoService = Depends(get_repo_service),
) -> RepoIngestResponse:
    """Ingest, parse, and index a Git repository or local codebase."""
    try:
        status_res = repo_service.ingest_repo(
            repo_url=request.repo_url,
            branch=request.branch,
        )
        return RepoIngestResponse(
            repo_id=status_res.repo_id,
            status=status_res.status,
            file_count=status_res.file_count,
            chunk_count=status_res.chunk_count,
        )
    except Exception as e:
        logger.error("api_ingest_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest repository: {str(e)}",
        )


@router.get("", response_model=list[RepoStatus])
async def list_repositories(
    repo_service: RepoService = Depends(get_repo_service),
) -> list[RepoStatus]:
    """List all ingested repositories."""
    return repo_service.list_repos()


@router.get("/{repo_id}/status", response_model=RepoStatus)
async def get_repository_status(
    repo_id: str,
    repo_service: RepoService = Depends(get_repo_service),
) -> RepoStatus:
    """Get indexing status and metrics for a repository."""
    repo = repo_service.get_repo_status(repo_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found.",
        )
    return repo


@router.delete("/{repo_id}", status_code=status.HTTP_200_OK)
async def delete_repository(
    repo_id: str,
    repo_service: RepoService = Depends(get_repo_service),
) -> dict[str, str]:
    """Delete a repository and its vector/BM25 index."""
    success = repo_service.delete_repo(repo_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found.",
        )
    return {"message": f"Repository '{repo_id}' deleted successfully."}
