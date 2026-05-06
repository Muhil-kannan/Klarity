"""
Background job tasks processed by the ARQ worker.
"""

import json
import re
from datetime import datetime
from typing import Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import get_logger
from app.db.base import AsyncSessionLocal
from app.db.models import PRScore, WebhookEvent
from app.github.client import GitHubClient
from app.github.comments import build_pr_score_comment
from app.klarity_config.parser import KlarityConfig, parse_config
from app.reputation.tracker import update_contributor_reputation
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

# Bots and automation accounts that should never be scored
DEFAULT_IGNORE_LIST = {
    "dependabot",
    "dependabot[bot]",
    "renovate",
    "renovate[bot]",
    "github-actions",
    "github-actions[bot]",
    "snyk-bot",
    "allcontributors[bot]",
    "imgbot[bot]",
}


async def process_pull_request_event(
    ctx: dict[str, Any],
    payload: dict[str, Any],
    delivery_id: str,
) -> None:
    """
    Main background task: score a PR and post results to GitHub.
    Handles both new PRs (opened) and updated PRs (synchronize/edited).
    """
    repo = payload["repository"]
    pr = payload["pull_request"]
    installation_id = payload["installation"]["id"]

    owner = repo["owner"]["login"]
    repo_name = repo["name"]
    repo_full_name = repo["full_name"]
    pr_number = pr["number"]
    author = pr["user"]["login"]

    # Skip bots and automation accounts
    if author.lower() in DEFAULT_IGNORE_LIST or author.lower().endswith("[bot]"):
        logger.info("task.process_pr.ignored_bot", author=author, repo=repo_full_name)
        return

    logger.info(
        "task.process_pr.start",
        repo=repo_full_name,
        pr_number=pr_number,
        author=author,
    )

    async with AsyncSessionLocal() as session:
        try:
            github = GitHubClient(installation_id)

            # Fetch PR details, files, commits concurrently
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

            # Build comment body
            comment_body = build_pr_score_comment(
                score=result.score,
                breakdown=result.breakdown,
                suggestions=result.suggestions,
                is_suspected_ai=result.is_suspected_ai,
                author=author,
            )

            # Check if we already have a score record (re-score case)
            existing = await _get_existing_score(session, repo_full_name, pr_number)

            if existing and existing.comment_id:
                # Update the existing comment instead of posting a new one
                await github.update_pr_comment(owner, repo_name, existing.comment_id, comment_body)
                comment_id = existing.comment_id
                # Update the existing record
                existing.score = result.score
                existing.linked_issue_score = result.breakdown.get("linked_issue", 0)
                existing.tests_score = result.breakdown.get("tests_changed", 0)
                existing.description_score = result.breakdown.get("description_quality", 0)
                existing.commit_quality_score = result.breakdown.get("commit_quality", 0)
                existing.author_history_score = result.breakdown.get("author_history", 0)
                existing.diff_size_score = result.breakdown.get("diff_size", 0)
                existing.is_suspected_ai = result.is_suspected_ai
                existing.slop_signals = json.dumps(result.slop_signals)
                session.add(existing)
            else:
                # New PR — post a fresh comment
                comment = await github.create_pr_comment(owner, repo_name, pr_number, comment_body)
                comment_id = comment.get("id")
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
                    comment_id=comment_id,
                )
                session.add(pr_score)

            # Update contributor reputation
            await update_contributor_reputation(
                session=session,
                repo_full_name=repo_full_name,
                author_login=author,
                score=result.score,
            )

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


async def _fetch_repo_config(github: GitHubClient, owner: str, repo: str) -> KlarityConfig:
    """Try to fetch .klarity.yml from the repo. Returns default config on failure."""
    try:
        content = await github.get_file_content(owner, repo, ".klarity.yml")
        return parse_config(content)
    except Exception:
        return parse_config(None)


async def _get_existing_score(
    session: AsyncSession, repo_full_name: str, pr_number: int
) -> PRScore | None:
    result = await session.exec(
        select(PRScore)
        .where(PRScore.repo_full_name == repo_full_name)
        .where(PRScore.pr_number == pr_number)
    )
    return result.first()


async def _mark_event_processed(session: AsyncSession, delivery_id: str) -> None:
    result = await session.exec(
        select(WebhookEvent).where(WebhookEvent.delivery_id == delivery_id)
    )
    event = result.first()
    if event:
        event.processed = True
        event.processed_at = datetime.utcnow()
        session.add(event)


