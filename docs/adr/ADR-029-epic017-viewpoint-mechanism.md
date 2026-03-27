# ADR-029: EPIC-017 -- Viewpoint Mechanism

## Status

PROPOSED

## Date

2026-03-25

## Context

The ArchiMate 3.2 specification (Section 13) defines a viewpoint mechanism that governs which concepts may appear in a given view. The `test_viewpoint_mechanism` conformance test (`test/test_conformance.py:212`) is currently `xfail`-ed, expecting `etcion.Viewpoint` to exist in the public API. No viewpoint, view, or concern types exist in the codebase today.

A Viewpoint is *not* an ArchiMate Concept (it is not an element, relationship, or connector). It is metamodel-level metadata that constrains model projections. This distinction drives the central design question: where does Viewpoint sit in the type hierarchy?

Prior decisions accepted without re-litigation:

- `Concept` as root ABC for all modelling constructs; `Element` and `Relationship` as direct subtypes (ADR-006, ADR-007).
- `Model` as the top-level concept container with `add()`, `__getitem__`, and `validate()` (ADR-010).
- Pydantic `BaseModel` as the foundation for all domain types (ADR-006).
- Exports deferred to a dedicated epic (ADR-026 pattern; EPIC-020 for viewpoint types).
- Enums centralized in `src/etcion/enums.py` at the bottom of the dependency graph (ADR-011).

Spec reference: `assets/archimate-spec-3.2/ch-viewpoints.html` [ArchiMate 3.2 Section 13].

## Decisions

### 1. File Placement

| Artifact | Location |
|---|---|
| `Viewpoint`, `View`, `Concern` | `src/etcion/metamodel/viewpoints.py` |
| `PurposeCategory`, `ContentCategory` | `src/etcion/enums.py` |

Viewpoints are metamodel infrastructure, not layer-specific elements. A single module avoids scattering three tightly coupled types across files.

### 2. Viewpoint Is a Pydantic BaseModel, Not a Concept

`Viewpoint` inherits from `pydantic.BaseModel` directly. It does *not* subclass `Concept`, `Element`, or any ABC in the concept hierarchy. Rationale: a Viewpoint is not an architectural construct that lives inside a `Model`; it is a constraint specification applied *to* a model. It has no `id` field, no `_type_name` property, and is never passed to `Model.add()`.

Pydantic is used (rather than a plain dataclass) for consistency with every other domain type in the library and to get field validation, immutability via `frozen=True`, and `frozenset` coercion for free.

### 3. Viewpoint Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | `str` | Yes | Non-empty; identifies the viewpoint |
| `purpose` | `PurposeCategory` | Yes | Spec Section 13.2 |
| `content` | `ContentCategory` | Yes | Spec Section 13.2 |
| `permitted_concept_types` | `frozenset[type[Concept]]` | Yes | Set of Concept subclasses allowed in views governed by this viewpoint |
| `representation_description` | `str \| None` | No | Free-text description of visual representation |
| `concerns` | `list[Concern]` | No | Defaults to `[]`; back-link populated by Concern (Decision 6) |

`permitted_concept_types` uses `frozenset` for hashability and to signal immutability after construction. The type parameter is `type[Concept]` (class references, not instances), consistent with how `is_permitted()` works with class-level type checks (ADR-028).

### 4. View as Model Projection, Not Container

A `View` holds *references* to `Concept` instances that already exist in an underlying `Model`. It is a projection (filter), not an independent container. Identity semantics: `view.concepts[i] is model[some_id]` is `True`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `governing_viewpoint` | `Viewpoint` | Yes | Cannot be `None` |
| `underlying_model` | `Model` | Yes | The model being projected |
| `concepts` | `list[Concept]` | No | Defaults to `[]`; populated via an `add()` method |

`View` is also a plain `pydantic.BaseModel` (not a `Concept`). It participates in no layer and has no `_type_name`.

Two validation rules enforced when adding a concept to a View:

