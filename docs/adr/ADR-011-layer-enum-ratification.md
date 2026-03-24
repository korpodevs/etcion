# ADR-011: Layer Enum Ratification

## Status

ACCEPTED

## Date

2026-03-24

## Context

FEAT-03.1 specifies a `Layer` enum with seven members representing the ArchiMate 3.2 framework layers: Strategy, Motivation, Business, Application, Technology, Physical, and Implementation and Migration. However, this enum was already implemented as part of FEAT-00.2 (ADR-002, module layout) in `src/pyarchi/enums.py`. The backlog stories for FEAT-03.1 were written before FEAT-00.2 was executed, creating a gap between the backlog's "To-Do" status and the actual codebase state.

This ADR serves to ratify the existing `Layer` implementation, confirm its design decisions align with EPIC-003's requirements, and address the remaining gap: `Layer` is not currently re-exported from `src/pyarchi/__init__.py`, which means `hasattr(pyarchi, "Layer")` returns `False`. The `language_structure` conformance test requires this attribute to be present on the package namespace.

The existing implementation defines `Layer` as a standard `enum.Enum` (not `enum.StrEnum`) with human-readable string values. This choice has implications for how downstream code compares and serializes layer values. With `enum.Enum`, `Layer.BUSINESS == "Business"` is `False` -- the string value is accessed via `.value`. With `enum.StrEnum` (Python 3.11+), `Layer.BUSINESS == "Business"` would be `True`, and the enum member could be used directly as a string argument. The `enum.Enum` choice was made in FEAT-00.2 and this ADR ratifies it.

Additionally, STORY-03.1.2 (tests asserting all seven values are present and accessible) has not yet been written. The ADR must note this remaining work item.

## Decision

### Ratification of Existing Implementation

The existing `Layer` enum in `src/pyarchi/enums.py` is ratified as the canonical implementation for FEAT-03.1:

```python
class Layer(Enum):
    STRATEGY = "Strategy"
    MOTIVATION = "Motivation"
    BUSINESS = "Business"
    APPLICATION = "Application"
    TECHNOLOGY = "Technology"
    PHYSICAL = "Physical"
    IMPLEMENTATION_MIGRATION = "Implementation and Migration"
```

### Member Names and String Values

| Member | String Value |
|---|---|
| `STRATEGY` | `"Strategy"` |
| `MOTIVATION` | `"Motivation"` |
| `BUSINESS` | `"Business"` |
| `APPLICATION` | `"Application"` |
| `TECHNOLOGY` | `"Technology"` |
| `PHYSICAL` | `"Physical"` |
| `IMPLEMENTATION_MIGRATION` | `"Implementation and Migration"` |

The member names use UPPER_SNAKE_CASE per PEP 8 convention for enum constants. The string values use the exact names from the ArchiMate 3.2 specification (Section 3.4), including the space-separated "Implementation and Migration" for the combined layer.

`IMPLEMENTATION_MIGRATION` uses an underscore to join the two words, following standard Python naming. The alternative `IMPLEMENTATION_AND_MIGRATION` was considered but rejected for verbosity -- the `_MIGRATION` suffix is unambiguous given the ArchiMate context.

### `enum.Enum`, Not `enum.StrEnum`

`Layer` inherits from `enum.Enum`, not `enum.StrEnum`. This means:

- `Layer.BUSINESS.value` returns `"Business"` (explicit value access).
- `Layer.BUSINESS == "Business"` returns `False` (no implicit string comparison).
- `str(Layer.BUSINESS)` returns `"Layer.BUSINESS"` (the enum representation, not the value).

This is the correct choice because:

1. **Type safety**: `enum.StrEnum` makes enum members interchangeable with strings, which defeats the purpose of using an enum for type discrimination. If `Layer.BUSINESS == "Business"` is `True`, a consumer can pass `"Business"` anywhere a `Layer` is expected, and comparisons silently succeed. With `enum.Enum`, the type checker enforces that only `Layer` members are used where `Layer` is expected.
2. **Serialization control**: When serializing to XML, the library must control the exact string representation. With `enum.Enum`, serialization code explicitly accesses `.value`, making the serialization point visible in the code. With `enum.StrEnum`, the enum member itself IS a string, and serialization happens implicitly anywhere the member is used in a string context.
3. **Consistency**: All other enums in `enums.py` (`Aspect`, `RelationshipCategory`, `AccessMode`, etc.) use `enum.Enum`. Using `enum.StrEnum` for `Layer` alone would be inconsistent.

### Module Location: `src/pyarchi/enums.py`

