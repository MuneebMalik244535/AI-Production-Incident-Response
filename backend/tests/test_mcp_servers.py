"""Unit tests for Log and GitHub MCP Servers."""

from __future__ import annotations

import pytest

from app.mcp_servers.log_server import (
    add_log_entry,
    get_error_summary,
    get_log_entry,
    search_logs,
)
from app.mcp_servers.github_server import (
    get_commit,
    get_pull_request,
    search_code,
    search_commits,
)


class TestLogMCPServer:
    """Tests for Log MCP Server functions."""

    def test_search_logs_all(self) -> None:
        logs = search_logs(time_range_minutes=120)
        assert isinstance(logs, list)
        assert len(logs) >= 1

    def test_search_logs_by_service(self) -> None:
        logs = search_logs(service="payment-api")
        assert all(l["service"] == "payment-api" for l in logs)

    def test_search_logs_by_severity(self) -> None:
        logs = search_logs(severity="CRITICAL")
        assert all(l["severity"] == "CRITICAL" for l in logs)

    def test_get_log_entry_success(self) -> None:
        entry = get_log_entry("log-db-timeout-101")
        assert "id" in entry
        assert entry["id"] == "log-db-timeout-101"
        assert entry["service"] == "payment-api"

    def test_get_log_entry_not_found(self) -> None:
        res = get_log_entry("non-existent-id")
        assert "error" in res

    def test_get_error_summary(self) -> None:
        summary = get_error_summary(service="payment-api")
        assert summary["service"] == "payment-api"
        assert summary["total_errors"] >= 1
        assert "error_counts_by_severity" in summary
        assert "top_error_messages" in summary

    def test_add_log_entry_dynamic(self) -> None:
        new_entry = add_log_entry(
            service="test-svc",
            severity="ERROR",
            message="Dynamic error for testing",
            metadata={"test_run": True},
        )
        assert new_entry["id"].startswith("log-")
        
        fetched = get_log_entry(new_entry["id"])
        assert fetched["message"] == "Dynamic error for testing"


class TestGitHubMCPServer:
    """Tests for GitHub MCP Server functions."""

    def test_search_commits(self) -> None:
        commits = search_commits(query="db")
        assert isinstance(commits, list)
        assert len(commits) >= 1
        assert "sha" in commits[0]
        assert "message" in commits[0]

    def test_get_commit_details(self) -> None:
        detail = get_commit(sha="8f32a1")
        assert detail["sha"].startswith("8f32a1")
        assert "files" in detail
        assert len(detail["files"]) > 0
        assert "patch" in detail["files"][0]

    def test_search_code(self) -> None:
        results = search_code(query="pool")
        assert isinstance(results, list)
        assert len(results) >= 1
        assert "path" in results[0]

    def test_get_pull_request(self) -> None:
        pr = get_pull_request(pr_number=101)
        assert pr["number"] == 101
        assert pr["state"] == "closed"
        assert "title" in pr
