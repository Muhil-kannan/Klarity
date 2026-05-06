"""
Contributor reputation tracker.
Maintains per-repo contributor history updated on every PR event.
"""

from datetime import datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import get_logger
from app.db.models import ContributorReputation

logger = get_logger(__name__)


async def update_contributor_reputation(
    session: AsyncSession,
    repo_full_name: str,
    author_login: str,
    score: int,
) -> ContributorReputation:
    """
    Upsert a contributor's reputation record after a PR is scored.
    Called on every pull_request event (opened or re-scored).
    """
    result = await session.exec(
        select(ContributorReputation)
        .where(ContributorReputation.repo_full_name == repo_full_name)
        .where(ContributorReputation.author_login == author_login)
    )
    rep = result.first()

    if rep is None:
        rep = ContributorReputation(
            repo_full_name=repo_full_name,
            author_login=author_login,
            total_prs=1,
            avg_score=float(score),
            first_contribution_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(rep)
        logger.info(
            "reputation.created",
            repo=repo_full_name,
            author=author_login,
            score=score,
        )
    else:
        # Recalculate rolling average
        new_total = rep.total_prs + 1
        rep.avg_score = round(
            (rep.avg_score * rep.total_prs + score) / new_total, 2
        )
        rep.total_prs = new_total
        rep.updated_at = datetime.utcnow()
        session.add(rep)
        logger.info(
            "reputation.updated",
            repo=repo_full_name,
            author=author_login,
            new_avg=rep.avg_score,
            total_prs=rep.total_prs,
        )

    return rep


async def get_contributor_reputation(
    session: AsyncSession,
    repo_full_name: str,
    author_login: str,
) -> ContributorReputation | None:
    result = await session.exec(
        select(ContributorReputation)
        .where(ContributorReputation.repo_full_name == repo_full_name)
        .where(ContributorReputation.author_login == author_login)
    )
    return result.first()
