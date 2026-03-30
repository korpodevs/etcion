# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
