# ADR-012: Aspect Enum Ratification

## Status

ACCEPTED

## Date

2026-03-24

## Context

FEAT-03.2 specifies an `Aspect` enum with five members representing the ArchiMate 3.2 framework aspects (the "columns" of the ArchiMate framework): Active Structure, Behavior, Passive Structure, Motivation, and Composite. Like `Layer` (ADR-011), this enum was already implemented as part of FEAT-00.2 in `src/pyarchi/enums.py`. The backlog stories for FEAT-03.2 were written before FEAT-00.2 was executed.

This ADR ratifies the existing `Aspect` implementation, confirms its design decisions, and addresses the same gap identified in ADR-011: `Aspect` is not currently re-exported from `src/pyarchi/__init__.py`, causing `hasattr(pyarchi, "Aspect")` to return `False`. The `language_structure` conformance test requires this attribute.

A notable design point is the naming collision between `Aspect.MOTIVATION` and `Layer.MOTIVATION`. Both enums contain a member named `MOTIVATION`. In the ArchiMate 3.2 framework, the Motivation layer and the Motivation aspect are distinct concepts: the Motivation layer contains element types like Stakeholder, Driver, and Goal, while the Motivation aspect classifies elements by their structural role (alongside Active Structure, Behavior, etc.). The collision is intentional -- both the layer and the aspect are named "Motivation" in the specification. Because `Aspect` and `Layer` are separate `enum.Enum` classes, `Aspect.MOTIVATION` and `Layer.MOTIVATION` are distinct objects with no type-system conflict. `Aspect.MOTIVATION == Layer.MOTIVATION` evaluates to `False`.

STORY-03.2.2 (tests asserting all five values are present and accessible) has not yet been written.

## Decision

### Ratification of Existing Implementation

The existing `Aspect` enum in `src/pyarchi/enums.py` is ratified as the canonical implementation for FEAT-03.2:

```python
class Aspect(Enum):
    ACTIVE_STRUCTURE = "Active Structure"
    BEHAVIOR = "Behavior"
    PASSIVE_STRUCTURE = "Passive Structure"
    MOTIVATION = "Motivation"
    COMPOSITE = "Composite"
```

### Member Names and String Values

| Member | String Value |
|---|---|
| `ACTIVE_STRUCTURE` | `"Active Structure"` |
| `BEHAVIOR` | `"Behavior"` |
| `PASSIVE_STRUCTURE` | `"Passive Structure"` |
| `MOTIVATION` | `"Motivation"` |
| `COMPOSITE` | `"Composite"` |

The member names use UPPER_SNAKE_CASE. The string values use the exact names from the ArchiMate 3.2 specification (Section 3.5). Multi-word aspect names use spaces in the string value and underscores in the member name.

### `enum.Enum`, Not `enum.StrEnum`

`Aspect` inherits from `enum.Enum` for the same reasons as `Layer` (ADR-011): type safety, serialization control, and consistency with all other enums in `enums.py`. The rationale is identical and not repeated here.

### Naming Collision: `Aspect.MOTIVATION` vs. `Layer.MOTIVATION`

Both `Aspect` and `Layer` define a `MOTIVATION` member. This is not a conflict:

1. **Different enum classes**: `Aspect.MOTIVATION` is an `Aspect` instance; `Layer.MOTIVATION` is a `Layer` instance. They are distinct objects in distinct types.
2. **Equality is `False`**: `Aspect.MOTIVATION == Layer.MOTIVATION` returns `False` because `enum.Enum` equality requires both the same type and the same value. While both have the string value `"Motivation"`, they are members of different enum classes.
3. **Type annotations disambiguate**: Any function parameter typed as `layer: Layer` or `aspect: Aspect` makes it clear which enum is expected. mypy will reject `Layer.MOTIVATION` where `Aspect` is expected, and vice versa.
4. **Spec-faithful**: The specification uses the word "Motivation" for both a layer and an aspect. Renaming one (e.g., `Aspect.MOTIVATION_ASPECT`) would deviate from the specification's vocabulary without adding clarity.

### Module Location: `src/pyarchi/enums.py`

