"""
Background job tasks processed by the ARQ worker.
"""

import json
from datetime import datetime
from typing import Any, Dict

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import get_logger
from app.db.base import AsyncSessionLocal
from app.db.models import PRScore, WebhookEvent
from app.github.client import GitHubClient
from app.github.comments import build_pr_score_comment
from app.klarity_config.parser import parse_config
from app.scoring.engine import score_pull_request

logger = get_logger(__name__)

# Label colors for GitHub
LABEL_COLORS = {
    "suspected-ai": "d93f0b",
    "needs-tests": "e4e669",
    "needs-issue-link": "0075ca",
    "low-quality": "e11d48",
}

LABEL_DESCRIPTIONS = {
    "suspected-ai": "Klarity: PR shows signals of AI generation without review",
    "needs-tests": "Klarity: PR is missing test coverage",
    "needs-issue-link": "Klarity: PR is not linked to an issue",
    "low-quality": "Klarity: PR scored below quality threshold",
}


async def process_pull_request_event(
    ctx: Dict[str, Any],
    payload: Dict[str, Any],
    delivery_id: str,
) -> None:
    """
    Main background task: score a PR and post results to GitHub.
    """
    repo = payload["repository"]
    pr = payload["pull_request"]
    installation_id = payload["installation"]["id"]

    owner = repo["owner"]["login"]
    repo_name = repo["name"]
    repo_full_name = repo["full_name"]
    pr_number = pr["number"]
    author = pr["user"]["login"]

    logger.info(
        "task.process_pr.start",
        repo=repo_full_name,
        pr_number=pr_number,
        author=author,
    )

    async with AsyncSessionLocal() as session:
        try:
            github = GitHubClient(installation_id)

            # Fetch PR details
            pr_data, files, commits = await _fetch_pr_data(github, owner, repo_name, pr_number)

            # Get author's merged PR count
            merged_count = await github.get_contributor_pr_count(owner, repo_name, author)

            # Fetch .klarity.yml config (best effort)
            config = await _fetch_repo_config(github, owner, repo_name)

            # Run scoring pipeline
            result = await score_pull_request(
                pr_data=pr_data,
                files=files,
                commits=commits,
                merged_pr_count=merged_count,
                config=config,
            )

            # Ensure labels exist in the repo
            for label in result.labels_to_apply:
                await github.ensure_label_exists(
                    owner, repo_name, label,
                    LABEL_COLORS.get(label, "cccccc"),
                    LABEL_DESCRIPTIONS.get(label, ""),
                )

            # Apply labels
            if result.labels_to_apply:
                await github.add_labels(owner, repo_name, pr_number, result.labels_to_apply)

            # Build and post comment
            comment_body = build_pr_score_comment(
                score=result.score,
                breakdown=result.breakdown,
                suggestions=result.suggestions,
                is_suspected_ai=result.is_suspected_ai,
                author=author,
            )
            comment = await github.create_pr_comment(owner, repo_name, pr_number, comment_body)

            # Persist score to DB
            pr_score = PRScore(
                repo_full_name=repo_full_name,
                pr_number=pr_number,
                pr_title=pr_data.get("title", ""),
                author_login=author,
                score=result.score,
                linked_issue_score=result.breakdown.get("linked_issue", 0),
                tests_score=result.breakdown.get("tests_changed", 0),
                description_score=result.breakdown.get("description_quality", 0),
                commit_quality_score=result.breakdown.get("commit_quality", 0),
                author_history_score=result.breakdown.get("author_history", 0),
                diff_size_score=result.breakdown.get("diff_size", 0),
                is_suspected_ai=result.is_suspected_ai,
                slop_signals=json.dumps(result.slop_signals),
                comment_id=comment.get("id"),
            )
            session.add(pr_score)

            # Mark webhook event as processed
            await _mark_event_processed(session, delivery_id)

            await session.commit()

            logger.info(
                "task.process_pr.complete",
                repo=repo_full_name,
                pr_number=pr_number,
                score=result.score,
                is_suspected_ai=result.is_suspected_ai,
            )

        except Exception as exc:
            await session.rollback()
            await _mark_event_failed(session, delivery_id, str(exc))
            await session.commit()
            logger.error(
                "task.process_pr.failed",
                repo=repo_full_name,
                pr_number=pr_number,
                error=str(exc),
                exc_info=True,
            )
            raise


async def _fetch_pr_data(github: GitHubClient, owner: str, repo: str, pr_number: int):
    import asyncio
    pr_data, files, commits = await asyncio.gather(
        github.get_pull_request(owner, repo, pr_number),
        github.get_pr_files(owner, repo, pr_number),
        github.get_pr_commits(owner, repo, pr_number),
    )
    return pr_data, files, commits


async def _fetch_repo_config(github: GitHubClient, owner: str, repo: str):
    """Try to fetch .klarity.yml from the repo. Returns default config on failure."""
    import httpx
    from app.klarity_config.parser import parse_config

    try:
        async with httpx.AsyncClient() as client:
            headers = await github._get_headers()
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/.klarity.yml",
                headers=headers,
            )
            if response.status_code == 200:
                import base64
                content = base64.b64decode(response.json()["content"]).decode("utf-8")
                return parse_config(content)
    except Exception:
        pass
    return parse_config(None)


async def _mark_event_processed(session: AsyncSession, delivery_id: str) -> None:
    from sqlmodel import select
    result = await session.exec(select(WebhookEvent).where(WebhookEvent.delivery_id == delivery_id))
    event = result.first()
    if event:
        event.processed = True
        event.processed_at = datetime.utcnow()
        session.add(event)


async def _mark_event_failed(session: AsyncSession, delivery_id: str, error: str) -> None:
    from sqlmodel import select
    result = await session.exec(select(WebhookEvent).where(WebhookEvent.delivery_id == delivery_id))
    event = result.first()
    if event:
        event.error = error[:500]
        session.add(event)
