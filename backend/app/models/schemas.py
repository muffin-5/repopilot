"""
Pydantic models for all RepoPilot API request / response types.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Repository ─────────────────────────────────────────────────────────────────


class RepoIngestRequest(BaseModel):
    """Request body for ingesting (cloning + indexing) a repository."""

    repo_url: str = Field(..., description="HTTPS URL of the Git repository to ingest.")
    branch: str = Field("main", description="Branch to clone.")


class RepoIngestResponse(BaseModel):
    """Response after a repository has been ingested."""

    repo_id: str
    status: str
    file_count: int
    chunk_count: int


class RepoStatus(BaseModel):
    """Current status of an indexed repository."""

    repo_id: str
    repo_url: str
    status: str
    file_count: int
    chunk_count: int
    indexed_at: str


# ── Chat / Q&A ─────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    """Request body for asking a question about an indexed repo."""

    repo_id: str
    question: str
    retrieval_mode: str = Field(
        "hybrid",
        description="Retrieval strategy: 'vector', 'bm25', or 'hybrid'.",
    )


class Citation(BaseModel):
    """A citation linking an answer back to a specific code location."""

    file_path: str
    start_line: int
    end_line: int
    content: str
    relevance_score: float


class ChatResponse(BaseModel):
    """Response to a code Q&A request."""

    answer: str
    citations: list[Citation]
    confidence: float
    tokens_used: int
    latency_ms: float
    cost_estimate: float
    retrieval_mode: str


# ── Bug Investigation ──────────────────────────────────────────────────────────


class BugReportRequest(BaseModel):
    """Request body for submitting a bug report for investigation."""

    repo_id: str
    bug_description: str
    error_message: str = ""
    stack_trace: str = ""


class PatchSuggestion(BaseModel):
    """A suggested code patch to fix a bug."""

    file_path: str
    original_code: str
    suggested_code: str
    explanation: str


class BugAnalysisResponse(BaseModel):
    """Response from the bug investigation agent."""

    analysis: str
    relevant_files: list[str]
    suggested_patches: list[PatchSuggestion]
    related_tests: list[str]
    confidence: float


# ── Evaluation ─────────────────────────────────────────────────────────────────


class EvalQuestion(BaseModel):
    """A single evaluation benchmark question."""

    question: str
    expected_files: list[str]
    expected_answer_contains: list[str]
    category: str


class EvalResult(BaseModel):
    """Result of evaluating a single question."""

    question: str
    answer: str
    citations: list[Citation]
    recall_at_5: float
    mrr: float
    citation_valid: bool
    latency_ms: float
    tokens_used: int
    cost: float


class EvalSummary(BaseModel):
    """Aggregated evaluation results."""

    total_questions: int
    avg_recall_at_5: float
    avg_mrr: float
    citation_accuracy: float
    avg_latency_ms: float
    total_tokens: int
    total_cost: float
    by_category: dict


class EvalCompareRequest(BaseModel):
    """Request to compare different retrieval configurations."""

    repo_id: str
    modes: list[str] = Field(
        default=["vector", "bm25", "hybrid"],
        description="Retrieval modes to compare.",
    )
    benchmark_file: str | None = None


class EvalCompareResponse(BaseModel):
    """Side-by-side comparison of retrieval configurations."""

    comparisons: dict[str, EvalSummary]
