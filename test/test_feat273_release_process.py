"""Tests for FEAT-27.3 -- Release Process documentation and pytest-cov configuration.

Verifies that:
- docs/releasing.md exists and is non-empty
- pytest-cov is listed in the [dev] optional-dependency group of pyproject.toml
"""

from pathlib import Path

import tomllib

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
        assert "Hotfix" in content, (
            "docs/releasing.md must document the hotfix process"
        )

    def test_releasing_doc_contains_tag_instructions(self) -> None:
        releasing = _REPO_ROOT / "docs" / "releasing.md"
        content = releasing.read_text(encoding="utf-8")
        assert "git tag" in content, (
            "docs/releasing.md must include git tag instructions"
        )


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
