# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.11.0] - 02 Apr 2026

### Added

- **User guide: Pattern matching & gap analysis** -- comprehensive guide covering
  pattern construction, matching, gap analysis, cardinality, attribute predicates,
  `where_attr()`, composition, serialization, and validation rules. Closes #81.
- **User guide: Impact analysis & what-if modeling** -- covers `analyze_impact()`,
  5 scenario types, `ImpactResult`, grouping methods, `chain_impacts()`,
  `follow_types`, and violation detection. Closes #82.
- **User guide: ModelBuilder fluent API** -- covers context manager, factory
  methods, `from_dicts()`, `from_dataframe()`, and comparison with `Model.add()`.
  Closes #83.
- **User guide: Model merge operations** -- covers `merge_models()`, 4 conflict
  strategies, `MergeResult`, `apply_diff()`, and conflict workflows. Closes #84.
- **User guide: Provenance metadata** -- covers `INGESTION_PROFILE`, 4 standard
  attributes, and query helpers. Closes #85.
- **User guide: Conformance profiles** -- covers `ConformanceProfile`, `CONFORMANCE`
  singleton, feature flags, and validation. Closes #86.
- **API reference pages** -- patterns, impact, builder, merge, provenance,
  conformance, graph_data modules. Closes #87, #88.
- **Example scripts** -- pattern matching, impact analysis, model builder, merge,
  advanced serialization, and graph export. Closes #93, #94.

### Changed

- **Querying guide** -- added `elements_where()` section. Closes #89.
- **Profiles guide** -- added declarative constraints section. Closes #90.
- **Serialization guide** -- added CSV, DataFrame, Parquet, DuckDB, and graph
  export sections. Closes #91.
- **API reference index** -- all 18 modules listed, stale TODO removed. Closes #92.
- **Housekeeping** -- classifier updated to Beta, ADR-042/043/044/045 accepted,
  `__init__.py` docstring expanded, README updated. Closes #95.

## [0.10.0] - 02 Apr 2026

### Changed

- **Infrastructure cleanup** -- consolidated shared stubs into
  `test/metamodel/conftest.py` and shared model fixtures into
  `test/serialization/conftest.py`. Removed duplicated definitions. Closes #74.
- **Layer test consolidation** -- replaced ~615 repetitive per-type tests with
  data-driven `ElementSpec` registry and 8 parametrized test methods covering
  all 58 concrete element types. Net −912 LOC from layer files. Closes #75.
- **Viewpoint catalogue consolidation** -- replaced per-concept-type tests with
  full-set equality assertions via `VIEWPOINT_EXPECTED` dict. 345 → 219 tests.
  Closes #76.
- **Export test consolidation** -- merged `_PHASE2_TYPES` and `PHASE_3_EXPORTS`
  into single `ALL_PUBLIC_TYPES` list. Removed brittle count assertion. 152 → 75
  tests. Closes #77.
- **Relationship test cleanup** -- data-driven `RelSpec` registry with
  `TestRelationshipCommon` parametrized class. Dedicated classes retained for
  Access, Influence, Association, Flow, Junction. Closes #78.
- **Benchmark consolidation** -- merged 6 benchmark files into single
  `test_benchmarks.py`. All 13 benchmarks preserved. Closes #79.

## [0.9.0] - 02 Apr 2026

### Added

- **End-to-end test infrastructure** -- `test/e2e/conftest.py` with session-scoped
  `petco_model`, function-scoped `petco_model_copy`, and `minimal_model` fixtures.
  Closes #66.
- **PawsPlus regression harness** -- 20 structural regression tests asserting
  element counts, relationship integrity, profile application, viewpoint
  coverage, capability hierarchy, and data governance completeness. Closes #67.
- **Serialization format matrix** -- 42 parametrized tests across 8 formats
  (XML, JSON, CSV, DataFrame, Parquet, DuckDB, Cytoscape, ECharts) × 4 model
  variants with round-trip and write-only validation. Closes #68.
