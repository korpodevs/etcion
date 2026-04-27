# ADR-050: extended_attributes lifted from Element to Concept

**Status:** ACCEPTED
**Date:** 2026-04-27
**Scope:** Pydantic surface of `etcion.metamodel.concepts.Concept` and ripple effects through Profile validation, `Model.validate()`, XML serialization, and provenance helpers.

## Context

Until v0.11.x, `extended_attributes: dict[str, Any]` lived on `Element` only. Relationships and Junctions -- both first-class `Concept` subclasses in the ArchiMate 3.2 metamodel and both legitimate carriers of `<properties>` per the Exchange Format XSD -- could not carry user-defined or profile-driven extended attributes. Downstream callers worked around this by stashing per-relationship metadata in side-channel dicts keyed on relationship `id`, which:

- bypassed `Profile` validation entirely,
- was lost on XML round-trip because `serialize_relationship` had no `<properties>` emit path,
- forced `Model.validate()` to skip half the model when checking profile-conformance.

The ArchiMate Exchange Format XSD permits `<properties>` on every concept (element, relationship, and junction alike), so the field's placement on `Element` was inconsistent with the format we serialize to. ADR-049 set the precedent for this kind of correction: align the Pydantic surface with what the spec already allows, but only where the spec actually demands it -- do not over-symmetrize.

Link: #100, see also ADR-049 (symmetry-only-where-spec-demands-it precedent), ADR-008 (`AttributeMixin` pattern).

## Decision

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Lift `extended_attributes: dict[str, Any] = Field(default_factory=dict)` from `Element` to `Concept` | Concept is the narrowest base that covers Element, Relationship, and Junction. Lifting here picks up all three in one move and matches the XSD scope of `<properties>`. |
| 2 | Do **not** lift to `AttributeMixin` | `AttributeMixin` carries *descriptive* attributes (`name`, `documentation`). `extended_attributes` is a profile/property bag, not a descriptive field; mixing them muddies ADR-008. `AttributeMixin` is also wider than Concept (Connector inherits it) which would over-broaden the surface. |
| 3 | Relax `Profile._validate_profile` so `attribute_extensions` accepts any `Concept` subclass key | A profile that types relationships needs to constrain relationship extended attributes; restricting keys to `Element` made profiles unable to validate the very fields we now permit. |
| 4 | Keep `Profile.specializations` keyed on `Element` only | Specialization in ArchiMate 3.2 is defined for elements; relationships have their own derivation rules and junctions are structural. Broadening `specializations` would invent semantics the spec does not. |
| 5 | Extend `Model.validate()` to walk all concepts, not just elements, when checking extended-attribute conformance | The validation pass must mirror the storage scope; otherwise invalid attribute values on relationships pass silently. |
| 6 | Add a `<properties>` emit path on `serialize_relationship` mirroring the Element path; update the propdef-discovery loop in `serialize_model` to walk relationships as well | XML round-trip is non-negotiable; without this the lift is invisible on disk. The propdef discovery loop must see relationship keys to emit a complete `<propertyDefinitions>` section. |
| 7 | Defer Junction `<properties>` XML round-trip to a follow-up | Connector serialization for Junction is opaque today (no `<properties>` emit, no propdef discovery). In-scope for v1 is Relationship XML round-trip; Junction parity is tracked separately to keep this PR reviewable. The Pydantic field is still present on Junction, so in-memory and JSON paths work immediately. |
| 8 | Keep `INGESTION_PROFILE` element-keyed | Provenance ingestion in practice tags elements; broadening the default profile to all concepts would force every existing ingestion run to start emitting relationship-level provenance keys whether they want to or not. Module docstring documents how to construct a relationship-targeted provenance profile for callers who need one. |
| 9 | Split provenance helpers: keep `unreviewed_elements` Element-scoped; add `unreviewed_concepts` that walks elements, relationships, and junctions | Preserves the existing helper's contract (callers expect `Element` instances back) while giving new callers a concept-wide sweep. Avoids a silent return-type change. |

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|-----------------|
| Lift `extended_attributes` to `AttributeMixin` (Element + Relationship) | `AttributeMixin` does not cover Junction (Junction is a `Concept` but has no `name`/`documentation`), so this misses one of the three concept kinds the XSD permits. Also conflates descriptive attributes with property bags -- see ADR-008. |
| Add `extended_attributes` only to `Relationship` and leave `Junction` without | Junction is a first-class Concept under the spec and can carry `<properties>` in the Exchange Format. Excluding it perpetuates the inconsistency we are fixing. |
| Keep the current state and let downstream code use a side-channel `dict[rel_id, dict]` | This is the workaround the bug report describes. It bypasses Profile validation, loses data on XML round-trip, and pushes the same problem onto every adapter (CSV, Parquet, DuckDB). Not a fix. |
| Broaden `INGESTION_PROFILE` to all concepts as the default | Forces relationship-level provenance keys onto every existing ingestion pipeline. Capability should be opt-in: the lift gives callers the *ability* to do this; the default profile should not silently start doing it for them. |

## Consequences

- **Public Python API: purely additive.** `Element.extended_attributes` callers continue to work unchanged (the field is still present, just inherited from one level up). `Relationship.extended_attributes` and `Junction.extended_attributes` become available; nothing existing breaks.
- **XML wire-format: forward-compat break.** Files written by etcion >= 0.12 that contain relationship-level `<properties>` cannot be deserialized by etcion < 0.12 -- the older parser ignores the element silently and the data is lost on re-serialize. This is documented as a one-way upgrade in the CHANGELOG.
- **ADR-008 (AttributeMixin pattern) is unaffected.** `extended_attributes` is not a descriptive attribute and was never a candidate for that mixin. The mixin's contract -- "fields that describe the concept to a human reader" -- is preserved.
- **Profile authoring surface widens.** Profiles can now declare `attribute_extensions` keyed on any `Concept` subclass. `specializations` deliberately stays Element-only; profile authors who try to specialize a `Relationship` will get the same `ValidationError` they get today.
- **`Model.validate()` cost grows linearly with relationship count** when profiles declare relationship-level extensions. For typical models (relationships outnumber elements ~3:1) this is the expected scale and remains O(n).
- **CHANGELOG entry required** under a "Behavior changes" heading: note the field lift, the relaxed Profile key constraint, the new XML emit path, the deferred Junction XML follow-up, and the new `unreviewed_concepts` helper alongside the unchanged `unreviewed_elements`.
- **Junction XML parity is a known gap.** Tracked as a follow-up issue; in-memory and non-XML serializers handle Junction extended attributes correctly from day one.