1. **Type gate.** `type(concept)` must be a subclass of at least one type in `governing_viewpoint.permitted_concept_types`. Failure raises `etcion.exceptions.ValidationError`.
2. **Membership gate.** The concept must exist in `underlying_model` (identity check against the model's internal store). Failure raises `etcion.exceptions.ValidationError`.

Both checks run eagerly on `View.add()`, not deferred to a `validate()` pass. Views are small (tens to hundreds of concepts); eager validation is appropriate and provides immediate feedback.

### 5. Enums: PurposeCategory and ContentCategory

| Enum | Members | Spec Reference |
|---|---|---|
| `PurposeCategory` | `DESIGNING`, `DECIDING`, `INFORMING` | Section 13.2 |
| `ContentCategory` | `DETAILS`, `COHERENCE`, `OVERVIEW` | Section 13.2 |

Both are `str`-valued `Enum` subclasses following the existing pattern (`Layer`, `Aspect`, etc.) in `src/etcion/enums.py`.

### 6. Concern Links Stakeholders to Viewpoints

`Concern` is a lightweight associative type, not a Concept.

| Field | Type | Required | Notes |
|---|---|---|---|
| `description` | `str` | Yes | Non-empty |
| `stakeholders` | `list[Stakeholder]` | No | References to `Stakeholder` elements in a model |
| `viewpoints` | `list[Viewpoint]` | No | Viewpoints that address this concern |

Navigation path: `Stakeholder` -> `Concern` -> `Viewpoint` -> `View`. This chain is spec-defined (Section 13.1) but implemented as forward references on `Concern`, not as back-pointers injected into `Stakeholder`. Reverse navigation (stakeholder to its concerns) is the caller's responsibility via list comprehension over a concern collection.

### 7. Custom Viewpoints Are First-Class; No Predefined Instances

The library ships the *mechanism* (classes and enums), not a catalogue of predefined viewpoint instances. The spec defines standard viewpoints in Appendix C, but they are informative, not normative. Any user-constructed `Viewpoint` with a valid `permitted_concept_types` set is accepted.

A future utility module (outside EPIC-017 scope) may provide factory functions for the Appendix C viewpoints (e.g., `viewpoints.application_cooperation()`). EPIC-017 does not block or constrain that work.

### 8. Exports Deferred to EPIC-020

Consistent with ADR-026, `Viewpoint`, `View`, `Concern`, `PurposeCategory`, and `ContentCategory` are not added to `etcion.__init__.__all__` in EPIC-017. The `test_viewpoint_mechanism` xfail will be resolved when EPIC-020 wires the exports.

## Alternatives Considered

### Viewpoint as a Concept Subclass

Making `Viewpoint` inherit from `Element` (or directly from `Concept`) so it could be stored in a `Model` via `model.add()`. Rejected because:

1. Viewpoints are not part of the architecture being described; they are metadata about how to *present* that architecture. Mixing them into the concept pool conflates metamodel levels.
2. `Concept` requires `_type_name` and `id`; viewpoints have no spec-defined identity semantics or XML element type.
3. `Model.elements` and `Model.relationships` would need filter logic to exclude viewpoints, complicating the container.

### View as Independent Container (Deep Copy)

Copying concepts into the View so it becomes a self-contained snapshot. Rejected because:

1. Doubles memory for every concept included in a view.
2. Breaks identity: changes to a concept in the model would not be reflected in the view, violating the spec's intent that a view is a "window" into a model.
3. Synchronization between view copies and model originals adds complexity with no spec justification.

### Predefined Viewpoint Instances as Module Constants

Shipping `ORGANIZATION_VIEWPOINT = Viewpoint(name="Organization", ...)` etc. in `viewpoints.py`. Rejected for EPIC-017 because:

1. Appendix C defines 20+ standard viewpoints; encoding their `permitted_concept_types` sets requires importing every concrete element class, creating a heavyweight import dependency.
2. Standard viewpoints are informative, not normative. Baking them in risks disagreement with tool-specific interpretations.
3. The mechanism is independently testable and useful without the catalogue.

## Consequences

### Positive

- The viewpoint mechanism is cleanly separated from the concept hierarchy. `Viewpoint` and `View` cannot accidentally be added to a `Model` or confused with architectural elements.
- Eager validation on `View.add()` gives immediate feedback, consistent with Pydantic's fail-fast philosophy.
- `frozenset[type[Concept]]` for permitted types reuses the existing class-reference pattern from `is_permitted()`, keeping the type-checking idiom uniform across the library.
- Custom viewpoints are unrestricted, supporting domain-specific modelling without library changes.

### Negative

- `View.add()` must perform an identity check against the underlying model's internal `_concepts` dict. This couples `View` to `Model`'s storage implementation. If `Model` gains lazy loading or external backing stores, `View` membership checks must be updated.
- The `Concern.viewpoints` and `Viewpoint.concerns` bidirectional association requires care to avoid circular construction. The `concerns` field on `Viewpoint` defaults to `[]` and is populated after both objects exist.
- Deferring exports to EPIC-020 means the `test_viewpoint_mechanism` xfail remains unresolved after EPIC-017 ships. Integration tests within `test/` can import directly from `etcion.metamodel.viewpoints` in the interim.