- **Analytical workflow tests** -- 35 tests for pattern matching, impact
  analysis, model diff, and model merge against PawsPlus. Closes #69.
- **Model lifecycle tests** -- 42 tests covering build → profile → viewpoint →
  view → serialize → deserialize → validate chains. Closes #70.
- **Negative path tests** -- 28 tests for invalid relationships, duplicate IDs,
  malformed XML, viewpoint violations, profile mismatches, and cycle safety.
  Closes #71.
- **User journey simulations** -- 4 end-to-end tests simulating enterprise
  architect, analyst, platform team, and data governance workflows. Closes #72.
- **CI marker-based test gating** -- `test-fast` (unit only) on every push,
  `test-full` (unit + integration) on develop/main/release, nightly schedule
  for slow benchmarks. Added `e2e` marker alias. Closes #73.

## [0.8.0] - 02 Apr 2026

### Added

- **`Model.elements_where()`** -- predicate query method for filtering elements
  by arbitrary conditions (extended attributes, type checks, name filters,
  compound predicates). Closes #51.
- **Declarative profile constraints** -- `attribute_extensions` values now accept
  constraint dicts with `allowed`, `min`/`max`, and `required` keys alongside
  the bare type form. `Model.validate()` enforces constraints. JSON and XML
  round-trip supported. ADR-030 updated. Closes #52.
- **`Pattern.where_attr()`** -- serializable declarative predicates for pattern
  matching with 8 operators (`==`, `!=`, `<`, `<=`, `>`, `>=`, `in`,
  `not_in`). `Pattern.to_dict()` / `Pattern.from_dict()` enable standalone
  pattern serialization for rule repositories. ADR-048 added. Closes #53.

## [0.7.0] - 02 Apr 2026

### Added

- **View/Viewpoint XML serialization** -- `serialize_model()` now emits
  `<views>` with `<diagrams><view>` elements containing nodes and connections.
  `deserialize_model()` reconstructs `View` and `Viewpoint` instances from the
  XML, enabling full round-trip of architectural views. Closes #61.
- **Element icon identifiers** -- `ELEMENT_ICONS` dict maps all 60 concrete
  Element types to stable lowercase icon strings (e.g. `"component"`,
  `"data-object"`, `"value-stream"`) for graph visualization tooling.
  Closes #46.
- **Petco example views** -- `build_model.py` now generates one `View` per
  viewpoint, giving the team concrete examples to reference.

## [0.6.0] - 01 Apr 2026

### Added

- **Parquet export** -- `to_parquet(model, path)` writes
  `{path}_elements.parquet` and `{path}_relationships.parquet` with column
  schemas matching `to_dataframe()`. New optional extra: `pip install
  etcion[parquet]` (requires pyarrow >= 14.0).
- **DuckDB export** -- `to_duckdb(model, path)` writes `elements` and
  `relationships` tables to a DuckDB database file. New optional extra:
  `pip install etcion[duckdb]` (requires duckdb >= 0.10).
- **View/Viewpoint metadata in JSON** -- `model_to_dict(model,
  include_views=True)` adds `"viewpoints"` and `"views"` keys to the output
  dict. Default behavior (`include_views=False`) is unchanged.
- **Model.add_view() / Model.views** -- `Model` now stores views via
  `add_view()` with a `views` read-only property.

## [0.5.1] - 01 Apr 2026

### Fixed

- **XML property type mapping** -- replaced invalid XSD type values `"real"` and
  `"integer"` with `"number"` per the ArchiMate Exchange Format enumeration
  (`string`, `boolean`, `currency`, `date`, `time`, `number`).
- **XML element ordering** -- moved `<propertyDefinitions>` after `<elements>`,
  `<relationships>`, and `<organizations>` to match the `ModelType` sequence
  required by the XSD.
- **XML specialization encoding** -- serialized `specialization` as a
  `<property>` referencing a well-known `propdef-specialization` property
  definition instead of an invalid XML attribute on `<element>`.
