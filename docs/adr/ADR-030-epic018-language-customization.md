# ADR-030: EPIC-018 -- Language Customization Mechanism

## Status

PROPOSED

## Date

2026-03-25

## Context

The ArchiMate 3.2 specification (Section 14) defines a language customization mechanism that allows users to specialize existing element types and attach additional attributes. The `test_language_customization` conformance test (`test/test_conformance.py:219`) is currently `xfail`-ed, expecting `pyarchi.Profile` to exist in the public API. No profile or specialization types exist in the codebase today.

A Profile is *not* an ArchiMate Concept. Like Viewpoint (ADR-029), it is metamodel-level metadata that extends the language rather than describing an architecture. This distinction drives the central design question: how do specializations manifest at runtime?

Prior decisions accepted without re-litigation:

- `Concept` as root ABC; `Element` and `Relationship` as direct subtypes (ADR-006, ADR-007).
- `Model` as the top-level concept container with `add()`, `__getitem__`, and `validate()` (ADR-010).
- Pydantic `BaseModel` as the foundation for all domain types (ADR-006).
- Viewpoint as a non-Concept Pydantic model -- establishes the pattern for metamodel metadata (ADR-029).
- Exports deferred to dedicated epics (ADR-026 pattern; EPIC-020 for profile types).

Spec reference: `assets/archimate-spec-3.2/ch-language-customization.html` [ArchiMate 3.2 Section 14].

## Decisions

### 1. File Placement

| Artifact | Location |
|---|---|
| `Profile` | `src/pyarchi/metamodel/profiles.py` |

Profiles are metamodel infrastructure, not layer-specific elements. A single module is sufficient; the type is self-contained.

### 2. Profile Is a Pydantic BaseModel, Not a Concept

`Profile` inherits from `pydantic.BaseModel` directly, following the Viewpoint precedent (ADR-029). It does *not* subclass `Concept`, `Element`, or any ABC in the concept hierarchy. Rationale: a Profile describes how the language *may be extended*; it is not an architectural construct that lives inside a `Model`. It has no `id` field, no `_type_name` property, and is never passed to `Model.add()`.

### 3. Tag-Based Specialization (Not Dynamic Classes)

| Approach | Description | Verdict |
|---|---|---|
| Dynamic class creation via `type()` | Creates Python subclasses at runtime | **Rejected** -- opaque to static analysis, complicates serialization, pollutes class hierarchy |
| Tag-based | Elements carry an optional `specialization: str | None` field | **Accepted** |
| Factory pattern | `profile.create("Microservice", ...)` returns an element | **Rejected** -- indirection without benefit; the factory still needs to set a field or create a class |

Elements gain an optional `specialization: str | None = None` field on `Element`. When set, it indicates the element is a named specialization of its base type (e.g., an `ApplicationComponent` with `specialization="Microservice"`). This is serialization-friendly, transparent to existing validation logic, and requires no runtime class generation.

The field is added to `Element` in `concepts.py`, not to each concrete subclass, because specialization applies uniformly to all element types per the spec.

### 4. Profile Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | `str` | Yes | Non-empty; identifies the profile |
| `specializations` | `dict[type[Element], list[str]]` | No | Maps base element types to specialization names; defaults to `{}` |
| `attribute_extensions` | `dict[type[Element], dict[str, type]]` | No | Maps element types to additional attribute name/type pairs; defaults to `{}` |

`specializations` uses `type[Element]` keys (class references, not strings) to maintain the type-safe pattern established by `Viewpoint.permitted_concept_types` (ADR-029). The value is `list[str]` because a single base type may have multiple named specializations within one profile.

`attribute_extensions` maps element types to dictionaries of attribute names and their Python types. These are metadata declarations; they do not alter the Pydantic schema of existing classes at runtime. Extended attributes are stored in a separate runtime store on the model (Decision 6), not injected into class fields.

### 5. Profile Validation

Two validation rules enforced at `Profile` construction time via Pydantic validators:

