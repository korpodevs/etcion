# ADR-002: Module Layout

## Status

ACCEPTED

## Date

2026-03-23

## Context

ADR-001 established the build system, package root (`src/pyarchi/`), and toolchain for the project. With that foundation in place, the next decision is the internal module structure of the package. This decision must be made now -- before any metamodel code is written -- because the module layout determines the import paths that every subsequent epic will depend on. Changing import paths after code exists means rewriting imports across the entire codebase and invalidating any downstream code that has already adopted the library.

The ArchiMate 3.2 specification defines a substantial type hierarchy: approximately 80 concrete element types spread across 7 layers and 5 aspects, 11 concrete relationship types organized into 4 categories, a relationship connector type (Junction), and a rich set of abstract base classes and mixins that structure the inheritance tree. Beyond the metamodel types themselves, the library requires a validation subsystem (encoding the normative Appendix B permission table and enforcing metamodel constraints), a derivation engine (computing derived relationships from chains), and a set of shared enumerations and exception types.

A naive flat layout -- placing all of these modules directly under `src/pyarchi/` -- would produce 100+ files in a single directory, making navigation impractical for both humans and tooling. Conversely, over-segmenting the package by ArchiMate layer (e.g., `src/pyarchi/business/`, `src/pyarchi/application/`) would create circular import problems because ArchiMate relationships routinely cross layer boundaries.

The layout must also satisfy two tooling constraints established in ADR-001:

1. **mypy strict mode** requires that each sub-package has well-defined module boundaries so that type-checking can operate on discrete units. Circular imports between sub-packages will cause mypy resolution failures.
2. **`src/pyarchi/__init__.py` is the sole public API surface.** Internal sub-packages are implementation details; they must support clean re-exports through the top-level `__init__.py` without forcing consumers to know the internal structure.

## Decision

### STORY-00.2.1 -- `src/pyarchi/metamodel/` Sub-package

All metamodel classes -- the abstract base classes, mixins, concrete element types, concrete relationship types, and the Model container -- will live under `src/pyarchi/metamodel/`.

The initial internal structure of this sub-package is:

```
src/pyarchi/metamodel/
    __init__.py       # Re-exports key types for internal convenience
    concepts.py       # Concept (root ABC), Element (ABC), Relationship (ABC), RelationshipConnector (ABC)
    mixins.py         # AttributeMixin (name, description, documentation_url)
    model.py          # Model container class
    notation.py       # NotationMetadata dataclass
```

As EPIC-004 (Abstract Element Hierarchy) and EPIC-005 (Relationships) are implemented, two additional sub-packages will be created:

```
src/pyarchi/metamodel/elements/
    __init__.py               # Re-exports all concrete element classes
    structure.py              # StructureElement, ActiveStructureElement, PassiveStructureElement, etc.
    behavior.py               # BehaviorElement, Process, Function, Interaction, Event, etc.
    motivation.py             # MotivationElement (ABC)
    composite.py              # CompositeElement (ABC), Grouping, Location

src/pyarchi/metamodel/relationships/
    __init__.py               # Re-exports all concrete relationship classes
    structural.py             # StructuralRelationship, Composition, Aggregation, Assignment, Realization
    dependency.py             # DependencyRelationship, Serving, Access, Influence, Association
    dynamic.py                # DynamicRelationship, Triggering, Flow
    other.py                  # OtherRelationship, Specialization
    connector.py              # Junction
```

At this stage (FEAT-00.2), `elements/` and `relationships/` are declared as planned sub-packages but are **not created yet**. They will be created when their respective epics begin. The decision to use sub-packages rather than flat modules is made now because:

- The element hierarchy alone will contain 50+ classes; a single `elements.py` file would exceed 2000 lines and violate the principle of one concern per module.
- Sub-packages allow each category (structure, behavior, motivation, composite) to be worked on independently without merge conflicts.
- The `__init__.py` in each sub-package provides a clean aggregation point for re-exports.

The `metamodel/__init__.py` will re-export the types that downstream sub-packages (validation, derivation) need, so that internal imports read as `from pyarchi.metamodel import Element, Relationship` rather than reaching into specific files.

### STORY-00.2.2 -- `src/pyarchi/enums.py`

