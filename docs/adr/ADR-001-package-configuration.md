# ADR-001: Package Configuration and Toolchain

## Status

ACCEPTED

## Date

2026-03-23

## Context

etcion is a greenfield Python library implementing the ArchiMate 3.2 metamodel. The repository skeleton exists with `src/`, `test/`, `docs/`, and `etc/` directories, a Python 3.12.3 virtual environment, and no source code or build configuration. Before any metamodel work can begin, the project needs a fully configured build system, package layout, test runner, linter, and type checker.

The library will model a complex, deeply nested type hierarchy (abstract base classes, mixins, enums, validation rules) derived from a formal specification. This places unusually high demands on static analysis tooling: every element type, relationship category, and validation constraint must be expressible through the type system and verifiable at both development time and CI time. The library will also depend on Pydantic v2 for runtime data validation of model instances, making type-checker compatibility with Pydantic a hard requirement.

The choices made here will constrain every subsequent epic in the backlog, so they must be deliberate.

## Decision

### Build System: `pyproject.toml` with Hatchling

Use a single `pyproject.toml` as the sole configuration file for project metadata, dependencies, and all tool settings. Use Hatchling as the build backend because it natively supports the `src/` layout without additional configuration, has minimal overhead, and follows modern Python packaging standards (PEP 621, PEP 517). No `setup.py`, `setup.cfg`, or `requirements.txt` files will exist.

### Python Version: 3.12 minimum

Set `requires-python = ">=3.12"`. Python 3.12 provides the full set of modern typing features needed by the library: `type` statement (PEP 695), improved error messages, and performance improvements to `dataclasses` and `typing`. Requiring 3.12 as the floor avoids conditional compatibility code and lets the library use the latest typing syntax natively.

### Package Layout: `src/etcion/`

Use the `src/` layout where the importable package lives at `src/etcion/`. This layout prevents accidental imports of the package from the project root during testing (a common source of "it works on my machine" bugs), enforces that tests always run against the installed package, and is the recommended layout by the Python Packaging Authority (PyPA).

The `__init__.py` at `src/etcion/` will serve as the public API surface, re-exporting the key types that downstream consumers need: `Model`, core element base classes, relationship types, and enums.

### Runtime Dependency: Pydantic v2

Declare `pydantic>=2.0,<3.0` as the sole runtime dependency. Pydantic v2 provides:

- **High-performance validation** built on pydantic-core (Rust), critical for validating large models with thousands of elements and relationships.
- **Native support for discriminated unions**, which maps directly to the ArchiMate pattern of abstract base types with many concrete subtypes.
- **JSON Schema generation** from models, which will later support the ArchiMate Exchange Format serialization.
- **Strict mode** for preventing implicit type coercion, aligning with the library's goal of preventing illegal models.

lxml is intentionally excluded from the initial dependency list. XML parsing and serialization (the Exchange Format) is a Phase 2+ concern and will be addressed in a separate ADR when that work begins.

### Test Runner: pytest

Configure pytest as the test runner via `[tool.pytest.ini_options]` in `pyproject.toml`. pytest is the de facto standard for Python testing, supports fixture-based composition (essential for sharing model fixtures across test modules), parametrized tests (essential for testing the Appendix B permission matrix), and has a rich plugin ecosystem.

A `test/conftest.py` file will provide shared fixtures that construct reusable model fragments -- element instances, relationship instances, and pre-built model containers -- so that test modules across all epics can compose test scenarios without duplicating setup logic.

The pytest configuration will set:
- `testpaths = ["test"]` to scope test discovery.
- `pythonpath = ["src"]` to ensure imports resolve against the source tree.
- Strict markers to prevent typos in custom markers from silently passing.

### Linter and Formatter: Ruff

Configure Ruff as both the linter and formatter via `[tool.ruff]` in `pyproject.toml`. Ruff replaces flake8, isort, pyflakes, pycodestyle, and Black with a single Rust-based tool that runs in milliseconds even on large codebases. The configuration will enforce:

- **PEP 8 compliance** (E, W rule sets).
- **Import sorting** (I rule set), replacing isort.
- **Type annotation enforcement** (ANN rule set), ensuring all public functions and methods carry type hints.
- **Bugbear rules** (B rule set), catching common Python pitfalls.
- **Pydantic-specific rules** (if available) to enforce Pydantic v2 best practices.

Target Python version will be set to `py312` to match the minimum version constraint.

### Type Checker: mypy (strict mode)

Configure mypy via `[tool.mypy]` in `pyproject.toml` with strict mode enabled. Key settings:

- `strict = true` -- enables all optional strictness flags.
- `plugins = ["pydantic.mypy"]` -- the Pydantic mypy plugin provides accurate type inference for Pydantic models, which is essential since the entire metamodel hierarchy will be built on Pydantic `BaseModel`.
- `warn_return_any = true` and `warn_unreachable = true` for catching subtle bugs in the complex type hierarchy.

