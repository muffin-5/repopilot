"""
End-to-End API integration tests for RepoPilot.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_and_tools(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    tools_res = client.get("/api/agent/tools")
    assert tools_res.status_code == 200
    assert len(tools_res.json()) >= 4


def test_repo_ingest_and_chat_e2e(client: TestClient) -> None:
    # Create a small sample repository directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        sample_file = Path(tmp_dir) / "app.py"
        sample_file.write_text(
            "def login(username, password):\n"
            "    # Authentication routine\n"
            "    if not username:\n"
            "        raise ValueError('Invalid user')\n"
            "    return True\n"
        )

        # Ingest the local folder as repo
        ingest_res = client.post(
            "/api/repos/ingest",
            json={"repo_url": str(tmp_dir), "branch": "main"},
        )
        assert ingest_res.status_code == 201
        data = ingest_res.json()
        repo_id = data["repo_id"]
        assert data["status"] == "ready"
        assert data["file_count"] >= 1

        # Ask a question via chat
        chat_res = client.post(
            "/api/chat",
            json={"repo_id": repo_id, "question": "Where is user login handled?", "retrieval_mode": "hybrid"},
        )
        assert chat_res.status_code == 200
        chat_data = chat_res.json()
        assert len(chat_data["answer"]) > 0
        assert len(chat_data["citations"]) > 0

        # Run bug investigation
        bug_res = client.post(
            "/api/agent/investigate",
            json={
                "repo_id": repo_id,
                "bug_description": "User login fails on empty username",
                "error_message": "ValueError: Invalid user",
            },
        )
        assert bug_res.status_code == 200
        bug_data = bug_res.json()
        assert len(bug_data["relevant_files"]) > 0
        assert len(bug_data["suggested_patches"]) > 0

        # Clean up repo
        del_res = client.delete(f"/api/repos/{repo_id}")
        assert del_res.status_code == 200