All enumeration types will live in a single flat module at `src/pyarchi/enums.py`. The enums defined here are:

| Enum | Members | Consuming Epic |
|---|---|---|
| `Layer` | `STRATEGY`, `MOTIVATION`, `BUSINESS`, `APPLICATION`, `TECHNOLOGY`, `PHYSICAL`, `IMPLEMENTATION_MIGRATION` | EPIC-003 |
| `Aspect` | `ACTIVE_STRUCTURE`, `BEHAVIOR`, `PASSIVE_STRUCTURE`, `MOTIVATION`, `COMPOSITE` | EPIC-003 |
| `RelationshipCategory` | `STRUCTURAL`, `DEPENDENCY`, `DYNAMIC`, `OTHER` | EPIC-005 |
| `AccessMode` | `READ`, `WRITE`, `READ_WRITE`, `UNSPECIFIED` | EPIC-005 |
| `InfluenceSign` | `STRONG_POSITIVE`, `POSITIVE`, `NEUTRAL`, `NEGATIVE`, `STRONG_NEGATIVE` | EPIC-005 |
| `AssociationDirection` | `UNDIRECTED`, `DIRECTED` | EPIC-005 |
| `JunctionType` | `AND`, `OR` | EPIC-005 |

A single flat file is chosen over an `enums/` sub-package because:

- Enums are small, self-contained definitions with no business logic. All seven enums together will total fewer than 100 lines.
- Enums are imported by nearly every other module in the library (metamodel, validation, derivation). A single import path (`from pyarchi.enums import Layer, Aspect`) is simpler and more discoverable than scattering enums across multiple files.
- Distributing enums near their consumers (e.g., `Layer` inside `metamodel/`, `AccessMode` inside `metamodel/relationships/`) would create import direction ambiguity: validation and derivation would need to import from deep inside metamodel just to get an enum value. Centralizing enums at the package root keeps them at the bottom of the dependency graph.

### STORY-00.2.3 -- `src/pyarchi/validation/` Sub-package

Validation logic will live in a dedicated sub-package at `src/pyarchi/validation/`. This sub-package is responsible for:

- **`permissions.py`**: The encoded Appendix B relationship permission table and the lookup function `is_permitted(rel_type, source_type, target_type) -> bool`.
- **`rules.py`** (future): Validation rule functions that enforce metamodel constraints beyond the permission table (e.g., Interaction requires >= 2 active structure elements, Specialization must be between same-type elements).
- **`__init__.py`**: Re-exports the public validation API.

Validation is separated from the metamodel classes for three reasons:

1. **Single Responsibility**: Metamodel classes define *what* ArchiMate types are. Validation logic defines *what combinations are legal*. These are distinct concerns that change for different reasons.
2. **Circular Import Prevention**: If validation logic lived inside metamodel classes (e.g., as `model_validator` methods on `Relationship`), and those validators needed to consult the permission table, the permission table would need to import all element types to build its lookup structure, creating a circular dependency. Separating validation into its own package enforces a clean one-way dependency: `validation` imports `metamodel`, never the reverse.
3. **Testability**: The permission table and validation rules can be unit-tested in isolation with mock or minimal element instances, without constructing full model graphs.

Exception types referenced by validation (e.g., `ValidationError`) are defined in `src/pyarchi/exceptions.py` (see STORY-00.2.5), not inside the validation sub-package. The validation sub-package imports from `exceptions`, not the other way around.

### STORY-00.2.4 -- `src/pyarchi/derivation/` Sub-package

The derivation engine will live in a dedicated sub-package at `src/pyarchi/derivation/`. This sub-package is responsible for:

- **`engine.py`**: The `DerivationEngine` class, which computes derived relationships by traversing relationship chains in a `Model` and applying the derivation rules from the ArchiMate specification.
- **`__init__.py`**: Re-exports `DerivationEngine`.

The derivation engine is isolated for two reasons:

1. **Highest dependency level**: The derivation engine is the most complex consumer in the library. It imports from `metamodel` (to traverse elements and relationships), `validation` (to check whether a derived relationship is permitted), and `enums` (to inspect relationship categories). No other sub-package should import from derivation; it is a leaf in the dependency graph.
2. **Optional execution**: Derivation is an expensive computation that users may not invoke on every model load. Isolating it means its module is not imported until explicitly needed, keeping baseline import time low for the common case of simply constructing or reading a model.

