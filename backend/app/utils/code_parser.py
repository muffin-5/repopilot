"""
RepoPilot – Code Parsing & Chunking Module.

Provides two chunking strategies:
  • FixedSizeChunker  – simple sliding-window chunks (Baseline A).
  • ASTChunker        – AST-aware or regex-fallback function/class level chunks
                        (Baseline B / Proposed System).

Both produce `CodeChunk` dataclass instances with full provenance metadata.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# ── Language map ───────────────────────────────────────────────────────────────

EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".cc": "cpp",
    ".hpp": "cpp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".cs": "csharp",
}

SUPPORTED_EXTENSIONS: set[str] = set(EXTENSION_LANGUAGE_MAP.keys())


# ── Data model ─────────────────────────────────────────────────────────────────


@dataclass
class CodeChunk:
    """A single chunk of source code with provenance metadata."""

    content: str
    file_path: str
    start_line: int
    end_line: int
    chunk_type: str  # "function", "class", "method", "module", "fixed"
    language: str
    metadata: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        """Return a deterministic identifier for this chunk."""
        return f"{self.file_path}:{self.start_line}-{self.end_line}"

    def __len__(self) -> int:
        return len(self.content)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixed-Size Chunker (Baseline A)
# ═══════════════════════════════════════════════════════════════════════════════


class FixedSizeChunker:
    """Split source files into overlapping fixed-size character chunks."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        """
        Args:
            chunk_size: Maximum number of characters per chunk.
            chunk_overlap: Number of overlapping characters between consecutive chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_file(self, content: str, file_path: str) -> list[CodeChunk]:
        """Split *content* into fixed-size chunks, tracking line numbers.

        Args:
            content: The full text of the source file.
            file_path: Path (relative or absolute) used for provenance.

        Returns:
            A list of ``CodeChunk`` objects.
        """
        if not content.strip():
            return []

        language = _detect_language(file_path)
        lines = content.split("\n")
        chunks: list[CodeChunk] = []

        step = max(self.chunk_size - self.chunk_overlap, 1)
        pos = 0
        while pos < len(content):
            end = min(pos + self.chunk_size, len(content))
            chunk_text = content[pos:end]

            start_line = content[:pos].count("\n") + 1
            end_line = content[:end].count("\n") + 1

            chunks.append(
                CodeChunk(
                    content=chunk_text,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    chunk_type="fixed",
                    language=language,
                    metadata={"chunk_size": self.chunk_size},
                )
            )

            if end >= len(content):
                break
            pos += step

        return chunks


# ═══════════════════════════════════════════════════════════════════════════════
# AST / Regex Chunker (Baseline B & Proposed System)
# ═══════════════════════════════════════════════════════════════════════════════


