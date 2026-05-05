"""
Unit tests for the AI slop detector.
"""

import pytest

from app.scoring.slop_detector import detect_slop


class TestSlopDetector:
    def test_clean_pr_not_flagged(self):
        files = [
            {"filename": "src/auth.py"},
            {"filename": "tests/test_auth.py"},
        ]
        commits = [{"commit": {"message": "feat: add OAuth2 login"}}]
        body = "Closes #42\n\nThis PR implements OAuth2 login using the GitHub provider. " * 5

        is_ai, signals = detect_slop(
            pr_body=body,
            files=files,
            commits=commits,
            merged_pr_count=3,
        )
        assert not is_ai

    def test_slop_pr_flagged(self):
        files = [
            {"filename": "src/main.py"},
            {"filename": "README.md"},
            {"filename": "config.yml"},
            {"filename": "setup.py"},
            {"filename": "requirements.txt"},
        ]
        commits = [
            {"commit": {"message": "fix bug"}},
            {"commit": {"message": "update code"}},
        ]
        body = "This PR adds the feature. I have implemented the changes. Please let me know if this looks good."

        is_ai, signals = detect_slop(
            pr_body=body,
            files=files,
            commits=commits,
            merged_pr_count=0,
        )
        assert is_ai
        assert len(signals) > 0

    def test_no_tests_logic_changed_is_signal(self):
        files = [{"filename": "src/core.py"}]
        commits = [{"commit": {"message": "fix bug"}}]

        is_ai, signals = detect_slop(
            pr_body="short",
            files=files,
            commits=commits,
            merged_pr_count=0,
        )
        assert "no_tests_logic_changed" in signals
