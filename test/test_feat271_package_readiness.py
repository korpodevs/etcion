"""Tests for FEAT-27.1 -- PyPI Package Readiness.

Verifies that:
- pyarchi exposes __version__ == "0.1.0"
- CHANGELOG.md exists at repo root and contains [0.1.0]
- python -m build produces a .whl and a .tar.gz
- twine check dist/* exits with code 0
"""

import subprocess
from pathlib import Path

import pytest

import pyarchi

# ---------------------------------------------------------------------------
# Resolve the repository root relative to this test file.
# test/ is one level below the repo root.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent


class TestVersionExposed:
    """pyarchi.__version__ is publicly accessible and correct."""

    def test_version_exposed(self) -> None:
        assert pyarchi.__version__ == "0.1.0"

    def test_version_is_string(self) -> None:
        assert isinstance(pyarchi.__version__, str)

    def test_version_in_all(self) -> None:
        assert "__version__" in pyarchi.__all__


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
        assert artifacts, (
            "No artifacts in dist/ -- run test_build_produces_artifacts first"
        )
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
