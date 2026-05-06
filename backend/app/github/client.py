"""
GitHub API client wrapper.
All GitHub API calls go through this module.
"""

import asyncio
from typing import Any

import httpx

from app.core.logging import get_logger
from app.github.auth import get_installation_token

logger = get_logger(__name__)

GITHUB_API_BASE = "https://api.github.com"
_RETRY_STATUSES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3


class GitHubClient:
    def __init__(self, installation_id: int):
        self.installation_id = installation_id
        self._token: str | None = None

    async def _get_headers(self) -> dict[str, str]:
        if not self._token:
            self._token = await get_installation_token(self.installation_id)
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make an HTTP request with exponential backoff on rate limits / transient errors."""
        async with httpx.AsyncClient() as client:
            for attempt in range(_MAX_RETRIES):
                response = await client.request(method, url, headers=await self._get_headers(), **kwargs)
                if response.status_code not in _RETRY_STATUSES:
                    response.raise_for_status()
                    return response
                retry_after = int(response.headers.get("Retry-After", 2 ** (attempt + 1)))
                logger.warning(
                    "github.rate_limited",
                    status=response.status_code,
                    retry_after=retry_after,
                    attempt=attempt + 1,
                )
                await asyncio.sleep(retry_after)
            response.raise_for_status()
            return response

    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> dict[str, Any]:
        response = await self._request("GET", f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}")
        return response.json()

    async def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """Returns list of files changed in the PR (handles pagination)."""
        files = []
        page = 1
        while True:
            response = await self._request(
                "GET",
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files",
                params={"per_page": 100, "page": page},
            )
            batch = response.json()
            if not batch:
                break
            files.extend(batch)
            page += 1
        return files

    async def get_pr_commits(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        response = await self._request(
            "GET",
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/commits",
            params={"per_page": 100},
        )
        return response.json()

    async def create_pr_comment(self, owner: str, repo: str, pr_number: int, body: str) -> dict[str, Any]:
        response = await self._request(
            "POST",
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{pr_number}/comments",
            json={"body": body},
        )
        return response.json()

    async def update_pr_comment(self, owner: str, repo: str, comment_id: int, body: str) -> dict[str, Any]:
        response = await self._request(
            "PATCH",
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/comments/{comment_id}",
            json={"body": body},
        )
        return response.json()

    async def add_labels(self, owner: str, repo: str, issue_number: int, labels: list[str]) -> None:
        await self._request(
            "POST",
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{issue_number}/labels",
            json={"labels": labels},
        )

    async def ensure_label_exists(self, owner: str, repo: str, name: str, color: str, description: str = "") -> None:
        """Create a label if it doesn't already exist."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/labels/{name}",
                headers=await self._get_headers(),
            )
            if response.status_code == 404:
                await self._request(
                    "POST",
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}/labels",
                    json={"name": name, "color": color, "description": description},
                )

    async def get_contributor_pr_count(self, owner: str, repo: str, author: str) -> int:
        """Get total merged PRs by an author in a repo."""
        response = await self._request(
            "GET",
            f"{GITHUB_API_BASE}/search/issues",
            params={"q": f"repo:{owner}/{repo} type:pr author:{author} is:merged", "per_page": 1},
        )
        return response.json().get("total_count", 0)

    async def get_file_content(self, owner: str, repo: str, path: str) -> str | None:
        """Fetch a file's decoded content from the repo. Returns None if not found."""
        import base64
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}",
                headers=await self._get_headers(),
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return base64.b64decode(response.json()["content"]).decode("utf-8")