class ASTChunker:
    """
    AST-aware code chunker.

    Tries to use tree-sitter for parsing; falls back to a regex-based
    heuristic that recognises function/class boundaries for many languages.
    """

    def __init__(self, max_chunk_size: int = 2048, overlap: int = 64, **kwargs: Any) -> None:
        """
        Args:
            max_chunk_size: If a single AST node exceeds this, it will be
                            sub-chunked with a FixedSizeChunker.
            overlap: Overlap for fixed-size sub-chunking.
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self._ts_available = _check_tree_sitter_available()
        self._fixed_chunker = FixedSizeChunker(chunk_size=max_chunk_size, chunk_overlap=overlap)

    # ── public API ─────────────────────────────────────────────────────

    def chunk_file(self, content: str, file_path: str) -> list[CodeChunk]:
        """Parse a source file and return function/class-level chunks.

        Args:
            content: Full file text.
            file_path: Path for provenance metadata.

        Returns:
            List of ``CodeChunk`` objects.
        """
        if not content.strip():
            return []

        language = _detect_language(file_path)

        # Try tree-sitter first
        if self._ts_available:
            try:
                chunks = self._chunk_with_tree_sitter(content, file_path, language)
                if chunks:
                    return chunks
            except Exception as exc:
                logger.warning(
                    "tree_sitter_failed_falling_back_to_regex",
                    file=file_path,
                    error=str(exc),
                )

        # Fallback: regex-based parser
        return self._chunk_with_regex(content, file_path, language)

    # ── tree-sitter implementation ─────────────────────────────────────

    def _chunk_with_tree_sitter(
        self, content: str, file_path: str, language: str
    ) -> list[CodeChunk]:
        """Use tree-sitter to extract function/class AST nodes."""
        try:
            from tree_sitter import Language, Parser  # type: ignore

            parser = Parser()
            ts_lang = _get_tree_sitter_language(language)
            if ts_lang is None:
                return []

            parser.set_language(ts_lang)
            tree = parser.parse(content.encode("utf-8"))

            node_types = _ast_node_types_for_language(language)
            chunks: list[CodeChunk] = []
            self._walk_tree(tree.root_node, content, file_path, language, node_types, chunks)

            # Add module-level code between AST nodes
            chunks = self._add_module_level_code(content, file_path, language, chunks)
            return chunks
        except Exception:
            return []

    def _walk_tree(
        self,
        node,
        content: str,
        file_path: str,
        language: str,
        node_types: set[str],
        chunks: list[CodeChunk],
    ) -> None:
        """Recursively walk a tree-sitter parse tree to extract chunks."""
        if node.type in node_types:
            start = node.start_point[0]
            end = node.end_point[0]
            lines = content.split("\n")
            chunk_text = "\n".join(lines[start: end + 1])

            chunk_type = _classify_node_type(node.type, language)

            chunk = CodeChunk(
                content=chunk_text,
                file_path=file_path,
                start_line=start + 1,
                end_line=end + 1,
                chunk_type=chunk_type,
                language=language,
                metadata={"ast_type": node.type},
            )

            if len(chunk_text) > self.max_chunk_size:
                sub_chunks = self._fixed_chunker.chunk_file(chunk_text, file_path)
                for sc in sub_chunks:
                    sc.chunk_type = chunk_type
                    sc.start_line += start
                    sc.end_line += start
                    sc.metadata["ast_type"] = node.type
                    sc.metadata["sub_chunked"] = True
                chunks.extend(sub_chunks)
            else:
                chunks.append(chunk)
            return

        for child in node.children:
            self._walk_tree(child, content, file_path, language, node_types, chunks)

    # ── regex fallback implementation ──────────────────────────────────

    def _chunk_with_regex(
        self, content: str, file_path: str, language: str
    ) -> list[CodeChunk]:
        """Extract function/class chunks using regex patterns.

        Works without tree-sitter installed.  Recognises standard
        function/class declaration syntax for each supported language.
        """
        lines = content.split("\n")
        patterns = _regex_patterns_for_language(language)

        if not patterns:
            # Unknown language – return the entire file as a single module chunk,
            # sub-chunked if too large.
            return self._module_fallback(content, file_path, language)

        boundaries: list[dict] = []

        for i, line in enumerate(lines):
            for pat_info in patterns:
                m = pat_info["pattern"].match(line)
                if m:
                    indent = len(line) - len(line.lstrip())
                    boundaries.append(
                        {
                            "line": i,
                            "type": pat_info["type"],
                            "indent": indent,
                            "name": m.group(1) if m.lastindex and m.lastindex >= 1 else "",
                        }
                    )
                    break

        if not boundaries:
            return self._module_fallback(content, file_path, language)

        chunks: list[CodeChunk] = []

        # Module-level code before the first boundary
        if boundaries[0]["line"] > 0:
            module_lines = lines[: boundaries[0]["line"]]
            module_text = "\n".join(module_lines).rstrip()
            if module_text.strip():
                chunks.append(
                    CodeChunk(
                        content=module_text,
                        file_path=file_path,
                        start_line=1,
                        end_line=boundaries[0]["line"],
                        chunk_type="module",
                        language=language,
                    )
                )

        for idx, boundary in enumerate(boundaries):
            start = boundary["line"]

            # Determine end: either next boundary at same or lower indent, or EOF
            if language in ("python", "ruby"):
                end = self._find_indent_block_end(lines, start, boundary["indent"])
            else:
                end = self._find_brace_block_end(lines, start)

            # Clamp to next boundary if needed
            if idx + 1 < len(boundaries):
                next_start = boundaries[idx + 1]["line"]
                if end >= next_start and boundaries[idx + 1]["indent"] <= boundary["indent"]:
                    end = next_start - 1

            end = min(end, len(lines) - 1)
            chunk_text = "\n".join(lines[start: end + 1]).rstrip()

            if not chunk_text.strip():
                continue

            chunk = CodeChunk(
                content=chunk_text,
                file_path=file_path,
                start_line=start + 1,
                end_line=end + 1,
                chunk_type=boundary["type"],
                language=language,
                metadata={"name": boundary["name"]},
            )

            if len(chunk_text) > self.max_chunk_size:
                sub_chunks = self._fixed_chunker.chunk_file(chunk_text, file_path)
                for sc in sub_chunks:
                    sc.chunk_type = boundary["type"]
                    sc.start_line += start
                    sc.end_line += start
                    sc.metadata["sub_chunked"] = True
                chunks.extend(sub_chunks)
            else:
                chunks.append(chunk)

        # Trailing module-level code after the last boundary block
        if boundaries:
            last_boundary = boundaries[-1]
            last_start = last_boundary["line"]
            if language in ("python", "ruby"):
                last_end = self._find_indent_block_end(lines, last_start, last_boundary["indent"])
            else:
                last_end = self._find_brace_block_end(lines, last_start)
            last_end = min(last_end, len(lines) - 1)

            if last_end + 1 < len(lines):
                trailing_text = "\n".join(lines[last_end + 1:]).rstrip()
                if trailing_text.strip():
                    chunks.append(
                        CodeChunk(
                            content=trailing_text,
                            file_path=file_path,
                            start_line=last_end + 2,
                            end_line=len(lines),
                            chunk_type="module",
                            language=language,
                        )
                    )

        return chunks if chunks else self._module_fallback(content, file_path, language)

    # ── block-end heuristics ───────────────────────────────────────────

    @staticmethod
    def _find_indent_block_end(lines: list[str], start: int, base_indent: int) -> int:
        """For indent-based languages (Python, Ruby) find the end of the block."""
        end = start
        for i in range(start + 1, len(lines)):
            stripped = lines[i].strip()
            if not stripped:
                end = i
                continue
            current_indent = len(lines[i]) - len(lines[i].lstrip())
            if current_indent <= base_indent and stripped:
                break
            end = i
        return end

    @staticmethod
    def _find_brace_block_end(lines: list[str], start: int) -> int:
        """For brace-based languages find the matching closing brace."""
        depth = 0
        found_open = False
        for i in range(start, len(lines)):
            for ch in lines[i]:
                if ch == "{":
                    depth += 1
                    found_open = True
                elif ch == "}":
                    depth -= 1
            if found_open and depth <= 0:
                return i
        return len(lines) - 1

    # ── helpers ────────────────────────────────────────────────────────

    def _module_fallback(
        self, content: str, file_path: str, language: str
    ) -> list[CodeChunk]:
        """Return the entire file as module-level chunk(s)."""
        if len(content) > self.max_chunk_size:
            chunks = self._fixed_chunker.chunk_file(content, file_path)
            for c in chunks:
                c.chunk_type = "module"
            return chunks
        return [
            CodeChunk(
                content=content,
                file_path=file_path,
                start_line=1,
                end_line=content.count("\n") + 1,
                chunk_type="module",
                language=language,
            )
        ]

    def _add_module_level_code(
        self,
        content: str,
        file_path: str,
        language: str,
        chunks: list[CodeChunk],
    ) -> list[CodeChunk]:
        """Add module-level (non-function/class) code that is not covered by any AST chunk."""
        if not chunks:
            return self._module_fallback(content, file_path, language)

        lines = content.split("\n")
        covered = set()
        for c in chunks:
            for ln in range(c.start_line, c.end_line + 1):
                covered.add(ln)

        module_lines: list[tuple[int, str]] = []
        for i, line in enumerate(lines):
            if (i + 1) not in covered:
                module_lines.append((i + 1, line))

        if not module_lines:
            return chunks

        # Group contiguous uncovered lines
        groups: list[list[tuple[int, str]]] = []
        current: list[tuple[int, str]] = [module_lines[0]]
        for ln, text in module_lines[1:]:
            if ln == current[-1][0] + 1:
                current.append((ln, text))
            else:
                groups.append(current)
                current = [(ln, text)]
        groups.append(current)

        all_chunks = list(chunks)
        for group in groups:
            text = "\n".join(t for _, t in group).strip()
            if text:
                all_chunks.append(
                    CodeChunk(
                        content=text,
                        file_path=file_path,
                        start_line=group[0][0],
                        end_line=group[-1][0],
                        chunk_type="module",
                        language=language,
                    )
                )

        all_chunks.sort(key=lambda c: c.start_line)
        return all_chunks


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level helper functions
# ═══════════════════════════════════════════════════════════════════════════════


def _detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    return EXTENSION_LANGUAGE_MAP.get(ext, "unknown")


def _check_tree_sitter_available() -> bool:
    """Check whether tree-sitter is importable and usable."""
    try:
        import tree_sitter  # noqa: F401
        return True
    except ImportError:
        return False


def _get_tree_sitter_language(language: str):
    """Attempt to load a tree-sitter Language object.

    Returns None if the grammar is not installed.
    """
    try:
        import importlib
        mod = importlib.import_module(f"tree_sitter_{language}")
        return mod.language()
    except Exception:
        return None


def _ast_node_types_for_language(language: str) -> set[str]:
    """Return the tree-sitter node types that represent functions/classes."""
    mapping: dict[str, set[str]] = {
        "python": {"function_definition", "class_definition", "decorated_definition"},
        "javascript": {
            "function_declaration",
            "class_declaration",
            "method_definition",
            "arrow_function",
            "function",
        },
        "typescript": {
            "function_declaration",
            "class_declaration",
            "method_definition",
            "arrow_function",
            "function",
        },
        "java": {"method_declaration", "class_declaration", "constructor_declaration"},
        "go": {"function_declaration", "method_declaration", "type_declaration"},
        "rust": {"function_item", "impl_item", "struct_item", "enum_item"},
        "c": {"function_definition", "struct_specifier"},
        "cpp": {"function_definition", "class_specifier", "struct_specifier"},
    }
    return mapping.get(language, {"function_definition", "class_definition"})


def _classify_node_type(ts_type: str, language: str) -> str:
    """Map a tree-sitter node type to a human-readable chunk type string."""
    if "class" in ts_type or "struct" in ts_type or "impl" in ts_type or "enum" in ts_type:
        return "class"
    if "method" in ts_type or "constructor" in ts_type:
        return "method"
    if "function" in ts_type or "arrow" in ts_type:
        return "function"
    return "function"


def _regex_patterns_for_language(language: str) -> list[dict]:
    """Return a list of ``{pattern, type}`` dicts for identifying code boundaries.

    Each ``pattern`` is a compiled regex that matches the *beginning* of a
    function or class declaration line.
    """
    mapping: dict[str, list[dict]] = {
        "python": [
            {"pattern": re.compile(r"^(\s*)class\s+(\w+)"), "type": "class"},
            {"pattern": re.compile(r"^(\s*)(?:async\s+)?def\s+(\w+)"), "type": "function"},
        ],
        "javascript": [
            {"pattern": re.compile(r"^\s*class\s+(\w+)"), "type": "class"},
            {"pattern": re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)"), "type": "function"},
            {"pattern": re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\("), "type": "function"},
        ],
        "typescript": [
            {"pattern": re.compile(r"^\s*(?:export\s+)?class\s+(\w+)"), "type": "class"},
            {"pattern": re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)"), "type": "function"},
            {"pattern": re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\("), "type": "function"},
            {"pattern": re.compile(r"^\s*(?:export\s+)?interface\s+(\w+)"), "type": "class"},
        ],
        "java": [
            {"pattern": re.compile(r"^\s*(?:public|private|protected)?\s*(?:static\s+)?class\s+(\w+)"), "type": "class"},
            {"pattern": re.compile(r"^\s*(?:public|private|protected)\s+(?:static\s+)?[\w<>\[\]]+\s+(\w+)\s*\("), "type": "function"},
        ],
        "go": [
            {"pattern": re.compile(r"^\s*func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\("), "type": "function"},
            {"pattern": re.compile(r"^\s*type\s+(\w+)\s+struct"), "type": "class"},
            {"pattern": re.compile(r"^\s*type\s+(\w+)\s+interface"), "type": "class"},
        ],
        "rust": [
            {"pattern": re.compile(r"^\s*(?:pub\s+)?fn\s+(\w+)"), "type": "function"},
            {"pattern": re.compile(r"^\s*(?:pub\s+)?struct\s+(\w+)"), "type": "class"},
            {"pattern": re.compile(r"^\s*(?:pub\s+)?enum\s+(\w+)"), "type": "class"},
            {"pattern": re.compile(r"^\s*impl(?:<[^>]+>)?\s+(\w+)"), "type": "class"},
        ],
        "c": [
            {"pattern": re.compile(r"^\s*(?:static\s+)?[\w\*]+\s+(\w+)\s*\([^;]*$"), "type": "function"},
            {"pattern": re.compile(r"^\s*(?:typedef\s+)?struct\s+(\w+)"), "type": "class"},
        ],
        "cpp": [
            {"pattern": re.compile(r"^\s*class\s+(\w+)"), "type": "class"},
            {"pattern": re.compile(r"^\s*(?:virtual\s+)?(?:static\s+)?[\w\*:&<>]+\s+(\w+)\s*\([^;]*$"), "type": "function"},
            {"pattern": re.compile(r"^\s*struct\s+(\w+)"), "type": "class"},
        ],
        "ruby": [
            {"pattern": re.compile(r"^\s*class\s+(\w+)"), "type": "class"},
            {"pattern": re.compile(r"^\s*(?:def)\s+(\w+)"), "type": "function"},
            {"pattern": re.compile(r"^\s*module\s+(\w+)"), "type": "class"},
        ],
        "php": [
            {"pattern": re.compile(r"^\s*class\s+(\w+)"), "type": "class"},
            {"pattern": re.compile(r"^\s*(?:public|private|protected|static)?\s*function\s+(\w+)"), "type": "function"},
        ],
        "csharp": [
            {"pattern": re.compile(r"^\s*(?:public|private|protected|internal)\s+(?:static\s+)?class\s+(\w+)"), "type": "class"},
            {"pattern": re.compile(r"^\s*(?:public|private|protected|internal)\s+(?:static\s+)?[\w<>\[\]]+\s+(\w+)\s*\("), "type": "function"},
        ],
    }
    return mapping.get(language, [])


def is_supported_file(file_path: str) -> bool:
    """Return True if the file extension is a supported code language."""
    ext = Path(file_path).suffix.lower()
    return ext in SUPPORTED_EXTENSIONS


def parse_directory(
    directory: str | Path,
    chunker: FixedSizeChunker | ASTChunker | None = None,
    *,
    max_file_size_kb: int = 512,
) -> list[CodeChunk]:
    """Recursively parse a directory and chunk all supported source files.

    Args:
        directory: Root directory to scan.
        chunker: Chunker instance to use; defaults to ``ASTChunker()``.
        max_file_size_kb: Skip files larger than this (in KiB).

    Returns:
        All chunks across all files.
    """
    if chunker is None:
        chunker = ASTChunker()

    directory = Path(directory)
    all_chunks: list[CodeChunk] = []
    skipped = 0

    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue

        # Skip hidden / vendored directories
        parts = path.relative_to(directory).parts
        if any(p.startswith(".") or p in ("node_modules", "vendor", "__pycache__", ".git") for p in parts):
            continue

        if not is_supported_file(str(path)):
            continue

        if path.stat().st_size > max_file_size_kb * 1024:
            skipped += 1
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            skipped += 1
            continue

        rel_path = str(path.relative_to(directory))
        file_chunks = chunker.chunk_file(content, rel_path)
        all_chunks.extend(file_chunks)

    if skipped:
        logger.info("parse_directory_skipped_files", count=skipped)

    logger.info(
        "parse_directory_done",
        directory=str(directory),
        files_chunked=len({c.file_path for c in all_chunks}),
        total_chunks=len(all_chunks),
    )
    return all_chunks