async def _mark_event_failed(session: AsyncSession, delivery_id: str, error: str) -> None:
    result = await session.exec(
        select(WebhookEvent).where(WebhookEvent.delivery_id == delivery_id)
    )
    event = result.first()
    if event:
        event.error = error[:500]
        session.add(event)


async def process_issue_event(
    ctx: dict[str, Any],
    payload: dict[str, Any],
    delivery_id: str,
) -> None:
    """
    Background task: triage an issue (label classification, template check).
    Full duplicate detection via ChromaDB comes in v0.2.
    """
    repo = payload["repository"]
    issue = payload["issue"]
    installation_id = payload["installation"]["id"]

    repo_full_name = repo["full_name"]
    issue_number = issue["number"]
    author = issue["user"]["login"]
    issue_body = issue.get("body") or ""
    issue_title = issue.get("title") or ""

    # Skip bots
    if author.lower() in DEFAULT_IGNORE_LIST or author.lower().endswith("[bot]"):
        logger.info("task.process_issue.ignored_bot", author=author, repo=repo_full_name)
        return

    logger.info("task.process_issue.start", repo=repo_full_name, issue=issue_number, author=author)

    async with AsyncSessionLocal() as session:
        try:
            github = GitHubClient(installation_id)
            owner = repo["owner"]["login"]
            repo_name = repo["name"]

            config = await _fetch_repo_config(github, owner, repo_name)

            if not config.features.issue_triage:
                return

            # Classify issue type from title + body
            label = _classify_issue(issue_title, issue_body)
            if label:
                await github.ensure_label_exists(owner, repo_name, label, _ISSUE_LABEL_COLORS.get(label, "cccccc"))
                await github.add_labels(owner, repo_name, issue_number, [label])

            # Check for missing reproduction steps on bug reports
            if label == "bug" and not _has_repro_steps(issue_body):
                comment = (
                    f"Hi @{author}! This looks like a bug report, but it doesn't seem to include "
                    "steps to reproduce the issue. Could you add:\n\n"
                    "1. Steps to reproduce\n2. Expected behavior\n3. Actual behavior\n\n"
                    "This helps maintainers investigate faster. Thanks!"
                )
                await github.create_pr_comment(owner, repo_name, issue_number, comment)

            await _mark_event_processed(session, delivery_id)
            await session.commit()

            logger.info("task.process_issue.complete", repo=repo_full_name, issue=issue_number, label=label)

        except Exception as exc:
            await session.rollback()
            await _mark_event_failed(session, delivery_id, str(exc))
            await session.commit()
            logger.error("task.process_issue.failed", repo=repo_full_name, issue=issue_number, error=str(exc), exc_info=True)
            raise


_ISSUE_LABEL_COLORS = {
    "bug": "d73a4a",
    "feature-request": "a2eeef",
    "question": "d876e3",
    "needs-more-info": "e4e669",
    "good-first-issue": "7057ff",
}

_BUG_PATTERN = re.compile(r"\b(bug|error|crash|exception|broken|fail|issue|problem|wrong|incorrect|unexpected)\b", re.IGNORECASE)
_FEATURE_PATTERN = re.compile(r"\b(feature|request|add|support|implement|enhance|improve|allow|enable|wish|would be nice)\b", re.IGNORECASE)
_QUESTION_PATTERN = re.compile(r"\b(how|why|what|when|where|can i|is it possible|does|should)\b", re.IGNORECASE)
_REPRO_PATTERN = re.compile(r"(steps to reproduce|to reproduce|reproduction|repro|how to reproduce)", re.IGNORECASE)


def _classify_issue(title: str, body: str) -> str | None:
    text = f"{title} {body}"
    bug_score = len(_BUG_PATTERN.findall(text))
    feature_score = len(_FEATURE_PATTERN.findall(text))
    question_score = len(_QUESTION_PATTERN.findall(text))

    if bug_score == 0 and feature_score == 0 and question_score == 0:
        return None

    if bug_score >= feature_score and bug_score >= question_score:
        return "bug"
    if feature_score >= question_score:
        return "feature-request"
    return "question"


def _has_repro_steps(body: str) -> bool:
    return bool(_REPRO_PATTERN.search(body))
