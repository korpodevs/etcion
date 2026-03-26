# ADR-035: EPIC-022 -- Predefined Viewpoint Catalogue

## Status

PROPOSED

## Date

2026-03-25

## Context

ADR-029 (Decision 7) explicitly deferred predefined viewpoint instances to a future epic, noting that the mechanism (`Viewpoint`, `View`, `Concern`) ships without a catalogue. EPIC-022 is that future epic.

The ArchiMate 3.2 Specification Appendix C defines ~25 standard viewpoints, each with a name, purpose category, content category, and a set of permitted concept types. The Exchange Format XSD (`ViewpointsEnum`, lines 263-315) enumerates them. These viewpoints are **informative** (not normative), but they are essential for interoperability with tools like Archi that use the standard names.

The `Viewpoint` class already exists in `src/pyarchi/metamodel/viewpoints.py` with `frozen=True`, `permitted_concept_types: frozenset[type[Concept]]`, and `purpose`/`content` enum fields. All concrete element and relationship types are exported from `pyarchi.__init__`. The infrastructure is complete; this epic populates it.

Prior decisions accepted without re-litigation:

- `Viewpoint` is a frozen Pydantic `BaseModel`, not a `Concept` (ADR-029 Decision 2).
- `permitted_concept_types` is `frozenset[type[Concept]]` using class references (ADR-029 Decision 3).
- `PurposeCategory` and `ContentCategory` enums live in `src/pyarchi/enums.py` (ADR-029 Decision 5).
- All concrete element and relationship classes are already in the public API (ADR-026, EPIC-014).

## Decisions

### 1. File Placement

| Option | Pros | Cons |
|---|---|---|
| Extend `metamodel/viewpoints.py` | Single file for viewpoint types and instances | Bloats mechanism module with ~25 data definitions; forces all concrete type imports into the mechanism module |
| New `metamodel/viewpoint_catalogue.py` | Separates mechanism from data; import cost is opt-in | Extra module |

**Decision:** New module `src/pyarchi/metamodel/viewpoint_catalogue.py`. The mechanism module (`viewpoints.py`) remains free of concrete type imports. The catalogue module imports all concrete types it needs; this is acceptable because the catalogue is a leaf module with no downstream dependents.

### 2. Representation: Lazy Registry, Not Constants

| Option | Construction | Lookup | Import Cost |
|---|---|---|---|
| Module-level constants | Eager at import time | `ORGANIZATION_VIEWPOINT` | All concrete types loaded on import |
| Factory functions | Per-call | `organization_viewpoint()` | Deferred, but no unified lookup |
| Lazy registry | On first access | `VIEWPOINT_CATALOGUE["Organization"]` | Deferred to first access |

**Decision:** Lazy registry via a module-level `VIEWPOINT_CATALOGUE` object that constructs `Viewpoint` instances on first access and caches them. Implementation: a custom `Mapping` subclass whose `__getitem__` calls a builder function and memoizes the result. This avoids importing all concrete types at module load time while providing the `dict`-style lookup the backlog specifies (`STORY-22.2.1`).

The registry key is the viewpoint name as it appears in the XSD `ViewpointsEnum` (e.g., `"Organization"`, `"Application Cooperation"`). This ensures round-trip compatibility with the Exchange Format.

### 3. Permitted Concept Types: Explicit Sets Per Viewpoint

Each catalogue entry defines its `permitted_concept_types` as a literal `frozenset` of class references, transcribed from Appendix C. No derivation logic, no wildcard "all elements in layer X" shortcuts. Rationale:

1. The spec defines exact sets per viewpoint; shorthand abstractions risk drift.
2. `frozenset` literals are auditable -- a reviewer can diff them against Appendix C.
3. Relationship types are included in the set alongside element types, consistent with the `Viewpoint.permitted_concept_types` field typing (`frozenset[type[Concept]]`).

### 4. Completeness: All 25 XSD Viewpoints

| Option | Count | Rationale |
|---|---|---|
| Representative subset | ~9 (backlog stories) | Faster delivery |
| All XSD viewpoints | 25 | Full interoperability with Exchange Format tooling |

**Decision:** All 25 viewpoints listed in the XSD `ViewpointsEnum`. The backlog stories (STORY-22.1.1 through 22.1.9) cover a representative subset in detail; the remaining viewpoints follow the same mechanical pattern and are added in a single pass without additional stories. STORY-22.1.10 tests all of them parametrically.

