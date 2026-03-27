# ADR-039: Documentation and API Reference (EPIC-026)

## Context

etcion has 31 source modules, 58 element types, 11 relationship types, 2460 tests, and production-grade features (validation, serialization, viewpoints, profiles, querying, diffing). The only user-facing documentation is `README.md` and inline docstrings. There is no auto-generated API reference, no user guide, and no architecture overview. This blocks adoption.

EPIC-026 covers three feature areas:
- **FEAT-26.1** -- API reference generation from docstrings
- **FEAT-26.2** -- User guide (Getting Started, Serialization, Validation, Viewpoints, Language Customization)
- **FEAT-26.3** -- Architecture documentation (ADR index, class hierarchy, permission matrix)

## Decisions

### D1: Documentation Toolchain

| Option | Pros | Cons |
|--------|------|------|
| Sphinx + autodoc | Established standard, RST cross-refs, PDF output | Heavy config, RST/MyST friction, verbose `conf.py` |
| **MkDocs + mkdocstrings** | Markdown-native, minimal config, Pydantic handler, Material theme | Less mature cross-ref system, no LaTeX/PDF |
| pdoc | Zero config, instant API docs | No user guide support, no nav customization |

**Decision: MkDocs + mkdocstrings with Material for MkDocs theme.**

Rationale:
- The project is Markdown-native (`README.md`, `BACKLOG.md`, all ADRs).
- `mkdocstrings-python` handles Pydantic models well (renders fields, validators, inherited members).
- Material for MkDocs provides search, dark mode, navigation tabs, and versioning support out of the box.
- 31 source files is well within mkdocstrings' comfort zone.
- `mkdocs.yml` is a single flat YAML file vs. Sphinx's multi-file configuration.

New optional dependency group in `pyproject.toml`:

```toml
[project.optional-dependencies]
docs = [
    "mkdocs>=1.6",
    "mkdocs-material>=9.5",
    "mkdocstrings[python]>=0.25",
]
```

### D2: Docstring Convention

| Option | Compatibility | Readability |
|--------|--------------|-------------|
| **Google-style** | mkdocstrings default parser | Clean, compact |
| NumPy-style | Supported via `numpy` style option | Verbose, better for heavy math |
| Sphinx RST (`:param:`) | Native Sphinx only | Noisy in plain text |

**Decision: Google-style docstrings.**

Rationale: mkdocstrings parses Google-style natively with `griffe`. Google-style is the most compact format and reads well in IDE tooltips. The library has no NumPy/math-heavy documentation needs.

### D3: Documentation Scope and Structure

```
docs/
  index.md                  # Landing page (mirrors README Quick Start)
  getting-started.md        # Install, first model, validate, export
  user-guide/
    building-models.md      # Elements, relationships, Junction, Model container
    validation.md           # Model.validate(), is_permitted(), error handling
    serialization.md        # XML (Exchange Format), JSON, round-trip, Archi compat
    viewpoints.md           # Viewpoint, View, Concern, predefined catalogue
    profiles.md             # Specializations, extended attributes, Profile
    querying.md             # QueryBuilder, filtering, traversal
    diffing.md              # diff_models(), ConceptChange, FieldChange
    extending.md            # Plugin system, custom validators
  architecture/
    overview.md             # Layer hierarchy diagram, module map
    adr-index.md            # Auto-generated index of docs/adr/
    permission-matrix.md    # Rendered Appendix B table with cross-refs
  api/                      # Auto-generated via mkdocstrings ::: directives
    index.md
    model.md
    elements.md
    relationships.md
    validation.md
    serialization.md
    viewpoints.md
    profiles.md
    querying.md
    comparison.md
    enums.md
    exceptions.md
  examples/
    index.md                # Gallery linking to focused examples
  changelog.md              # Keep a Changelog format
```

### D4: Hosting and Deployment

| Option | Pros | Cons |
|--------|------|------|
| **GitHub Pages via `mkdocs gh-deploy`** | Zero external dependency, free, direct from repo | Manual deploy (until CI) |
| Read the Docs | Auto-builds on push, versioning built-in | External service, `.readthedocs.yaml` config |

**Decision: GitHub Pages.**

Rationale: Simpler. No external service account required. `mkdocs gh-deploy` pushes to `gh-pages` branch in one command. EPIC-027 will add CI/CD that automates this on tagged releases.

### D5: CHANGELOG Format

**Decision: `CHANGELOG.md` using [Keep a Changelog](https://keepachangelog.com/) format.**

Sections: Added, Changed, Deprecated, Removed, Fixed, Security. Retroactively document Phases 1-3 under a single `[0.1.0] - Unreleased` heading. Future releases get individual entries.

### D6: Examples Expansion

| Example | Feature Coverage |
|---------|-----------------|
| `examples/pet_shop.py` (existing) | Full model with all layers |
| `examples/quick_start.py` | Minimal 4-element model from README |
| `examples/validation_demo.py` | Invalid model, error inspection |
| `examples/xml_roundtrip.py` | Export, re-import, diff for equality |
| `examples/viewpoint_filter.py` | Apply predefined viewpoint, inspect allowed types |
| `examples/profile_extension.py` | Custom specialization with extended attributes |
| `examples/query_builder.py` | QueryBuilder chains, layer/type/relationship filters |
| `examples/model_diff.py` | Compare two model versions, inspect changes |

Each example is a standalone runnable `.py` file with inline comments. User guide sections cross-reference the corresponding example.

### D7: Priority and Sequencing

| Phase | Stories | Rationale |
|-------|---------|-----------|
| First | STORY-26.1.1 (mkdocs config), STORY-26.1.4 (docstring coverage test) | Establishes toolchain, creates quality gate |
| Second | STORY-26.1.2, STORY-26.1.3 (fill missing docstrings) | Prerequisite for useful API reference |
| Third | STORY-26.2.1 (Getting Started), STORY-26.3.1 (ADR index) | Highest-value user-facing pages |
| Ongoing | Remaining user guide sections, examples | Fill in as features stabilize |

## Consequences

**Positive:**
- API reference is auto-generated from source -- stays in sync with code.
- Markdown-native toolchain matches existing project conventions.
- Docstring coverage test (STORY-26.1.4) prevents regression.
- GitHub Pages deployment has zero operational cost.

**Negative:**
- mkdocstrings is less battle-tested than Sphinx autodoc for edge cases (complex generics, overloaded signatures).
- Retroactive docstring standardization across 31 modules is significant effort.
- No PDF output for offline distribution (acceptable for a developer library).