- **XML dangling property refs** -- `serialize_model()` now emits
  `<propertyDefinition>` entries for all extended attributes used by elements,
  not just those declared in profile `attribute_extensions`.
- **Petco example** -- changed ApplicationComponent → ApplicationInterface
  relationship from `Assignment` to `Composition` per ArchiMate spec.

## [0.5.0] - 01 Apr 2026

### Added

- **JSON profile serialization** -- `model_to_dict()` now includes a `"profiles"`
  key serializing `Profile` objects with type-name strings for class keys and
  Python type-name strings for attribute types. `model_from_dict()` reconstructs
  profiles and calls `apply_profile()` before adding elements. Specialization,
  extended attributes, and `model.validate()` all survive JSON round-trip.
- **XML profile serialization** -- `serialize_model()` emits
  `<propertyDefinitions>` for profile attribute extensions; `serialize_element()`
  emits a `specialization` attribute and `<properties>` sub-elements for
  extended attributes. `deserialize_model()` reconstructs a synthetic profile
  from property definitions and element specializations, applying it before
  adding elements.
- **Round-trip integrity tests** -- comprehensive idempotency and edge-case
  coverage for both JSON and XML profile serialization, including dict
  idempotency, XML element-data stability, empty-attributes noise checks,
  and specializations-only profile round-trips.

## [0.4.1] - 01 Apr 2026

### Fixed

- Fixed `Flow` relationship XML serialization: removed invalid `flowType`
  attribute that caused errors when exporting models with Flow relationships
  to Exchange Format XML.

## [0.4.0] - 01 Apr 2026

### Added

- **Data export contracts** -- stable, versioned `to_dict()` on all analytical
  result types (`ImpactResult`, `MatchResult`, `MergeResult`, `ModelDiff`,
  `model_to_dict`). All include `_schema_version: "1.0"` per ADR-046.
- **View materialization** -- `View.to_model(source)` produces a filtered,
  deep-copied Model containing only viewpoint-permitted concepts.
  `View.to_networkx()` chains materialization with graph conversion.
- **DataFrame exports** -- `diff_to_dataframe()`, `impact_to_dataframe()`, and
  `to_flat_dataframe()` for direct import into BI tools (Tableau, Power BI).
  Denormalized flat export joins elements with relationships in a single table.
- **Graph metadata export** -- `to_cytoscape_json()` and `to_echarts_graph()`
  produce dicts matching Cytoscape.js and ECharts JSON schemas. `LAYER_COLORS`
  constant maps ArchiMate layers to standard hex colors with `color_map`
  override for custom theming.

## [0.3.0] - 31 Mar 2026

### Added

- **ModelBuilder fluent API** -- context manager and standalone usage with
  snake_case factory methods for all 58 element types and 12 relationship types.
  `ModelBuilder.from_dicts()` for batch construction from JSON/API output.
  `ModelBuilder.from_dataframe()` for optional pandas integration.
- **Model merge operations** -- `merge_models(base, fragment)` with four conflict
  resolution strategies (`prefer_base`, `prefer_fragment`, `fail_on_conflict`,
  `custom` with resolver callback). `apply_diff()` applies a `ModelDiff` as a
  patch with round-trip fidelity.
- **Provenance metadata** -- built-in `INGESTION_PROFILE` with `_provenance_source`,
  `_provenance_confidence`, `_provenance_reviewed`, `_provenance_timestamp`
  extended attributes. Query helpers: `unreviewed_elements()`,
  `elements_by_source()`, `low_confidence_elements()`.
- **CSV/TSV import/export** -- `from_csv()` / `to_csv()` in
  `etcion.serialization.csv` with delimiter parameter and type resolution.
- **DataFrame import/export** -- `from_dataframe()` / `to_dataframe()` in
  `etcion.serialization.dataframe`. Optional pandas dependency via
  `pip install etcion[dataframe]`.
