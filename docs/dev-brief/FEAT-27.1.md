# Technical Brief: FEAT-27.1 -- PyPI Package Readiness

**Status:** Ready for Implementation
**ADR:** `docs/adr/ADR-040-epic027-packaging-distribution-cicd.md`
**Epic:** EPIC-027 Packaging, Distribution, and CI/CD

## Story Disposition

| Story | Description | Action | Notes |
|---|---|---|---|
| STORY-27.1.1 | Finalize `pyproject.toml` metadata | **Implement** | Add `keywords`, `[project.urls]`, Python 3.13 classifier |
| STORY-27.1.2 | Configure optional dependency groups | **Skip** | Already done: `[xml]`, `[dev]`, `[docs]` exist. Add `pytest-cov` to `[dev]` only |
| STORY-27.1.3 | Add `py.typed` marker | **Skip** | Already exists at `src/pyarchi/py.typed` |
| STORY-27.1.4 | Build and validate sdist + wheel | **Implement** | `python -m build` + `twine check dist/*` |
| STORY-27.1.5 | Smoke-test installed wheel | **Implement** | Install in clean venv, `import pyarchi; pyarchi.__version__` |

## Implementation Scope

### 1. `pyproject.toml` Changes

Add after the `classifiers` list:

```toml
keywords = ["archimate", "enterprise-architecture", "metamodel", "archi", "open-group"]
```

Add new classifier:

```toml
"Programming Language :: Python :: 3.13",
```

Add new section after `[project.optional-dependencies]`:

```toml
[project.urls]
Homepage = "https://github.com/pyarchi-org/pyarchi"
Documentation = "https://pyarchi-org.github.io/pyarchi/"
Repository = "https://github.com/pyarchi-org/pyarchi"
Issues = "https://github.com/pyarchi-org/pyarchi/issues"
Changelog = "https://github.com/pyarchi-org/pyarchi/blob/main/CHANGELOG.md"
```

Add `pytest-cov` to `[project.optional-dependencies] dev`:

```toml
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "mypy>=1.10",
    "pydantic>=2.0,<3.0",
    "ruff>=0.4",
    "lxml>=5.0,<6.0",
    "build>=1.0",
    "twine>=5.0",
]
```

### 2. `src/pyarchi/__init__.py` -- Add `__version__`

Insert near top of file, after the module docstring:

```python
from importlib.metadata import version as _meta_version

__version__: str = _meta_version("pyarchi")
```

### 3. `CHANGELOG.md` -- New File at Repo Root

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Unreleased

### Added

- ArchiMate 3.2 metamodel: all element types across Business, Application,
  Technology, Strategy, Motivation, Implementation & Migration, and Composite layers.
- Complete relationship type system with source/target validation matrix.
- Open Group Exchange Format XML serialization and deserialization.
- XSD validation against bundled ArchiMate 3.1 schemas.
- Model comparison and diff utilities (`diff_models`).
- Conformance profiles (flag, standard, full).
- Opaque XML preservation for organizations and views during round-trip.
- Archi tool interoperability (import and export verified).
- PEP 561 `py.typed` marker for downstream type checking.
```

### 4. Build Verification Commands

```bash
pip install -e ".[dev]"
python -m build
twine check dist/*
```

Both commands must exit 0. The `dist/` directory must contain exactly one `.tar.gz` and one `.whl`.

## Validation

| Check | Command | Expected |
|---|---|---|
| Version exposed | `python -c "import pyarchi; print(pyarchi.__version__)"` | `0.1.0` |
| Keywords in metadata | `twine check dist/*` | PASSED |
| URLs in metadata | `unzip -p dist/*.whl '*/METADATA' \| grep Homepage` | Contains placeholder URL |
| Wheel contents | `unzip -l dist/*.whl \| grep py.typed` | File present |

## TDD Anchors

| Test | Description |
|---|---|
| `test_version_exposed` | `import pyarchi; assert pyarchi.__version__ == "0.1.0"` |
| `test_version_is_string` | `assert isinstance(pyarchi.__version__, str)` |
| `test_changelog_exists` | `Path("CHANGELOG.md").exists()` and contains `[0.1.0]` |
| `test_build_produces_artifacts` | `python -m build` in subprocess; assert `.whl` and `.tar.gz` in `dist/` |
| `test_twine_check_passes` | `twine check dist/*` exits 0 |
