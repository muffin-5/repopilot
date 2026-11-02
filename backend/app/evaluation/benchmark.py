"""
RepoPilot – Evaluation Benchmark Runner.

Executes quantitative evaluations against test sets, measures Recall@5, MRR,
citation validity, latency, and cost across different retrieval configurations.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from app.core.config import Settings
from app.evaluation.metrics import (
    calculate_mrr,
    calculate_recall_at_k,
    check_abstention_accuracy,
    verify_citation_validity,
)
from app.models.schemas import Citation, EvalQuestion, EvalResult, EvalSummary
from app.retrieval.hybrid_search import HybridRetriever
from app.services.chat_service import ChatService

logger = structlog.get_logger(__name__)


class BenchmarkRunner:
    """Executes benchmarks and compiles comparative evaluation reports."""

    def __init__(
        self,
        settings: Settings,
        retriever: HybridRetriever,
        chat_service: ChatService,
    ) -> None:
        self.settings = settings
        self.retriever = retriever
        self.chat_service = chat_service

    def load_benchmark_questions(self, file_path: str | Path | None = None) -> list[EvalQuestion]:
        """Load benchmark questions from JSON file."""
        if file_path is None:
            # Try default sample locations
            candidates = [
                self.settings.data_path.parent / "evaluation" / "benchmarks" / "sample_benchmark.json",
                Path("/home/muffin/Desktop/advance_se_project/repopilot/evaluation/benchmarks/sample_benchmark.json"),
                Path(__file__).parent / "sample_benchmark.json",
            ]
            for c in candidates:
                if c.exists():
                    file_path = c
                    break

        if file_path is None or not Path(file_path).exists():
            # Return built-in default benchmark questions if file not found
            return [
                EvalQuestion(
                    question="Where is the user authentication function defined?",
                    expected_files=["app/auth.py", "app/services/auth_service.py"],
                    expected_answer_contains=["authenticate", "login"],
                    category="function_location",
                ),
                EvalQuestion(
                    question="What middleware is used in this project?",
                    expected_files=["app/middleware.py", "app/main.py"],
                    expected_answer_contains=["middleware"],
                    category="architecture",
                ),
                EvalQuestion(
                    question="How does GraphQL subscription work in this codebase?",
                    expected_files=[],
                    expected_answer_contains=["cannot", "not found"],
                    category="unanswerable",
                ),
            ]

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_questions = data.get("questions", [])
        questions = []
        for q in raw_questions:
            questions.append(
                EvalQuestion(
                    question=q.get("question", ""),
                    expected_files=q.get("expected_files", []),
                    expected_answer_contains=q.get("expected_answer_contains", []),
                    category=q.get("category", "general"),
                )
            )
        return questions

    def run_evaluation(
        self,
        repo_id: str,
        retrieval_mode: str = "hybrid",
        benchmark_file: str | None = None,
    ) -> tuple[EvalSummary, list[EvalResult]]:
        """Run full evaluation suite for a repository under a specific retrieval mode."""
        questions = self.load_benchmark_questions(benchmark_file)
        results: list[EvalResult] = []

        logger.info(
            "running_evaluation_benchmark",
            repo_id=repo_id,
            mode=retrieval_mode,
            question_count=len(questions),
        )

        category_stats: dict[str, dict[str, float]] = {}

        total_recall = 0.0
        total_mrr = 0.0
        valid_citations_count = 0
        total_citations = 0
        total_latency = 0.0
        total_tokens = 0
        total_cost = 0.0

        for q in questions:
            # 1. Measure retrieval directly
            retrieved = self.retriever.search(
                repo_id=repo_id,
                query=q.question,
                mode=retrieval_mode,
                top_k=5,
            )
            retrieved_files = [c.file_path for c in retrieved]

            recall = calculate_recall_at_k(retrieved_files, q.expected_files, k=5)
            mrr = calculate_mrr(retrieved_files, q.expected_files)

            # 2. Get answer from chat service
            chat_resp = self.chat_service.answer_question(
                repo_id=repo_id,
                question=q.question,
                retrieval_mode=retrieval_mode,
            )

            # 3. Check citations validity
            cit_valid = True
            for cit in chat_resp.citations:
                total_citations += 1
                if verify_citation_validity(cit.file_path, cit.start_line, cit.end_line):
                    valid_citations_count += 1
                else:
                    cit_valid = False

            total_recall += recall
            total_mrr += mrr
            total_latency += chat_resp.latency_ms
            total_tokens += chat_resp.tokens_used
            total_cost += chat_resp.cost_estimate

            # Record category stats
            cat = q.category
            if cat not in category_stats:
                category_stats[cat] = {"count": 0, "recall": 0.0, "mrr": 0.0}
            category_stats[cat]["count"] += 1
            category_stats[cat]["recall"] += recall
            category_stats[cat]["mrr"] += mrr

            eval_res = EvalResult(
                question=q.question,
                answer=chat_resp.answer[:300],
                citations=chat_resp.citations,
                recall_at_5=recall,
                mrr=mrr,
                citation_valid=cit_valid,
                latency_ms=chat_resp.latency_ms,
                tokens_used=chat_resp.tokens_used,
                cost=chat_resp.cost_estimate,
            )
            results.append(eval_res)

        n = max(1, len(questions))
        avg_recall = round(total_recall / n, 4)
        avg_mrr = round(total_mrr / n, 4)
        cit_acc = round(valid_citations_count / max(1, total_citations), 4)
        avg_latency = round(total_latency / n, 2)

        # Average category scores
        by_category_summary = {}
        for cat, data in category_stats.items():
            cnt = max(1, int(data["count"]))
            by_category_summary[cat] = {
                "recall_at_5": round(data["recall"] / cnt, 4),
                "mrr": round(data["mrr"] / cnt, 4),
                "sample_count": cnt,
            }

        summary = EvalSummary(
            total_questions=len(questions),
            avg_recall_at_5=avg_recall,
            avg_mrr=avg_mrr,
            citation_accuracy=cit_acc,
            avg_latency_ms=avg_latency,
            total_tokens=total_tokens,
            total_cost=round(total_cost, 6),
            by_category=by_category_summary,
        )

        # Save result JSON
        self._save_results(repo_id, retrieval_mode, summary, results)

        return summary, results

    def compare_configurations(
        self,
        repo_id: str,
        modes: list[str] = ["vector", "bm25", "hybrid"],
        benchmark_file: str | None = None,
    ) -> dict[str, EvalSummary]:
        """Run comparison across multiple retrieval modes for research ablation study."""
        comparisons: dict[str, EvalSummary] = {}
        for m in modes:
            summary, _ = self.run_evaluation(
                repo_id=repo_id,
                retrieval_mode=m,
                benchmark_file=benchmark_file,
            )
            comparisons[m] = summary
        return comparisons

    def _save_results(
        self,
        repo_id: str,
        mode: str,
        summary: EvalSummary,
        results: list[EvalResult],
    ) -> None:
        """Write evaluation results to disk."""
        out_dir = self.settings.eval_results_path
        out_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{repo_id}_{mode}_{int(time.time())}.json"
        data = {
            "repo_id": repo_id,
            "mode": mode,
            "summary": summary.model_dump(),
            "results": [r.model_dump() for r in results],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        with open(out_dir / fname, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
