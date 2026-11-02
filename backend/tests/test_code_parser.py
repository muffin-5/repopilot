"""
Unit tests for code chunking (FixedSizeChunker and ASTChunker).
"""

from __future__ import annotations

import pytest
from app.utils.code_parser import ASTChunker, CodeChunk, FixedSizeChunker

SAMPLE_PYTHON_CODE = """
import os
import sys

def calculate_fibonacci(n: int) -> int:
    \"\"\"Return the nth Fibonacci number.\"\"\"
    if n <= 1:
        return n
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)

class DataProcessor:
    \"\"\"Process repository data.\"\"\"
    def __init__(self, name: str):
        self.name = name

    def process_records(self, records: list) -> int:
        count = 0
        for r in records:
            if r is not None:
                count += 1
        return count
"""


def test_fixed_size_chunker() -> None:
    chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.chunk_file(SAMPLE_PYTHON_CODE, "sample.py")

    assert len(chunks) > 0
    for c in chunks:
        assert isinstance(c, CodeChunk)
        assert c.file_path == "sample.py"
        assert c.chunk_type == "fixed"
        assert c.start_line >= 1
        assert c.end_line >= c.start_line
        assert len(c.content) > 0


def test_ast_chunker_extracts_functions_and_classes() -> None:
    chunker = ASTChunker(max_chunk_size=1000)
    chunks = chunker.chunk_file(SAMPLE_PYTHON_CODE, "processor.py")

    assert len(chunks) >= 2
    types = {c.chunk_type for c in chunks}
    assert "function" in types or "class" in types

    func_chunks = [c for c in chunks if "calculate_fibonacci" in c.content]
    assert len(func_chunks) > 0
    assert func_chunks[0].language == "python"
    assert func_chunks[0].start_line > 0
