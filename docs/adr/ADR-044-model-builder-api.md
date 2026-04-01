# ADR-044: Model Builder API

**Status:** PROPOSED
**Date:** 2026-03-29
**Scope:** Design of `ModelBuilder` -- a fluent construction API for programmatic model population, supporting context manager usage, factory methods, batch construction, and deferred validation.

## Context

Every ingestion pipeline and scripted model construction workflow terminates by creating etcion objects and adding them to a `Model`. The current API requires explicit instantiation of each element, each relationship, and individual `model.add()` calls:

```python
crm = ApplicationComponent(name="CRM System")
db = DataObject(name="Customer Database")
rel = Access(source=crm, target=db, access_mode=AccessMode.READ_WRITE)
model = Model()
model.add(crm)
model.add(db)
model.add(rel)
```

This boilerplate scales poorly when constructing models from CMDB exports, dataframes, or AI extraction outputs. A builder pattern would reduce friction while preserving type safety.

The key design questions:
1. Context manager vs. standalone fluent builder?
2. Factory method naming convention (snake_case element names vs. generic `add_element`)?
3. How to handle batch/bulk construction from dicts or dataframes?
4. When does validation run -- per-add or deferred to `build()`?

Link to: `drafts/model-ingestion-pipeline-recommendation.md` (Priority 1)

## Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Context manager AND standalone usage**: `ModelBuilder` supports both `with ModelBuilder() as b: ...` and standalone `b = ModelBuilder(); ...; b.build()`. The context manager calls `build()` on `__exit__` and stores the result on `b.model`. | Context manager is idiomatic Python for "setup/teardown" patterns. Standalone usage is needed for dynamic construction in loops and conditionals. Both patterns are common in builder APIs (e.g., `io.BytesIO`, `tempfile.NamedTemporaryFile`). |
| 2 | **Snake_case factory methods per element type**: `b.application_component("CRM")`, `b.business_actor("Alice")`, `b.data_object("DB")`. Each returns the created element instance for wiring into relationships. | Snake_case matches Python naming conventions. Per-type methods enable IDE autocompletion of all ArchiMate element types. Generic `add_element(ApplicationComponent, name="CRM")` loses discoverability. |
| 3 | **Relationship factory methods named by relationship type**: `b.access(source, target)`, `b.serving(source, target)`, `b.composition(source, target)`. Accept element instances (returned by element factories) or string IDs. | Mirrors the element factory pattern. Passing instances avoids string-based wiring. Accepting IDs as fallback supports batch construction where elements are added in separate steps. |
| 4 | **Deferred validation by default**: Elements and relationships are accumulated in an internal list. `build()` calls `Model.validate()` at the end. A `validate=False` parameter on `build()` skips validation for performance-critical bulk loading. | Per-add validation is expensive for large models (re-validates the entire model on each add). Deferred validation amortizes the cost. The `validate=False` escape hatch supports trusted sources (e.g., round-tripping from known-good XML). |
| 5 | **`from_dicts()` class method for batch construction**: `ModelBuilder.from_dicts(elements=[...], relationships=[...])` accepts lists of dicts with `type` and field keys. Returns a `ModelBuilder` pre-populated with the parsed concepts. | Dicts are the natural interchange format from JSON APIs, pandas `to_dict("records")`, and AI extraction outputs. A class method keeps batch construction discoverable without polluting the instance API. |
| 6 | **`from_dataframe()` class method (optional pandas dependency)**: `ModelBuilder.from_dataframe(df, type_column="type", ...)`. Requires `pandas` at call time (not import time). | DataFrames are the standard format for CMDB exports and tabular data. Optional dependency follows the `networkx` precedent (ADR-041). |
| 7 | **New module `src/etcion/builder.py`**: `ModelBuilder` lives in its own module, not in `model.py` or `comparison.py`. | Keeps `Model` focused on container semantics (ADR-010). Builder is a construction concern, not a container concern. Follows the pattern of `comparison.py` and `impact.py` as separate modules for separate concerns. |
| 8 | **Factory methods accept `**kwargs` for all element/relationship fields**: `b.application_component("CRM", documentation="Main CRM system")`. Name is the first positional argument; all other fields are keyword-only. | Reduces boilerplate while preserving explicit field assignment. Pydantic validation on the underlying element class catches invalid kwargs at construction time. |

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|-----------------|
| Generic `builder.add(ApplicationComponent, name="CRM")` instead of per-type factories | Loses IDE autocompletion and type-specific parameter hints. Forces users to import every element class. |
| Validation on every `add()` call | O(n * R) complexity for n additions. Prohibitively slow for 10k+ element models from CMDB imports. |
| Builder as a `Model` method (`Model.builder()`) | Conflates container and construction concerns. `Model` is already the largest class in the codebase. |
| Separate `ElementBuilder` and `RelationshipBuilder` | Over-engineering. A single builder that handles both is simpler and matches the mental model of "I'm building a model." |
| Automatic relationship inference from element proximity | Magic behavior. Violates "explicit is better than implicit." ArchiMate relationships carry semantic meaning that cannot be inferred from construction order. |

## Consequences

### Positive

- Pipeline authors write ~60% less boilerplate for model construction.
- IDE autocompletion surfaces all ArchiMate element types as builder methods.
- Deferred validation enables bulk construction at near-zero overhead per element.
- `from_dicts()` and `from_dataframe()` provide natural integration points for external data sources.
- Builder returns standard `Model` instances -- no special wrapper types downstream.

### Negative

- ~60 factory methods (one per concrete element type + one per relationship type) create a large API surface on `ModelBuilder`. Mitigated by code generation or a registry-driven approach.
- Deferred validation means errors are reported at `build()` time, not at the point of the invalid addition. Users must interpret validation errors after the fact.
- `from_dataframe()` introduces an optional dependency on pandas, adding a new extras group to `pyproject.toml`.
