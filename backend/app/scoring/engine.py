"""
Main scoring orchestrator.
Coordinates heuristics, slop detection, and produces the final score.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.klarity_config.parser import KlarityConfig
from app.scoring.heuristics import HeuristicWeights, run_all_checks
from app.scoring.slop_detector import detect_slop

logger = get_logger(__name__)


@dataclass
class ScoringResult:
    score: int
    breakdown: Dict[str, int]
    suggestions: List[str]
    is_suspected_ai: bool
    slop_signals: List[str]
    labels_to_apply: List[str]


async def score_pull_request(
    pr_data: Dict[str, Any],
    files: List[Dict[str, Any]],
    commits: List[Dict[str, Any]],
    merged_pr_count: int,
    config: Optional[KlarityConfig] = None,
) -> ScoringResult:
    """
    Run the full scoring pipeline for a pull request.
    """
    if config is None:
        config = KlarityConfig()

    weights = HeuristicWeights(
        linked_issue=config.scoring.linked_issue_weight,
        tests_changed=config.scoring.tests_changed_weight,
        description_quality=config.scoring.description_quality_weight,
        commit_quality=config.scoring.commit_quality_weight,
        author_history=config.scoring.author_history_weight,
        diff_size=config.scoring.diff_size_weight,
        min_description_words=config.scoring.min_description_words,
        max_diff_lines=config.scoring.max_diff_lines,
    )

    pr_body = pr_data.get("body") or ""
    author = pr_data.get("user", {}).get("login", "unknown")

    # Run heuristic checks
    score, breakdown, suggestions = run_all_checks(
        pr_body=pr_body,
        files=files,
        commits=commits,
        merged_pr_count=merged_pr_count,
        weights=weights,
    )

    # Run slop detector
    is_suspected_ai, slop_signals = detect_slop(
        pr_body=pr_body,
        files=files,
        commits=commits,
        merged_pr_count=merged_pr_count,
        slop_threshold=config.ai_detection.slop_threshold,
    )

    # Determine labels to apply
    labels = _determine_labels(score, breakdown, is_suspected_ai, config)

    logger.info(
        "scoring.complete",
        author=author,
        score=score,
        is_suspected_ai=is_suspected_ai,
        labels=labels,
    )

    return ScoringResult(
        score=score,
        breakdown=breakdown,
        suggestions=suggestions,
        is_suspected_ai=is_suspected_ai,
        slop_signals=slop_signals,
        labels_to_apply=labels,
    )


def _determine_labels(
    score: int,
    breakdown: Dict[str, int],
    is_suspected_ai: bool,
    config: KlarityConfig,
) -> List[str]:
    labels = []

    if is_suspected_ai:
        labels.append("suspected-ai")

    if breakdown.get("tests_changed", 1) == 0:
        labels.append("needs-tests")

    if breakdown.get("linked_issue", 1) == 0:
        labels.append("needs-issue-link")

    if score < 40:
        labels.append("low-quality")

    return labels