The 25 viewpoints:

| Category | Viewpoints |
|---|---|
| Composition | Organization, Application Platform, Application Structure, Information Structure, Technology, Layered, Physical |
| Support | Product, Application Usage, Technology Usage |
| Cooperation | Business Process Cooperation, Application Cooperation |
| Realization | Service Realization, Implementation and Deployment, Goal Realization, Goal Contribution, Principles, Requirements Realization, Motivation |
| Strategy | Strategy, Capability Map, Outcome Realization, Resource Map, Value Stream |
| Impl. & Migration | Project, Migration, Implementation and Migration |
| Other | Stakeholder |

### 5. Purpose and Content Categories

Each viewpoint's `purpose` and `content` fields are set per Appendix C Table C-1. The mapping is stored as data alongside the `permitted_concept_types` in each builder function. No additional enums or fields are introduced.

### 6. Exports

| Symbol | Exported from `pyarchi.__init__` | Rationale |
|---|---|---|
| `VIEWPOINT_CATALOGUE` | Yes | Primary public API for accessing predefined viewpoints |
| Individual viewpoint constants | No | Registry is the single access point; avoids 25 module-level names |

Import path: `from pyarchi import VIEWPOINT_CATALOGUE` or `from pyarchi.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE`.

### 7. Testing Strategy

All 25 viewpoints are tested via `pytest.mark.parametrize` over `VIEWPOINT_CATALOGUE.keys()`. No per-viewpoint test functions.

| Test | Assertion |
|---|---|
| Name matches key | `vp.name == key` for each entry |
| Purpose is valid | `isinstance(vp.purpose, PurposeCategory)` |
| Content is valid | `isinstance(vp.content, ContentCategory)` |
| Non-empty permitted types | `len(vp.permitted_concept_types) > 0` |
| All types are Concept subclasses | `all(issubclass(t, Concept) for t in vp.permitted_concept_types)` |
| Registry is complete | `len(VIEWPOINT_CATALOGUE) == 25` |
| Lookup by XSD name | `VIEWPOINT_CATALOGUE["Application Cooperation"].name == "Application Cooperation"` |
| View integration | A `View` governed by a catalogue viewpoint accepts permitted types and rejects others |

## Alternatives Considered

### Enum-Based Viewpoint Identifiers

Adding a `StandardViewpoint` enum with 25 members and using `VIEWPOINT_CATALOGUE[StandardViewpoint.ORGANIZATION]` instead of string keys. Rejected because:

1. The XSD uses string tokens, not enum values. String keys provide direct round-trip fidelity.
2. An enum adds a type that must be kept in sync with the catalogue -- one more thing to update when viewpoints change.
3. Users already know viewpoint names from the spec and from other tools; string lookup is more discoverable.

### Declarative YAML/JSON Data File

Storing viewpoint definitions in a data file and loading them at runtime. Rejected because:

1. `permitted_concept_types` are class references (`type[Concept]`), not strings. A data file would require a string-to-class resolution layer.
2. Adds a runtime dependency on a data file path, complicating packaging.
3. Python code is already the most readable format for "a dict of frozensets of classes."

### Eager Module-Level Constants

`ORGANIZATION_VIEWPOINT = Viewpoint(...)` at module scope. Rejected per ADR-029's analysis: importing all concrete types at module load time is heavyweight, and 25 constants pollute the namespace.

## Consequences

### Positive

- Full catalogue of Appendix C viewpoints available via a single import (`VIEWPOINT_CATALOGUE`).
- Lazy construction avoids paying the import cost of all concrete types unless the catalogue is actually used.
- String-keyed lookup matches the XSD `ViewpointsEnum` tokens, enabling seamless Exchange Format round-tripping.
- Parametric testing covers all 25 viewpoints with a single test function, keeping the test surface compact.

### Negative

- The `Mapping` wrapper adds a small amount of indirection compared to plain dict access. Debugger inspection of `VIEWPOINT_CATALOGUE` before first access shows an empty cache rather than pre-populated entries.
- Permitted concept type sets are manually transcribed from Appendix C. Transcription errors are possible and must be caught by review against the spec. No automated spec-to-code pipeline exists.
- Adding the 25th+ viewpoint (custom or future spec revision) still requires a code change in `viewpoint_catalogue.py`. The registry is not user-extensible at runtime by design -- custom viewpoints are constructed directly via `Viewpoint(...)`.
