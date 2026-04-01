# ADR-047: Graph Metadata Export for Visualization Libraries

**Status:** PROPOSED
**Date:** 2026-03-31
**Scope:** Design of `to_cytoscape_json()` and `to_echarts_graph()` export helpers in `serialization/graph_data.py`, plus ArchiMate layer color constants and element icon identifiers as shared notation metadata.

## Context

The companion visualization project needs to render ArchiMate models as interactive graphs using Cytoscape.js and ECharts. Both libraries consume specific JSON structures:

- **Cytoscape.js** expects `{"elements": {"nodes": [...], "edges": [...]}}` where each node/edge has a `data` dict.
- **ECharts graph series** expects `{"nodes": [...], "links": [...], "categories": [...]}`.

These JSON structures must be produced from the networkx `MultiDiGraph` that `Model.to_networkx()` already provides. The question is where this transformation lives and what additional metadata (colors, icons) it requires.

Additionally, ArchiMate has standard layer colors (yellow for Business, blue for Application, green for Technology, etc.) and element notation (icons/shapes). Both etcion core and the companion project need to reference these constants. If they are defined only in the companion, etcion's own graph metadata export cannot include them.

Link to strategy document: `drafts/visualization-and-communication-strategy.md`
Link to parent ADR: `docs/adr/ADR-046-data-export-contract-architecture.md` (Decision #6)

## Decision

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Graph metadata export belongs in etcion core** (`serialization/graph_data.py`): `to_cytoscape_json(graph) -> dict` and `to_echarts_graph(graph) -> dict` are module-level functions that accept a `networkx.MultiDiGraph` (from `Model.to_networkx()` or `View.to_networkx()`) and return plain dicts. | These are data transformations, not rendering. They translate networkx graph attributes into a target JSON schema. No JS libraries are imported. The companion project consumes the output dict and passes it to the JS runtime. Keeping them in etcion ensures the node/edge attribute contract is self-contained. |
| 2 | **Cytoscape.js JSON schema**: Each node produces `{"data": {"id": str, "name": str, "type": str, "layer": str, "color": str}}`. Each edge produces `{"data": {"id": str, "source": str, "target": str, "type": str, "label": str}}`. The top-level structure is `{"elements": {"nodes": [...], "edges": [...]}}`. | Matches the Cytoscape.js `cy.add()` / `cy.json()` format exactly. The `color` field uses `LAYER_COLORS` defaults but can be overridden via a `color_map` parameter. |
| 3 | **ECharts graph JSON schema**: Nodes produce `{"id": str, "name": str, "category": int, "symbolSize": int, ...}`. Links produce `{"source": str, "target": str, "label": {"show": bool, "formatter": str}}`. Categories are derived from ArchiMate layers. The top-level structure is `{"nodes": [...], "links": [...], "categories": [...]}`. | Matches the ECharts `graph` series `data` format. Categories map to layers, enabling automatic color assignment via ECharts' category color system. |
| 4 | **`LAYER_COLORS: dict[Layer, str]`** defined in `etcion/notation.py` (or extending `etcion/metamodel/notation.py`): Maps each `Layer` enum value to a hex color string using the ArchiMate 3.2 specification defaults. Exported in `__all__` and importable as `from etcion import LAYER_COLORS`. | Standard ArchiMate colors are part of the specification's notation, not rendering logic. Both etcion's graph metadata helpers and the companion project's renderers need these values. Defining them once in etcion avoids duplication and ensures consistency. |
| 5 | **`ELEMENT_ICONS: dict[type[Element], str]`** mapping each concrete element class to a short icon identifier string (e.g., `"actor"`, `"component"`, `"node"`): Defined alongside `LAYER_COLORS`. | Icon identifiers are stable strings that the companion project maps to SVG icons or Unicode symbols. etcion defines the identifiers; the companion provides the actual icon assets. This separation keeps etcion free of image assets while ensuring consistent naming. |
| 6 | **Both functions require `etcion[graph]` extra**: They accept networkx graphs and raise `ImportError` if networkx is not installed. They do not depend on pandas or any rendering library. | Consistent with existing optional dependency gating. networkx is already the `[graph]` extra. |
| 7 | **`color_map` override parameter**: Both `to_cytoscape_json()` and `to_echarts_graph()` accept an optional `color_map: dict[str, str] | None` parameter that overrides `LAYER_COLORS` for custom theming. | Corporate branding often requires non-standard colors. The override is a simple dict merge, not a complex theming system. |

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|-----------------|
| Graph metadata export in the companion package only | The companion would need to understand networkx node/edge attribute names (`type`, `layer`, `name`), which are an internal contract of `Model.to_networkx()`. Any change to those attributes would silently break the companion. Keeping the export in etcion makes the contract self-contained. |
| Produce graph metadata as DataFrames instead of dicts | Cytoscape.js and ECharts consume JSON, not DataFrames. An intermediate DataFrame step adds overhead and a pandas dependency without benefit. The companion would still need to convert DataFrame rows to the JS-specific JSON schema. |
| Define `LAYER_COLORS` in the companion only | etcion's own `to_cytoscape_json()` needs default colors. Duplicating the color map in both packages creates drift risk. |
| Use CSS class names instead of hex colors in graph metadata | Pushes styling responsibility to every consumer. Hex colors are universally understood. Consumers who prefer CSS classes can ignore the `color` field and use the `layer` field to assign classes. |
| Full SVG icon embedding in `ELEMENT_ICONS` | Bloats etcion with image assets. Short string identifiers are lightweight and allow the companion to choose its own icon format (SVG, PNG, Unicode, font icons). |

## Consequences

### Positive

- The companion project receives graph data in exactly the JSON format its JS libraries expect -- no transformation needed on the JS side.
- `LAYER_COLORS` and `ELEMENT_ICONS` are defined once and shared, eliminating drift between etcion and the companion.
- `color_map` override enables corporate theming without forking or subclassing.
- No new required dependencies -- both functions gate on the existing `[graph]` extra.

### Negative

- etcion is now coupled to the Cytoscape.js and ECharts JSON schemas. If either library changes its format in a major version, etcion must update `serialization/graph_data.py`. Mitigation: these JSON formats have been stable for years and are unlikely to change.
- `ELEMENT_ICONS` must be updated whenever a new concrete element type is added. Mitigation: this is a small maintenance burden and is naturally caught by test coverage (a test can assert all concrete types are present in the mapping).
- Two graph export functions now live in etcion that are only useful to consumers doing JS visualization. Users who only need XML/JSON serialization pay no runtime cost (functions are not called unless imported), but the module exists in the package.
