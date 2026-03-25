---
project: pyarchi
phase: 3
last_updated: 2026-03-25
total_epics: 21
total_features: 79
total_stories: 311
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

## Phase 3 — Model Validation, Viewpoints, Serialization, and Customization

Phase 3 covers the remaining specification requirements not addressed in Phases 1 and 2: model-level validation enforcement, the complete Appendix B permission table as declarative data, the viewpoint mechanism (Requirement 14), language customization, the Open Group Exchange Format serialization layer, and conformance cleanup.

---

## [EPIC-015] Model-Level Validation Engine
**Status:** Complete
**Priority:** High

Resolves all deferred model-level validation xfails (ADR-017 ss5/ss6). Adds construction-time and model-time enforcement of relationship direction, source/target type constraints, and Junction homogeneity.

### [FEAT-15.1] Relationship Direction Enforcement
- [x] [STORY-15.1.1] Implement `Assignment` direction validation: source must be active structure or behavior, target must be behavior or passive structure; raise `ValidationError` on wrong direction
- [x] [STORY-15.1.2] Implement `Access` direction validation: source must be behavior or active structure, target must be passive structure; raise `ValidationError` on wrong direction
- [x] [STORY-15.1.3] Implement `Serving` direction validation: source is provider, target is consumer; raise `ValidationError` on wrong direction
- [x] [STORY-15.1.4] Implement `Realization` direction validation: source is lower abstraction (realizer), target is higher abstraction (realized); raise `ValidationError` on wrong direction
- [x] [STORY-15.1.5] Write test: `Assignment(source=PassiveStructureElement, target=BehaviorElement)` raises `ValidationError` (resolve xfail in `test_feat052_structural.py`)
- [x] [STORY-15.1.6] Write test: `Access(source=PassiveStructureElement, target=BehaviorElement)` raises `ValidationError` (resolve xfail in `test_feat054_access.py`)
- [x] [STORY-15.1.7] Write test: `Serving` wrong direction raises `ValidationError` (resolve xfail in `test_feat053_serving.py`)

### [FEAT-15.2] Aggregation/Composition Target Validation
- [x] [STORY-15.2.1] Implement rule: when target of `Aggregation` or `Composition` is a `Relationship`, source must be a `CompositeElement`; raise `ValidationError` otherwise
- [x] [STORY-15.2.2] Write test: `Aggregation(source=NonComposite, target=some_relationship)` raises `ValidationError` (resolve xfail in `test_feat052_structural.py`)

### [FEAT-15.3] Specialization Same-Type Enforcement
- [x] [STORY-15.3.1] Implement construction-time or model-time check: `Specialization` only permitted between same concrete type; raise `ValidationError` for cross-type
- [x] [STORY-15.3.2] Write test: `Specialization(source=BusinessProcess, target=ApplicationFunction)` raises `ValidationError` (resolve xfail in `test_feat058_specialization.py`)

### [FEAT-15.4] Junction Validation
- [x] [STORY-15.4.1] Implement validation: all relationships connected to a `Junction` must be of the same concrete relationship type; raise `ValidationError` otherwise
- [x] [STORY-15.4.2] Implement validation: endpoint elements connected via a `Junction` chain must permit the relationship type per Appendix B
- [x] [STORY-15.4.3] Write test: connecting `Composition` and `Serving` to the same `Junction` raises `ValidationError` (resolve xfail in `test_feat059_junction.py`)
- [x] [STORY-15.4.4] Write test: endpoint permission violation through `Junction` raises `ValidationError` (resolve xfail in `test_feat059_junction.py`)

### [FEAT-15.5] Collaboration Minimum-Two Constraint Enforcement
- [x] [STORY-15.5.1] Implement model-level validation: `Collaboration` subclasses (Business, Application, Technology) must have at least 2 internal active structure elements assigned; raise `ValidationError` otherwise
- [x] [STORY-15.5.2] Write test: `BusinessCollaboration` with only 1 assigned element raises `ValidationError` (resolve xfail in `test_feat046_validation.py`)

### [FEAT-15.6] Passive Structure Cannot Perform Behavior
- [x] [STORY-15.6.1] Implement model-level rule: `PassiveStructureElement` subclasses may not be `Assignment` source targeting `BehaviorElement`; raise `ValidationError`
- [x] [STORY-15.6.2] Write test: `Assignment(source=BusinessObject, target=BusinessProcess)` raises `ValidationError` (resolve xfail in `test_feat046_validation.py`)

