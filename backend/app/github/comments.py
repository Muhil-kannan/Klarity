"""
PR and issue comment templates.
Generates the markdown comment body posted to GitHub.
"""


SCORE_EMOJI = {
    range(80, 101): "🟢",
    range(60, 80): "🟡",
    range(40, 60): "🟠",
    range(20, 40): "🔴",
    range(0, 20): "⛔",
}

SCORE_LABEL = {
    range(80, 101): "Excellent",
    range(60, 80): "Good",
    range(40, 60): "Needs Work",
    range(20, 40): "Poor",
    range(0, 20): "Suspected Slop",
}


def _get_score_meta(score: int) -> tuple[str, str]:
    for r, emoji in SCORE_EMOJI.items():
        if score in r:
            label = SCORE_LABEL[r]
            return emoji, label
    return "⛔", "Unknown"


def build_pr_score_comment(
    score: int,
    breakdown: dict[str, int],
    suggestions: list[str],
    is_suspected_ai: bool,
    author: str,
) -> str:
    emoji, label = _get_score_meta(score)

    score_bar = _build_score_bar(score)

    breakdown_rows = "\n".join([
        f"| {factor.replace('_', ' ').title()} | {pts} pts |"
        for factor, pts in breakdown.items()
    ])

    suggestions_text = ""
    if suggestions:
        suggestions_list = "\n".join(f"- {s}" for s in suggestions)
        suggestions_text = f"\n\n**To improve this score:**\n{suggestions_list}"

    ai_warning = ""
    if is_suspected_ai:
        ai_warning = f"""
> ⚠️ **AI Generation Detected**
> Hi @{author}, this PR shows signals that suggest it may have been AI-generated without full review.
> Could you confirm you've read and understood every line of code? We want to make sure you can support this change after it merges.

"""

    return f"""## {emoji} Klarity Score: {score}/100 — {label}

{score_bar}
{ai_warning}
<details>
<summary>Score Breakdown</summary>

| Factor | Points |
|--------|--------|
{breakdown_rows}
| **Total** | **{score}/100** |

</details>
{suggestions_text}

---
<sub>Powered by [Klarity](https://github.com/your-org/klarity) — AI Triage Assistant for Open Source Maintainers</sub>
"""


def _build_score_bar(score: int) -> str:
    filled = round(score / 10)
    empty = 10 - filled
    return "█" * filled + "░" * empty + f" {score}%"
