# ADR-046: Data Export Contract Architecture

**Status:** PROPOSED
**Date:** 2026-03-31
**Scope:** Stable `to_dict()`, DataFrame, and graph metadata export interfaces as the boundary between etcion core and downstream visualization consumers.

## Context

etcion now provides querying, diffing, impact analysis, merge operations, and viewpoint filtering. The next strategic question is how to get analytical results out of the library and into the hands of downstream consumers: a companion visualization package, Jupyter notebooks, and BI tools (Tableau, Power BI, DuckDB).

Currently, consumers must reach into internal data structures to extract results. This is fragile -- any internal refactor breaks downstream code. We need a stable, documented export contract: a set of methods that produce JSON-serializable dicts and DataFrames with a versioned schema.

Several design questions arise:

1. **Scope boundary**: Should etcion import rendering libraries (matplotlib, Jinja2, Cytoscape.js wrappers), or should it strictly produce data and leave rendering to a companion package?
2. **Dict schema stability**: How do we version the output of `to_dict()` so consumers can detect breaking changes?
3. **DataFrame as optional extra**: pandas is heavyweight. Should DataFrame export be always available or gated behind an optional extra?
4. **View materialization**: `View` currently describes a filter but has no method to produce a filtered subgraph. Should `View.to_model()` exist in etcion core?
5. **Graph metadata for JS libraries**: Cytoscape.js and ECharts expect specific JSON shapes. Should etcion produce those shapes, or is that the companion's job?

Link to strategy document: `drafts/visualization-and-communication-strategy.md`

## Decision

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **All analytical result types must provide `to_dict() -> dict[str, Any]`**: `ImpactResult`, `MatchResult`, `MergeResult`, `ModelDiff`, and the existing `model_to_dict()` all return JSON-serializable dicts. | A dict is the universal interchange format. It can be serialized to JSON, passed to Jinja2 templates, loaded into DataFrames, or consumed by JavaScript visualization libraries. Every result type needs this method to be useful outside of Python. |
| 2 | **Schema versioning via `_schema_version` key**: Every `to_dict()` output includes a `_schema_version: str` key (e.g., `"1.0"`). The version increments when the dict structure changes in a breaking way (removed keys, changed value types). Additive changes (new keys) do not require a version bump. | Consumers can assert `d["_schema_version"] == "1.0"` and fail fast if the schema has changed. This is lightweight -- no external schema registry, just a string in the dict. The leading underscore signals it is metadata, not domain data. |
| 3 | **DataFrame exports are gated behind `etcion[dataframe]` optional extra**: `pip install etcion[dataframe]` adds the `pandas` dependency. DataFrame export functions live in `serialization/dataframe.py` and raise `ImportError` with a helpful message if pandas is not installed. | pandas is ~30MB and not needed for core metamodel operations. Gating it keeps the base install lightweight. The `[dataframe]` extra follows the existing pattern (`[graph]` for networkx). |
| 4 | **`View.to_model(source: Model) -> Model` materializes a filtered subgraph**: Given a `Model` and a `View` whose `Viewpoint` restricts element/relationship types, `view.to_model(model)` returns a new `Model` containing only matching concepts. The returned model is independent (deep-copied, no shared references). | View materialization is a data transformation, not rendering. It belongs in etcion core because the companion project and notebooks both need it. Without it, every consumer must re-implement viewpoint filtering logic. |
| 5 | **etcion produces data, never imports rendering libraries**: etcion's responsibility ends at producing dicts, DataFrames, and graph metadata. It never imports matplotlib, Jinja2, Graphviz, Cytoscape.js wrappers, or any rendering library. The companion package (`etcion-workbench` or similar) consumes these exports and handles all rendering. | Strict scope boundary prevents etcion from becoming a monolith. It also avoids forcing heavyweight rendering dependencies on users who only need the metamodel. The companion package can evolve on its own release cadence. |
| 6 | **Graph metadata export helpers live in etcion core** (`serialization/graph_data.py`): Functions like `to_cytoscape_json(graph)` and `to_echarts_graph(graph)` consume `Model.to_networkx()` output and produce plain dicts matching Cytoscape.js and ECharts JSON schemas. They do not import any JS library or rendering code. | These are pure data transformations (networkx graph -> dict). They belong in etcion because they define the contract between the model and the visualization layer. Moving them to the companion would force the companion to understand networkx graph attribute schemas, breaking the abstraction. |
| 7 | **`View.to_networkx()` is a convenience method**: `view.to_networkx(model)` chains `view.to_model(model)` then `result.to_networkx()`. | One-liner convenience avoids boilerplate in notebooks. Follows the principle that common two-step operations should have a shortcut. |

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|-----------------|
| Embed rendering in etcion (matplotlib, Jinja2 imports) | Violates single-responsibility. Forces heavyweight dependencies on all users. Couples release cadence of core metamodel to rendering library updates. |
| No `_schema_version` key; rely on etcion package version | Package version tracks code changes, not dict schema changes. A patch release might not change any dict schema, while a minor release might change several. Consumers need schema-level versioning, not package-level. |
| DataFrame export always available (pandas as required dependency) | pandas is ~30MB. Most users importing etcion for metamodel operations or XML serialization do not need DataFrames. Optional extras are the established pattern. |
| `View.to_model()` in the companion package | Forces the companion to re-implement viewpoint filtering, duplicating logic. Every consumer (notebooks, BI pipelines, companion) would need its own filter implementation. |
| Graph metadata export in the companion package | The companion would need to understand networkx node/edge attribute naming, which is an internal contract of `Model.to_networkx()`. Keeping graph metadata export in etcion means the contract is self-contained. |

## Consequences

### Positive

- Downstream consumers depend on a stable, versioned dict contract. Internal refactors to etcion's data structures do not break them as long as the dict schema is maintained.
- `View.to_model()` eliminates duplicated filtering logic across consumers.
- DataFrame and graph metadata exports enable zero-code notebook workflows: `model.to_networkx() |> to_cytoscape_json() |> display()`.
- The `[dataframe]` extra keeps the base install under 5MB.
- `_schema_version` enables forward-compatible consumers that can detect and adapt to schema changes.

### Negative

- Every new result type must implement `to_dict()` with a versioned schema -- this is ongoing maintenance.
- Graph metadata helpers (`to_cytoscape_json`, `to_echarts_graph`) couple etcion to specific JS library JSON formats. If those libraries change their format, etcion must update.
- `View.to_model()` produces a full deep copy, which may be expensive for large models with many views. A lazy/streaming alternative may be needed later.