### [FEAT-15.7] Model.validate() Method
- [x] [STORY-15.7.1] Add `Model.validate() -> list[ValidationError]` method that runs all model-level validation rules against all concepts in the model
- [x] [STORY-15.7.2] Add `Model.validate(strict=True)` mode that raises on first error instead of collecting
- [x] [STORY-15.7.3] Write test: `Model.validate()` on a model with mixed valid and invalid relationships returns the correct error list
- [x] [STORY-15.7.4] Write test: `Model.validate(strict=True)` raises `ValidationError` on first invalid relationship

---

## [EPIC-016] Declarative Relationship Permission Table
**Status:** Complete
**Priority:** High

Replaces the current ad-hoc rule-based `is_permitted()` implementation with a declarative, machine-readable Appendix B table. Enables spec revision updates without code changes.

### [FEAT-16.1] Permission Table Data Structure
- [x] [STORY-16.1.1] Design the permission table data format: `frozenset[tuple[type[Relationship], type[Element], type[Element]]]` loaded from a CSV or embedded data structure
- [x] [STORY-16.1.2] Encode all explicit triples from Appendix B of the ArchiMate 3.2 specification (beyond the universal rules already implemented)
- [x] [STORY-16.1.3] Write ADR documenting the declarative table approach and migration from rule-based to data-driven
- [x] [STORY-16.1.4] Write test: every Appendix B triple is present in the loaded table

### [FEAT-16.2] Hierarchical Type Matching
- [x] [STORY-16.2.1] Implement type-hierarchy-aware lookup: a permission for `InternalBehaviorElement` as source covers all its subclasses (Business, Application, Technology)
- [x] [STORY-16.2.2] Ensure universal rules (Composition, Aggregation, Specialization same-type; Association any-pair) remain as fast-path short-circuits
- [x] [STORY-16.2.3] Write test: permission granted for abstract base type also covers concrete subclass queries

### [FEAT-16.3] Permission Table Completeness Audit
- [x] [STORY-16.3.1] Add a parametrized test that checks every concrete element type pair against Appendix B expected results
- [x] [STORY-16.3.2] Add a parametrized test for all explicitly prohibited triples (e.g., `Realization` targeting `BusinessActor`)
- [x] [STORY-16.3.3] Write test: `is_permitted` returns `False` for triples not in the table and not covered by universal rules

---

## [EPIC-017] Viewpoint Mechanism (Requirement 14)
**Status:** To-Do
**Priority:** High

Implements the mandatory viewpoint mechanism per Section 13 of the ArchiMate 3.2 specification. Resolves the `test_viewpoint_mechanism` conformance xfail.

### [FEAT-17.1] Viewpoint Enums and Data Types
- [ ] [STORY-17.1.1] Define `PurposeCategory` enum with members: `DESIGNING`, `DECIDING`, `INFORMING`
- [ ] [STORY-17.1.2] Define `ContentCategory` enum with members: `DETAILS`, `COHERENCE`, `OVERVIEW`
- [ ] [STORY-17.1.3] Write test: both enums have exactly 3 members each

### [FEAT-17.2] Viewpoint Class
- [ ] [STORY-17.2.1] Define `Viewpoint` Pydantic model with fields: `name: str`, `purpose: PurposeCategory`, `content: ContentCategory`, `permitted_concept_types: frozenset[type[Concept]]`
- [ ] [STORY-17.2.2] Add optional field: `representation_description: str | None = None`
- [ ] [STORY-17.2.3] Add optional field: `concerns: list[Concern] = []`
- [ ] [STORY-17.2.4] Write test: `Viewpoint` can be instantiated with `purpose`, `content`, and `permitted_concept_types`
- [ ] [STORY-17.2.5] Write test: `Viewpoint` allows custom (user-defined) viewpoints, not restricted to predefined list

### [FEAT-17.3] View Class
- [ ] [STORY-17.3.1] Define `View` class with fields: `governing_viewpoint: Viewpoint`, `concepts: list[Concept]`, `underlying_model: Model`
- [ ] [STORY-17.3.2] Implement validation: `View.governing_viewpoint` is required; `None` raises `ValidationError`
- [ ] [STORY-17.3.3] Implement validation: adding a concept whose type is not in `governing_viewpoint.permitted_concept_types` raises `ValidationError`
- [ ] [STORY-17.3.4] Implement validation: adding a concept not present in `underlying_model` raises `ValidationError`
- [ ] [STORY-17.3.5] Write test: adding `BusinessProcess` to a `View` whose viewpoint does not include `BusinessProcess` raises `ValidationError`
- [ ] [STORY-17.3.6] Write test: `View` with viewpoint permitting `{ApplicationComponent, ApplicationService, Serving}` accepts a `Serving` relationship
- [ ] [STORY-17.3.7] Write test: `View` is a projection, not a copy; concepts reference the same objects as the underlying model

