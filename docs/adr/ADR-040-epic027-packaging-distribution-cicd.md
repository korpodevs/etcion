# ADR-040: Packaging, Distribution, and CI/CD

## Context

etcion is feature-complete through Phase 3 with Phase 4 enhancements delivered.
The library is only installable via `pip install -e .` from a source checkout.
EPIC-027 covers everything needed to publish to PyPI, automate quality gates, and
establish a repeatable release process.

Current state of `pyproject.toml`:

- Build backend: `hatchling` (already configured)
- Version: `0.1.0` (already set)
- Extras: `[xml]`, `[dev]`, `[docs]` (already defined)
- `py.typed` marker: present at `src/etcion/py.typed`
- XSD schemas: bundled at `src/etcion/serialization/schema/*.xsd`
- Classifiers, license, readme: present but incomplete (missing `urls`, `keywords`)

## Decisions

### D1 -- Build System

| Aspect | Decision |
|---|---|
| Backend | **hatchling** (no change) -- already configured, generates sdist + wheel |
| Build command | `python -m build` (PEP 517 frontend) |
| Artifacts | sdist (`.tar.gz`) + wheel (`.whl`) |
| Schema inclusion | XSD files already inside `src/etcion/` tree -- included automatically by hatchling wheel target |

**Rationale:** hatchling is already wired up, produces standards-compliant packages,
and supports the `packages = ["src/etcion"]` layout without additional plugins.

### D2 -- Version Strategy

| Aspect | Decision |
|---|---|
| Scheme | Semantic Versioning (MAJOR.MINOR.PATCH) |
| First release | `0.1.0` -- pre-1.0 signals API may evolve |
| Source of truth | `pyproject.toml` `[project] version` field |
| Runtime access | `etcion.__version__` read from `importlib.metadata` |
| Bump mechanism | Manual edit of `pyproject.toml` (no `setuptools-scm` or `hatch version` -- one field, low ceremony) |

**Rationale:** A single-source version in `pyproject.toml` avoids sync issues.
`importlib.metadata.version("etcion")` is the standard way to expose it at runtime
without duplicating the string.

### D3 -- PyPI Publishing

| Aspect | Decision |
|---|---|
| Method | **GitHub Actions Trusted Publishing** (OIDC) |
| Token management | None -- OIDC exchanges a short-lived token per workflow run |
| Test index | `test.pypi.org` for dry-run validation before first real publish |
| Action | `pypa/gh-action-pypi-publish@release/v1` |

**Rationale:** Trusted publishing eliminates long-lived API tokens. The PyPA-maintained
action is the recommended path and handles attestation.

### D4 -- CI/CD Pipelines

Two workflow files in `.github/workflows/`:

| Workflow | Trigger | Jobs |
|---|---|---|
| `ci.yml` | push, pull_request (all branches) | lint, typecheck, test |
| `release.yml` | push tag `v*` | build, publish to PyPI |

**`ci.yml` job matrix:**

| Job | Command | Python |
|---|---|---|
| Lint | `ruff check src/ test/` | 3.12 |
| Format | `ruff format --check src/ test/` | 3.12 |
| Type-check | `mypy src/` | 3.12 |
| Test | `pytest --strict-markers` | 3.12, 3.13 |

**`release.yml` steps:**

1. Checkout with full history
2. `python -m build` (sdist + wheel)
3. `twine check dist/*` (metadata validation)
4. Publish via `pypa/gh-action-pypi-publish` (trusted publishing)

**Rationale:** Two workflows keep concerns separate. Tag-based release is the simplest
trigger that maps to semver. Python 3.12 is primary; 3.13 in the test matrix catches
forward-compatibility issues early.

### D5 -- Package Metadata Completions

Fields to add or update in `pyproject.toml`:

| Field | Value |
|---|---|
| `keywords` | `["archimate", "enterprise-architecture", "metamodel", "archi", "open-group"]` |
| `[project.urls] Homepage` | `https://github.com/<org>/etcion` |
| `[project.urls] Documentation` | `https://<org>.github.io/etcion/` |
| `[project.urls] Repository` | `https://github.com/<org>/etcion` |
| `[project.urls] Issues` | `https://github.com/<org>/etcion/issues` |
| `[project.urls] Changelog` | `https://github.com/<org>/etcion/blob/main/CHANGELOG.md` |

Existing fields (`name`, `version`, `description`, `readme`, `license`,
`requires-python`, `authors`, `classifiers`) are already present and sufficient.

### D6 -- CHANGELOG

| Aspect | Decision |
|---|---|
| Format | [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) |
| File | `CHANGELOG.md` at repository root |
| Initial entry | `## [0.1.0] - <release-date>` covering Phases 1-4 |

**Rationale:** ADR-039 D5 (EPIC-026) specified the format. This decision confirms
the initial release content scope.

### D7 -- Pre-commit Hooks

| Aspect | Decision |
|---|---|
| Adoption | **Deferred** |

**Rationale:** The CI pipeline enforces the same checks (ruff, mypy). Adding
pre-commit introduces a local setup step with no additional coverage. Revisit
when contributor count increases.

### D8 -- Release Process

Tag-driven, fully automated:

```
git tag v0.1.0
git push --tags
```

The `release.yml` workflow builds, validates, and publishes. No manual `twine upload`.

### D9 -- Coverage Reporting

| Aspect | Decision |
|---|---|
| Tool | `pytest-cov` |
| Threshold | 90% line coverage (fail CI if below) |
| Reporting | Terminal summary in CI; no external service initially |

## Consequences

**Positive:**

- Zero-token publishing via OIDC reduces secret management burden.
- Tag-based releases make the version-to-artifact mapping auditable.
- CI catches lint, type, and test regressions on every push.
- Metadata completions ensure discoverability on PyPI.

**Negative:**

- Trusted publishing requires one-time configuration in PyPI project settings.
- Manual version bumps in `pyproject.toml` could drift from tags (mitigated by
  CI `twine check` comparing built metadata against the tag).
- No Windows/macOS CI matrix -- pure-Python library, low risk, but not zero.
