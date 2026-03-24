---
project: pyarchi
phase: 1
last_updated: 2026-03-23
total_epics: 6
total_features: 24
total_stories: 96
---

# Phase 1 Backlog

Phase 1 covers Requirements 1 through 5 from the PRD: project scaffold, scope and conformance, root type hierarchy, language structure and classification framework, abstract element hierarchy, all eleven relationships, Junction, and the derivation engine.

---

## [EPIC-000] Project Scaffold and Build System
**Status:** Complete
**Priority:** High

### [FEAT-00.1] Package Configuration
- [x] [STORY-00.1.1] Create `pyproject.toml` with project metadata, Python 3.12 minimum, and dependency declarations (pydantic v2)
- [x] [STORY-00.1.2] Establish `src/pyarchi/` package directory with `__init__.py` exposing the public API
- [x] [STORY-00.1.3] Configure pytest as the test runner in `pyproject.toml` and create `test/conftest.py` with shared fixtures
- [x] [STORY-00.1.4] Configure ruff as the linter and formatter with strict PEP 8 and type-hint enforcement rules
- [x] [STORY-00.1.5] Add mypy configuration for strict static type checking across the library

### [FEAT-00.2] Module Layout
- [x] [STORY-00.2.1] Create `src/pyarchi/metamodel/` sub-package for all metamodel classes (concepts, elements, relationships)
- [x] [STORY-00.2.2] Create `src/pyarchi/enums.py` module for all enumeration types (Layer, Aspect, RelationshipCategory, etc.)
- [x] [STORY-00.2.3] Create `src/pyarchi/validation/` sub-package for validation logic and error types
- [x] [STORY-00.2.4] Create `src/pyarchi/derivation/` sub-package for the derivation engine
- [x] [STORY-00.2.5] Create `src/pyarchi/exceptions.py` module defining `ValidationError` and other custom exception types
- [x] [STORY-00.2.6] Update `CLAUDE.md` with build, test, and lint commands once tooling is configured

---

## [EPIC-001] Scope and Conformance (Requirement 1)
**Status:** To-Do
**Priority:** High

### [FEAT-01.1] ConformanceProfile
- [x] [STORY-01.1.1] Define `ConformanceProfile` dataclass in `src/pyarchi/conformance.py` enumerating all mandatory spec features as queryable boolean attributes
- [x] [STORY-01.1.2] Include attributes for: language structure, generic metamodel, all layer element types, cross-layer dependencies, iconography metadata, viewpoint mechanism, language customization, Appendix B relationship table
- [x] [STORY-01.1.3] Add class-level constant `SPEC_VERSION = "3.2"` and expose it in the library `__init__.py`
- [x] [STORY-01.1.4] Mark optional features (Appendix C example viewpoints) with a `may` designation that does not affect conformance checks

### [FEAT-01.2] Conformance Test Suite
- [ ] [STORY-01.2.1] Create `test/test_conformance.py` with assertions for each `shall`-level mandatory feature presence in the public API
- [ ] [STORY-01.2.2] Add warning-level checks for `should`-level features using `pytest.warns` or custom markers
- [ ] [STORY-01.2.3] Verify that `may`-level features do not cause test failure when absent

### [FEAT-01.3] Undefined Type Guard
- [ ] [STORY-01.3.1] Implement guard logic so that attempting to use an element type not defined in the ArchiMate 3.2 spec raises `NotImplementedError` or `TypeError`
- [ ] [STORY-01.3.2] Write tests confirming that fabricated/undefined element type names raise errors, not silent failures

---

## [EPIC-002] Definitions and Root Type Hierarchy (Requirement 2)
**Status:** To-Do
**Priority:** High

### [FEAT-02.1] Concept Abstract Base Class
- [ ] [STORY-02.1.1] Define `Concept` as an ABC in `src/pyarchi/metamodel/concepts.py` that cannot be directly instantiated
- [ ] [STORY-02.1.2] Add unique identifier field (`id: str`) with UUID-based generation as default, supporting Archi-standard ID format override
- [ ] [STORY-02.1.3] Write test asserting `Concept()` raises `TypeError`