### [FEAT-17.4] Concern Class
- [ ] [STORY-17.4.1] Define `Concern` class with fields: `description: str`, `stakeholders: list[Stakeholder]`, `viewpoints: list[Viewpoint]`
- [ ] [STORY-17.4.2] Implement navigable associations: from `Stakeholder` to `Concern`, from `Concern` to `Viewpoint`, from `Viewpoint` to `View`
- [ ] [STORY-17.4.3] Write test: stakeholder-concern-viewpoint-view navigation chain works end-to-end

---

## [EPIC-018] Language Customization Mechanism
**Status:** To-Do
**Priority:** Medium

Implements the language customization mechanism (Chapter 14 of the ArchiMate 3.2 specification). Resolves the `test_language_customization` conformance xfail.

### [FEAT-18.1] Profile Class
- [ ] [STORY-18.1.1] Define `Profile` class that represents a named customization of the ArchiMate language
- [ ] [STORY-18.1.2] Implement `Profile.specializations: dict[type[Element], list[str]]` mapping base element types to custom specialization names
- [ ] [STORY-18.1.3] Implement `Profile.attribute_extensions: dict[type[Element], dict[str, type]]` mapping element types to additional custom attributes
- [ ] [STORY-18.1.4] Write ADR documenting the language customization design
- [ ] [STORY-18.1.5] Write test: `Profile` can be instantiated with custom specializations
- [ ] [STORY-18.1.6] Write test: `Profile` can extend an element type with additional attributes

### [FEAT-18.2] Profile Validation
- [ ] [STORY-18.2.1] Implement validation: profile specializations must reference valid ArchiMate element types
- [ ] [STORY-18.2.2] Implement validation: profile attribute extensions must not conflict with existing element attributes
- [ ] [STORY-18.2.3] Write test: specialization referencing a non-existent base type raises `ValidationError`
- [ ] [STORY-18.2.4] Write test: attribute extension conflicting with existing field raises `ValidationError`

### [FEAT-18.3] Profile Application to Model
- [ ] [STORY-18.3.1] Implement `Model.apply_profile(profile: Profile)` to register a customization profile with a model
- [ ] [STORY-18.3.2] Implement runtime element creation from profile specializations (e.g., dynamically creating a `CloudService` as a specialization of `TechnologyService`)
- [ ] [STORY-18.3.3] Write test: applying a profile to a model allows creation of specialized elements
- [ ] [STORY-18.3.4] Write test: serialized model preserves profile metadata

---

## [EPIC-019] Open Group Exchange Format Serialization
**Status:** To-Do
**Priority:** High

Implements XML serialization and deserialization for the Open Group ArchiMate Model Exchange File Format, enabling cross-tool interoperability. This is the primary persistence layer.

### [FEAT-19.1] XML Namespace and Schema Setup
- [ ] [STORY-19.1.1] Define XML namespace constants for the ArchiMate Exchange Format (namespace URI, schema location)
- [ ] [STORY-19.1.2] Embed or reference the Exchange Format XSD for validation
- [ ] [STORY-19.1.3] Write ADR documenting the serialization strategy (`lxml` for parsing, Pydantic for validation)
- [ ] [STORY-19.1.4] Write test: namespace constants match the Open Group Exchange Format specification

### [FEAT-19.2] Element Serialization
- [ ] [STORY-19.2.1] Implement `to_xml()` method on `Element` base class returning an `lxml.etree.Element`
- [ ] [STORY-19.2.2] Map each concrete element type to its Exchange Format XML tag name
- [ ] [STORY-19.2.3] Serialize element attributes: `identifier`, `name`, `documentation`, custom properties
- [ ] [STORY-19.2.4] Write test: `BusinessActor(name="Alice").to_xml()` produces correct XML element with namespace
- [ ] [STORY-19.2.5] Write test: round-trip serialization preserves element identity (`id`) and attributes

### [FEAT-19.3] Relationship Serialization
- [ ] [STORY-19.3.1] Implement `to_xml()` method on `Relationship` base class
- [ ] [STORY-19.3.2] Serialize relationship attributes: `identifier`, `source`, `target`, `name`, type-specific fields (`access_mode`, `sign`, `direction`, etc.)
- [ ] [STORY-19.3.3] Write test: `Serving(source=a, target=b).to_xml()` produces correct XML with source/target references
- [ ] [STORY-19.3.4] Write test: `Influence` serialization includes `sign` and `strength` attributes when present