- **Notebook-friendly rendering** -- `_repr_html_()` on `ModelDiff`,
  `ImpactResult`, `GapResult`, and `MergeResult` with color-coded inline-styled
  HTML tables (green=added, red=removed, amber=modified).

## [0.2.0] - 30 Mar 2026

### Added

- **Pattern matching engine** -- define structural patterns with typed node
  placeholders, relationship constraints, attribute filters (`.node(**kwargs)`),
  lambda predicates (`.where()`), and cardinality constraints (`.min_edges()`,
  `.max_edges()`). Find all matches (`pattern.match(model)`), check existence
  (`pattern.exists(model)`), and identify gaps (`pattern.gaps(model, anchor=...)`).
- **Pattern composition** -- combine reusable pattern fragments via
  `pattern_a.compose(pattern_b)`, with conflict detection on shared aliases.
- **Pattern serialization** -- `pattern.to_dict()` and `Pattern.from_dict(data)`
  for JSON storage and sharing. Includes version field for forward compatibility.
- **Pattern validation rules** -- `PatternValidationRule` (pattern must exist),
  `AntiPatternRule` (pattern must NOT exist), `RequiredPatternRule` (every
  anchor-type element must participate). All integrate with `Model.validate()`.
- **Impact analysis (what-if modeling)** -- `analyze_impact()` computes the
  blast radius of proposed changes: `remove`, `merge`, `replace`,
  `add_relationship`, `remove_relationship`. Returns `ImpactResult` with
  affected concepts (depth + path metadata), broken relationships, permission
  violations, and an immutable result model.
- **Change chaining** -- `chain_impacts()` combines sequential operations with
  ID-based deduplication. Feed `impact.resulting_model` into the next analysis
  for multi-step migration planning.
- **Model querying** -- `elements_of_type()`, `elements_by_layer()`,
  `elements_by_aspect()`, `elements_by_name()` (substring or regex),
  `relationships_of_type()`, `connected_to()`, `sources_of()`, `targets_of()`.
- **networkx integration** -- `Model.to_networkx()` converts to a cached
  `MultiDiGraph` with full element/relationship attributes. Optional dependency
  via `pip install etcion[graph]`.
- **Viewpoint catalogue** -- 28 predefined standard viewpoints from the
  ArchiMate specification, accessible via `VIEWPOINT_CATALOGUE["Organization"]`.
- **Model comparison** -- `diff_models()` with `ModelDiff`, `ConceptChange`,
  `FieldChange` dataclasses. Supports `match_by="id"` and `match_by="type_name"`.
- **Plugin hooks** -- `register_element_type()`, `register_permission_rule()`,
  `ValidationRule` protocol with `Model.add_validation_rule()`.
- **Permission cache warming** -- `warm_cache()` for deterministic startup
  latency in performance-sensitive environments.
- **Performance benchmark suite** -- `test/benchmarks/` with import, construction,
  validation, serialization, and memory benchmarks.
- **MkDocs documentation site** -- API reference (auto-generated), user guide,
  architecture overview, ADR index, permission matrix.
- **CI/CD pipelines** -- GitHub Actions for lint, format, typecheck, test
  (Python 3.12 + 3.13 matrix), and tag-triggered PyPI publishing.
- **Viewpoint-constrained patterns** -- optional `Pattern(viewpoint=vp)`
  validates all node/edge types at construction time.

## [0.1.0] - 26 Mar 2026

### Added

- ArchiMate 3.2 metamodel: all element types across Business, Application,
  Technology, Strategy, Motivation, Implementation & Migration, and Composite layers.
- Complete relationship type system with source/target validation matrix.
- Open Group Exchange Format XML serialization and deserialization.
- XSD validation against bundled ArchiMate 3.1 schemas.
- Conformance profiles (flag, standard, full).
- Opaque XML preservation for organizations and views during round-trip.
- Archi tool interoperability (import and export verified).
- PEP 561 `py.typed` marker for downstream type checking.