### STORY-00.2.5 -- `src/pyarchi/exceptions.py`

All custom exception types will live in a single flat module at `src/pyarchi/exceptions.py`. The initial exception classes are:

- **`PyArchiError(Exception)`**: Base exception class for all library errors. Allows consumers to catch all pyarchi errors with a single `except PyArchiError`.
- **`ValidationError(PyArchiError)`**: Raised when a metamodel constraint is violated (invalid relationship source/target, missing required fields, illegal `is_nested` flag, etc.). This is a pyarchi-specific type, distinct from `pydantic.ValidationError`, to give the library control over error formatting and to avoid coupling consumer error handling to Pydantic internals.
- **`DerivationError(PyArchiError)`**: Raised when the derivation engine encounters an invalid state (e.g., a cycle that prevents termination).
- **`ConformanceError(PyArchiError)`**: Raised when a model fails a conformance check against the ArchiMate 3.2 specification.

Exceptions are placed in a dedicated module rather than co-located with the code that raises them because:

- Exception types sit at the **bottom** of the dependency graph. Every sub-package may need to raise or catch them. If `ValidationError` lived inside `validation/`, then `metamodel` could not import it without creating an upward dependency. A root-level `exceptions.py` has no internal imports and can be imported by any sub-package without risk.
- Consumers who want to catch library exceptions need a single, predictable import path: `from pyarchi.exceptions import ValidationError`.

### STORY-00.2.6 -- `CLAUDE.md` Update

This story is **superseded**. `CLAUDE.md` was already updated with build, test, and lint commands as part of the FEAT-00.1 implementation (ADR-001). No further changes are required for FEAT-00.2. This story should be marked as complete with a note referencing ADR-001.

## Dependency Graph

The following diagram shows the allowed import directions between the sub-packages. The strict rule is: **a module may only import from modules below it in this graph.** Violations will cause circular import errors at runtime.

```
src/pyarchi/
    __init__.py          (public API surface; imports from all sub-packages)

    exceptions.py        (no internal imports)
         ^
         |
    enums.py             (no internal imports)
         ^
         |
    metamodel/           (imports: enums, exceptions)
         ^
         |
    validation/          (imports: metamodel, enums, exceptions)
         ^
         |
    derivation/          (imports: metamodel, validation, enums, exceptions)
```

Note that `enums.py` and `exceptions.py` are at the same level -- neither imports from the other. Both are leaf dependencies. The `conformance.py` module (EPIC-001, future) will sit at the same level as `validation/`, importing from `metamodel` and `enums`.

## Alternatives Considered

### Flat Layout -- Everything Directly in `src/pyarchi/`

Placing all modules directly under the package root was considered for its simplicity. This approach was rejected because the ArchiMate 3.2 metamodel produces approximately 80 concrete element types, 11 concrete relationship types, 7 enum types, a permission table, validation rules, a derivation engine, and supporting abstract classes and mixins. This totals well over 100 modules in a single directory, making file navigation impractical, IDE file trees unusable, and `__init__.py` re-exports unmanageable.

### Domain-Driven Sub-packages by ArchiMate Layer

An alternative layout organized by ArchiMate layer was considered:

```
src/pyarchi/strategy/
src/pyarchi/business/
src/pyarchi/application/
src/pyarchi/technology/
src/pyarchi/physical/
src/pyarchi/motivation/
src/pyarchi/implementation_migration/
```

This was rejected because ArchiMate's cross-layer relationships are a core feature of the language. A `Serving` relationship can connect an `ApplicationService` (Application layer) to a `BusinessProcess` (Business layer). A `Realization` can connect a `TechnologyService` to an `ApplicationComponent`. The permission table in Appendix B is defined across all layers simultaneously. Organizing by layer would force relationship types and validation logic to import from multiple layer packages, creating unavoidable circular dependencies. The metamodel's natural grouping is by *kind* (elements, relationships, validation), not by *layer*.

### Separate Top-Level Packages