### [FEAT-02.2] Element Abstract Base Class
- [ ] [STORY-02.2.1] Define `Element(Concept)` as an ABC that cannot be directly instantiated
- [ ] [STORY-02.2.2] Apply the `Attribute` mixin to `Element` providing `name: str`, `description: str | None`, and `documentation_url: str | None` fields
- [ ] [STORY-02.2.3] Write test asserting `Element()` raises `TypeError`
- [ ] [STORY-02.2.4] Write test asserting `isinstance(any_concrete_element, Concept)` returns `True`

### [FEAT-02.3] Relationship Abstract Base Class
- [ ] [STORY-02.3.1] Define `Relationship(Concept)` as an ABC with `source` and `target` fields typed as `Concept`
- [ ] [STORY-02.3.2] Apply the `Attribute` mixin to `Relationship` providing `name`, `description`, and `documentation_url` fields
- [ ] [STORY-02.3.3] Add `is_derived: bool = False` field on `Relationship` for derivation engine use
- [ ] [STORY-02.3.4] Add `category: RelationshipCategory` as an abstract class-level attribute that subclasses must define
- [ ] [STORY-02.3.5] Write test asserting `Relationship()` raises `TypeError`
- [ ] [STORY-02.3.6] Write test asserting `isinstance(any_concrete_relationship, Concept)` returns `True`

### [FEAT-02.4] RelationshipConnector Abstract Base Class
- [ ] [STORY-02.4.1] Define `RelationshipConnector(Concept)` as an ABC that is a sibling of `Relationship`, not a subtype
- [ ] [STORY-02.4.2] Write test asserting `RelationshipConnector()` raises `TypeError`
- [ ] [STORY-02.4.3] Write test asserting `RelationshipConnector` is not a subclass of `Relationship`

### [FEAT-02.5] Attribute Mixin
- [ ] [STORY-02.5.1] Define `AttributeMixin` (or shared base) in `src/pyarchi/metamodel/mixins.py` with fields: `name: str`, `description: str | None = None`, `documentation_url: str | None = None`
- [ ] [STORY-02.5.2] Write test confirming the mixin is present on both a concrete element and a concrete relationship instance

### [FEAT-02.6] Model Container
- [ ] [STORY-02.6.1] Define `Model` class in `src/pyarchi/metamodel/model.py` with `concepts: list[Concept]` as the primary container
- [ ] [STORY-02.6.2] Implement `__iter__` on `Model` to iterate over all concepts
- [ ] [STORY-02.6.3] Implement `__getitem__` on `Model` to retrieve concepts by ID
- [ ] [STORY-02.6.4] Add helper properties: `model.elements` (filtered view of Element instances), `model.relationships` (filtered view of Relationship instances)
- [ ] [STORY-02.6.5] Write test asserting `Model` accepts a list of `Concept` instances and `model.concepts` is iterable

---

## [EPIC-003] Language Structure and Classification Framework (Requirement 3)
**Status:** To-Do
**Priority:** High

### [FEAT-03.1] Layer Enum
- [ ] [STORY-03.1.1] Define `Layer` enum in `src/pyarchi/enums.py` with seven members: `STRATEGY`, `MOTIVATION`, `BUSINESS`, `APPLICATION`, `TECHNOLOGY`, `PHYSICAL`, `IMPLEMENTATION_MIGRATION`
- [ ] [STORY-03.1.2] Write test asserting all seven values are present and accessible

### [FEAT-03.2] Aspect Enum
- [ ] [STORY-03.2.1] Define `Aspect` enum in `src/pyarchi/enums.py` with five members: `ACTIVE_STRUCTURE`, `BEHAVIOR`, `PASSIVE_STRUCTURE`, `MOTIVATION`, `COMPOSITE`
- [ ] [STORY-03.2.2] Write test asserting all five values are present and accessible