### [FEAT-19.4] Model Serialization (Write)
- [ ] [STORY-19.4.1] Implement `Model.to_xml() -> lxml.etree.ElementTree` producing a complete Exchange Format document
- [ ] [STORY-19.4.2] Implement `Model.to_file(path: Path)` writing the XML tree to disk with proper encoding and declaration
- [ ] [STORY-19.4.3] Include model metadata: name, documentation, property definitions
- [ ] [STORY-19.4.4] Write test: `Model.to_xml()` produces a valid XML document with correct root element and namespace
- [ ] [STORY-19.4.5] Write test: `Model.to_file()` writes a file that can be read back

### [FEAT-19.5] Model Deserialization (Read)
- [ ] [STORY-19.5.1] Implement `Model.from_xml(tree: lxml.etree.ElementTree) -> Model` class method
- [ ] [STORY-19.5.2] Implement `Model.from_file(path: Path) -> Model` class method with stream parsing for large files
- [ ] [STORY-19.5.3] Resolve element cross-references: relationship source/target IDs to element instances
- [ ] [STORY-19.5.4] Handle unknown element types gracefully: log warning, skip or store as generic `Element`
- [ ] [STORY-19.5.5] Write test: round-trip `Model -> XML -> Model` preserves all elements and relationships
- [ ] [STORY-19.5.6] Write test: loading a file with 1000+ elements completes in under 5 seconds

### [FEAT-19.6] Exchange Format Compliance
- [ ] [STORY-19.6.1] Validate serialized XML against the Exchange Format XSD schema
- [ ] [STORY-19.6.2] Ensure ID format compliance: identifiers use the `id-` prefix format compatible with Archi tooling
- [ ] [STORY-19.6.3] Preserve visual/diagrammatic data (view coordinates, bendpoints) during round-trip even if not interpreted
- [ ] [STORY-19.6.4] Write test: serialized XML passes XSD validation
- [ ] [STORY-19.6.5] Write test: visual data present in input XML is preserved in output XML (no data loss)

### [FEAT-19.7] JSON Serialization (Optional / Secondary)
- [ ] [STORY-19.7.1] Implement `Model.to_dict() -> dict` for JSON-compatible dictionary output
- [ ] [STORY-19.7.2] Implement `Model.from_dict(data: dict) -> Model` for JSON-compatible input
- [ ] [STORY-19.7.3] Write test: round-trip `Model -> dict -> Model` preserves all concepts

---

## [EPIC-020] Conformance Cleanup and Phase 3 Public API
**Status:** To-Do
**Priority:** Medium

Resolves all remaining conformance xfails, exports Phase 3 types from the public API, and ensures the conformance test suite passes fully.

### [FEAT-20.1] Resolve Conformance xfails
- [ ] [STORY-20.1.1] Remove `xfail` from `TestShouldFeatures.test_viewpoint_mechanism` after EPIC-017 ships
- [ ] [STORY-20.1.2] Remove `xfail` from `TestShouldFeatures.test_language_customization` after EPIC-018 ships
- [ ] [STORY-20.1.3] Verify all `TestShallFeatures` tests continue to pass
- [ ] [STORY-20.1.4] Write test: every Phase 3 concrete class is importable from `pyarchi` top-level

### [FEAT-20.2] Resolve Deferred Validation xfails
- [ ] [STORY-20.2.1] Remove `xfail` from `test_feat052_structural.py::TestDeferredValidation` after FEAT-15.1 and FEAT-15.2 ship
- [ ] [STORY-20.2.2] Remove `xfail` from `test_feat053_serving.py::TestDeferredValidation` after FEAT-15.1 ships
- [ ] [STORY-20.2.3] Remove `xfail` from `test_feat054_access.py::TestDeferredValidation` after FEAT-15.1 ships
- [ ] [STORY-20.2.4] Remove `xfail` from `test_feat058_specialization.py::TestDeferredValidation` after FEAT-15.3 ships
- [ ] [STORY-20.2.5] Remove `xfail` from `test_feat059_junction.py::TestDeferredValidation` after FEAT-15.4 ships
- [ ] [STORY-20.2.6] Remove `xfail` from `test_feat046_validation.py::TestCollaborationValidation` after FEAT-15.5 ships
- [ ] [STORY-20.2.7] Remove `xfail` from `test_feat046_validation.py::TestPassiveCannotPerformBehavior` after FEAT-15.6 ships

### [FEAT-20.3] Update __init__.py Exports
- [ ] [STORY-20.3.1] Export `Viewpoint`, `View`, `Concern`, `PurposeCategory`, `ContentCategory` from `pyarchi`
- [ ] [STORY-20.3.2] Export `Profile` from `pyarchi`
- [ ] [STORY-20.3.3] Update `__all__` list to include all Phase 3 public types
- [ ] [STORY-20.3.4] Write test: `__all__` list matches the actual public API surface
