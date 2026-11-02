"""
Unit tests for evaluation metrics (Recall@k, MRR, citation validity, abstention).
"""

from __future__ import annotations

import pytest
from app.evaluation.metrics import (
    calculate_mrr,
    calculate_recall_at_k,
    check_abstention_accuracy,
    verify_citation_validity,
)


def test_recall_at_k() -> None:
    expected = ["app/auth.py", "app/main.py"]

    # Both present in top-2
    retrieved_1 = ["app/auth.py", "app/main.py", "app/db.py"]
    assert calculate_recall_at_k(retrieved_1, expected, k=5) == 1.0

    # 1 present in top-5
    retrieved_2 = ["app/auth.py", "app/utils.py", "app/db.py"]
    assert calculate_recall_at_k(retrieved_2, expected, k=5) == 0.5

    # 0 present
    retrieved_3 = ["other/file.py", "tests/test.py"]
    assert calculate_recall_at_k(retrieved_3, expected, k=5) == 0.0


def test_mrr() -> None:
    expected = ["app/services/user_service.py"]

    # Found at rank 1
    r1 = ["app/services/user_service.py", "app/main.py"]
    assert calculate_mrr(r1, expected) == 1.0

    # Found at rank 2
    r2 = ["app/main.py", "app/services/user_service.py"]
    assert calculate_mrr(r2, expected) == 0.5

    # Found at rank 4
    r4 = ["f1.py", "f2.py", "f3.py", "app/services/user_service.py"]
    assert calculate_mrr(r4, expected) == 0.25

    # Not found
    r_none = ["f1.py", "f2.py"]
    assert calculate_mrr(r_none, expected) == 0.0


def test_verify_citation_validity() -> None:
    assert verify_citation_validity("app/main.py", 10, 25) is True
    assert verify_citation_validity("", 10, 25) is False
    assert verify_citation_validity("app/main.py", -1, 10) is False
    assert verify_citation_validity("app/main.py", 20, 10) is False  # end < start


def test_check_abstention_accuracy() -> None:
    unanswerable_ans = "I cannot determine this from the available repository code."
    answerable_ans = "The function is defined in app/auth.py at line 14."

    assert check_abstention_accuracy(unanswerable_ans, is_unanswerable=True) is True
    assert check_abstention_accuracy(answerable_ans, is_unanswerable=True) is False
    assert check_abstention_accuracy(answerable_ans, is_unanswerable=False) is True
    assert check_abstention_accuracy(unanswerable_ans, is_unanswerable=False) is False
