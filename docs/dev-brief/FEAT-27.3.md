# Technical Brief: FEAT-27.3 -- Release Process

**Status:** Ready for Implementation
**ADR:** `docs/adr/ADR-040-epic027-packaging-distribution-cicd.md`
**Epic:** EPIC-027 Packaging, Distribution, and CI/CD

## Story Disposition

| Story | Description | Action | Notes |
|---|---|---|---|
| STORY-27.3.1 | Version management via hatch/setuptools-scm | **Skip** | ADR-040 D2 chose manual `pyproject.toml` edit; no tooling needed |
| STORY-27.3.2 | Create `CHANGELOG.md` | **Covered by FEAT-27.1** | Created in STORY-27.1.4 scope |
| STORY-27.3.3 | Release checklist document | **Implement** | `docs/releasing.md` |

## File: `docs/releasing.md`

```markdown
# Release Process

## Prerequisites

- Write access to the repository
- PyPI trusted publishing configured (see ADR-040 D3)

## Release Checklist

1. **Confirm CI is green** on the `main` branch.

2. **Update version** in `pyproject.toml`:
   ```
   version = "X.Y.Z"
   ```

3. **Update CHANGELOG.md**:
   - Rename `## [X.Y.Z] - Unreleased` to `## [X.Y.Z] - YYYY-MM-DD`
   - Add a new `## [Unreleased]` section above it

4. **Commit the version bump**:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Release vX.Y.Z"
   ```

5. **Create and push the tag**:
   ```bash
   git tag vX.Y.Z
   git push origin main --tags
   ```

6. **Verify the release**:
   - Watch `.github/workflows/release.yml` in the Actions tab
   - Confirm the package appears on [PyPI](https://pypi.org/project/pyarchi/)
   - Verify: `pip install pyarchi==X.Y.Z`

## Local Build Verification (Optional)

```bash
rm -rf dist/
python -m build
twine check dist/*
```

## Hotfix Process

1. Branch from the release tag: `git checkout -b hotfix/vX.Y.Z vX.Y.Z`
2. Apply fix, update CHANGELOG, bump patch version
3. Merge to `main`, tag, push
```

## `pyproject.toml` -- pytest-cov Configuration

Add to existing `[tool.pytest.ini_options]`:

```toml
[tool.pytest.ini_options]
testpaths = ["test"]
pythonpath = ["src"]
addopts = "-ra -q --strict-markers --cov=pyarchi --cov-report=term-missing --cov-fail-under=90"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks integration tests requiring external resources",
]
```

**Note:** Adding `--cov` flags to `addopts` means every local `pytest` run produces coverage. This is the simplest configuration. If developers find it noisy, coverage can be moved to CI-only by removing it from `addopts` and keeping it only in the `ci.yml` command.

## End-to-End Verification

| Step | Command | Expected |
|---|---|---|
| Clean build | `rm -rf dist/ && python -m build` | Exit 0, one `.tar.gz` + one `.whl` |
| Metadata check | `twine check dist/*` | PASSED for both artifacts |
| Install wheel | `pip install dist/pyarchi-0.1.0-py3-none-any.whl` | Success |
| Version check | `python -c "import pyarchi; print(pyarchi.__version__)"` | `0.1.0` |
| Coverage | `pytest --cov=pyarchi --cov-fail-under=90` | Passes threshold |

## TDD Anchors

| Test | Description |
|---|---|
| `test_releasing_doc_exists` | `docs/releasing.md` exists and is non-empty |
| `test_pytest_cov_configured` | Parse `pyproject.toml`; assert `--cov=pyarchi` in `addopts` or verify `pytest-cov` in dev deps |
| `test_full_build_pipeline` | Subprocess: `python -m build` then `twine check dist/*`; both exit 0 |