mypy strict mode is chosen over pyright/pylance because of its mature Pydantic plugin support and because the library's target audience (enterprise architects using Python) is more likely to encounter mypy in CI pipelines.

## Alternatives Considered

### Build Backend: Poetry vs. Hatchling vs. Flit

**Poetry** was considered but rejected. Poetry uses a non-standard `[tool.poetry]` section rather than PEP 621 `[project]` metadata, introduces its own lock file and dependency resolver that would add complexity without benefit for a library (as opposed to an application), and its virtual environment management conflicts with the existing `.venv/` setup.

**Flit** was considered as a minimal alternative. Flit is excellent for pure-Python packages but offers less configuration flexibility than Hatchling for managing complex project layouts and build-time hooks that may be needed later (e.g., generating code from the ArchiMate spec).

**Hatchling** was selected as the middle ground: PEP 621 native, `src/` layout support out of the box, and extensible without being heavyweight.

### Linter: Ruff vs. flake8 + isort + Black

The traditional stack of flake8 + isort + Black requires three separate tools, three configuration sections, and introduces version compatibility concerns between them. Ruff consolidates all of these into a single tool with a single configuration block, runs 10-100x faster, and is actively maintained with frequent rule additions. The only trade-off is that Ruff is younger and its formatting output may differ slightly from Black in edge cases, but this is acceptable for a new project with no existing code style to preserve.

### Type Checker: mypy vs. pyright

**pyright** offers faster execution and tighter integration with VS Code. However, mypy was chosen because:
1. The Pydantic mypy plugin is first-class and battle-tested; pyright's Pydantic support, while improving, is less mature for advanced patterns like generic models and discriminated unions.
2. mypy's strict mode has well-documented semantics that can be referenced in the project's contribution guidelines.
3. mypy is more commonly available in enterprise CI environments.

### Runtime Validation: Pydantic v2 vs. attrs + cattrs vs. dataclasses

**attrs + cattrs** was considered. attrs provides similar performance and a clean API, but lacks Pydantic's built-in JSON Schema support and its ecosystem of plugins (mypy, FastAPI, OpenAPI). Since the library will eventually need to serialize models to the ArchiMate Exchange Format (XML/JSON), Pydantic's serialization capabilities provide a strategic advantage.

**Plain dataclasses** were considered for the metamodel types to minimize dependencies. However, dataclasses lack runtime validation, discriminated union support, and the serialization infrastructure that Pydantic provides. Adding those features manually would effectively mean re-implementing Pydantic.

## Consequences

### Positive

- **Single source of truth**: All project configuration lives in `pyproject.toml`. No scattered config files.
- **Type safety from day one**: mypy strict mode plus Pydantic's runtime validation creates a two-layer safety net -- illegal models are caught at both development time and runtime.
- **Fast feedback loops**: Ruff's sub-second linting and formatting means developers get instant feedback without waiting for slow tools.
- **Future-proof packaging**: PEP 621 metadata and the `src/` layout are the modern standard, ensuring compatibility with future Python tooling.
- **Test composability**: pytest fixtures in `conftest.py` provide a scalable pattern for sharing model instances across the 96+ stories in the Phase 1 backlog.
- **IDE experience**: Pydantic models + mypy strict mode + type hints on all public APIs deliver full auto-completion and inline documentation in VS Code, PyCharm, and other editors.

### Negative

- **Pydantic coupling**: The entire metamodel hierarchy will inherit from Pydantic `BaseModel`, making Pydantic a deeply embedded dependency. Migrating away from Pydantic in the future would be a major refactor. This is accepted because the library's validation and serialization needs align closely with Pydantic's capabilities.
- **mypy strict mode friction**: Strict mode will require explicit type annotations everywhere, including internal helper functions. This adds verbosity but is justified by the complexity of the type hierarchy.
- **Hatchling learning curve**: Hatchling is less widely known than setuptools or Poetry. Contributors unfamiliar with it may need to consult documentation. This is mitigated by the simplicity of the `pyproject.toml` configuration.
- **Python 3.12 floor excludes older environments**: Some enterprise environments may still run Python 3.10 or 3.11. This is accepted because the library's type system requirements (PEP 695, improved generics) justify the version floor, and Python 3.12 has been available since October 2023.

## Compliance

This ADR provides the architectural rationale for each story in FEAT-00.1:

| Story | Decision Implemented |
|---|---|
| STORY-00.1.1 | `pyproject.toml` with Hatchling backend, PEP 621 metadata, `requires-python >= 3.12`, `pydantic>=2.0,<3.0` |
| STORY-00.1.2 | `src/etcion/` layout with `__init__.py` re-exporting the public API surface |
| STORY-00.1.3 | pytest configured in `[tool.pytest.ini_options]`, `test/conftest.py` for shared fixtures |
| STORY-00.1.4 | Ruff configured in `[tool.ruff]` with PEP 8, import, annotation, and bugbear rule sets |
| STORY-00.1.5 | mypy configured in `[tool.mypy]` with `strict = true` and `pydantic.mypy` plugin |