### [FEAT-03.3] NotationMetadata Dataclass
- [ ] [STORY-03.3.1] Define `NotationMetadata` dataclass in `src/pyarchi/metamodel/notation.py` with fields: `corner_shape: str`, `layer_color: str`, `badge_letter: str | None`
- [ ] [STORY-03.3.2] Attach `NotationMetadata` as an optional class-level attribute on concrete element classes (not part of core data model)
- [ ] [STORY-03.3.3] Write test confirming `NotationMetadata` exists for concrete element classes and contains all three fields

### [FEAT-03.4] Classification Metadata on Elements
- [ ] [STORY-03.4.1] Add `layer: Layer` and `aspect: Aspect` as class-level attributes on each concrete element class
- [ ] [STORY-03.4.2] Write test confirming every concrete element class exposes `.layer` and `.aspect` as enum members

### [FEAT-03.5] Nesting Rendering Hint
- [ ] [STORY-03.5.1] Add `is_nested: bool = False` field on `StructuralRelationship` base class only
- [ ] [STORY-03.5.2] Implement validation that `is_nested = True` raises `ValidationError` on non-structural relationships (dependency, dynamic, other)
- [ ] [STORY-03.5.3] Write test confirming `is_nested = True` on `Composition` does not change any validation outcome
- [ ] [STORY-03.5.4] Write test confirming `is_nested = True` on `Triggering` raises `ValidationError`

---

## [EPIC-004] Generic Metamodel -- Abstract Element Hierarchy (Requirement 4)
**Status:** To-Do
**Priority:** High

### [FEAT-04.1] StructureElement Hierarchy
- [ ] [STORY-04.1.1] Define `StructureElement(Element)` as an ABC
- [ ] [STORY-04.1.2] Define `ActiveStructureElement(StructureElement)` as an ABC
- [ ] [STORY-04.1.3] Define `InternalActiveStructureElement(ActiveStructureElement)` as an ABC
- [ ] [STORY-04.1.4] Define `ExternalActiveStructureElement(ActiveStructureElement)` as an ABC (i.e., Interface)
- [ ] [STORY-04.1.5] Define `PassiveStructureElement(StructureElement)` as an ABC
- [ ] [STORY-04.1.6] Write tests asserting direct instantiation of each ABC raises `TypeError`

### [FEAT-04.2] BehaviorElement Hierarchy
- [ ] [STORY-04.2.1] Define `BehaviorElement(Element)` as an ABC
- [ ] [STORY-04.2.2] Define `InternalBehaviorElement(BehaviorElement)` as an ABC
- [ ] [STORY-04.2.3] Define `Process(InternalBehaviorElement)` as an ABC (sequence-oriented)
- [ ] [STORY-04.2.4] Define `Function(InternalBehaviorElement)` as an ABC (criteria/resource-oriented)
- [ ] [STORY-04.2.5] Define `Interaction(InternalBehaviorElement)` as an ABC with validation requiring >= 2 active structure elements assigned
- [ ] [STORY-04.2.6] Define `ExternalBehaviorElement(BehaviorElement)` as an ABC (i.e., Service)
- [ ] [STORY-04.2.7] Define `Event(BehaviorElement)` as an ABC with optional `time: datetime | str | None = None` attribute
- [ ] [STORY-04.2.8] Write tests asserting direct instantiation of each ABC raises `TypeError`

### [FEAT-04.3] MotivationElement and CompositeElement
- [ ] [STORY-04.3.1] Define `MotivationElement(Element)` as an ABC
- [ ] [STORY-04.3.2] Define `CompositeElement(Element)` as an ABC
- [ ] [STORY-04.3.3] Write tests asserting direct instantiation of each ABC raises `TypeError`

### [FEAT-04.4] Grouping (Concrete)
- [ ] [STORY-04.4.1] Define `Grouping(CompositeElement)` as a concrete class with `layer = Layer.IMPLEMENTATION_MIGRATION` and `aspect = Aspect.COMPOSITE`
- [ ] [STORY-04.4.2] Implement `members: list[Concept]` on `Grouping` accepting both `Element` and `Relationship` instances
- [ ] [STORY-04.4.3] Write test confirming `Grouping` can be instantiated
- [ ] [STORY-04.4.4] Write test confirming `isinstance(Grouping(), CompositeElement)` and `isinstance(Grouping(), Element)` are both `True`
- [ ] [STORY-04.4.5] Write test confirming `Grouping` accepts both an `Element` and a `Relationship` as members

