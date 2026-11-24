"""Tests for conversational follow-up handling in ChatService."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.chat_service import ChatService


class _Retriever:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, **kwargs):  # type: ignore[no-untyped-def]
        self.queries.append(kwargs["query"])
        return []


class _LLM:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str, **kwargs):  # type: ignore[no-untyped-def]
        self.prompts.append(prompt)
        return SimpleNamespace(
            content="Grounded answer.",
            total_tokens=10,
            cost_estimate=0.0,
        )


def test_follow_up_uses_previous_topic_for_retrieval_and_prompt() -> None:
    retriever = _Retriever()
    llm = _LLM()
    service = ChatService(
        settings=SimpleNamespace(top_k=5),
        retriever=retriever,
        llm_service=llm,
    )
    service._history["repo"] = [
        {"role": "user", "content": "How does hybrid retrieval work?"},
        {"role": "assistant", "content": "It combines BM25 and vectors."},
    ]

    service.answer_question("repo", "Explain in detail")

    assert "How does hybrid retrieval work?" in retriever.queries[0]
    assert "RECENT CONVERSATION" in llm.prompts[0]
    assert "It combines BM25 and vectors." in llm.prompts[0]


def test_new_question_does_not_inherit_an_unrelated_topic() -> None:
    retriever = _Retriever()
    llm = _LLM()
    service = ChatService(
        settings=SimpleNamespace(top_k=5),
        retriever=retriever,
        llm_service=llm,
    )
    service._history["repo"] = [
        {"role": "user", "content": "How does hybrid retrieval work?"},
        {"role": "assistant", "content": "It combines BM25 and vectors."},
    ]

    service.answer_question("repo", "How does AST chunking work?")

    assert retriever.queries == ["How does AST chunking work?"]
    assert "RECENT CONVERSATION" not in llm.prompts[0]
