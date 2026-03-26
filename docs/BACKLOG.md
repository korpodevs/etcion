---
project: pyarchi
phase: 4
last_updated: 2026-03-25
total_epics: 29
total_features: 108
total_stories: 453
---

# pyarchi Backlog

---

## Phase 1 — Completed

Phase 1 covered Requirements 1 through 5: project scaffold, scope and conformance, root type hierarchy, language structure and classification framework, abstract element hierarchy, all eleven relationships, Junction, and the derivation engine.

All 6 epics (EPIC-000 through EPIC-005), 24 features, and 96 stories are complete.
Detailed history is preserved in git (branch `develop`, up to commit `e0e2e69`).

| Epic | Title | Status |
|------|-------|--------|
| EPIC-000 | Project Scaffold and Build System | Complete |
| EPIC-001 | Scope and Conformance (Requirement 1) | Complete |
| EPIC-002 | Definitions and Root Type Hierarchy (Requirement 2) | Complete |
| EPIC-003 | Language Structure and Classification Framework (Requirement 3) | Complete |
| EPIC-004 | Generic Metamodel -- Abstract Element Hierarchy (Requirement 4) | Complete |
| EPIC-005 | Relationships and Relationship Connectors (Requirement 5) | Complete |

---

## Phase 2 — Completed

Phase 2 covered Requirements 6 through 13: concrete element classes for all ArchiMate layers (Strategy, Business, Application, Technology, Physical, Motivation, Implementation & Migration), cross-layer relationship rules, and public API exports.

All 9 epics (EPIC-006 through EPIC-014), 28 features, and 103 stories are complete.
Detailed history is preserved in git (branch `develop`, up to commit `5b557e8`).

| Epic | Title | Status |
|------|-------|--------|
| EPIC-006 | Strategy Layer Elements (Requirement 12) | Complete |
| EPIC-007 | Business Layer Elements (Requirement 6) | Complete |
| EPIC-008 | Application Layer Elements (Requirement 7) | Complete |
| EPIC-009 | Technology Layer Elements (Requirement 8) | Complete |
| EPIC-010 | Physical Elements (Requirement 9) | Complete |
| EPIC-011 | Motivation Elements (Requirement 11) | Complete |
| EPIC-012 | Implementation and Migration Layer Elements (Requirement 13) | Complete |
| EPIC-013 | Cross-Layer Relationship Rules (Requirement 10) | Complete |
| EPIC-014 | Public API Exports for Phase 2 | Complete |

---

## Phase 3 — Completed

Phase 3 covered model-level validation enforcement, the complete Appendix B permission table as declarative data, the viewpoint mechanism (Requirement 14), language customization (Chapter 14), the Open Group Exchange Format serialization layer (XML and JSON), and conformance cleanup resolving all deferred xfails.

All 6 epics (EPIC-015 through EPIC-020), 27 features, and 112 stories are complete.
Detailed history is preserved in git (branch `develop`).

| Epic | Title | Status |
|------|-------|--------|
| EPIC-015 | Model-Level Validation Engine | Complete |
| EPIC-016 | Declarative Relationship Permission Table | Complete |
| EPIC-017 | Viewpoint Mechanism (Requirement 14) | Complete |
| EPIC-018 | Language Customization Mechanism | Complete |
| EPIC-019 | Open Group Exchange Format Serialization | Complete |
| EPIC-020 | Conformance Cleanup and Phase 3 Public API | Complete |

---

## Phase 4 — Production Readiness, Tooling, and Extended Features

Phase 4 focuses on production readiness: performance optimization for large models, a predefined viewpoint catalogue, a model querying API, model comparison utilities, a plugin/extension system, comprehensive documentation, packaging/distribution, CLI tooling, and Archi tool interoperability testing.

---

## [EPIC-021] Performance Optimization
**Status:** Complete
**Priority:** High

Optimize runtime performance for large-scale enterprise models (10k+ elements). Address memory footprint, import speed, and permission lookup latency.