### [FEAT-04.5] Location (Concrete)
- [ ] [STORY-04.5.1] Define `Location(CompositeElement)` as a concrete class with `aspect = Aspect.COMPOSITE`
- [ ] [STORY-04.5.2] Implement aggregation of structure elements (active or passive) and behavior elements on `Location`
- [ ] [STORY-04.5.3] Write test confirming `Location` can be instantiated and accepts structure and behavior elements

### [FEAT-04.6] Interaction and Collaboration Validation
- [ ] [STORY-04.6.1] Implement validation rule: `Interaction` subclass requires >= 2 active structure elements assigned at validation time; fewer raises `ValidationError`
- [ ] [STORY-04.6.2] Implement validation rule: `Collaboration` (future layer-specific subclass marker) must aggregate >= 2 internal active structure elements
- [ ] [STORY-04.6.3] Implement validation rule: `PassiveStructureElement` subclasses may not be assigned to perform behavior (wrong-direction Assignment raises `ValidationError`)
- [ ] [STORY-04.6.4] Write test confirming assigning a single active structure element to an `Interaction` subclass raises `ValidationError`
- [ ] [STORY-04.6.5] Write test confirming `Event` subclass instance has `time` attribute defaulting to `None` and accepting `datetime` or `str`

---

## [EPIC-005] Relationships and Relationship Connectors (Requirement 5)
**Status:** To-Do
**Priority:** High

### [FEAT-05.1] RelationshipCategory Enum
- [ ] [STORY-05.1.1] Define `RelationshipCategory` enum in `src/pyarchi/enums.py` with members: `STRUCTURAL`, `DEPENDENCY`, `DYNAMIC`, `OTHER`
- [ ] [STORY-05.1.2] Write test asserting all four values are present

### [FEAT-05.2] Structural Relationships
- [ ] [STORY-05.2.1] Define `StructuralRelationship(Relationship)` as an ABC with `category = RelationshipCategory.STRUCTURAL` and `is_nested: bool = False`
- [ ] [STORY-05.2.2] Define `Composition(StructuralRelationship)` as a concrete class
- [ ] [STORY-05.2.3] Define `Aggregation(StructuralRelationship)` as a concrete class
- [ ] [STORY-05.2.4] Define `Assignment(StructuralRelationship)` as a concrete class
- [ ] [STORY-05.2.5] Define `Realization(StructuralRelationship)` as a concrete class
- [ ] [STORY-05.2.6] Implement validation: Composition source is the whole, target is the part; permitted between same-type elements universally
- [ ] [STORY-05.2.7] Implement validation: Aggregation source is the whole, target is the part; permitted between same-type elements universally
- [ ] [STORY-05.2.8] Implement validation: when target of Aggregation or Composition is a `Relationship`, source must be a `CompositeElement`; otherwise raise `ValidationError`
- [ ] [STORY-05.2.9] Implement validation: Assignment enforces directionality (active structure toward behavior, active structure toward passive structure, behavior toward passive structure); wrong direction raises `ValidationError`
- [ ] [STORY-05.2.10] Implement validation: Realization is directed from realizing (lower abstraction) to realized (higher abstraction); wrong direction raises `ValidationError`
- [ ] [STORY-05.2.11] Implement validation: no structural relationship may have a `Relationship` as target unless source is a `CompositeElement`
- [ ] [STORY-05.2.12] Write test: `Composition(source=A, target=B)` where A and B are same-type elements is valid
- [ ] [STORY-05.2.13] Write test: `Assignment(source=PassiveStructureElement, target=BehaviorElement)` raises `ValidationError`
- [ ] [STORY-05.2.14] Write test: `Aggregation(source=non_composite, target=relationship)` raises `ValidationError`
- [ ] [STORY-05.2.15] Write test: `is_nested = True` on `Composition` does not affect validation outcome

