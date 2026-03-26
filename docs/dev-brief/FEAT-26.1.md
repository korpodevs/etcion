# Technical Brief: FEAT-26.1 -- API Reference Generation

**Status:** Ready for Implementation
**ADR:** `docs/adr/ADR-039-epic026-documentation-api-reference.md`

## Stories

| Story | Description | Deliverable |
|-------|-------------|-------------|
| STORY-26.1.1 | Configure MkDocs with mkdocstrings | `mkdocs.yml`, `pyproject.toml` change, `docs/` scaffold |
| STORY-26.1.2 | Docstrings on all public classes in `__all__` | Edits across 31 source modules |
| STORY-26.1.3 | Docstrings on all public methods of `Model`, `QueryBuilder`, `DerivationEngine` | Edits to 3 modules |
| STORY-26.1.4 | Docstring coverage test | `test/test_docstring_coverage.py` |

## pyproject.toml Change

Add `docs` optional dependency group:

```toml
docs = [
    "mkdocs>=1.6",
    "mkdocs-material>=9.5",
    "mkdocstrings[python]>=0.25",
]
```

## mkdocs.yml

Create `/home/kiera/dev/pyarchi/mkdocs.yml`:

```yaml
site_name: pyarchi
site_description: Python implementation of the ArchiMate 3.2 metamodel
repo_url: https://github.com/YOUR_ORG/pyarchi
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - search.highlight
    - content.code.copy
plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
          options:
            docstring_style: google
            show_source: true
            show_root_heading: true
            members_order: source
            merge_init_into_class: true
            show_if_no_docstring: false
nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - User Guide:
    - Building Models: user-guide/building-models.md
    - Validation: user-guide/validation.md
    - Serialization: user-guide/serialization.md
    - Viewpoints: user-guide/viewpoints.md
    - Profiles: user-guide/profiles.md
    - Querying: user-guide/querying.md
    - Diffing: user-guide/diffing.md
    - Extending: user-guide/extending.md
  - Architecture:
    - Overview: architecture/overview.md
    - ADR Index: architecture/adr-index.md
    - Permission Matrix: architecture/permission-matrix.md
  - API Reference:
    - Overview: api/index.md
    - Model: api/model.md
    - Elements: api/elements.md
    - Relationships: api/relationships.md
    - Validation: api/validation.md
    - Serialization: api/serialization.md
    - Viewpoints: api/viewpoints.md
    - Profiles: api/profiles.md
    - Querying: api/querying.md
    - Comparison: api/comparison.md
    - Enums: api/enums.md
    - Exceptions: api/exceptions.md
  - Examples: examples/index.md
  - Changelog: changelog.md
markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - toc:
      permalink: true
```

## API Reference Pages (mkdocstrings directives)

All files under `docs/api/`. Each file contains `::: module.path` directives.

| File | Directive(s) |
|------|-------------|
| `api/index.md` | Overview text, links to subpages |
| `api/model.md` | `::: pyarchi.metamodel.model` |
| `api/elements.md` | `::: pyarchi.metamodel.elements`, `::: pyarchi.metamodel.business`, `::: pyarchi.metamodel.application`, `::: pyarchi.metamodel.technology`, `::: pyarchi.metamodel.physical`, `::: pyarchi.metamodel.strategy`, `::: pyarchi.metamodel.motivation`, `::: pyarchi.metamodel.implementation_migration` |
| `api/relationships.md` | `::: pyarchi.metamodel.relationships` |
| `api/validation.md` | `::: pyarchi.validation.permissions`, `::: pyarchi.validation.rules` |
| `api/serialization.md` | `::: pyarchi.serialization.xml`, `::: pyarchi.serialization.json`, `::: pyarchi.serialization.registry` |
| `api/viewpoints.md` | `::: pyarchi.metamodel.viewpoints`, `::: pyarchi.metamodel.viewpoint_catalogue` |
| `api/profiles.md` | `::: pyarchi.metamodel.profiles` |
| `api/querying.md` | `::: pyarchi.metamodel.model` (QueryBuilder section -- or separate module if extracted) |
| `api/comparison.md` | `::: pyarchi.comparison` |
| `api/enums.md` | `::: pyarchi.enums` |
| `api/exceptions.md` | `::: pyarchi.exceptions` |

## Docs Scaffold (placeholder files)

Create these as minimal placeholder `.md` files (title + "TODO" body) so `mkdocs build` succeeds before content is written in FEAT-26.2 and FEAT-26.3:

```
docs/index.md
docs/getting-started.md
docs/user-guide/building-models.md
docs/user-guide/validation.md
docs/user-guide/serialization.md
docs/user-guide/viewpoints.md
docs/user-guide/profiles.md
docs/user-guide/querying.md
docs/user-guide/diffing.md
docs/user-guide/extending.md
docs/architecture/overview.md
docs/architecture/adr-index.md
docs/architecture/permission-matrix.md
docs/api/index.md
docs/api/model.md
docs/api/elements.md
docs/api/relationships.md
docs/api/validation.md
docs/api/serialization.md
docs/api/viewpoints.md
docs/api/profiles.md
docs/api/querying.md
docs/api/comparison.md
docs/api/enums.md
docs/api/exceptions.md
docs/examples/index.md
docs/changelog.md
```

## Docstring Coverage Test

Create `test/test_docstring_coverage.py`:

**Logic:**
1. Import `pyarchi`.
2. Iterate over every name in `pyarchi.__all__`.
3. For each name, resolve `getattr(pyarchi, name)`.
4. Assert `obj.__doc__` is not `None` and `len(obj.__doc__.strip()) > 0`.
5. For classes: iterate over public methods (no leading `_`), assert each has a non-empty `__doc__`.
6. Skip inherited dunder methods and Pydantic internal methods (`model_*`).

**Test cases:**
- `test_all_public_symbols_have_docstrings` -- every symbol in `__all__` has `__doc__`.
- `test_all_public_methods_have_docstrings` -- every public method on classes in `__all__` has `__doc__`.
- `test_all_modules_have_docstrings` -- every `.py` file under `src/pyarchi/` that is not `__init__.py` has a module-level docstring.

## Verification

```bash
pip install -e ".[docs]"
mkdocs build --strict   # must exit 0
mkdocs serve            # local preview at http://127.0.0.1:8000
pytest test/test_docstring_coverage.py -v
```