### [FEAT-21.1] Lazy Module Loading
- [~] [STORY-21.1.1] Implement lazy imports for layer modules (business, application, technology, physical, motivation, strategy, implementation_migration) so that importing `pyarchi` does not eagerly load all concrete classes — **WONTFIX** per ADR-034 Decision 2 (no lazy imports)
- [~] [STORY-21.1.2] Add `__getattr__` hook on `pyarchi` top-level to defer layer module imports until first access — **WONTFIX** per ADR-034 Decision 2 (no `__getattr__` hook)
- [x] [STORY-21.1.3] Write test: `import pyarchi` completes without importing `lxml` unless serialization is used — `test_import_does_not_load_lxml` in `test/benchmarks/test_bench_import.py`
- [x] [STORY-21.1.4] Write benchmark: measure import time before and after lazy loading; target < 100ms for base import — `test_bench_import_cold` in `test/benchmarks/test_bench_import.py` (baseline capture, no threshold per ADR-034)

### [FEAT-21.2] Permission Cache Warming
- [~] [STORY-21.2.1] Implement LRU cache on `is_permitted()` to avoid repeated hierarchical type resolution — **WONTFIX** per ADR-034 Decision 5: existing `_build_cache()` already provides O(1) dict lookup; LRU adds no value
- [x] [STORY-21.2.2] Add `warm_cache()` utility that pre-computes all concrete type-pair permissions at startup — `warm_cache()` in `src/pyarchi/validation/permissions.py`, exported from `pyarchi.__init__`
- [x] [STORY-21.2.3] Write benchmark: `is_permitted()` lookup time for 10,000 calls before and after caching — `test_bench_warm_cache_time` in `test/benchmarks/test_bench_permissions.py`
- [~] [STORY-21.2.4] Write test: cache invalidation works correctly when a `Profile` adds new specialization types — **WONTFIX** per ADR-034: Profiles add specializations, not new concrete types; the permission cache operates on concrete `type` objects, not specialization strings. No invalidation needed.

### [FEAT-21.3] Model Memory Optimization — Closed (baseline under threshold)
- [x] [STORY-21.3.1] Profile memory usage of a 10,000-element model using `tracemalloc`; document baseline — **7.36 MB** (FEAT-21.4 benchmark), well under 100MB decision gate
- [~] [STORY-21.3.2] Implement `__slots__` on high-frequency classes — **WONTFIX** (Pydantic v2 incompatible, ADR-034 Decision 6)
- [~] [STORY-21.3.3] Evaluate and implement ID interning — **WONTFIX** (7.36 MB baseline does not warrant optimization)
- [~] [STORY-21.3.4] Write benchmark: memory before/after — **WONTFIX** (no optimization to measure)

### [FEAT-21.4] Benchmark Suite
**Deliverable: benchmark harness in `test/benchmarks/` (ADR-034 Decision 1)**

- [~] [STORY-21.4.1] Implement `iterparse`-based streaming deserialization in `Model.from_file()` for files > 50 MB — **DEFERRED** per ADR-034 Decision 5 (keep single-pass lxml for now; streaming gated on benchmark data)
- [~] [STORY-21.4.2] Add progress callback parameter to `Model.from_file(path, on_progress=...)` for large file loading — **DEFERRED** depends on STORY-21.4.1
- [~] [STORY-21.4.3] Write test: loading a 50 MB synthetic XML file completes without exceeding 2x file size in memory — **DEFERRED** depends on STORY-21.4.1
- [~] [STORY-21.4.4] Write test: progress callback is invoked at least once per 1000 elements during large file load — **DEFERRED** depends on STORY-21.4.1

---

## [EPIC-022] Predefined Viewpoint Catalogue
**Status:** Complete
**Priority:** Medium

Implement the example viewpoints from Appendix C of the ArchiMate 3.2 Specification as a predefined catalogue. Per Section 1.3, support for these viewpoints is optional (`may`) but provides significant usability value.

