"""Tests for FEAT-27.2: CI/CD Pipelines.

Verifies that the GitHub Actions workflow files exist and contain
the required structural elements as specified in the dev brief.
All assertions use plain string containment — no YAML parser required.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_YML = REPO_ROOT / ".github" / "workflows" / "release.yml"


# ---------------------------------------------------------------------------
# Existence tests
# ---------------------------------------------------------------------------


def test_ci_yml_exists() -> None:
    """ci.yml must exist at .github/workflows/ci.yml."""
    assert CI_YML.exists(), f"Expected {CI_YML} to exist"


def test_release_yml_exists() -> None:
    """release.yml must exist at .github/workflows/release.yml."""
    assert RELEASE_YML.exists(), f"Expected {RELEASE_YML} to exist"


# ---------------------------------------------------------------------------
# ci.yml structural tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def ci_text() -> str:
    """Return the raw text content of ci.yml."""
    return CI_YML.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def release_text() -> str:
    """Return the raw text content of release.yml."""
    return RELEASE_YML.read_text(encoding="utf-8")


def test_ci_has_required_jobs(ci_text: str) -> None:
    """ci.yml must declare lint, format, typecheck, and test jobs."""
    for job in ("lint:", "format:", "typecheck:", "test:"):
        assert job in ci_text, f"Expected job '{job}' to be present in ci.yml"


def test_ci_test_matrix(ci_text: str) -> None:
    """ci.yml test job matrix must include Python 3.12 and 3.13."""
    assert '"3.12"' in ci_text, "Expected Python 3.12 in test matrix"
    assert '"3.13"' in ci_text, "Expected Python 3.13 in test matrix"


def test_ci_coverage_threshold(ci_text: str) -> None:
    """ci.yml must pass --cov-fail-under=90 to pytest."""
    assert "--cov-fail-under=90" in ci_text, (
        "Expected --cov-fail-under=90 coverage threshold in ci.yml"
    )


def test_ci_runs_ruff_check(ci_text: str) -> None:
    """ci.yml lint job must invoke ruff check."""
    assert "ruff check src/ test/" in ci_text, "Expected 'ruff check src/ test/' in ci.yml lint job"


def test_ci_runs_ruff_format(ci_text: str) -> None:
    """ci.yml format job must invoke ruff format --check."""
    assert "ruff format --check src/ test/" in ci_text, (
        "Expected 'ruff format --check src/ test/' in ci.yml format job"
    )


def test_ci_runs_mypy(ci_text: str) -> None:
    """ci.yml typecheck job must invoke mypy src/."""
    assert "mypy src/" in ci_text, "Expected 'mypy src/' in ci.yml typecheck job"


def test_ci_concurrency_cancel(ci_text: str) -> None:
    """ci.yml must configure concurrency with cancel-in-progress."""
    assert "cancel-in-progress: true" in ci_text, "Expected 'cancel-in-progress: true' in ci.yml"


# ---------------------------------------------------------------------------
# release.yml structural tests
# ---------------------------------------------------------------------------


def test_release_triggers_on_vtag(release_text: str) -> None:
    """release.yml must trigger on push of tags matching v*."""
    assert 'tags: ["v*"]' in release_text, "Expected 'tags: [\"v*\"]' push trigger in release.yml"


def test_release_has_trusted_publishing(release_text: str) -> None:
    """release.yml must grant id-token: write for OIDC trusted publishing."""
    assert "id-token: write" in release_text, "Expected 'id-token: write' permission in release.yml"


def test_release_has_build_job(release_text: str) -> None:
    """release.yml must contain a build job."""
    assert "build:" in release_text, "Expected 'build:' job in release.yml"


def test_release_has_publish_job(release_text: str) -> None:
    """release.yml must contain a publish job."""
    assert "publish:" in release_text, "Expected 'publish:' job in release.yml"


def test_release_publish_uses_pypi_action(release_text: str) -> None:
    """release.yml publish job must use the official PyPI publish action."""
    assert "pypa/gh-action-pypi-publish" in release_text, (
        "Expected 'pypa/gh-action-pypi-publish' action in release.yml"
    )


def test_release_publish_needs_build(release_text: str) -> None:
    """release.yml publish job must declare a dependency on the build job."""
    assert "needs: build" in release_text, "Expected 'needs: build' in release.yml publish job"
