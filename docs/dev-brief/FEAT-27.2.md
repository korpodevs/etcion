# Technical Brief: FEAT-27.2 -- CI/CD Pipelines

**Status:** Ready for Implementation
**ADR:** `docs/adr/ADR-040-epic027-packaging-distribution-cicd.md`
**Epic:** EPIC-027 Packaging, Distribution, and CI/CD

## Story Disposition

| Story | Description | Action | Notes |
|---|---|---|---|
| STORY-27.2.1 | GitHub Actions: lint, typecheck, test on 3.12 | **Implement** | Part of `ci.yml` |
| STORY-27.2.2 | Matrix testing for 3.11 and 3.13 | **Partial** | ADR-040 specifies 3.12 + 3.13 only (no 3.11); `requires-python = ">=3.12"` |
| STORY-27.2.3 | Coverage reporting with 90% threshold | **Implement** | `pytest-cov` with `--cov-fail-under=90` |
| STORY-27.2.4 | Automated PyPI publishing on tags | **Implement** | `release.yml` with trusted publishing |
| STORY-27.2.5 | CI config files are valid YAML | **Skip** | GitHub Actions validates on push; separate test adds no value |

## File: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["**"]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: ruff check src/ test/

  format:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: ruff format --check src/ test/

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: mypy src/

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest --cov=pyarchi --cov-report=term-missing --cov-fail-under=90
```

## File: `.github/workflows/release.yml`

```yaml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build twine
      - run: python -m build
      - run: twine check dist/*
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
```

## Key Decisions

| Aspect | Value |
|---|---|
| Python matrix (test only) | 3.12, 3.13 |
| Python for lint/format/typecheck | 3.12 only |
| Coverage threshold | 90% line coverage |
| Concurrency | Cancel in-progress runs on same ref |
| Publishing auth | OIDC trusted publishing (no tokens) |
| Publish environment | `pypi` (must be created in GitHub repo settings) |

## Setup Required After Repo Creation

1. Create GitHub repository
2. Go to PyPI project settings, configure trusted publisher:
   - Owner: `pyarchi-org`
   - Repository: `pyarchi`
   - Workflow: `release.yml`
   - Environment: `pypi`
3. In GitHub repo Settings > Environments, create `pypi` environment

## TDD Anchors

| Test | Description |
|---|---|
| `test_ci_yml_exists` | `.github/workflows/ci.yml` exists and is valid YAML |
| `test_release_yml_exists` | `.github/workflows/release.yml` exists and is valid YAML |
| `test_ci_has_required_jobs` | Parse `ci.yml`; assert jobs `lint`, `format`, `typecheck`, `test` present |
| `test_ci_test_matrix` | Parse `ci.yml`; assert `test` job matrix includes `3.12` and `3.13` |
| `test_release_has_trusted_publishing` | Parse `release.yml`; assert `id-token: write` permission present |
| `test_release_triggers_on_vtag` | Parse `release.yml`; assert trigger is `push.tags: ["v*"]` |
