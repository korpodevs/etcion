"""Merged tests for test_packaging."""

import subprocess
import tomllib
from pathlib import Path

import pytest

import etcion

# ---------------------------------------------------------------------------
# Resolve the repository root relative to this test file.
# test/ is one level below the repo root.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent


class TestVersionExposed:
    """etcion.__version__ is publicly accessible and correct."""

    def test_version_exposed(self) -> None:
        assert etcion.__version__ == "0.11.0"

    def test_version_is_string(self) -> None:
        assert isinstance(etcion.__version__, str)

    def test_version_in_all(self) -> None:
        assert "__version__" in etcion.__all__


class TestChangelogExists:
    """CHANGELOG.md exists at repo root and documents the current release."""

    def test_changelog_file_exists(self) -> None:
        changelog = _REPO_ROOT / "CHANGELOG.md"
        assert changelog.exists(), f"CHANGELOG.md not found at {changelog}"

    def test_changelog_contains_current_version(self) -> None:
        changelog = _REPO_ROOT / "CHANGELOG.md"
        content = changelog.read_text(encoding="utf-8")
        assert "[0.1.0]" in content, "CHANGELOG.md must contain [0.1.0] section"

    def test_changelog_has_keep_a_changelog_reference(self) -> None:
        changelog = _REPO_ROOT / "CHANGELOG.md"
        content = changelog.read_text(encoding="utf-8")
        assert "Keep a Changelog" in content


@pytest.mark.slow
class TestBuildArtifacts:
    """Building the package produces valid sdist and wheel artifacts."""

    def test_build_produces_artifacts(self) -> None:
        """Running python -m build must produce exactly one .whl and one .tar.gz."""
        result = subprocess.run(
            ["python", "-m", "build", str(_REPO_ROOT)],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )
        assert result.returncode == 0, (
            f"python -m build failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        dist_dir = _REPO_ROOT / "dist"
        wheels = list(dist_dir.glob("*.whl"))
        sdists = list(dist_dir.glob("*.tar.gz"))
        assert len(wheels) >= 1, f"No .whl found in {dist_dir}"
        assert len(sdists) >= 1, f"No .tar.gz found in {dist_dir}"

    def test_twine_check_passes(self) -> None:
        """twine check must report PASSED for all dist artifacts."""
        dist_dir = _REPO_ROOT / "dist"
        artifacts = list(dist_dir.glob("*.whl")) + list(dist_dir.glob("*.tar.gz"))
        assert artifacts, "No artifacts in dist/ -- run test_build_produces_artifacts first"
        result = subprocess.run(
            ["twine", "check", *[str(a) for a in artifacts]],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )
        assert result.returncode == 0, (
            f"twine check failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "PASSED" in result.stdout or "PASSED" in result.stderr


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
    """ci.yml must declare lint, format, typecheck, test-fast, and test-full jobs."""
    for job in ("lint:", "format:", "typecheck:", "test-fast:", "test-full:"):
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


# ---------------------------------------------------------------------------
# Resolve the repository root relative to this test file.
# test/ is one level below the repo root.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent


class TestReleasingDocExists:
    """docs/releasing.md must exist and contain the release checklist."""

    def test_releasing_doc_exists(self) -> None:
        releasing = _REPO_ROOT / "docs" / "releasing.md"
        assert releasing.exists(), f"docs/releasing.md not found at {releasing}"

    def test_releasing_doc_is_non_empty(self) -> None:
        releasing = _REPO_ROOT / "docs" / "releasing.md"
        content = releasing.read_text(encoding="utf-8")
        assert len(content.strip()) > 0, "docs/releasing.md must not be empty"

    def test_releasing_doc_contains_checklist(self) -> None:
        releasing = _REPO_ROOT / "docs" / "releasing.md"
        content = releasing.read_text(encoding="utf-8")
        assert "Release Checklist" in content, (
            "docs/releasing.md must contain a 'Release Checklist' section"
        )

    def test_releasing_doc_contains_hotfix_process(self) -> None:
        releasing = _REPO_ROOT / "docs" / "releasing.md"
        content = releasing.read_text(encoding="utf-8")
        assert "Hotfix" in content, "docs/releasing.md must document the hotfix process"

    def test_releasing_doc_contains_tag_instructions(self) -> None:
        releasing = _REPO_ROOT / "docs" / "releasing.md"
        content = releasing.read_text(encoding="utf-8")
        assert "git tag" in content, "docs/releasing.md must include git tag instructions"


class TestPytestCovInDevDeps:
    """pytest-cov must be declared in the [dev] optional-dependency group."""

    def test_pytest_cov_in_dev_deps(self) -> None:
        pyproject = _REPO_ROOT / "pyproject.toml"
        with pyproject.open("rb") as fh:
            data = tomllib.load(fh)

        dev_deps: list[str] = data["project"]["optional-dependencies"].get("dev", [])
        has_pytest_cov = any("pytest-cov" in dep for dep in dev_deps)
        assert has_pytest_cov, (
            f"pytest-cov not found in [project.optional-dependencies.dev]. "
            f"Current dev deps: {dev_deps}"
        )
