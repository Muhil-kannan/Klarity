"""
SQLModel database models.
"""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Repository(SQLModel, table=True):
    __tablename__ = "repositories"

    id: int | None = Field(default=None, primary_key=True)
    github_id: int = Field(unique=True, index=True)
    full_name: str = Field(index=True)          # e.g. "owner/repo"
    installation_id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PRScore(SQLModel, table=True):
    __tablename__ = "pr_scores"

    id: int | None = Field(default=None, primary_key=True)
    repo_full_name: str = Field(index=True)
    pr_number: int
    pr_title: str
    author_login: str = Field(index=True)
    score: int                                  # 0–100
    linked_issue_score: int = Field(default=0)
    tests_score: int = Field(default=0)
    description_score: int = Field(default=0)
    commit_quality_score: int = Field(default=0)
    author_history_score: int = Field(default=0)
    diff_size_score: int = Field(default=0)
    is_suspected_ai: bool = Field(default=False)
    slop_signals: str = Field(default="[]")     # JSON list of triggered signals
    comment_id: int | None = Field(default=None)  # GitHub comment ID
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContributorReputation(SQLModel, table=True):
    __tablename__ = "contributor_reputations"

    id: int | None = Field(default=None, primary_key=True)
    repo_full_name: str = Field(index=True)
    author_login: str = Field(index=True)
    total_prs: int = Field(default=0)
    merged_prs: int = Field(default=0)
    closed_prs: int = Field(default=0)
    abandoned_prs: int = Field(default=0)
    avg_score: float = Field(default=0.0)
    first_contribution_at: datetime | None = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WebhookEvent(SQLModel, table=True):
    __tablename__ = "webhook_events"

    id: int | None = Field(default=None, primary_key=True)
    delivery_id: str = Field(unique=True, index=True)
    event_type: str                             # pull_request, issues, etc.
    action: str                                 # opened, edited, closed, etc.
    repo_full_name: str = Field(index=True)
    payload_summary: str = Field(default="{}")  # JSON summary (not full payload)
    processed: bool = Field(default=False)
    error: str | None = Field(default=None)
    received_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime | None = Field(default=None)