`Aspect` remains in `src/pyarchi/enums.py` alongside `Layer` and all other enumerations. Same rationale as ADR-011.

### `__init__.py` Re-export

`Aspect` must be added to `src/pyarchi/__init__.py` as a re-export and included in `__all__`:

```python
from pyarchi.enums import Aspect
# in __all__:
"Aspect",
```

This satisfies the `language_structure` conformance test and enables `from pyarchi import Aspect`.

### Remaining Work: Tests (STORY-03.2.2)

STORY-03.2.2 requires a test asserting all five `Aspect` members are present and accessible. The test should verify:

1. `len(Aspect)` equals 5.
2. Each member name (`ACTIVE_STRUCTURE`, `BEHAVIOR`, `PASSIVE_STRUCTURE`, `MOTIVATION`, `COMPOSITE`) is accessible as `Aspect.<name>`.
3. Each member's `.value` matches the expected string from the specification.

## Alternatives Considered

### Rename `MOTIVATION` to Avoid Collision

Renaming `Aspect.MOTIVATION` to `Aspect.MOTIVATION_ASPECT` (or `Layer.MOTIVATION` to `Layer.MOTIVATION_LAYER`) was considered to eliminate the naming collision. This was rejected because:

1. The specification uses "Motivation" without qualification in both contexts. Adding a suffix deviates from the spec vocabulary.
2. There is no actual collision in Python's type system. The members belong to different enum classes and are fully distinguishable by type.
3. The suffix adds no information -- the enum class name already disambiguates. `Aspect.MOTIVATION` is self-evidently the Motivation aspect; `Layer.MOTIVATION` is self-evidently the Motivation layer.

### Merge Aspect into Layer

Combining `Layer` and `Aspect` into a single two-dimensional classification enum (e.g., `Classification.BUSINESS_ACTIVE_STRUCTURE`) was considered. This was rejected because:

1. Layer and Aspect are orthogonal dimensions. A `BusinessActor` is in the Business layer AND the Active Structure aspect. These are two independent classifications, not a single combined classification.
2. A combined enum would have up to 35 members (7 layers x 5 aspects), most of which would be invalid combinations (e.g., there is no Motivation layer / Active Structure aspect element). Managing the validity matrix inside an enum is cumbersome.
3. The specification treats Layer and Aspect as independent dimensions, and the code should mirror this structure.

### Use Integer Values Instead of Strings

Using integer values (`ACTIVE_STRUCTURE = 1`, `BEHAVIOR = 2`, etc.) was considered for compactness. This was rejected because:

1. String values serve as human-readable labels for debugging, logging, and serialization. `Aspect.BEHAVIOR.value` returning `"Behavior"` is more useful than returning `2`.
2. The ArchiMate Exchange Format uses string identifiers, not integer codes, for layer and aspect classification. String values align with the serialization target.

## Consequences

### Positive

- **No code changes to `enums.py`**: The existing implementation is ratified. No regression risk.
- **Conformance gap closed**: Adding `Aspect` to `__init__.py` re-exports enables the `language_structure` conformance test.
- **Naming collision is a non-issue**: `Aspect.MOTIVATION` and `Layer.MOTIVATION` coexist safely in Python's type system. The ADR documents this explicitly so future contributors do not attempt to "fix" a non-problem.

### Negative

- **Post-hoc ratification**: Same limitation as ADR-011 -- this ADR documents a decision already made. The design discussion is confirmatory rather than exploratory.
- **Five-member enum may grow**: If a future ArchiMate version adds aspects (unlikely given the framework's stability), the enum must be extended. This is a trivial change but requires a library release.

## Compliance

This ADR provides the architectural rationale for each story in FEAT-03.2:

| Story | Decision Implemented |
|---|---|
| STORY-03.2.1 | Ratified: `Aspect` enum defined in `src/pyarchi/enums.py` with five members (`ACTIVE_STRUCTURE`, `BEHAVIOR`, `PASSIVE_STRUCTURE`, `MOTIVATION`, `COMPOSITE`) and their specification-defined string values. `Aspect` re-exported from `__init__.py`. |
| STORY-03.2.2 | Test not yet written; ADR specifies the three assertions required (member count, name accessibility, value correctness). |