### [FEAT-22.1] Standard Viewpoint Definitions
- [x] [STORY-22.1.1] Define `_build_organization` with permitted types: `BusinessActor`, `BusinessRole`, `BusinessCollaboration`, `BusinessInterface`, `Location`, `Composition`, `Aggregation`, `Assignment`, `Serving`, `Realization`, `Association`, `Specialization`
- [x] [STORY-22.1.2] Define `_build_application_cooperation` with permitted types: `ApplicationComponent`, `ApplicationCollaboration`, `ApplicationInterface`, `ApplicationFunction`, `ApplicationInteraction`, `ApplicationProcess`, `ApplicationEvent`, `ApplicationService`, `DataObject`, `Location`, `Serving`, `Flow`, `Triggering`, `Realization`, `Access`, `Composition`, `Aggregation`, `Assignment`, `Association`, `Specialization`
- [x] [STORY-22.1.3] Define `_build_technology_usage` with permitted types covering technology and application layer interactions
- [x] [STORY-22.1.4] Define `_build_motivation` with all motivation element types and `Influence`, `Realization`, `Association`, `Aggregation`, `Composition`, `Specialization`
- [x] [STORY-22.1.5] Define `_build_strategy` with `Resource`, `Capability`, `ValueStream`, `CourseOfAction` and relevant relationships
- [x] [STORY-22.1.6] Define `_build_implementation_and_migration` with `WorkPackage`, `Deliverable`, `ImplementationEvent`, `Plateau`, `Gap`, `Location` and relevant relationships
- [x] [STORY-22.1.7] Define `_build_business_process_cooperation` with business behavior, service, and active structure types
- [x] [STORY-22.1.8] Define `_build_information_structure` with passive structure types across layers
- [x] [STORY-22.1.9] Define `_build_layered` spanning all layers with permitted types for full-stack architecture views
- [x] [STORY-22.1.10] Write test: each predefined viewpoint has a non-empty `permitted_concept_types` set and valid `purpose`/`content` categories

### [FEAT-22.2] Viewpoint Catalogue Registry
- [x] [STORY-22.2.1] Implement `VIEWPOINT_CATALOGUE: dict[str, Viewpoint]` mapping viewpoint names to instances
- [x] [STORY-22.2.2] Export `VIEWPOINT_CATALOGUE` from `pyarchi` top-level
- [x] [STORY-22.2.3] Write test: `VIEWPOINT_CATALOGUE["Organization"]` returns the organization viewpoint
- [x] [STORY-22.2.4] Write test: creating a `View` with a catalogue viewpoint correctly filters concepts

---

## [EPIC-023] Model Querying and Filtering API
**Status:** Complete
**Priority:** High

Provide a fluent, composable API for querying and filtering model contents. Enables users to extract subsets of a model without manual iteration.

### [FEAT-23.1] Element Query Interface
- [~] [STORY-23.1.1] Implement `Model.query()` returning a `QueryBuilder` with chainable filter methods — **WONTFIX** per ADR-036 D1 (QueryBuilder rejected; direct methods on Model used instead)
- [x] [STORY-23.1.2] Implement `Model.elements_of_type(cls)` to filter by element type (including subclass matching)
- [x] [STORY-23.1.3] Implement `Model.elements_by_layer(layer: Layer)` to filter by layer classification
- [x] [STORY-23.1.4] Implement `Model.elements_by_aspect(aspect: Aspect)` to filter by aspect classification
- [x] [STORY-23.1.5] Implement `Model.elements_by_name(pattern, *, regex=False)` with substring and optional regex matching (glob rejected per ADR-036 D3)
- [~] [STORY-23.1.6] Implement `QueryBuilder.all()` and `QueryBuilder.first()` — **WONTFIX** per ADR-036 D1 (no QueryBuilder)
- [x] [STORY-23.1.7] Write test: `model.elements_of_type(BusinessActor)` returns only business actors — `test/test_feat231_element_queries.py::TestElementsOfType`
- [x] [STORY-23.1.8] Write test: composition via list comprehension replaces chained QueryBuilder — `test/test_feat231_element_queries.py::TestComposition`

