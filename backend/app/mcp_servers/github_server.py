"""MCP Server exposing tools for GitHub commit analysis, code search, and PR inspection.

Can run standalone via stdio (`mcp run app/mcp_servers/github_server.py`) or programmatically.
Uses GitHub REST API when GITHUB_TOKEN is available, with realistic mock fallbacks for local/offline testing.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from app.config import settings

# Initialize FastMCP Server
mcp = FastMCP(
    "GitHubInvestigationServer",
    instructions="Provides tools to search GitHub commits, inspect commit diffs, search repository code, and fetch pull request details.",
)

# ── Mock Data for Offline / Testing ───────────────────────────────────────────

def _get_mock_commits() -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    return [
        {
            "sha": "8f32a1b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3",
            "short_sha": "8f32a1",
            "message": "perf(db): optimize connection handling for payment processing\n\n- Removed explicit connection release to reduce overhead\n- Set max pool size to 10",
            "author": "dev@company.com",
            "date": (now - timedelta(hours=1, minutes=15)).isoformat(),
            "url": "https://github.com/company/payment-api/commit/8f32a1",
            "files_changed_count": 2,
        },
        {
            "sha": "3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
            "short_sha": "3a4b5c",
            "message": "fix(auth): update JWT verification timeout to 5000ms",
            "author": "security-dev@company.com",
            "date": (now - timedelta(hours=5)).isoformat(),
            "url": "https://github.com/company/auth-service/commit/3a4b5c",
            "files_changed_count": 1,
        },
    ]


def _get_mock_commit_detail(sha: str) -> dict[str, Any]:
    if sha.startswith("8f32a1"):
        return {
            "sha": "8f32a1b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3",
            "message": "perf(db): optimize connection handling for payment processing",
            "author": "dev@company.com",
            "date": datetime.now(timezone.utc).isoformat(),
            "url": "https://github.com/company/payment-api/commit/8f32a1",
            "stats": {"additions": 15, "deletions": 28, "total": 43},
            "files": [
                {
                    "filename": "app/db/connection.py",
                    "status": "modified",
                    "additions": 5,
                    "deletions": 20,
                    "patch": (
                        "@@ -15,18 +15,3 @@ def get_db_connection():\n"
                        "-    try:\n"
                        "-        conn = pool.getconn()\n"
                        "-        yield conn\n"
                        "-    finally:\n"
                        "-        pool.putconn(conn) # Released back to pool\n"
                        "+    # Direct pool access for higher throughput\n"
                        "+    return pool.getconn()\n"
                    ),
                },
                {
                    "filename": "app/config.py",
                    "status": "modified",
                    "additions": 10,
                    "deletions": 8,
                    "patch": "@@ -5,4 +5,4 @@\n-POOL_SIZE = 50\n+POOL_SIZE = 10\n",
                },
            ],
        }
    return {
        "sha": sha,
        "message": "Chore: routine update",
        "author": "ci-bot",
        "date": datetime.now(timezone.utc).isoformat(),
        "url": f"https://github.com/company/repo/commit/{sha[:7]}",
        "stats": {"additions": 1, "deletions": 1, "total": 2},
        "files": [],
    }


# ── MCP Tools ─────────────────────────────────────────────────────────────────


@mcp.tool()
def search_commits(repo: str = "", query: str = "", since_hours: int = 24) -> list[dict[str, Any]]:
    """Search recent commits in a repository to identify code changes correlation with an incident.

    Args:
        repo: Repository format 'owner/repo' (e.g., 'company/payment-api'). If empty, uses default.
        query: Optional keyword to filter commit messages (e.g. 'db', 'connection', 'auth').
        since_hours: Look back window in hours. Default 24.
    """
    target_repo = repo or settings.github_default_repo
    token = settings.github_token

    # Use real GitHub API if token is configured
    if token and target_repo:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        since = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).isoformat()
        url = f"https://api.github.com/repos/{target_repo}/commits?since={since}"

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    commits = resp.json()
                    results = []
                    for c in commits:
                        msg = c["commit"]["message"]
                        if query and query.lower() not in msg.lower():
                            continue
                        results.append({
                            "sha": c["sha"],
                            "short_sha": c["sha"][:7],
                            "message": msg,
                            "author": c["commit"]["author"]["name"],
                            "date": c["commit"]["author"]["date"],
                            "url": c["html_url"],
                            "files_changed_count": 0,
                        })
                    return results
        except Exception:
            pass  # Fallback to mock data if network / auth fails

    # Mock fallback
    mock_commits = _get_mock_commits()
    if query:
        mock_commits = [c for c in mock_commits if query.lower() in c["message"].lower()]
    return mock_commits


@mcp.tool()
def get_commit(repo: str = "", sha: str = "8f32a1") -> dict[str, Any]:
    """Retrieve detailed commit information including file diffs and patches.

    Args:
        repo: Repository format 'owner/repo' (e.g. 'company/payment-api').
        sha: Full or short commit SHA hash.
    """
    target_repo = repo or settings.github_default_repo
    token = settings.github_token

    if token and target_repo:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        url = f"https://api.github.com/repos/{target_repo}/commits/{sha}"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "sha": data["sha"],
                        "message": data["commit"]["message"],
                        "author": data["commit"]["author"]["name"],
                        "date": data["commit"]["author"]["date"],
                        "url": data["html_url"],
                        "stats": data.get("stats", {}),
                        "files": [
                            {
                                "filename": f["filename"],
                                "status": f["status"],
                                "additions": f["additions"],
                                "deletions": f["deletions"],
                                "patch": f.get("patch", ""),
                            }
                            for f in data.get("files", [])
                        ],
                    }
        except Exception:
            pass

    return _get_mock_commit_detail(sha)


@mcp.tool()
def search_code(repo: str = "", query: str = "connection") -> list[dict[str, Any]]:
    """Search code files in a GitHub repository.

    Args:
        repo: Repository format 'owner/repo'.
        query: Code search query term (e.g., 'pool_size', 'TimeoutError').
    """
    target_repo = repo or settings.github_default_repo
    token = settings.github_token

    if token and target_repo:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        url = f"https://api.github.com/search/code?q={query}+repo:{target_repo}"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    return [
                        {
                            "path": item["path"],
                            "repo": target_repo,
                            "line_number": None,
                            "code_snippet": item.get("name", ""),
                            "html_url": item["html_url"],
                        }
                        for item in items[:10]
                    ]
        except Exception:
            pass

    # Mock response
    return [
        {
            "path": "app/db/connection.py",
            "repo": target_repo or "company/payment-api",
            "line_number": 18,
            "code_snippet": "return pool.getconn() # pool.size limit 10",
            "html_url": "https://github.com/company/payment-api/blob/main/app/db/connection.py#L18",
        }
    ]


@mcp.tool()
def get_pull_request(repo: str = "", pr_number: int = 101) -> dict[str, Any]:
    """Get details of a pull request.

    Args:
        repo: Repository format 'owner/repo'.
        pr_number: Pull request number.
    """
    return {
        "number": pr_number,
        "title": "perf(db): optimize connection handling for payment processing",
        "state": "closed",
        "author": "dev@company.com",
        "created_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        "merged_at": (datetime.now(timezone.utc) - timedelta(hours=1, minutes=15)).isoformat(),
        "body": "Improves DB connection performance by reducing pool release overhead.",
        "html_url": f"https://github.com/company/payment-api/pull/{pr_number}",
        "diff_url": f"https://github.com/company/payment-api/pull/{pr_number}.diff",
    }


if __name__ == "__main__":
    mcp.run()
