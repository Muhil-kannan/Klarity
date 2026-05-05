"""
AI slop signal detector.
Aggregates heuristic signals to flag suspected AI-generated PRs.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


# Known AI boilerplate patterns in PR descriptions
AI_BOILERPLATE_PATTERNS = [
    re.compile(r"this (pr|pull request) (adds|implements|introduces|updates|fixes)", re.IGNORECASE),
    re.compile(r"i (have|'ve) (added|implemented|updated|fixed|refactored)", re.IGNORECASE),
    re.compile(r"(the following changes (have been|were) made)", re.IGNORECASE),
    re.compile(r"(please (let me know|review|feel free))", re.IGNORECASE),
    re.compile(r"(hope this helps|happy to (make|discuss|address))", re.IGNORECASE),
    re.compile(r"(lgtm|looks good to me)", re.IGNORECASE),
]

GENERIC_COMMIT_PATTERN = re.compile(
    r"^(fix|update|change|misc|wip|temp|patch|hotfix|refactor|cleanup|"
    r"add feature|bug fix|fix bug|update code|minor fix|small fix|quick fix|"
    r"initial commit|first commit|commit|changes|stuff|things)\.?$",
    re.IGNORECASE,
)


@dataclass
class SlopSignal:
    name: str
    weight: str          # "high" | "medium" | "low"
    triggered: bool
    reason: str = ""


WEIGHT_VALUES = {"high": 3, "medium": 2, "low": 1}
DEFAULT_SLOP_THRESHOLD = 5   # total weight to trigger suspected-ai label


def detect_slop(
    pr_body: Optional[str],
    files: List[Dict[str, Any]],
    commits: List[Dict[str, Any]],
    merged_pr_count: int,
    slop_threshold: int = DEFAULT_SLOP_THRESHOLD,
) -> tuple[bool, List[str]]:
    """
    Returns (is_suspected_ai, list_of_triggered_signal_names).
    """
    signals: List[SlopSignal] = []

    # Signal 1: Generic commit messages (high)
    generic_commits = [
        c for c in commits
        if GENERIC_COMMIT_PATTERN.match(
            c.get("commit", {}).get("message", "").strip().split("\n")[0]
        )
    ]
    signals.append(SlopSignal(
        name="generic_commit_messages",
        weight="high",
        triggered=len(generic_commits) > 0 and len(generic_commits) / max(len(commits), 1) > 0.5,
        reason=f"{len(generic_commits)}/{len(commits)} commits have generic messages",
    ))

    # Signal 2: No tests but logic files changed (high)
    logic_pattern = re.compile(r"\.(py|ts|tsx|js|jsx|go|rs|java|rb|cs)$", re.IGNORECASE)
    test_pattern = re.compile(r"(test|spec|__tests__|_test\.)", re.IGNORECASE)
    has_logic = any(logic_pattern.search(f.get("filename", "")) for f in files)
    has_tests = any(test_pattern.search(f.get("filename", "")) for f in files)
    signals.append(SlopSignal(
        name="no_tests_logic_changed",
        weight="high",
        triggered=has_logic and not has_tests,
        reason="Logic files changed but no test files added or modified",
    ))

    # Signal 3: Very short description (medium)
    word_count = len(pr_body.split()) if pr_body else 0
    signals.append(SlopSignal(
        name="short_description",
        weight="medium",
        triggered=word_count < 20,
        reason=f"PR description is only {word_count} words",
    ))

    # Signal 4: Zero prior contributions (medium)
    signals.append(SlopSignal(
        name="zero_repo_history",
        weight="medium",
        triggered=merged_pr_count == 0,
        reason="Author has no prior merged PRs in this repository",
    ))

    # Signal 5: Touches many unrelated files (medium)
    file_extensions = set()
    for f in files:
        ext = f.get("filename", "").rsplit(".", 1)[-1].lower()
        if ext:
            file_extensions.add(ext)
    signals.append(SlopSignal(
        name="unrelated_file_changes",
        weight="medium",
        triggered=len(files) >= 5 and len(file_extensions) >= 4,
        reason=f"PR touches {len(files)} files across {len(file_extensions)} different file types",
    ))

    # Signal 6: AI boilerplate in description (high)
    boilerplate_matches = 0
    if pr_body:
        boilerplate_matches = sum(1 for p in AI_BOILERPLATE_PATTERNS if p.search(pr_body))
    signals.append(SlopSignal(
        name="boilerplate_description",
        weight="high",
        triggered=boilerplate_matches >= 2,
        reason=f"PR description matches {boilerplate_matches} AI boilerplate patterns",
    ))

    # Calculate total weight
    total_weight = sum(
        WEIGHT_VALUES[s.weight] for s in signals if s.triggered
    )

    triggered_names = [s.name for s in signals if s.triggered]
    is_suspected_ai = total_weight >= slop_threshold

    if is_suspected_ai:
        logger.info(
            "slop_detector.suspected_ai",
            total_weight=total_weight,
            threshold=slop_threshold,
            signals=triggered_names,
        )

    return is_suspected_ai, triggered_names