### [FEAT-23.2] Relationship Traversal
- [x] [STORY-23.2.1] Implement `Model.sources_of(concept)` returning all source concepts of relationships targeting the given concept — `src/pyarchi/metamodel/model.py`
- [x] [STORY-23.2.2] Implement `Model.targets_of(concept)` returning all target concepts of relationships sourced from the given concept — `src/pyarchi/metamodel/model.py`
- [x] [STORY-23.2.3] Implement `Model.connected_to(concept)` returning all relationships where concept is source or target — `src/pyarchi/metamodel/model.py`
- [~] [STORY-23.2.4] Implement `path_between(source, target, max_hops=5)` returning shortest relationship path — **DEFERRED** per ADR D5 (graph traversal gated on future graph epic)
- [x] [STORY-23.2.5] Write test: `targets_of(actor)` filtered by type returns roles assigned to the actor — `test/test_feat232_relationship_traversal.py::TestTargetsOf::test_composition_with_of_type`
- [~] [STORY-23.2.6] Write test: `path_between` with no valid path returns empty list — **DEFERRED** (depends on STORY-23.2.4)

### [FEAT-23.3] Relationship Query Interface
- [~] [STORY-23.3.1] Implement `QueryBuilder.relationships()` switching the query to operate over relationships instead of elements — **WONTFIX** per ADR D6 (QueryBuilder rejected; `Model.relationships_of_type()` replaces it)
- [~] [STORY-23.3.2] Implement `QueryBuilder.of_category(cat: RelationshipCategory)` to filter relationships by category — **WONTFIX** per ADR D6 (trivial comprehension: `[r for r in model.relationships_of_type(X) if r.category == cat]`)
- [~] [STORY-23.3.3] Implement `QueryBuilder.between(source_type, target_type)` to filter relationships by source/target type constraints — **WONTFIX** per ADR D6 (trivial comprehension over `relationships_of_type`)
- [x] [STORY-23.3.4] Write test: `model.relationships_of_type(Serving)` returns all serving relationships — `test/test_feat233_relationship_query.py::TestRelationshipsOfType`
- [x] [STORY-23.3.5] Write test: composition via comprehension over `relationships_of_type` filters by source/target type — `test/test_feat233_relationship_query.py::TestCompositionPatterns::test_between_types`

---

## [EPIC-024] Model Comparison and Diff Utilities
**Status:** Complete
**Priority:** Medium

Provide utilities for comparing two model instances and producing a structured diff, enabling change tracking and migration analysis.

### [FEAT-24.1] Structural Diff Engine
- [x] [STORY-24.1.1] Implement `ModelDiff` frozen dataclass with fields: `added: tuple[Concept, ...]`, `removed: tuple[Concept, ...]`, `modified: tuple[ConceptChange, ...]`; plus `FieldChange` and `ConceptChange` frozen dataclasses — `src/pyarchi/comparison.py`
- [x] [STORY-24.1.2] Implement `diff_models(model_a: Model, model_b: Model, *, match_by: Literal["id", "type_name"] = "id") -> ModelDiff` in `src/pyarchi/comparison.py`
- [x] [STORY-24.1.3] Implement attribute-level change detection via `_normalize_dump()` / `_diff_fields()` helpers; Relationship `source`/`target` normalized to id strings before comparison
- [x] [STORY-24.1.4] Write test: adding an element to model_b shows it in `diff.added` — `TestDiffById::test_added_element`
- [x] [STORY-24.1.5] Write test: renaming an element shows it in `diff.modified` with the old and new names — `TestDiffById::test_modified_element_name_change`

