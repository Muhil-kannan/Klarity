"""
Dashboard API endpoints.
Returns scored PRs and stats for the frontend dashboard.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.models import PRScore
from app.db.session import get_session

router = APIRouter()


@router.get("/scores")
async def list_pr_scores(
    repo: Optional[str] = Query(default=None, description="Filter by repo full name"),
    min_score: int = Query(default=0, ge=0, le=100),
    max_score: int = Query(default=100, ge=0, le=100),
    suspected_ai_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> List[PRScore]:
    query = select(PRScore)

    if repo:
        query = query.where(PRScore.repo_full_name == repo)
    if suspected_ai_only:
        query = query.where(PRScore.is_suspected_ai == True)  # noqa: E712

    query = (
        query
        .where(PRScore.score >= min_score)
        .where(PRScore.score <= max_score)
        .order_by(PRScore.score.desc())
        .offset(offset)
        .limit(limit)
    )

    results = await session.exec(query)
    return results.all()


@router.get("/scores/{repo_full_name}/{pr_number}")
async def get_pr_score(
    repo_full_name: str,
    pr_number: int,
    session: AsyncSession = Depends(get_session),
) -> PRScore:
    result = await session.exec(
        select(PRScore)
        .where(PRScore.repo_full_name == repo_full_name)
        .where(PRScore.pr_number == pr_number)
    )
    score = result.first()
    if not score:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score not found")
    return score
