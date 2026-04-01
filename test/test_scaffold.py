"""Acceptance tests for FEAT-00.1: Package Configuration.

Covers five stories:
  STORY-00.1.1 — pyproject.toml
  STORY-00.1.2 — package layout and importability
  STORY-00.1.3 — pytest configuration
  STORY-00.1.4 — Ruff configuration
  STORY-00.1.5 — mypy configuration
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _load_toml() -> dict[str, Any]:
    with PYPROJECT.open("rb") as fh:
        return tomllib.load(fh)


# ===========================================================================
# STORY-00.1.1 — pyproject.toml
# ===========================================================================


class TestPyprojectExists:
    def test_pyproject_toml_exists(self) -> None:
        assert PYPROJECT.exists(), "pyproject.toml must exist at the repo root"

    def test_pyproject_is_valid_toml(self) -> None:
        # tomllib raises an exception on invalid TOML
        data = _load_toml()
        assert isinstance(data, dict)

    def test_no_setup_py(self) -> None:
        assert not (REPO_ROOT / "setup.py").exists(), "setup.py must not exist"

    def test_no_setup_cfg(self) -> None:
        assert not (REPO_ROOT / "setup.cfg").exists(), "setup.cfg must not exist"

    def test_no_requirements_txt(self) -> None:
        assert not (REPO_ROOT / "requirements.txt").exists(), "requirements.txt must not exist"


class TestBuildSystem:
    def test_build_backend_is_hatchling(self) -> None:
        data = _load_toml()
        assert data["build-system"]["build-backend"] == "hatchling.build"

    def test_hatchling_in_requires(self) -> None:
        data = _load_toml()
        requires = data["build-system"]["requires"]
        assert any("hatchling" in r for r in requires)


class TestProjectMetadata:
    def test_project_name(self) -> None:
        data = _load_toml()
        assert data["project"]["name"] == "etcion"

    def test_project_version(self) -> None:
        data = _load_toml()
        assert data["project"]["version"] == "0.4.0"

    def test_requires_python(self) -> None:
        data = _load_toml()
        assert data["project"]["requires-python"] == ">=3.12"

    def test_pydantic_in_dependencies(self) -> None:
        data = _load_toml()
        deps: list[str] = data["project"]["dependencies"]
        assert any("pydantic" in dep for dep in deps), (
            "pydantic must be listed in [project] dependencies"
        )

    def test_pydantic_dependency_version_bounds(self) -> None:
        data = _load_toml()
        deps: list[str] = data["project"]["dependencies"]
        pydantic_dep = next((d for d in deps if "pydantic" in d), None)
        assert pydantic_dep is not None
        assert ">=2.0" in pydantic_dep
        assert "<3.0" in pydantic_dep


# ===========================================================================
# STORY-00.1.2 — package layout and importability
# ===========================================================================


class TestPackageLayout:
    def test_init_py_exists(self) -> None:
        assert (REPO_ROOT / "src" / "etcion" / "__init__.py").exists()

    def test_py_typed_exists(self) -> None:
        assert (REPO_ROOT / "src" / "etcion" / "py.typed").exists(), (
            "py.typed marker file (PEP 561) must exist"
        )


class TestPackageImport:
    def test_etcion_is_importable(self) -> None:
        import etcion  # noqa: PLC0415

        assert etcion is not None

    def test_spec_version_is_3_2(self) -> None:
        import etcion  # noqa: PLC0415

        assert etcion.SPEC_VERSION == "3.2"

    def test_all_is_defined(self) -> None:
        import etcion  # noqa: PLC0415

        assert hasattr(etcion, "__all__")
        assert isinstance(etcion.__all__, list)

    def test_spec_version_in_all(self) -> None:
        import etcion  # noqa: PLC0415

        assert "SPEC_VERSION" in etcion.__all__


# ===========================================================================
# STORY-00.1.3 — pytest configuration
# ===========================================================================


class TestPytestConfig:
    def test_pytest_ini_options_section_exists(self) -> None:
        data = _load_toml()
        assert "tool" in data
        assert "pytest" in data["tool"]
        assert "ini_options" in data["tool"]["pytest"]

    def test_testpaths_contains_test(self) -> None:
        data = _load_toml()
        testpaths: list[str] = data["tool"]["pytest"]["ini_options"]["testpaths"]
        assert "test" in testpaths

    def test_pythonpath_contains_src(self) -> None:
        data = _load_toml()
        pythonpath: list[str] = data["tool"]["pytest"]["ini_options"]["pythonpath"]
        assert "src" in pythonpath

    def test_addopts_contains_strict_markers(self) -> None:
        data = _load_toml()
        addopts: str = data["tool"]["pytest"]["ini_options"]["addopts"]
        assert "--strict-markers" in addopts

    def test_conftest_exists(self) -> None:
        assert (REPO_ROOT / "test" / "conftest.py").exists()


class TestConftestFixtures:
    def test_empty_model_fixture(self, empty_model: dict[str, Any]) -> None:
        assert "elements" in empty_model
        assert "relationships" in empty_model
        assert empty_model["elements"] == []
        assert empty_model["relationships"] == []

    def test_sample_element_fixture(self, sample_element: dict[str, Any]) -> None:
        assert "id" in sample_element
        assert "name" in sample_element
        assert sample_element["name"] == "Sample Element"
        assert "description" in sample_element
        assert "documentation_url" in sample_element


# ===========================================================================
# STORY-00.1.4 — Ruff configuration
# ===========================================================================


class TestRuffConfig:
    def test_ruff_section_exists(self) -> None:
        data = _load_toml()
        assert "ruff" in data["tool"], "[tool.ruff] section must exist"

    def test_ruff_target_version(self) -> None:
        data = _load_toml()
        assert data["tool"]["ruff"]["target-version"] == "py312"

    def test_ruff_lint_section_exists(self) -> None:
        data = _load_toml()
        assert "lint" in data["tool"]["ruff"], "[tool.ruff.lint] section must exist"

    def test_ruff_lint_select_contains_required_codes(self) -> None:
        data = _load_toml()
        select: list[str] = data["tool"]["ruff"]["lint"]["select"]
        for code in ("E", "W", "I", "ANN", "B"):
            assert code in select, f"Ruff lint select must contain '{code}'"

    def test_ruff_per_file_ignores_test_ann(self) -> None:
        data = _load_toml()
        per_file: dict[str, list[str]] = data["tool"]["ruff"]["lint"]["per-file-ignores"]
        assert "test/**" in per_file, "per-file-ignores must have a 'test/**' key"
        assert "ANN" in per_file["test/**"], "ANN must be suppressed for test/** files"


# ===========================================================================
# STORY-00.1.5 — mypy configuration
# ===========================================================================


class TestMypyConfig:
    def test_mypy_section_exists(self) -> None:
        data = _load_toml()
        assert "mypy" in data["tool"], "[tool.mypy] section must exist"

    def test_mypy_strict(self) -> None:
        data = _load_toml()
        assert data["tool"]["mypy"]["strict"] is True

    def test_mypy_plugins_contains_pydantic(self) -> None:
        data = _load_toml()
        plugins: list[str] = data["tool"]["mypy"]["plugins"]
        assert "pydantic.mypy" in plugins

    def test_mypy_warn_return_any(self) -> None:
        data = _load_toml()
        assert data["tool"]["mypy"]["warn_return_any"] is True

    def test_mypy_warn_unreachable(self) -> None:
        data = _load_toml()
        assert data["tool"]["mypy"]["warn_unreachable"] is True