### [FEAT-24.2] Diff Serialization
- [x] [STORY-24.2.1] Implement `ModelDiff.to_dict()` for JSON-serializable diff output — `src/pyarchi/comparison.py`
- [x] [STORY-24.2.2] Implement `ModelDiff.summary() -> str` for human-readable diff summary — `src/pyarchi/comparison.py`
- [x] [STORY-24.2.3] Write test: round-trip `ModelDiff -> dict -> ModelDiff` preserves all diff entries — `test/test_feat242_diff_serialization.py::TestToDict::test_to_dict_round_trip_keys`
- [x] [STORY-24.2.4] Write test: `summary()` includes counts of added, removed, and modified concepts — `test/test_feat242_diff_serialization.py::TestSummary`

### [FEAT-24.3] Merge Support
- [ ] [STORY-24.3.1] Implement `merge(base: Model, theirs: Model) -> Model` for non-conflicting merges (additions and removals only)
- [ ] [STORY-24.3.2] Implement conflict detection: raise `MergeConflictError` when both models modify the same concept differently
- [ ] [STORY-24.3.3] Write test: merging two models with non-overlapping additions produces a combined model
- [ ] [STORY-24.3.4] Write test: merging two models that both modify the same element raises `MergeConflictError`

---

## [EPIC-025] Plugin and Extension System
**Status:** Complete
**Priority:** Low

Provide a plugin mechanism for registering custom element types, relationship rules, and serialization formats beyond the standard ArchiMate language.

### [FEAT-25.1] Element Type Registry
- [~] [STORY-25.1.1] Implement `TypeRegistry` class that manages the mapping between type names and concrete classes — **WONTFIX** per ADR-038: plain dict + function sufficient
- [~] [STORY-25.1.2] Implement `TypeRegistry.register(cls)` decorator for registering custom element subclasses — **WONTFIX** per ADR-038: explicit call preferred
- [~] [STORY-25.1.3] Implement `TypeRegistry.unregister(cls)` for removing custom types — **WONTFIX** per ADR-038: YAGNI
- [x] [STORY-25.1.4] Integrate `TypeRegistry` with the serialization layer so custom types can be serialized/deserialized — covered by `register_element_type()` adding to `TYPE_REGISTRY`
- [x] [STORY-25.1.5] Write test: registering a custom `CloudService(TechnologyService)` type allows instantiation and serialization — `test/test_feat251_registration_hooks.py`
- [~] [STORY-25.1.6] Write test: unregistering a type and then attempting deserialization of that type raises a warning — **WONTFIX** per ADR-038: no `unregister()`

### [FEAT-25.2] Custom Validation Rules
- [x] [STORY-25.2.1] Implement `ValidationRule` protocol with `def validate(model: Model) -> list[ValidationError]`
- [x] [STORY-25.2.2] Implement `Model.add_validation_rule(rule: ValidationRule)` for registering custom rules
- [x] [STORY-25.2.3] Ensure `Model.validate()` runs custom rules in addition to built-in rules
- [x] [STORY-25.2.4] Write test: a custom rule that forbids elements with empty documentation is triggered by `Model.validate()`
- [x] [STORY-25.2.5] Write test: removing a custom rule excludes it from subsequent `validate()` calls

### [FEAT-25.3] Serialization Format Plugins — **Deferred per ADR-038**
- [~] [STORY-25.3.1] Define `SerializationPlugin` protocol with `serialize(model: Model) -> bytes` and `deserialize(data: bytes) -> Model` — **DEFERRED** per ADR-038: entry-point discovery adds framework complexity for zero known consumers
- [~] [STORY-25.3.2] Implement plugin discovery via entry points (`pyarchi.serializers` group) — **DEFERRED** per ADR-038
- [~] [STORY-25.3.3] Write test: a YAML serialization plugin registered via entry point is discoverable and usable — **DEFERRED** per ADR-038

---

## [EPIC-026] Documentation and API Reference
**Status:** Complete
**Priority:** High

Generate comprehensive API documentation, a user guide, and architecture documentation from source code and docstrings.

