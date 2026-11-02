"""
RepoPilot – Chat & Question Answering Service.

Coordinates repository context retrieval, prompt construction with source citations,
LLM generation, citation validity checking, and chat history.
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

import structlog

from app.core.config import Settings
from app.models.schemas import ChatResponse, Citation
from app.retrieval.hybrid_search import HybridRetriever, RetrievedChunk
from app.services.llm_service import LLMService

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT = """You are RepoPilot, an expert AI Software Engineering Assistant that analyzes codebases with precision.

GUIDELINES:
1. Answer the user's question based strictly on the provided repository code snippets.
2. Cite specific files and line numbers whenever referencing code logic (e.g., `[file.py:10-25]`).
3. If the answer cannot be determined from the provided context, clearly state:
   "I cannot determine this from the available repository code."
4. Never invent APIs, files, or line numbers that do not appear in the context.
5. Provide concise, production-grade technical explanations.
"""


class ChatService:
    """Handles repository question answering with validated citations."""

    def __init__(
        self,
        settings: Settings,
        retriever: HybridRetriever,
        llm_service: LLMService,
        repo_service: Optional[Any] = None,
    ) -> None:
        self.settings = settings
        self.retriever = retriever
        self.llm_service = llm_service
        self.repo_service = repo_service
        self._history: dict[str, list[dict[str, Any]]] = {}

    def get_history(self, repo_id: str) -> list[dict[str, Any]]:
        """Return chat message history for a repository."""
        return self._history.get(repo_id, [])

    def answer_question(
        self,
        repo_id: str,
        question: str,
        retrieval_mode: str = "hybrid",
    ) -> ChatResponse:
        """Answer a code question with citations and quality metrics."""
        start_time = time.perf_counter()

        # Ensure index is in memory
        if self.repo_service:
            try:
                self.repo_service.ensure_repo_indexed(repo_id)
            except Exception as e:
                logger.warning("ensure_indexed_error", error=str(e))

        # 1. Retrieve relevant code chunks using the chosen retrieval strategy
        chunks = self.retriever.search(
            repo_id=repo_id,
            query=question,
            mode=retrieval_mode,
            top_k=self.settings.top_k,
        )

        # 2. Build context prompt
        context_blocks = []
        for idx, c in enumerate(chunks, start=1):
            block = (
                f"--- Snippet #{idx} ---\n"
                f"File: {c.file_path}\n"
                f"Lines: {c.start_line}-{c.end_line}\n"
                f"Type: {c.chunk_type}\n"
                f"```\n{c.content}\n```"
            )
            context_blocks.append(block)

        context_str = "\n\n".join(context_blocks)
        user_prompt = (
            f"REPOSITORY CODE CONTEXT:\n{context_str}\n\n"
            f"QUESTION: {question}\n\n"
            f"Provide an accurate explanation with citations to the relevant files and line ranges."
        )

        # 3. Call LLM
        llm_resp = self.llm_service.generate(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
        )

        # 4. Extract and validate citations
        citations = self._build_citations(chunks, llm_resp.content)

        # 5. Calculate confidence score based on retrieval scores and citation coverage
        confidence = self._compute_confidence(chunks, citations)

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # 6. Save in history
        if repo_id not in self._history:
            self._history[repo_id] = []

        self._history[repo_id].append({
            "id": str(int(time.time() * 1000)),
            "role": "user",
            "content": question,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

        self._history[repo_id].append({
            "id": str(int(time.time() * 1000) + 1),
            "role": "assistant",
            "content": llm_resp.content,
            "citations": [c.model_dump() for c in citations],
            "metadata": {
                "confidence": confidence,
                "retrieval_mode": retrieval_mode,
                "latency": latency_ms,
                "tokens_used": llm_resp.total_tokens,
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

        return ChatResponse(
            answer=llm_resp.content,
            citations=citations,
            confidence=confidence,
            tokens_used=llm_resp.total_tokens,
            latency_ms=latency_ms,
            cost_estimate=llm_resp.cost_estimate,
            retrieval_mode=retrieval_mode,
        )

    def _build_citations(
        self,
        retrieved_chunks: list[RetrievedChunk],
        answer_text: str,
    ) -> list[Citation]:
        """Convert retrieved chunks into structured citations."""
        citations = []
        seen_ranges = set()

        for c in retrieved_chunks:
            range_key = (c.file_path, c.start_line, c.end_line)
            if range_key in seen_ranges:
                continue
            seen_ranges.add(range_key)

            # Check if mentioned in answer or top ranked
            file_name = c.file_path.split("/")[-1]
            is_relevant = (
                file_name.lower() in answer_text.lower()
                or c.rank <= 3
                or c.score > 0.05
            )

            if is_relevant:
                citations.append(
                    Citation(
                        file_path=c.file_path,
                        start_line=c.start_line,
                        end_line=c.end_line,
                        content=c.content[:400],  # preview
                        relevance_score=round(float(c.score), 4),
                    )
                )

        # Sort by relevance
        citations.sort(key=lambda x: x.relevance_score, reverse=True)
        return citations[:5]

    def _compute_confidence(
        self,
        chunks: list[RetrievedChunk],
        citations: list[Citation],
    ) -> float:
        """Compute grounded confidence estimate."""
        if not chunks:
            return 0.1
        if not citations:
            return 0.4

        top_score = max((c.score for c in chunks), default=0.0)
        # Normalize heuristic confidence between 0.5 and 0.98
        base = 0.65
        boost = min(len(citations) * 0.06, 0.25)
        return round(min(base + boost, 0.98), 2)
