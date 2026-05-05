"""
GitHub API client wrapper.
All GitHub API calls go through this module.
"""

from typing import Any, Dict, List, Optional

import httpx

from app.core.logging import get_logger
from app.github.auth import get_installation_token

logger = get_logger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class GitHubClient:
    def __init__(self, installation_id: int):
        self.installation_id = installation_id
        self._token: Optional[str] = None

    async def _get_headers(self) -> Dict[str, str]:
        if not self._token:
            self._token = await get_installation_token(self.installation_id)
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers=await self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Returns list of files changed in the PR."""
        files = []
        page = 1
        async with httpx.AsyncClient() as client:
            while True:
                response = await client.get(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files",
                    headers=await self._get_headers(),
                    params={"per_page": 100, "page": page},
                )
                response.raise_for_status()
                batch = response.json()
                if not batch:
                    break
                files.extend(batch)
                page += 1
        return files

    async def get_pr_commits(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/commits",
                headers=await self._get_headers(),
                params={"per_page": 100},
            )
            response.raise_for_status()
            return response.json()

    async def create_pr_comment(self, owner: str, repo: str, pr_number: int, body: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{pr_number}/comments",
                headers=await self._get_headers(),
                json={"body": body},
            )
            response.raise_for_status()
            return response.json()

    async def update_pr_comment(self, owner: str, repo: str, comment_id: int, body: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/comments/{comment_id}",
                headers=await self._get_headers(),
                json={"body": body},
            )
            response.raise_for_status()
            return response.json()

    async def add_labels(self, owner: str, repo: str, issue_number: int, labels: List[str]) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{issue_number}/labels",
                headers=await self._get_headers(),
                json={"labels": labels},
            )
            response.raise_for_status()

    async def ensure_label_exists(self, owner: str, repo: str, name: str, color: str, description: str = "") -> None:
        """Create a label if it doesn't already exist."""
        async with httpx.AsyncClient() as client:
            # Check if label exists
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/labels/{name}",
                headers=await self._get_headers(),
            )
            if response.status_code == 404:
                await client.post(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}/labels",
                    headers=await self._get_headers(),
                    json={"name": name, "color": color, "description": description},
                )

    async def get_contributor_pr_count(self, owner: str, repo: str, author: str) -> int:
        """Get total merged PRs by an author in a repo."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/search/issues",
                headers=await self._get_headers(),
                params={
                    "q": f"repo:{owner}/{repo} type:pr author:{author} is:merged",
                    "per_page": 1,
                },
            )
            response.raise_for_status()
            return response.json().get("total_count", 0)