Splitting the library into separate installable packages (`pyarchi-metamodel`, `pyarchi-validation`, `pyarchi-derivation`) was considered for maximum decoupling. This was rejected as premature. The library is in its first phase with zero consumers. Separate packages would introduce cross-package version management, separate release cycles, and integration testing overhead with no offsetting benefit. The internal sub-package structure achieves the same separation of concerns without the operational cost. If a future need arises (e.g., a consumer wants the metamodel without the derivation engine), the sub-package boundaries established here make a future split straightforward.

### Enums Distributed Near Consumers

An alternative placed each enum adjacent to the types that use it: `Layer` and `Aspect` inside `metamodel/`, `RelationshipCategory` inside `metamodel/relationships/`, `AccessMode` inside the `Access` relationship module. This was rejected because enums are consumed by multiple sub-packages at different levels of the dependency graph. `Layer` is needed by metamodel classes, validation rules, and the derivation engine. Placing it inside `metamodel/` would force validation and derivation to import from within `metamodel` for a simple enum value, blurring the dependency boundaries. A centralized `enums.py` at the package root keeps enums at the bottom of the dependency graph where any module can import them without architectural compromise.

## Consequences

### Positive

- **Clear separation of concerns**: Metamodel types, validation logic, derivation computation, enums, and exceptions are independently importable sub-packages with well-defined responsibilities.
- **Circular import risk is eliminated by design**: The strict one-way dependency graph (exceptions/enums -> metamodel -> validation -> derivation) makes circular imports structurally impossible as long as contributors follow the layering discipline.
- **Incremental implementation**: The `metamodel/elements/` and `metamodel/relationships/` sub-packages are declared as planned structure but not created until their respective epics begin. This avoids premature empty directories while documenting the intended layout for all contributors.
- **mypy can type-check each sub-package independently**: The clean module boundaries mean mypy can resolve types within each sub-package without needing to load the entire library graph, improving type-checking speed on large codebases.
- **Scalable for Phase 2+**: New element types (layer-specific concrete classes) can be added as new files under `metamodel/elements/` without touching `validation/`, `derivation/`, or the top-level `__init__.py` re-exports (beyond adding the new type to the public API).
- **Single import path for consumers**: All public types are re-exported through `src/pyarchi/__init__.py`. Consumers write `from pyarchi import BusinessActor, Serving, ValidationError` without needing to know the internal package structure.

### Negative

- **Import direction discipline must be manually enforced**: The layered dependency graph is a convention, not a mechanism. Python does not prevent a module in `metamodel/` from importing `validation/`. Violations will cause circular import errors at runtime, but mypy will not catch all cases at development time. A future CI check (e.g., an import linter or `importlib` cycle detector) may be needed if the team grows.
- **`__init__.py` maintenance burden**: Each sub-package's `__init__.py` must be updated whenever a new public type is added. As the library grows to 80+ concrete types, the re-export lists in `metamodel/__init__.py`, `metamodel/elements/__init__.py`, and `metamodel/relationships/__init__.py` will become long. This is an acceptable trade-off for clean import paths.
- **Indirection cost for contributors**: A new contributor looking for the `Composition` class must navigate from `src/pyarchi/` to `metamodel/` to `relationships/` to `structural.py`. This three-level nesting is deeper than a flat layout, but is mitigated by IDE "go to definition" and the predictable naming convention.

## Compliance

This ADR provides the architectural rationale for each story in FEAT-00.2:

| Story | Decision Implemented |
|---|---|
| STORY-00.2.1 | `src/pyarchi/metamodel/` sub-package with `concepts.py`, `mixins.py`, `model.py`, `notation.py`, and planned `elements/` and `relationships/` sub-packages |
| STORY-00.2.2 | `src/pyarchi/enums.py` as a single flat module containing `Layer`, `Aspect`, `RelationshipCategory`, `AccessMode`, `InfluenceSign`, `AssociationDirection`, `JunctionType` |
| STORY-00.2.3 | `src/pyarchi/validation/` sub-package with `permissions.py` and `rules.py`; imports metamodel, never imported by metamodel |
| STORY-00.2.4 | `src/pyarchi/derivation/` sub-package with `engine.py`; leaf node in the dependency graph |
| STORY-00.2.5 | `src/pyarchi/exceptions.py` at the package root defining `PyArchiError`, `ValidationError`, `DerivationError`, `ConformanceError` |
| STORY-00.2.6 | Superseded by FEAT-00.1 / ADR-001; no action required |
