# ADR-003: ConformanceProfile

## Status

ACCEPTED

## Date

2026-03-23

## Context

With the build system (ADR-001) and module layout (ADR-002) established, the library has a package skeleton but no metamodel code. Before implementing any concrete ArchiMate types (EPIC-002+), the library needs a machine-readable declaration of what it commits to implementing and at what compliance level. This is the purpose of the `ConformanceProfile`.

The ArchiMate 3.2 specification defines three compliance levels for conformant implementations:

- **shall** -- mandatory features that a conformant tool/model must support.
- **should** -- recommended features that are not required for conformance.
- **may** -- optional features that a conformant implementation may or may not provide.

The mandatory (`shall`) features include: the language structure (layers, aspects), the generic metamodel (Concept, Element, Relationship, RelationshipConnector ABCs), all layer-specific element types (Strategy, Motivation, Business, Application, Technology, Physical, Implementation & Migration), cross-layer dependency relationships, all 11 concrete relationship types, the Junction relationship connector, the Appendix B relationship permission table, and iconography metadata (visual notation rules). The `should`-level features include the viewpoint mechanism and language customization (profiles, extensions). The `may`-level features include Appendix C example viewpoints.

A `ConformanceProfile` is needed now -- before the metamodel types exist -- for three reasons:

1. **Contract declaration**: It establishes the set of features the library commits to implementing. Downstream consumers (and the library's own test suite) can query `CONFORMANCE.business_elements` to determine whether Business layer types are in scope. This makes the library's roadmap programmatically inspectable rather than buried in prose documentation.
2. **Machine-readable spec version**: The profile carries `spec_version = "3.2"`, making the targeted specification version available to tooling, serialization logic, and compatibility checks.
3. **Test-driven development anchor**: FEAT-01.2 (Conformance Test Suite) will write assertions against this profile. The profile must exist before the tests can be written.

The module placement question is critical. `conformance.py` should NOT live inside `metamodel/` because it describes the library's contract, not the ArchiMate type hierarchy. It should NOT live inside `validation/` because it is not a runtime validation mechanism for user-constructed models. It belongs at the `src/pyarchi/` package root, at the same dependency level as `enums.py` and `exceptions.py`. Its only internal import is `SPEC_VERSION` from `pyarchi.__init__` (or it could define its own default; see Decision below) and optionally `Layer` from `pyarchi.enums` for documentation cross-referencing.

There is a design tension between making conformance queryable at runtime versus simply documenting it in prose. A prose-only approach (README, specification document) cannot be tested programmatically and drifts out of sync with the code. A runtime-queryable `ConformanceProfile` dataclass can be asserted against in CI, ensuring the declaration stays honest as implementation progresses.

## Decision

### Module Location

Create `src/pyarchi/conformance.py` at the package root. It imports from `pyarchi` (for `SPEC_VERSION`) only. No imports from `metamodel/`, `validation/`, or `derivation/`. This places it at the bottom of the dependency graph alongside `enums.py` and `exceptions.py`, importable by any sub-package without circular import risk.

```
src/pyarchi/
    exceptions.py        (no internal imports)
    enums.py             (no internal imports)
    conformance.py       (imports: SPEC_VERSION from __init__)
         ^
    metamodel/           (imports: enums, exceptions)
         ^
    validation/          (imports: metamodel, enums, exceptions)
         ^
    derivation/          (imports: metamodel, validation, enums, exceptions)
```

Note: To avoid a circular import (`__init__.py` imports from `conformance.py`, and `conformance.py` imports `SPEC_VERSION` from `__init__.py`), the `conformance.py` module will define `SPEC_VERSION` as a string literal default on the dataclass field: `spec_version: str = "3.2"`. The `__init__.py` module already defines `SPEC_VERSION = "3.2"` independently. Both values are the same constant. If a future need arises to unify them, `conformance.py` can import from a shared `_constants.py` module.

### Implementation: `dataclass` with `frozen=True`

`ConformanceProfile` is implemented as a `@dataclass(frozen=True)`, not a Pydantic `BaseModel`. Rationale:

- This is configuration metadata, not a user-constructed domain object. It does not need runtime validation, JSON serialization, field aliases, or discriminated unions.
- A frozen dataclass is immutable, preventing accidental mutation of the library's conformance declaration.
- It has zero dependencies beyond the standard library, keeping the import cost negligible.
- Pydantic `BaseModel` would add unnecessary weight for a class that is instantiated exactly once and never deserialized from external input.

### Attribute Definitions

The `ConformanceProfile` dataclass defines the following fields. Each field is a `bool` except `spec_version`. Fields are grouped by compliance level.

**Spec version:**

| Field | Type | Default | Description |
|---|---|---|---|
| `spec_version` | `str` | `"3.2"` | The ArchiMate specification version this profile targets. |

**`shall`-level features (mandatory for conformance):**

All default to `True`, representing the library's declared intent to implement these features by the end of Phase 1. They are `True` from day one because the profile represents the library's commitment, not a runtime capability check of whether the implementing code currently exists. The test suite (FEAT-01.2) is responsible for verifying that the commitment is fulfilled.

| Field | Type | Default | Description |
|---|---|---|---|
| `language_structure` | `bool` | `True` | Full classification framework: layers (7), aspects (5). |
| `generic_metamodel` | `bool` | `True` | Abstract element hierarchy: Concept, Element, Relationship, RelationshipConnector ABCs. |
| `strategy_elements` | `bool` | `True` | Strategy layer element types (Resource, Capability, ValueStream, CourseOfAction). |
| `motivation_elements` | `bool` | `True` | Motivation layer element types (Stakeholder, Driver, Assessment, Goal, Outcome, Principle, Requirement, Constraint, Meaning, Value). |
| `business_elements` | `bool` | `True` | Business layer element types (BusinessActor, BusinessRole, BusinessCollaboration, BusinessInterface, BusinessProcess, BusinessFunction, BusinessInteraction, BusinessEvent, BusinessService, BusinessObject, Contract, Representation, Product). |
| `application_elements` | `bool` | `True` | Application layer element types (ApplicationComponent, ApplicationCollaboration, ApplicationInterface, ApplicationFunction, ApplicationInteraction, ApplicationProcess, ApplicationEvent, ApplicationService, DataObject). |
| `technology_elements` | `bool` | `True` | Technology layer element types (Node, Device, SystemSoftware, TechnologyCollaboration, TechnologyInterface, Path, CommunicationNetwork, TechnologyFunction, TechnologyProcess, TechnologyInteraction, TechnologyEvent, TechnologyService, Artifact). |
| `physical_elements` | `bool` | `True` | Physical layer element types (Equipment, Facility, DistributionNetwork, Material). |
| `implementation_migration_elements` | `bool` | `True` | Implementation & Migration layer element types (WorkPackage, Deliverable, ImplementationEvent, Plateau, Gap). |
| `cross_layer_relationships` | `bool` | `True` | Support for relationships that cross layer boundaries. |
| `relationship_permission_table` | `bool` | `True` | Full Appendix B permission matrix encoding. |
| `iconography_metadata` | `bool` | `True` | Notation metadata: corner shapes, default colors, badge letters per element type. |

**`should`-level features (recommended, not mandatory):**

Default to `True` because the library plans to support them in Phase 2.

| Field | Type | Default | Description |
|---|---|---|---|
| `viewpoint_mechanism` | `bool` | `True` | Defining and applying viewpoints to filter model views. |
| `language_customization` | `bool` | `True` | Profile and extension mechanisms for customizing the language. |

**`may`-level features (optional):**

Default to `False` because Appendix C example viewpoints are explicitly out of scope.

| Field | Type | Default | Description |
|---|---|---|---|
| `example_viewpoints` | `bool` | `False` | Appendix C example viewpoints (Basic, Organization, etc.). |

### The `CONFORMANCE` Singleton

A module-level constant is exported from `conformance.py`:

```python
CONFORMANCE: ConformanceProfile = ConformanceProfile()
```

This is the single instance that consumers and the test suite inspect. Because the dataclass is frozen and all fields have defaults, the default-constructed instance represents the library's full conformance declaration. Consumers query it as `pyarchi.CONFORMANCE.business_elements`.

### `__init__.py` Re-export

Both `ConformanceProfile` and `CONFORMANCE` are re-exported from `src/pyarchi/__init__.py` and added to `__all__`. This gives consumers the import path `from pyarchi import CONFORMANCE, ConformanceProfile`.

## Alternatives Considered

### Pydantic BaseModel Instead of Dataclass

Using a Pydantic `BaseModel` for `ConformanceProfile` was considered for consistency with the metamodel types (which will use Pydantic per ADR-001). This was rejected because `ConformanceProfile` has fundamentally different characteristics: it is instantiated exactly once, never deserialized from external input, never validated against user data, and never serialized to JSON/XML. A Pydantic model would add import cost (Pydantic's module initialization is non-trivial) and conceptual weight for zero benefit. The dataclass is the minimal correct tool.

### Runtime Capability Check Instead of Declared Intent

An alternative design would have each `shall`-level field default to `False` and flip to `True` only when the implementing code is actually importable (e.g., `business_elements` becomes `True` only when `pyarchi.BusinessActor` exists). This was rejected for two reasons:

1. It conflates "what the library commits to" with "what is implemented so far," making the profile useless for planning and roadmap communication.
2. It would require import-time introspection logic (try/except around imports) inside a module that should be dependency-free.

The correct separation is: `ConformanceProfile` declares intent; `test/test_conformance.py` (FEAT-01.2) verifies fulfillment.

### Conformance Inside `metamodel/__init__.py`

Placing the profile inside the `metamodel` sub-package was considered since conformance describes the metamodel's scope. This was rejected because `conformance.py` has no dependency on any metamodel type -- it is pure metadata. Placing it inside `metamodel/` would violate the principle that a module should live at the lowest level of the dependency graph that its imports require. It would also create the false impression that conformance is an internal metamodel concern rather than a library-level contract.

### Enum-Based Compliance Levels

An alternative used a `ComplianceLevel` enum (`SHALL`, `SHOULD`, `MAY`) and a dictionary mapping feature names to levels, instead of individual `bool` fields. This was rejected because:

- It loses IDE auto-completion: `CONFORMANCE["business_elements"]` has no type hint on the value.
- It makes the test suite harder to write: assertions against dictionary keys are less readable than assertions against named attributes.
- The compliance level of each feature is fixed by the spec and does not change at runtime. Encoding it as field documentation (docstrings, comments) is sufficient; it does not need to be a queryable runtime value.

## Consequences

### Positive

- **Machine-readable contract**: The library's conformance commitment is inspectable at runtime via `pyarchi.CONFORMANCE`, not buried in documentation that drifts from reality.
- **Self-documenting**: The dataclass fields, their names, types, defaults, and docstrings serve as a structured summary of the ArchiMate 3.2 specification's conformance requirements.
- **Testable**: FEAT-01.2 can write direct assertions against `CONFORMANCE` attribute values. The `TestConformanceProfile` test class will pass as soon as `conformance.py` is implemented, providing immediate green tests.
- **Zero-cost at runtime**: A frozen dataclass with no imports beyond the standard library adds negligible overhead to library initialization.
- **IDE-friendly**: Named `bool` fields provide full auto-completion and inline documentation in VS Code, PyCharm, and other editors. `CONFORMANCE.` triggers a completion list of all conformance attributes.

### Negative

- **`True` fields may misrepresent incomplete implementation**: Until EPIC-002 through EPIC-005 are complete, `CONFORMANCE.business_elements = True` is a promise, not a fact. A consumer inspecting the profile could incorrectly conclude that Business layer types are already available. This risk is mitigated by the conformance test suite (FEAT-01.2), which will fail in CI until the implementing code exists, making the gap between declaration and reality visible.
- **Dual `SPEC_VERSION` definition**: Both `__init__.py` and `conformance.py` define the string `"3.2"` independently to avoid circular imports. If the spec version changes, both locations must be updated. This is a minor maintenance cost, mitigated by the fact that specification version changes are rare and will be caught by the test suite (which asserts `CONFORMANCE.spec_version == pyarchi.SPEC_VERSION`).
- **Static profile**: The profile cannot express partial implementation (e.g., "3 of 13 Business layer elements are implemented"). It is all-or-nothing per feature area. This is acceptable because the profile's purpose is to declare the library's target scope, not to report implementation progress. Build status is tracked in `BACKLOG.md` and CI test results.

## Compliance

This ADR provides the architectural rationale for each story in FEAT-01.1:

| Story | Decision Implemented |
|---|---|
| STORY-01.1.1 | `ConformanceProfile` as a `@dataclass(frozen=True)` in `src/pyarchi/conformance.py` |
| STORY-01.1.2 | All 16 attributes defined: `spec_version`, 12 `shall`-level booleans, 2 `should`-level booleans, 1 `may`-level boolean |
| STORY-01.1.3 | `spec_version` field defaults to `"3.2"`; `SPEC_VERSION` in `__init__.py` already exists; test suite will assert equality |
| STORY-01.1.4 | `example_viewpoints` field defaults to `False` with `may` designation; does not affect conformance checks |
