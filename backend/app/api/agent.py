"""
RepoPilot – Bug Investigation Agent API Router.
"""

from __future__ import annotations

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from app.agents.bug_agent import BugInvestigationAgent
from app.core.dependencies import get_bug_agent, get_repo_service
from app.models.schemas import BugAnalysisResponse, BugReportRequest
from app.services.repo_service import RepoService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/agent", tags=["Agent"])


@router.post("/investigate", response_model=BugAnalysisResponse)
async def investigate_bug(
    request: BugReportRequest,
    agent: BugInvestigationAgent = Depends(get_bug_agent),
    repo_service: RepoService = Depends(get_repo_service),
) -> BugAnalysisResponse:
    """Run autonomous ReAct bug investigation workflow."""
    repo = repo_service.get_repo_status(request.repo_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{request.repo_id}' not found.",
        )

    try:
        return agent.investigate(
            repo_id=request.repo_id,
            bug_description=request.bug_description,
            error_message=request.error_message,
            stack_trace=request.stack_trace,
        )
    except Exception as e:
        logger.error("bug_investigation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent investigation failed: {str(e)}",
        )


@router.get("/tools")
async def list_agent_tools(
    agent: BugInvestigationAgent = Depends(get_bug_agent),
) -> list[dict[str, str]]:
    """List tools available to the bug investigation agent."""
    return agent.get_available_tools()