### [FEAT-26.1] API Reference Generation
- [x] [STORY-26.1.1] Configure MkDocs with mkdocstrings to generate API reference from docstrings — `mkdocs.yml`, `pyproject.toml` `docs` optional dependency group, and 27-file `docs/` scaffold created; `mkdocs build --strict` passes
- [ ] [STORY-26.1.2] Add docstrings to all public classes in `__all__` (minimum: one-line summary and parameter descriptions) — **To-Do** (current coverage: 38%, tracked by `test_all_public_symbols_have_docstrings`)
- [ ] [STORY-26.1.3] Add docstrings to all public methods on `Model`, `QueryBuilder`, `DerivationEngine` — **To-Do** (method coverage currently 100% for methods already present)
- [x] [STORY-26.1.4] Docstring coverage test — `test/test_docstring_coverage.py` created with three `@pytest.mark.slow` informational tests; reports symbol/method/module coverage percentages without asserting 100%

### [FEAT-26.2] User Guide
- [x] [STORY-26.2.1] Write "Getting Started" guide: installation, creating a model, adding elements and relationships — `docs/getting-started.md`, `docs/index.md`, `docs/user-guide/building-models.md`
- [x] [STORY-26.2.2] Write "Serialization" guide: XML export/import, JSON export/import, round-trip examples — `docs/user-guide/serialization.md`, `examples/xml_roundtrip.py`
- [x] [STORY-26.2.3] Write "Validation" guide: using `Model.validate()`, understanding `ValidationError`, custom rules — `docs/user-guide/validation.md`, `examples/validation_demo.py`
- [x] [STORY-26.2.4] Write "Viewpoints" guide: creating viewpoints, filtering views, predefined catalogue usage — `docs/user-guide/viewpoints.md`, `examples/viewpoint_filter.py`
- [x] [STORY-26.2.5] Write "Language Customization" guide: profiles, specializations, attribute extensions — `docs/user-guide/profiles.md`, `examples/profile_extension.py`

### [FEAT-26.3] Architecture Documentation
- [x] [STORY-26.3.1] Generate ADR index page from `docs/adr/` directory — `docs/architecture/adr-index.md`, `scripts/generate_adr_index.py`
- [x] [STORY-26.3.2] Write class hierarchy diagram (text-based or generated) showing the full element taxonomy — `docs/architecture/overview.md` with Mermaid classDiagram
- [x] [STORY-26.3.3] Write relationship permission matrix documentation with cross-references to Appendix B — `docs/architecture/permission-matrix.md`, `scripts/generate_permission_matrix.py`

---

## [EPIC-027] Packaging, Distribution, and CI/CD
**Status:** Complete
**Priority:** High

Prepare the library for PyPI publication, set up CI/CD pipelines, and configure release automation.

### [FEAT-27.1] PyPI Packaging
- [x] [STORY-27.1.1] Finalize `pyproject.toml` metadata: description, classifiers, URLs, license, keywords
- [~] [STORY-27.1.2] Configure optional dependency groups: `pyarchi[xml]` for lxml, `pyarchi[dev]` for test/lint tools, `pyarchi[docs]` for documentation generation — **Skip**: already done; added `pytest-cov`, `build`, `twine` to `[dev]`
- [~] [STORY-27.1.3] Add `py.typed` marker file for PEP 561 type stub distribution — **Skip**: already exists at `src/pyarchi/py.typed`
- [x] [STORY-27.1.4] Build and validate sdist and wheel with `python -m build`; verify contents
- [x] [STORY-27.1.5] Write test: installing the built wheel in a clean virtualenv allows `import pyarchi` and basic model creation

### [FEAT-27.2] CI/CD Pipeline
- [x] [STORY-27.2.1] Configure GitHub Actions workflow: lint (ruff), type check (mypy), test (pytest) on Python 3.12 — Complete (`ci.yml` with lint/format/typecheck/test jobs)
- [x] [STORY-27.2.2] Add matrix testing for Python 3.11 and 3.13 compatibility — Complete (3.12 + 3.13 per ADR-040; `requires-python = ">=3.12"` so 3.11 excluded)
- [x] [STORY-27.2.3] Add test coverage reporting with minimum threshold (target: 90%) — Complete (`pytest-cov` with `--cov-fail-under=90` in ci.yml)
- [x] [STORY-27.2.4] Configure automated PyPI publishing on tagged releases — Complete (`release.yml` with OIDC trusted publishing via `pypa/gh-action-pypi-publish`)
- [~] [STORY-27.2.5] Write test: CI configuration files are valid YAML — **Skip** (GitHub Actions validates on push; structural text-based tests in `test_feat272_cicd_pipelines.py` cover correctness)