### [FEAT-05.3] Dependency Relationships -- Serving
- [ ] [STORY-05.3.1] Define `DependencyRelationship(Relationship)` as an ABC with `category = RelationshipCategory.DEPENDENCY`
- [ ] [STORY-05.3.2] Define `Serving(DependencyRelationship)` as a concrete class
- [ ] [STORY-05.3.3] Implement validation: Serving direction is from provider (source) to consumer (target)

### [FEAT-05.4] Dependency Relationships -- Access
- [ ] [STORY-05.4.1] Define `AccessMode` enum with members: `READ`, `WRITE`, `READ_WRITE`, `UNSPECIFIED`
- [ ] [STORY-05.4.2] Define `Access(DependencyRelationship)` as a concrete class with `access_mode: AccessMode = AccessMode.UNSPECIFIED`
- [ ] [STORY-05.4.3] Implement validation: Access is directed from behavior or active structure element (accessor) to passive structure element (accessed); reversed direction raises `ValidationError`
- [ ] [STORY-05.4.4] Write test: `Access(source=PassiveStructureElement, target=BehaviorElement)` raises `ValidationError`
- [ ] [STORY-05.4.5] Write test: `Access` instance accepts all four `AccessMode` enum values

### [FEAT-05.5] Dependency Relationships -- Influence
- [ ] [STORY-05.5.1] Define `InfluenceSign` enum with members: `STRONG_POSITIVE` ("++"), `POSITIVE` ("+"), `NEUTRAL` ("0"), `NEGATIVE` ("-"), `STRONG_NEGATIVE` ("--")
- [ ] [STORY-05.5.2] Define `Influence(DependencyRelationship)` as a concrete class with `sign: InfluenceSign | None = None` and `strength: str | None = None`
- [ ] [STORY-05.5.3] Write test: `Influence` instance `sign` and `strength` both default to `None`

### [FEAT-05.6] Dependency Relationships -- Association
- [ ] [STORY-05.6.1] Define `AssociationDirection` enum with members: `UNDIRECTED`, `DIRECTED`
- [ ] [STORY-05.6.2] Define `Association(DependencyRelationship)` as a concrete class with `direction: AssociationDirection = AssociationDirection.UNDIRECTED`
- [ ] [STORY-05.6.3] Implement validation: undirected Association is always permitted between any two concepts (elements and/or relationships)
- [ ] [STORY-05.6.4] Write test: `Association(source=any_element, target=some_relationship)` is valid without restriction
- [ ] [STORY-05.6.5] Write test: directed Association is valid between any two element types

### [FEAT-05.7] Dynamic Relationships
- [ ] [STORY-05.7.1] Define `DynamicRelationship(Relationship)` as an ABC with `category = RelationshipCategory.DYNAMIC`
- [ ] [STORY-05.7.2] Define `Triggering(DynamicRelationship)` as a concrete class
- [ ] [STORY-05.7.3] Define `Flow(DynamicRelationship)` as a concrete class with `flow_type: str | None = None`
- [ ] [STORY-05.7.4] Implement validation: setting `is_nested = True` on `Triggering` or `Flow` raises `ValidationError`
- [ ] [STORY-05.7.5] Write test: `Triggering` and `Flow` have `category == RelationshipCategory.DYNAMIC`
- [ ] [STORY-05.7.6] Write test: `Flow` has `flow_type` attribute defaulting to `None`
- [ ] [STORY-05.7.7] Write test: `is_nested = True` on `Triggering` raises `ValidationError`

