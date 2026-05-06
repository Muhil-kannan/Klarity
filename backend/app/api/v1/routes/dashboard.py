"""
Dashboard API endpoints.
Returns scored PRs, stats, and contributor data for the frontend.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.models import ContributorReputation, PRScore
from app.db.session import get_session

router = APIRouter()


# ── Response schemas ──────────────────────────────────────────────────────────

class StatsResponse(BaseModel):
    total_prs: int
    avg_score: float
    high_quality: int       # score >= 60
    needs_work: int         # score < 40
    suspected_ai: int
    repos: int              # distinct repos tracked


class ContributorResponse(BaseModel):
    author_login: str
    repo_full_name: str
    total_prs: int
    merged_prs: int
    abandoned_prs: int
    avg_score: float
    first_contribution_at: str | None
    updated_at: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/scores", response_model=list[PRScore])
async def list_pr_scores(
    repo: str | None = Query(default=None),
    min_score: int = Query(default=0, ge=0, le=100),
    max_score: int = Query(default=100, ge=0, le=100),
    suspected_ai_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[PRScore]:
    query = select(PRScore)

    if repo:
        query = query.where(PRScore.repo_full_name == repo)
    if suspected_ai_only:
        query = query.where(PRScore.is_suspected_ai == True)  # noqa: E712

    query = (
        query
        .where(PRScore.score >= min_score)
        .where(PRScore.score <= max_score)
        .order_by(col(PRScore.score).desc())
        .offset(offset)
        .limit(limit)
    )

    results = await session.exec(query)
    return list(results.all())


@router.get("/scores/{repo_owner}/{repo_name}/{pr_number}", response_model=PRScore)
async def get_pr_score(
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    session: AsyncSession = Depends(get_session),
) -> PRScore:
    repo_full_name = f"{repo_owner}/{repo_name}"
    result = await session.exec(
        select(PRScore)
        .where(PRScore.repo_full_name == repo_full_name)
        .where(PRScore.pr_number == pr_number)
    )
    score = result.first()
    if not score:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score not found")
    return score


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    repo: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> StatsResponse:
    query = select(PRScore)
    if repo:
        query = query.where(PRScore.repo_full_name == repo)

    results = await session.exec(query)
    scores = results.all()

    if not scores:
        return StatsResponse(
            total_prs=0, avg_score=0.0, high_quality=0,
            needs_work=0, suspected_ai=0, repos=0,
        )

    total = len(scores)
    avg = round(sum(s.score for s in scores) / total, 1)
    repos = len({s.repo_full_name for s in scores})

    return StatsResponse(
        total_prs=total,
        avg_score=avg,
        high_quality=sum(1 for s in scores if s.score >= 60),
        needs_work=sum(1 for s in scores if s.score < 40),
        suspected_ai=sum(1 for s in scores if s.is_suspected_ai),
        repos=repos,
    )


@router.get("/contributors", response_model=list[ContributorResponse])
async def list_contributors(
    repo: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[ContributorResponse]:
    query = select(ContributorReputation)
    if repo:
        query = query.where(ContributorReputation.repo_full_name == repo)

    query = query.order_by(col(ContributorReputation.avg_score).desc()).offset(offset).limit(limit)
    results = await session.exec(query)
    reps = results.all()

    return [
        ContributorResponse(
            author_login=r.author_login,
            repo_full_name=r.repo_full_name,
            total_prs=r.total_prs,
            merged_prs=r.merged_prs,
            abandoned_prs=r.abandoned_prs,
            avg_score=r.avg_score,
            first_contribution_at=r.first_contribution_at.isoformat() if r.first_contribution_at else None,
            updated_at=r.updated_at.isoformat(),
        )
        for r in reps
    ]
