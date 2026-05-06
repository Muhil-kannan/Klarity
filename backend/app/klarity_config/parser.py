"""
.klarity.yml configuration parser.
Loads and validates per-repo configuration with sensible defaults.
"""


import yaml
from pydantic import BaseModel, Field


class ScoringConfig(BaseModel):
    linked_issue_weight: int = Field(default=15, ge=0, le=100)
    tests_changed_weight: int = Field(default=20, ge=0, le=100)
    description_quality_weight: int = Field(default=15, ge=0, le=100)
    commit_quality_weight: int = Field(default=20, ge=0, le=100)
    author_history_weight: int = Field(default=20, ge=0, le=100)
    diff_size_weight: int = Field(default=10, ge=0, le=100)
    min_description_words: int = Field(default=30, ge=0)
    max_diff_lines: int = Field(default=500, ge=0)


class AIDetectionConfig(BaseModel):
    enabled: bool = True
    slop_threshold: int = Field(default=5, ge=0)
    checks: dict[str, bool] = Field(default_factory=lambda: {
        "generic_commit_messages": True,
        "no_tests_large_diff": True,
        "zero_repo_history": True,
        "boilerplate_description": True,
        "unrelated_file_changes": True,
    })


class AutoResponsesConfig(BaseModel):
    no_linked_issue: str = (
        "Hi @{author}! Thanks for opening this PR. "
        "Could you link it to an existing issue? If there isn't one yet, "
        "please open an issue first so we can discuss the change."
    )
    no_tests: str = (
        "Thanks @{author}! This PR doesn't seem to include test changes. "
        "Could you add tests for the new behavior?"
    )
    suspected_ai: str = (
        "Hi @{author}! This PR has some signals that suggest parts of it "
        "may have been AI-generated without full review. "
        "Could you confirm you've read and understood every line of code?"
    )
    first_time_contributor: str = (
        "Welcome @{author}! This is your first contribution to this project. "
        "We appreciate you taking the time! A maintainer will review this soon."
    )
    low_score: str = (
        "Hi @{author}! Klarity flagged a few things on this PR that might "
        "help it get reviewed faster. See the score breakdown above for details."
    )


class FeaturesConfig(BaseModel):
    scoring: bool = True
    ai_detection: bool = True
    issue_triage: bool = True
    contributor_reputation: bool = True
    weekly_digest: bool = True
    dashboard: bool = True


class KlarityConfig(BaseModel):
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    ai_detection: AIDetectionConfig = Field(default_factory=AIDetectionConfig)
    auto_responses: AutoResponsesConfig = Field(default_factory=AutoResponsesConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)


def parse_config(yaml_content: str | None) -> KlarityConfig:
    """
    Parse a .klarity.yml string into a KlarityConfig.
    Falls back to defaults if content is None or invalid.
    """
    if not yaml_content:
        return KlarityConfig()

    try:
        raw = yaml.safe_load(yaml_content)
        if not isinstance(raw, dict):
            return KlarityConfig()

        klarity_section = raw.get("klarity", raw)  # support both root and nested
        return KlarityConfig.model_validate(klarity_section)
    except Exception:
        # Never crash on bad config — fall back to defaults
        return KlarityConfig()
