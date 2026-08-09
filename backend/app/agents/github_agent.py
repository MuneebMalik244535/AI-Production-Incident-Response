"""GitHub Investigation Agent definition and logic."""

from __future__ import annotations

from typing import Any
from agents import Agent, function_tool
from app.agents.models import GitHubFindings
from app.mcp_servers.github_server import get_commit, get_pull_request, search_code, search_commits


@function_tool
def tool_search_commits(repo: str = "", query: str = "", since_hours: int = 24) -> list[dict[str, Any]]:
    """Search recent commits in a repository."""
    return search_commits(repo=repo, query=query, since_hours=since_hours)


@function_tool
def tool_get_commit(repo: str = "", sha: str = "8f32a1") -> dict[str, Any]:
    """Get commit details including file diff patches."""
    return get_commit(repo=repo, sha=sha)


@function_tool
def tool_search_code(repo: str = "", query: str = "connection") -> list[dict[str, Any]]:
    """Search repository code files."""
    return search_code(repo=repo, query=query)


@function_tool
def tool_get_pull_request(repo: str = "", pr_number: int = 101) -> dict[str, Any]:
    """Get details of a pull request."""
    return get_pull_request(repo=repo, pr_number=pr_number)


github_agent = Agent(
    name="GitHub Investigation Agent",
    instructions=(
        "You are an expert DevOps engineer specializing in code forensics. "
        "Search recent commits, inspect diffs, and identify commits that caused the incident."
    ),
    model="gpt-4o",
    tools=[tool_search_commits, tool_get_commit, tool_search_code, tool_get_pull_request],
    output_type=GitHubFindings,
)


def run_github_investigation(service: str, query: str = "db") -> GitHubFindings:
    """Fallback deterministic GitHub investigation for test environments without API keys."""
    commits = search_commits(query=query)
    target_sha = commits[0]["sha"] if commits else "8f32a1"
    commit_detail = get_commit(sha=target_sha)

    files_changed = [f["filename"] for f in commit_detail.get("files", [])]

    return GitHubFindings(
        repository=f"company/{service}",
        suspicious_commits=[
            {
                "sha": commit_detail.get("sha", "8f32a1")[:7],
                "author": commit_detail.get("author", "dev@company.com"),
                "message": commit_detail.get("message", "perf(db): optimize connection handling"),
                "files_changed": files_changed,
            }
        ],
        relevant_files=files_changed or ["app/db/connection.py", "app/config.py"],
        code_changes_summary=(
            "Commit 8f32a1 modified database connection handling: removed explicit connection pool release "
            "and reduced POOL_SIZE from 50 to 10."
        ),
        deployment_correlation="Commit deployed 4 minutes prior to initial error spike.",
        summary=f"Identified commit {target_sha[:7]} by dev@company.com changing DB connection handling as primary suspect.",
    )