`Layer` remains in `src/pyarchi/enums.py` as established in ADR-002. All enumerations live at the bottom of the dependency graph, importable by any sub-package without circular import risk. Moving `Layer` to a layer-specific module (e.g., `src/pyarchi/metamodel/layers.py`) would fragment the enum definitions and introduce a new module for a single 10-line class.

### `__init__.py` Re-export

`Layer` must be added to `src/pyarchi/__init__.py` as a re-export and included in `__all__`. The import statement and `__all__` entry are:

```python
from pyarchi.enums import Layer
# in __all__:
"Layer",
```

This satisfies the `language_structure` conformance test requirement that `hasattr(pyarchi, "Layer")` returns `True` and enables the consumer import path `from pyarchi import Layer`.

### Remaining Work: Tests (STORY-03.1.2)

STORY-03.1.2 requires a test asserting all seven `Layer` members are present and accessible. This test has not been written. The test should verify:

1. `len(Layer)` equals 7.
2. Each member name (`STRATEGY`, `MOTIVATION`, `BUSINESS`, `APPLICATION`, `TECHNOLOGY`, `PHYSICAL`, `IMPLEMENTATION_MIGRATION`) is accessible as `Layer.<name>`.
3. Each member's `.value` matches the expected string from the specification.

## Alternatives Considered

### Re-implement Layer in a New Module

Defining a new `Layer` enum in `src/pyarchi/metamodel/notation.py` or a dedicated `src/pyarchi/metamodel/classification.py` was considered, on the rationale that EPIC-003 should own its types. This was rejected because:

1. `Layer` already exists in `enums.py` with the correct members and values. Re-implementing it would create a duplicate that must be kept in sync with the original, or the original must be deleted, breaking the existing import chain.
2. ADR-002 established `enums.py` as the canonical location for all enumerations. Overriding this decision for one enum would create precedent for scattering enums across the codebase.

### Upgrade to `enum.StrEnum`

Changing `Layer` from `enum.Enum` to `enum.StrEnum` was considered for serialization convenience. This was rejected for the type-safety and consistency reasons described above. Additionally, other enums (`RelationshipCategory`, `AccessMode`, etc.) would need the same upgrade for consistency, which is a broader change than FEAT-03.1 warrants.

### Add a `__str__` Override to Return the Value

Adding `def __str__(self) -> str: return self.value` to `Layer` was considered as a middle ground between `enum.Enum` and `enum.StrEnum`. This would make `str(Layer.BUSINESS)` return `"Business"` while keeping `Layer.BUSINESS == "Business"` as `False`. This was rejected because:

1. It creates an inconsistency between `str()` behavior and equality behavior. `str(Layer.BUSINESS) == "Business"` would be `True`, but `Layer.BUSINESS == "Business"` would be `False`. This is confusing.
2. Serialization code should use `.value` explicitly, not rely on `__str__`. The explicit access makes the serialization point visible in code review.

## Consequences

### Positive

- **No code changes to `enums.py`**: The existing implementation is ratified as-is. No risk of introducing regressions in code that already depends on `Layer`.
- **Conformance gap closed**: Adding `Layer` to `__init__.py` re-exports enables the `language_structure` conformance test to pass.
- **Consistent enum pattern**: `Layer` follows the same `enum.Enum` pattern as every other enum in `enums.py`. Contributors learning the codebase encounter one enum style, not two.

### Negative

- **Pre-implementation acknowledged**: This ADR ratifies a decision made before the ADR was written. The design discussion is post-hoc rather than prospective. This is acceptable because the decision is sound and the implementation is minimal (7-member enum with string values), but it sets a precedent where backlog stories may lag behind implementation.
- **No format validation on `.value` strings**: The string values are hardcoded and not validated against an external source (e.g., an XSD schema). If the ArchiMate specification changes a layer name in a future version, the library must be manually updated. This is acceptable for a specification-implementing library.

## Compliance

This ADR provides the architectural rationale for each story in FEAT-03.1:

| Story | Decision Implemented |
|---|---|
| STORY-03.1.1 | Ratified: `Layer` enum defined in `src/pyarchi/enums.py` with seven members (`STRATEGY`, `MOTIVATION`, `BUSINESS`, `APPLICATION`, `TECHNOLOGY`, `PHYSICAL`, `IMPLEMENTATION_MIGRATION`) and their specification-defined string values. `Layer` re-exported from `__init__.py`. |
| STORY-03.1.2 | Test not yet written; ADR specifies the three assertions required (member count, name accessibility, value correctness). |