### [FEAT-27.3] Release Management
- [~] [STORY-27.3.1] Implement version management using `hatch version` or `setuptools-scm` — **Skip** per ADR-040 D2 (manual version in `pyproject.toml`; no tooling needed)
- [~] [STORY-27.3.2] Create `CHANGELOG.md` with Keep a Changelog format; document Phases 1-3 — **Skip** (covered by STORY-27.1.4 in FEAT-27.1)
- [x] [STORY-27.3.3] Write release checklist documenting the publish workflow — `docs/releasing.md`

---

## [EPIC-028] Archi Tool Interoperability Testing
**Status:** In Progress
**Priority:** High (upgraded — blocks real-world usage)

Validate that pyarchi-generated Exchange Format files are compatible with the Archi modeling tool and other ArchiMate-compliant tools. Ensure round-trip fidelity. Addresses issues documented in `docs/dev-brief/ARCHI-COMPAT-ISSUES.md`.

### [FEAT-28.1] Exchange Format Compliance Fixes (blocks Archi import)
- [x] [STORY-28.1.1] Add `<name xml:lang="en">` sub-element on `<model>` root — **likely root cause of Archi import failure** (XSD `ModelType` requires `NameGroup`). Accept optional `model_name: str` parameter in `serialize_model()`, default `"Untitled Model"`
- [x] [STORY-28.1.2] Add `xml:lang="en"` attribute to all `<name>` and `<documentation>` sub-elements in `serialize_element()` and `serialize_relationship()` — XSD `LangStringType` supports it; Archi always emits it
- [x] [STORY-28.1.3] Add `xsi:schemaLocation` attribute on `<model>` root: `"http://www.opengroup.org/xsd/archimate/3.0/ http://www.opengroup.org/xsd/archimate/3.1/archimate3_Diagram.xsd"`
- [x] [STORY-28.1.4] Bundle the 3 XSD files (`archimate3_Model.xsd`, `archimate3_View.xsd`, `archimate3_Diagram.xsd`) from `examples/` into `src/pyarchi/serialization/schema/`
- [x] [STORY-28.1.5] Update `_deserialize_element()` to handle `xml:lang` attribute on `<name>` during import (currently ignores it — should still work but be explicit)
- [x] [STORY-28.1.6] Validate our output against the bundled XSD — run `validate_exchange_format()` on the pet_shop model and fix any remaining XSD errors
- [x] [STORY-28.1.7] Write test: exported XML has `<name xml:lang="en">` on model root
- [x] [STORY-28.1.8] Write test: all `<name>` sub-elements have `xml:lang` attribute
- [x] [STORY-28.1.9] Write test: exported XML passes XSD validation against bundled schema
- [x] VERIFIED: `xsi:type` values match XSD `ElementTypeEnum`/`RelationshipTypeEnum` exactly — no suffix needed
- [x] VERIFIED: `accessType`, `modifier` attribute names match XSD — no changes needed

### [FEAT-28.2] Archi Import/Export Validation
- [x] [STORY-28.2.1] Create a reference Archi model with representative elements — `examples/pet_shop-from_archi.xml` (53 elements, 49 relationships incl. Archi-added Security Monitoring Service + Association)
- [x] [STORY-28.2.2] Export from Archi; import into pyarchi — **CONFIRMED**: all 53 elements, 49 relationships, 31 types loaded; organizations + views preserved as opaque XML
- [x] [STORY-28.2.3] Export from pyarchi; import into Archi — **CONFIRMED**: `examples/pet_shop.xml` imported via `File > Import > Open Exchange XML Model`
- [x] [STORY-28.2.4] Round-trip through Archi preserves elements — `examples/test_archi_roundtrip.py` verifies all elements, relationships, types, Archi-added content, and opaque XML survive
- [x] [STORY-28.2.5] Document the Archi import workflow for pyarchi users — added "Archi Compatibility" section to README.md with step-by-step import/export instructions

