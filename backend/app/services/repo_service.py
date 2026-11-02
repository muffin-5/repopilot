"""
RepoPilot – Repository Service.

Handles cloning public repositories, parsing code files, chunking,
building vector and lexical indices, and tracking repository lifecycle metadata.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from app.core.config import Settings
from app.models.schemas import RepoStatus
from app.retrieval.hybrid_search import HybridRetriever
from app.utils.code_parser import ASTChunker, CodeChunk, FixedSizeChunker, parse_directory

logger = structlog.get_logger(__name__)


class RepoService:
    """Manages repository ingestion, indexing, and persistent metadata."""

    def __init__(self, settings: Settings, retriever: HybridRetriever) -> None:
        self.settings = settings
        self.retriever = retriever
        self.metadata_file = settings.metadata_path
        self._ensure_storage()
        self._warmup_indices()

    def _ensure_storage(self) -> None:
        """Ensure directories and metadata JSON exist."""
        self.settings.repos_path.mkdir(parents=True, exist_ok=True)
        self.settings.data_path.mkdir(parents=True, exist_ok=True)
        if not self.metadata_file.exists():
            self._save_metadata({})

    def _warmup_indices(self) -> None:
        """Warm up indices for all ready repositories on service initialization."""
        meta = self._load_metadata()
        for repo_id, item in meta.items():
            if item.get("status") == "ready":
                try:
                    self.ensure_repo_indexed(repo_id)
                except Exception as e:
                    logger.warning("warmup_repo_failed", repo_id=repo_id, error=str(e))

    def ensure_repo_indexed(self, repo_id: str) -> None:
        """Ensure chunks for repo_id are loaded into VectorStore and BM25."""
        if repo_id in self.retriever._bm25_indices and repo_id in self.retriever.vector_store._inmemory_stores:
            return

        meta = self._load_metadata()
        item = meta.get(repo_id)
        if not item:
            return

        target_dir = Path(item.get("target_dir", self.settings.repos_path / repo_id))
        chunks_file = target_dir / "chunks.json"

        chunk_dicts = []
        if chunks_file.exists():
            try:
                with open(chunks_file, "r", encoding="utf-8") as f:
                    chunk_dicts = json.load(f)
            except Exception as e:
                logger.warning("load_chunks_failed_rechunking", error=str(e))

        if not chunk_dicts and target_dir.exists():
            chunker = ASTChunker(max_chunk_size=self.settings.chunk_size, overlap=self.settings.chunk_overlap)
            code_chunks = parse_directory(target_dir, chunker=chunker)
            for idx, c in enumerate(code_chunks):
                cid = f"{repo_id}_{idx}"
                chunk_dicts.append({
                    "chunk_id": cid,
                    "file_path": c.file_path,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "chunk_type": c.chunk_type,
                    "language": c.language,
                    "content": c.content,
                    "repo_id": repo_id,
                })
            try:
                with open(chunks_file, "w", encoding="utf-8") as f:
                    json.dump(chunk_dicts, f)
            except Exception:
                pass

        if chunk_dicts:
            self.retriever.index_repo_chunks(repo_id, chunk_dicts)
            logger.info("reloaded_repo_index", repo_id=repo_id, chunks=len(chunk_dicts))

    def _load_metadata(self) -> dict[str, dict[str, Any]]:
        """Load repository metadata mapping."""
        if not self.metadata_file.exists():
            return {}
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("load_metadata_failed", error=str(e))
            return {}

    def _save_metadata(self, data: dict[str, dict[str, Any]]) -> None:
        """Save repository metadata mapping."""
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _generate_repo_id(self, repo_url: str) -> str:
        """Create deterministic ID from repo URL."""
        clean_url = repo_url.strip().lower().rstrip("/")
        digest = hashlib.sha256(clean_url.encode("utf-8")).hexdigest()[:12]
        name = clean_url.split("/")[-1].replace(".git", "")
        return f"{name}-{digest}"

    def list_repos(self) -> list[RepoStatus]:
        """List all indexed repositories."""
        meta = self._load_metadata()
        results = []
        for rid, item in meta.items():
            results.append(
                RepoStatus(
                    repo_id=rid,
                    repo_url=item.get("repo_url", ""),
                    status=item.get("status", "unknown"),
                    file_count=item.get("file_count", 0),
                    chunk_count=item.get("chunk_count", 0),
                    indexed_at=item.get("indexed_at", ""),
                )
            )
        return results

    def get_repo_status(self, repo_id: str) -> Optional[RepoStatus]:
        """Get status of a specific repository."""
        meta = self._load_metadata()
        item = meta.get(repo_id)
        if not item:
            return None
        return RepoStatus(
            repo_id=repo_id,
            repo_url=item.get("repo_url", ""),
            status=item.get("status", "unknown"),
            file_count=item.get("file_count", 0),
            chunk_count=item.get("chunk_count", 0),
            indexed_at=item.get("indexed_at", ""),
        )

    def ingest_repo(
        self,
        repo_url: str,
        branch: str = "main",
        chunk_strategy: str = "ast",
    ) -> RepoStatus:
        """Clone and index a Git repository or local directory path."""
        repo_id = self._generate_repo_id(repo_url)
        target_dir = self.settings.repos_path / repo_id

        # Update metadata to indexing
        meta = self._load_metadata()
        meta[repo_id] = {
            "repo_id": repo_id,
            "repo_url": repo_url,
            "branch": branch,
            "status": "indexing",
            "file_count": 0,
            "chunk_count": 0,
            "indexed_at": datetime.datetime.utcnow().isoformat(),
        }
        self._save_metadata(meta)

        try:
            # 1. Fetch / Clone repository
            if Path(repo_url).exists() and Path(repo_url).is_dir():
                # Local directory support for testing / fast offline benchmarking
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                shutil.copytree(repo_url, target_dir)
                logger.info("copied_local_repo", src=repo_url, dest=str(target_dir))
            else:
                # Clone via Git
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                import git
                git.Repo.clone_from(repo_url, target_dir, depth=1, branch=branch)
                logger.info("cloned_remote_repo", url=repo_url, branch=branch)

            # 2. Parse and chunk repository
            if chunk_strategy.lower() == "fixed":
                chunker = FixedSizeChunker(
                    chunk_size=self.settings.chunk_size,
                    chunk_overlap=self.settings.chunk_overlap,
                )
            else:
                chunker = ASTChunker(
                    max_chunk_size=self.settings.chunk_size,
                    overlap=self.settings.chunk_overlap,
                )

            code_chunks: list[CodeChunk] = parse_directory(target_dir, chunker=chunker)

            # 3. Transform chunks for indexing
            chunk_dicts: list[dict[str, Any]] = []
            unique_files = set()
            for idx, c in enumerate(code_chunks):
                unique_files.add(c.file_path)
                cid = f"{repo_id}_{idx}"
                chunk_dicts.append({
                    "chunk_id": cid,
                    "file_path": c.file_path,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "chunk_type": c.chunk_type,
                    "language": c.language,
                    "content": c.content,
                    "repo_id": repo_id,
                })

            # 4. Index in Vector Store and BM25
            self.retriever.index_repo_chunks(repo_id, chunk_dicts)

            # Save chunks.json for persistence across restarts
            try:
                with open(target_dir / "chunks.json", "w", encoding="utf-8") as f:
                    json.dump(chunk_dicts, f)
            except Exception as e:
                logger.warning("save_chunks_failed", error=str(e))

            # 5. Update metadata to ready
            meta[repo_id]["status"] = "ready"
            meta[repo_id]["file_count"] = len(unique_files)
            meta[repo_id]["chunk_count"] = len(chunk_dicts)
            meta[repo_id]["target_dir"] = str(target_dir)
            self._save_metadata(meta)

            logger.info(
                "repo_ingestion_complete",
                repo_id=repo_id,
                files=len(unique_files),
                chunks=len(chunk_dicts),
            )

            return RepoStatus(
                repo_id=repo_id,
                repo_url=repo_url,
                status="ready",
                file_count=len(unique_files),
                chunk_count=len(chunk_dicts),
                indexed_at=meta[repo_id]["indexed_at"],
            )

        except Exception as e:
            logger.error("repo_ingestion_failed", repo_id=repo_id, error=str(e))
            meta[repo_id]["status"] = f"error: {str(e)}"
            self._save_metadata(meta)
            raise

    def delete_repo(self, repo_id: str) -> bool:
        """Remove a repository from index and storage."""
        meta = self._load_metadata()
        if repo_id not in meta:
            return False

        target_dir = self.settings.repos_path / repo_id
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)

        self.retriever.vector_store.delete_collection(repo_id)
        if repo_id in self.retriever._bm25_indices:
            del self.retriever._bm25_indices[repo_id]

        del meta[repo_id]
        self._save_metadata(meta)
        logger.info("repo_deleted", repo_id=repo_id)
        return True