### [FEAT-05.8] Other Relationships -- Specialization
- [ ] [STORY-05.8.1] Define `OtherRelationship(Relationship)` as an ABC with `category = RelationshipCategory.OTHER`
- [ ] [STORY-05.8.2] Define `Specialization(OtherRelationship)` as a concrete class
- [ ] [STORY-05.8.3] Implement validation: Specialization is only permitted between elements of the same concrete type; different types raise `ValidationError`
- [ ] [STORY-05.8.4] Write test: `Specialization(source=BusinessProcess, target=BusinessProcess)` is valid
- [ ] [STORY-05.8.5] Write test: `Specialization(source=BusinessProcess, target=ApplicationFunction)` raises `ValidationError`
- [ ] [STORY-05.8.6] Write test: `Specialization` has `category == RelationshipCategory.OTHER`

### [FEAT-05.9] Junction (Relationship Connector)
- [ ] [STORY-05.9.1] Define `JunctionType` enum in `src/pyarchi/enums.py` with members: `AND`, `OR`
- [ ] [STORY-05.9.2] Define `Junction(RelationshipConnector)` as a concrete class with mandatory `junction_type: JunctionType` field
- [ ] [STORY-05.9.3] Implement validation: all relationships connected to a Junction must be of the same concrete relationship type; mixed types raise `ValidationError`
- [ ] [STORY-05.9.4] Implement validation: endpoint elements of a chain through a Junction must permit a direct relationship of the connected type (per Appendix B); otherwise raise `ValidationError`
- [ ] [STORY-05.9.5] Support multiple incoming/one outgoing, one incoming/multiple outgoing, and multiple/multiple connection topologies
- [ ] [STORY-05.9.6] Write test: `Junction` cannot be instantiated without providing `junction_type`
- [ ] [STORY-05.9.7] Write test: connecting `Composition` and `Serving` to the same `Junction` raises `ValidationError`
- [ ] [STORY-05.9.8] Write test: `isinstance(Junction(junction_type=JunctionType.AND), RelationshipConnector)` is `True`
- [ ] [STORY-05.9.9] Write test: `isinstance(Junction(junction_type=JunctionType.AND), Relationship)` is `False`
- [ ] [STORY-05.9.10] Write test: Junction connecting two `Serving` relationships where endpoint elements do not permit direct `Serving` raises `ValidationError`

### [FEAT-05.10] Derivation Engine
- [ ] [STORY-05.10.1] Define `DerivationEngine` class in `src/pyarchi/derivation/engine.py`
- [ ] [STORY-05.10.2] Implement `derive(self, model: Model) -> list[Relationship]` method that computes all derivable relationships from chains in the model
- [ ] [STORY-05.10.3] Implement `is_directly_permitted(self, rel_type: type[Relationship], source: Element, target: Element) -> bool` method that checks the Appendix B permission table
- [ ] [STORY-05.10.4] Implement chain traversal rules: structural relationships propagate through structural chains, dependency through dependency chains
- [ ] [STORY-05.10.5] Mark all derived relationships with `is_derived = True`
- [ ] [STORY-05.10.6] Ensure `derive()` does not modify the source `Model` in-place; it returns new `Relationship` objects
- [ ] [STORY-05.10.7] Implement derivation direction constraint: valid only from more detail to less detail (abstraction direction)
- [ ] [STORY-05.10.8] Write test: three-hop realization chain produces one derived `Realization` between endpoints
- [ ] [STORY-05.10.9] Write test: derived relationships have `is_derived == True`
- [ ] [STORY-05.10.10] Write test: `derive()` returns new objects and source model remains unmodified
- [ ] [STORY-05.10.11] Write test: `is_directly_permitted(Serving, ApplicationService, BusinessProcess)` returns `True`

### [FEAT-05.11] Appendix B Permission Table
- [ ] [STORY-05.11.1] Encode the normative Appendix B relationship permission table as a data structure in `src/pyarchi/validation/permissions.py`
- [ ] [STORY-05.11.2] Implement lookup function: given a relationship type, source element type, and target element type, return whether the relationship is permitted
- [ ] [STORY-05.11.3] Include universal same-type permissions for Composition, Aggregation, and Specialization
- [ ] [STORY-05.11.4] Include universal Association permission between any two concepts
- [ ] [STORY-05.11.5] Write tests verifying representative permitted and forbidden relationship/source/target triplets from the table