1. **Valid base types.** Every key in `specializations` and `attribute_extensions` must be a concrete or abstract subclass of `Element`. Non-`Element` types (e.g., `Relationship`, `str`) raise `ValidationError`.
2. **No field conflicts.** Every attribute name in `attribute_extensions` must not collide with existing Pydantic model fields on the target `Element` type. Collision raises `ValidationError`. Checked via `element_type.model_fields`.

### 6. Model.apply_profile() Registers Metadata

`Model` gains an `apply_profile(profile: Profile)` method that:

1. Stores the profile in an internal `_profiles: list[Profile]` collection.
2. Registers the profile's specialization names in a lookup table `_specialization_registry: dict[str, type[Element]]` mapping specialization name to base element type. Duplicate specialization names across profiles raise `ValueError`.

This registry enables the model to validate that an element's `specialization` string corresponds to a declared profile entry and that the element's concrete type matches the expected base type. Validation is performed in `Model.validate()`, not eagerly on `add()`, to allow profile application order flexibility.

A convenience property `Model.profiles` exposes the registered profiles as a read-only list.

### 7. Extended Attribute Storage

Extended attributes declared via `attribute_extensions` are stored in a `dict[str, Any]` on the element instance, accessed through a dedicated field `extended_attributes: dict[str, Any] = Field(default_factory=dict)` on `Element`. Type checking of extended attribute values against the profile's declared types is performed during `Model.validate()`.

This avoids mutating Pydantic model schemas at runtime while still providing a structured place for custom data that survives serialization.

### 8. Exports Deferred to EPIC-020

Consistent with ADR-026 and ADR-029, `Profile` is not added to `pyarchi.__init__.__all__` in EPIC-018. The `test_language_customization` xfail will be resolved when EPIC-020 wires the exports.

## Alternatives Considered

### Dynamic Class Creation

Using `type("Microservice", (ApplicationComponent,), {})` to generate real Python subclasses at runtime. Rejected because:

1. Dynamically created classes are invisible to static type checkers and IDE autocompletion, undermining a core library design goal.
2. Serialization must map dynamic class names back to base ArchiMate types plus a specialization tag -- the tag is needed regardless, making the dynamic class redundant.
3. Dynamic classes accumulate in memory and pollute `__subclasses__()` results, complicating the permission validation engine (ADR-028) which introspects the class hierarchy.

### Profile as a Concept Subclass

Making `Profile` inherit from `Element` so it could be stored in a `Model` via `model.add()`. Rejected for the same reasons as Viewpoint (ADR-029): profiles are not part of the architecture being described, `Concept` requires `_type_name` and `id`, and `Model.elements` would need filter logic to exclude profiles.

### Storing Extended Attributes in a Separate Side Table on Model

Keeping elements unmodified and storing extended attributes in `Model._extended_attrs: dict[str, dict[str, Any]]` keyed by element ID. Rejected because:

1. Extended attributes would be lost if an element is accessed outside its model context.
2. Serialization would need to cross-reference two disconnected data structures.
3. The element instance would have no indication that it carries additional data, making debugging opaque.

## Consequences

### Positive

- The tag-based approach adds minimal complexity: one optional string field on `Element` and one optional dict field for extended attributes. No runtime class generation, no metaclass magic.
- Profile validation at construction time prevents invalid configurations early, consistent with Pydantic's fail-fast philosophy.
- The `_specialization_registry` on `Model` enables O(1) lookup of specialization names during validation and future serialization.
- The pattern mirrors Viewpoint (ADR-029): metamodel metadata as a plain Pydantic model, registered with `Model` but not stored in the concept pool.

### Negative

- Adding `specialization` and `extended_attributes` fields to `Element` increases the base class surface area for all elements, even those that never use profiles. The fields default to `None` and `{}` respectively, so memory overhead is minimal.
- Deferred validation of specialization consistency (in `Model.validate()` rather than `Model.add()`) means invalid specialization strings are not caught until validation is explicitly invoked. This is a deliberate trade-off for profile application order flexibility.
- Deferring exports to EPIC-020 means the `test_language_customization` xfail remains unresolved after EPIC-018 ships. Integration tests can import directly from `pyarchi.metamodel.profiles` in the interim.
