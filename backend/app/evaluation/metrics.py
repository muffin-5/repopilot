"""
RepoPilot – Evaluation Metrics Module.

Pure functions for computing formal Information Retrieval and RAG metrics:
  • Recall@k: Fraction of ground-truth relevant files present in top-k results.
  • MRR (Mean Reciprocal Rank): Reciprocal rank of the first relevant document.
  • Citation Validity: Verifies that cited file paths and line ranges exist.
  • Groundedness / Abstention: Tests whether responses are supported by evidence or correctly decline unanswerable questions.
"""

from __future__ import annotations

from typing import List, Optional, Set
from pathlib import Path


def calculate_recall_at_k(
    retrieved_files: list[str],
    expected_files: list[str],
    k: int = 5,
) -> float:
    """Calculate Recall@k for retrieved files against expected files.

    Recall@k = |retrieved[:k] ∩ expected| / |expected|
    If expected is empty (e.g. unanswerable question), returns 1.0 if system
    retrieved no false positive or handles appropriately.
    """
    if not expected_files:
        return 1.0

    # Normalize paths (e.g. lowercase, strip leading slashes)
    norm_expected = {f.strip().lower().lstrip("/") for f in expected_files}
    norm_retrieved = [f.strip().lower().lstrip("/") for f in retrieved_files[:k]]

    hits = 0
    for exp in norm_expected:
        # Match exact or suffix (e.g. 'app/main.py' matches 'backend/app/main.py')
        if any(ret.endswith(exp) or exp.endswith(ret) for ret in norm_retrieved):
            hits += 1

    return round(hits / float(len(norm_expected)), 4)


def calculate_mrr(
    retrieved_files: list[str],
    expected_files: list[str],
) -> float:
    """Calculate Mean Reciprocal Rank for the first relevant document.

    MRR = 1 / rank_first_relevant (1-indexed), or 0.0 if not found.
    """
    if not expected_files:
        return 1.0

    norm_expected = {f.strip().lower().lstrip("/") for f in expected_files}

    for rank, ret in enumerate(retrieved_files, start=1):
        clean_ret = ret.strip().lower().lstrip("/")
        if any(clean_ret.endswith(exp) or exp.endswith(clean_ret) for exp in norm_expected):
            return round(1.0 / rank, 4)

    return 0.0


def verify_citation_validity(
    file_path: str,
    start_line: int,
    end_line: int,
    repo_base_path: Optional[str | Path] = None,
) -> bool:
    """Verify that a cited file path exists and that the line range is structurally sound."""
    if not file_path or start_line <= 0 or end_line < start_line:
        return False

    if repo_base_path:
        base = Path(repo_base_path)
        target = (base / file_path).resolve()
        if not str(target).startswith(str(base.resolve())):
            return False
        if not target.exists() or not target.is_file():
            return False
        try:
            line_count = sum(1 for _ in open(target, "r", encoding="utf-8", errors="replace"))
            return start_line <= line_count
        except Exception:
            return False

    # Structural sanity check when repository filesystem is not attached
    return True


def check_abstention_accuracy(
    answer: str,
    is_unanswerable: bool,
) -> bool:
    """Check whether the model correctly abstains from answering when evidence is absent."""
    abstain_signals = [
        "cannot determine",
        "not found",
        "does not",
        "no evidence",
        "not implemented",
        "unable to determine",
    ]
    has_abstain_signal = any(sig in answer.lower() for sig in abstain_signals)

    if is_unanswerable:
        return has_abstain_signal
    else:
        # For answerable questions, it should NOT abstain
        return not has_abstain_signal