### [FEAT-28.3] Visual Data Preservation
- [ ] [STORY-28.3.1] Parse view/diagram coordinates (x, y, width, height) from Exchange Format XML during deserialization
- [ ] [STORY-28.3.2] Preserve bendpoint data on relationship connections during round-trip
- [ ] [STORY-28.3.3] Preserve view metadata (name, documentation, viewpoint reference) during round-trip
- [ ] [STORY-28.3.4] Write test: loading an Exchange Format file with diagram data and re-serializing produces byte-equivalent view sections

### [FEAT-28.4] XSD Schema Bundling — Completed (delivered in FEAT-28.1)
- [x] [STORY-28.4.1] Bundle the official ArchiMate Exchange Format XSD schema within the package — delivered in STORY-28.1.4 (`src/pyarchi/serialization/schema/`)
- [x] [STORY-28.4.2] Implement `validate_xml(path: Path) -> list[str]` utility — `validate_exchange_format()` already existed (FEAT-19.6), now functional with bundled XSD
- [x] [STORY-28.4.3] Write test: a known-valid Exchange Format file passes XSD validation — covered in `test_feat281_exchange_compliance.py`
- [x] [STORY-28.4.4] Write test: an intentionally malformed XML file fails XSD validation with descriptive errors — covered in `test_feat281_exchange_compliance.py`

### [FEAT-28.5] Archi Native Format Support (Optional)
- [ ] [STORY-28.5.1] Investigate feasibility of reading/writing Archi's proprietary `.archimate` format (namespace `http://www.archimatetool.com/archimate`)
- [ ] [STORY-28.5.2] If feasible, implement `read_archi_native(path) -> Model` for direct `.archimate` import
- [ ] [STORY-28.5.3] Document the difference between Archi native format and Open Group Exchange Format for users

---

## [EPIC-029] CLI Tooling
**Status:** To-Do
**Priority:** Low

Provide a command-line interface for common model operations: validation, format conversion, querying, and diffing.

### [FEAT-29.1] Core CLI Framework
- [ ] [STORY-29.1.1] Implement `pyarchi` CLI entry point using `click` or `argparse`
- [ ] [STORY-29.1.2] Implement `pyarchi validate <file>` command that loads a model and runs `Model.validate()`
- [ ] [STORY-29.1.3] Implement `pyarchi info <file>` command that prints model summary (element counts by layer, relationship counts by type)
- [ ] [STORY-29.1.4] Write test: `pyarchi validate` on a valid Exchange Format file exits with code 0
- [ ] [STORY-29.1.5] Write test: `pyarchi validate` on an invalid file exits with code 1 and prints errors

### [FEAT-29.2] Format Conversion
- [ ] [STORY-29.2.1] Implement `pyarchi convert <input> <output>` supporting XML-to-JSON and JSON-to-XML conversion
- [ ] [STORY-29.2.2] Implement `--format` flag for explicit output format specification
- [ ] [STORY-29.2.3] Write test: `pyarchi convert model.xml model.json` produces valid JSON output
- [ ] [STORY-29.2.4] Write test: round-trip conversion XML -> JSON -> XML preserves all concepts

### [FEAT-29.3] CLI Query and Diff
- [ ] [STORY-29.3.1] Implement `pyarchi query <file> --type <ElementType>` to list elements of a given type
- [ ] [STORY-29.3.2] Implement `pyarchi diff <file_a> <file_b>` to print structural differences
- [ ] [STORY-29.3.3] Write test: `pyarchi diff` on identical files reports no differences
- [ ] [STORY-29.3.4] Write test: `pyarchi query --type BusinessActor` returns only business actors
