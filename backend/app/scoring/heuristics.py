"""
Heuristic-based PR scoring checks.
Each check returns a score (0 to its max weight) and an optional suggestion.
"""

import re
from dataclasses import dataclass
from typing import Any

GENERIC_COMMIT_PATTERNS = re.compile(
    r"^(fix|update|change|misc|wip|temp|test|patch|hotfix|refactor|cleanup|"
    r"add feature|bug fix|fix bug|update code|minor fix|small fix|quick fix|"
    r"initial commit|first commit|commit|changes|stuff|things|work in progress)\.?$",
    re.IGNORECASE,
)

ISSUE_LINK_PATTERN = re.compile(
    r"(closes|fixes|resolves|close|fix|resolve)\s+#\d+",
    re.IGNORECASE,
)


@dataclass
class CheckResult:
    score: int
    max_score: int
    passed: bool
    suggestion: str | None = None


@dataclass
class HeuristicWeights:
    linked_issue: int = 15
    tests_changed: int = 20
    description_quality: int = 15
    commit_quality: int = 20
    author_history: int = 20
    diff_size: int = 10
    min_description_words: int = 30
    max_diff_lines: int = 500


def check_linked_issue(pr_body: str | None, weights: HeuristicWeights) -> CheckResult:
    """Check if the PR body references a GitHub issue."""
    if pr_body and ISSUE_LINK_PATTERN.search(pr_body):
        return CheckResult(score=weights.linked_issue, max_score=weights.linked_issue, passed=True)
    return CheckResult(
        score=0,
        max_score=weights.linked_issue,
        passed=False,
        suggestion="Link this PR to an existing issue using 'Closes #N' or 'Fixes #N'.",
    )


def check_tests_changed(files: list[dict[str, Any]], weights: HeuristicWeights) -> CheckResult:
    """Check if any test files were added or modified."""
    test_pattern = re.compile(r"(test|spec|__tests__|_test\.)", re.IGNORECASE)
    has_tests = any(test_pattern.search(f.get("filename", "")) for f in files)

    # Also check if any logic files were changed (if only docs changed, tests aren't needed)
    logic_pattern = re.compile(r"\.(py|ts|tsx|js|jsx|go|rs|java|rb|cs)$", re.IGNORECASE)
    has_logic_changes = any(logic_pattern.search(f.get("filename", "")) for f in files)

    if not has_logic_changes:
        # No logic changed — tests not required
        return CheckResult(score=weights.tests_changed, max_score=weights.tests_changed, passed=True)

    if has_tests:
        return CheckResult(score=weights.tests_changed, max_score=weights.tests_changed, passed=True)

    return CheckResult(
        score=0,
        max_score=weights.tests_changed,
        passed=False,
        suggestion="Add or update tests to cover the changes in this PR.",
    )


def check_description_quality(pr_body: str | None, weights: HeuristicWeights) -> CheckResult:
    """Check if the PR description is meaningful."""
    if not pr_body or not pr_body.strip():
        return CheckResult(
            score=0,
            max_score=weights.description_quality,
            passed=False,
            suggestion=f"Add a PR description with at least {weights.min_description_words} words explaining what changed and why.",
        )

    word_count = len(pr_body.split())

    if word_count >= weights.min_description_words:
        return CheckResult(score=weights.description_quality, max_score=weights.description_quality, passed=True)

    # Partial score for short descriptions
    partial = int((word_count / weights.min_description_words) * weights.description_quality)
    return CheckResult(
        score=partial,
        max_score=weights.description_quality,
        passed=False,
        suggestion=f"Expand the PR description — currently {word_count} words, aim for {weights.min_description_words}+.",
    )


def check_commit_quality(commits: list[dict[str, Any]], weights: HeuristicWeights) -> CheckResult:
    """Check if commit messages are descriptive."""
    if not commits:
        return CheckResult(score=0, max_score=weights.commit_quality, passed=False,
                           suggestion="Add descriptive commit messages.")

    generic_count = 0
    for commit in commits:
        message = commit.get("commit", {}).get("message", "").strip().split("\n")[0]
        if GENERIC_COMMIT_PATTERNS.match(message):
            generic_count += 1

    ratio_generic = generic_count / len(commits)

    if ratio_generic == 0:
        return CheckResult(score=weights.commit_quality, max_score=weights.commit_quality, passed=True)
    elif ratio_generic < 0.5:
        partial = int(weights.commit_quality * 0.5)
        return CheckResult(score=partial, max_score=weights.commit_quality, passed=False,
                           suggestion="Some commit messages are too generic. Use descriptive messages like 'fix: handle null user in auth middleware'.")
    else:
        return CheckResult(
            score=0,
            max_score=weights.commit_quality,
            passed=False,
            suggestion="Commit messages are too generic (e.g., 'fix bug', 'update'). Write descriptive messages that explain the why.",
        )


def check_author_history(merged_pr_count: int, weights: HeuristicWeights) -> CheckResult:
    """Score based on author's prior merged PRs in this repo."""
    if merged_pr_count >= 5:
        return CheckResult(score=weights.author_history, max_score=weights.author_history, passed=True)
    elif merged_pr_count > 0:
        partial = int((merged_pr_count / 5) * weights.author_history)
        return CheckResult(score=partial, max_score=weights.author_history, passed=True)
    else:
        # First-time contributor — not penalized heavily, just no bonus
        return CheckResult(score=0, max_score=weights.author_history, passed=True)


def check_diff_size(
    files: list[dict[str, Any]],
    pr_body: str | None,
    weights: HeuristicWeights,
) -> CheckResult:
    """Check if the diff size is proportionate to the stated scope."""
    total_changes = sum(f.get("changes", 0) for f in files)

    if total_changes <= weights.max_diff_lines:
        return CheckResult(score=weights.diff_size, max_score=weights.diff_size, passed=True)

    # Large diff — check if there's an issue link (context provided)
    has_context = bool(pr_body and ISSUE_LINK_PATTERN.search(pr_body))

    if has_context:
        # Large but has context — partial score
        return CheckResult(score=int(weights.diff_size * 0.5), max_score=weights.diff_size, passed=False,
                           suggestion=f"This is a large PR ({total_changes} lines changed). Consider breaking it into smaller PRs.")
    else:
        return CheckResult(
            score=0,
            max_score=weights.diff_size,
            passed=False,
            suggestion=f"This PR changes {total_changes} lines with no linked issue. Large PRs without context are hard to review.",
        )


def run_all_checks(
    pr_body: str | None,
    files: list[dict[str, Any]],
    commits: list[dict[str, Any]],
    merged_pr_count: int,
    weights: HeuristicWeights | None = None,
) -> tuple[int, dict[str, int], list[str]]:
    """
    Run all heuristic checks and return:
    - total score (0–100)
    - breakdown dict {factor: points}
    - list of suggestions
    """
    if weights is None:
        weights = HeuristicWeights()

    checks = {
        "linked_issue": check_linked_issue(pr_body, weights),
        "tests_changed": check_tests_changed(files, weights),
        "description_quality": check_description_quality(pr_body, weights),
        "commit_quality": check_commit_quality(commits, weights),
        "author_history": check_author_history(merged_pr_count, weights),
        "diff_size": check_diff_size(files, pr_body, weights),
    }

    breakdown = {name: result.score for name, result in checks.items()}
    total_score = sum(breakdown.values())
    suggestions = [r.suggestion for r in checks.values() if r.suggestion]

    return total_score, breakdown, suggestions
