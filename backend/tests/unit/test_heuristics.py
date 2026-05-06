"""
Unit tests for the heuristic scoring checks.
"""


from app.scoring.heuristics import (
    HeuristicWeights,
    check_author_history,
    check_commit_quality,
    check_description_quality,
    check_linked_issue,
    check_tests_changed,
    run_all_checks,
)

weights = HeuristicWeights()


class TestLinkedIssue:
    def test_closes_issue(self):
        result = check_linked_issue("Closes #42", weights)
        assert result.passed
        assert result.score == weights.linked_issue

    def test_fixes_issue(self):
        result = check_linked_issue("This PR fixes #10 by refactoring the auth module.", weights)
        assert result.passed

    def test_no_link(self):
        result = check_linked_issue("Just a small change", weights)
        assert not result.passed
        assert result.score == 0
        assert result.suggestion is not None

    def test_empty_body(self):
        result = check_linked_issue(None, weights)
        assert not result.passed


class TestTestsChanged:
    def test_has_test_file(self):
        files = [{"filename": "src/auth.py"}, {"filename": "tests/test_auth.py"}]
        result = check_tests_changed(files, weights)
        assert result.passed

    def test_no_tests_logic_changed(self):
        files = [{"filename": "src/auth.py"}]
        result = check_tests_changed(files, weights)
        assert not result.passed
        assert result.score == 0

    def test_no_logic_changed_no_tests_needed(self):
        files = [{"filename": "README.md"}, {"filename": "docs/guide.md"}]
        result = check_tests_changed(files, weights)
        assert result.passed


class TestDescriptionQuality:
    def test_good_description(self):
        body = " ".join(["word"] * 50)
        result = check_description_quality(body, weights)
        assert result.passed
        assert result.score == weights.description_quality

    def test_short_description(self):
        result = check_description_quality("fix bug", weights)
        assert not result.passed
        assert result.score < weights.description_quality

    def test_empty_description(self):
        result = check_description_quality(None, weights)
        assert not result.passed
        assert result.score == 0


class TestCommitQuality:
    def test_good_commits(self):
        commits = [
            {"commit": {"message": "feat: add JWT authentication middleware"}},
            {"commit": {"message": "test: add unit tests for auth module"}},
        ]
        result = check_commit_quality(commits, weights)
        assert result.passed

    def test_generic_commits(self):
        commits = [
            {"commit": {"message": "fix bug"}},
            {"commit": {"message": "update"}},
        ]
        result = check_commit_quality(commits, weights)
        assert not result.passed
        assert result.score == 0


class TestAuthorHistory:
    def test_experienced_contributor(self):
        result = check_author_history(10, weights)
        assert result.score == weights.author_history

    def test_new_contributor(self):
        result = check_author_history(0, weights)
        assert result.score == 0

    def test_some_history(self):
        result = check_author_history(2, weights)
        assert 0 < result.score < weights.author_history


class TestRunAllChecks:
    def test_perfect_pr(self):
        files = [{"filename": "src/auth.py", "changes": 50}, {"filename": "tests/test_auth.py", "changes": 30}]
        commits = [{"commit": {"message": "feat: implement OAuth2 login flow"}}]
        body = "Closes #42\n\n" + " ".join(["word"] * 50)

        score, breakdown, suggestions = run_all_checks(
            pr_body=body,
            files=files,
            commits=commits,
            merged_pr_count=5,
        )
        assert score == 100
        assert len(suggestions) == 0

    def test_empty_pr(self):
        score, breakdown, suggestions = run_all_checks(
            pr_body=None,
            files=[{"filename": "src/main.py", "changes": 600}],
            commits=[{"commit": {"message": "fix"}}],
            merged_pr_count=0,
        )
        assert score < 20
        assert len(suggestions) > 0
