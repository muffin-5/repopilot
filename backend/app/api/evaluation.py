"""
RepoPilot – Evaluation & Quality Dashboard API Router.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from app.core.dependencies import get_app_settings, get_benchmark_runner, get_repo_service
from app.evaluation.benchmark import BenchmarkRunner
from app.models.schemas import (
    EvalCompareRequest,
    EvalCompareResponse,
    EvalResult,
    EvalSummary,
)
from app.services.repo_service import RepoService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/eval", tags=["Evaluation"])


@router.post("/run")
async def run_evaluation(
    payload: dict[str, Any],
    benchmark_runner: BenchmarkRunner = Depends(get_benchmark_runner),
    repo_service: RepoService = Depends(get_repo_service),
) -> dict[str, Any]:
    """Run evaluation benchmark across one or more retrieval modes."""
    repo_id = payload.get("repo_id")
    benchmark_file = payload.get("benchmark_file")
    retrieval_modes = payload.get("retrieval_modes", ["hybrid"])

    if not repo_id:
        raise HTTPException(status_code=400, detail="Missing 'repo_id' in payload.")

    repo = repo_service.get_repo_status(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository '{repo_id}' not found.")

    summaries = {}
    detailed_results = {}

    for mode in retrieval_modes:
        summary, results = benchmark_runner.run_evaluation(
            repo_id=repo_id,
            retrieval_mode=mode,
            benchmark_file=benchmark_file,
        )
        summaries[mode] = summary.model_dump()
        detailed_results[mode] = [r.model_dump() for r in results]

    return {
        "repo_id": repo_id,
        "modes": retrieval_modes,
        "summaries": summaries,
        "results": detailed_results,
    }


@router.post("/compare", response_model=EvalCompareResponse)
async def compare_retrieval_configurations(
    request: EvalCompareRequest,
    benchmark_runner: BenchmarkRunner = Depends(get_benchmark_runner),
    repo_service: RepoService = Depends(get_repo_service),
) -> EvalCompareResponse:
    """Run systematic comparison between vector-only, BM25, and hybrid retrieval."""
    repo = repo_service.get_repo_status(request.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository '{request.repo_id}' not found.")

    comparisons = benchmark_runner.compare_configurations(
        repo_id=request.repo_id,
        modes=request.modes,
        benchmark_file=request.benchmark_file,
    )
    return EvalCompareResponse(comparisons=comparisons)


@router.get("/results")
async def list_evaluation_results(
    settings=Depends(get_app_settings),
) -> list[dict[str, Any]]:
    """List historical benchmark evaluation runs stored on disk."""
    results_dir = settings.eval_results_path
    if not results_dir.exists():
        return []

    runs = []
    for p in sorted(results_dir.glob("*.json"), reverse=True):
        try:
            with open(p, "r", encoding="utf-8") as f:
                runs.append(json.load(f))
        except Exception:
            pass
    return runs
