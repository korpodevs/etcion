# ADR-037: Model Comparison and Diff Utilities (EPIC-024)

## Context

Users need to compare two `Model` instances to identify what changed between them -- for governance reviews, migration planning, and version control of architecture models. The backlog defines three feature areas: structural diff engine (FEAT-24.1), diff serialization (FEAT-24.2), and merge support (FEAT-24.3). This ADR covers FEAT-24.1 and FEAT-24.2 only; merge (FEAT-24.3) is deferred to a future ADR.

## Decisions

| # | Question | Options Considered | Decision | Rationale |
|---|----------|--------------------|----------|-----------|
| 1 | **Diff scope** | (a) Element-level only, (b) Element + Relationship, (c) Full structural with field-level detail | **(c) Full structural** | Partial diffs lose rename/re-target information that governance needs. |
| 2 | **Comparison key** | (a) `id` only, (b) `(type, name)` only, (c) Configurable | **(c) Configurable**, default `id` | `id` covers the common same-provenance case; `(type, name)` supports independently-created models. Parameter: `match_by: Literal["id", "type_name"]`. |
| 3 | **Output type** | (a) Plain dict, (b) Pydantic model, (c) Frozen dataclass | **(c) Frozen dataclass `ModelDiff`** | No validation needed on diff output; frozen enforces immutability; `__str__` gives human-readable summary. |
| 4 | **API location** | (a) `Model.diff()` method, (b) Standalone function in `comparison.py` | **(b) `src/etcion/comparison.py`** | Keeps `Model` focused on containment. Diff is a cross-model operation, not owned by either operand. |
| 5 | **Function signature** | -- | `diff_models(model_a: Model, model_b: Model, *, match_by: Literal["id", "type_name"] = "id") -> ModelDiff` | `model_a` is the baseline ("before"), `model_b` is the revised ("after"). |
| 6 | **Field comparison** | (a) Custom per-field, (b) `Concept.model_dump()` dict diff | **(b) `model_dump()` diff** | Leverages Pydantic serialization; automatically picks up new fields. `id` is excluded from change detection (it is the match key). `source`/`target` on relationships are compared by their `id` strings. |
| 7 | **Modified-item representation** | (a) Tuple `(old, new)`, (b) Dedicated `ConceptChange` dataclass | **(b) `ConceptChange` dataclass** | Fields: `concept_id: str`, `concept_type: str`, `changes: dict[str, FieldChange]`. Cleaner than raw tuples. |
| 8 | **Field change representation** | -- | `FieldChange` dataclass with `field: str`, `old: Any`, `new: Any` | Minimal, JSON-serializable via `to_dict()`. |
| 9 | **Relationship matching** | (a) By `id`, (b) By `(type, source_id, target_id)` | **(a) By `id`** (same `match_by` parameter applies) | Consistent with element matching. A relationship is "modified" if source/target id or any field changed. |
| 10 | **Merge** | (a) Include in EPIC-024, (b) Defer | **(b) Defer** | FEAT-24.3 is a separate concern with conflict-resolution complexity. |
| 11 | **Exports** | -- | `ModelDiff`, `diff_models`, `ConceptChange`, `FieldChange` added to `etcion.__init__` | Top-level public API. |

## Data Model

```python
@dataclass(frozen=True)
class FieldChange:
    field: str
    old: Any
    new: Any

@dataclass(frozen=True)
class ConceptChange:
    concept_id: str
    concept_type: str          # e.g. "BusinessActor", "ServingRelationship"
    changes: dict[str, FieldChange]

@dataclass(frozen=True)
class ModelDiff:
    added: tuple[Concept, ...]
    removed: tuple[Concept, ...]
    modified: tuple[ConceptChange, ...]

    def to_dict(self) -> dict[str, Any]: ...
    def summary(self) -> str: ...
    def __str__(self) -> str: ...      # delegates to summary()
    def __bool__(self) -> bool: ...    # True if any changes exist
```

## Algorithm Sketch

1. Build lookup `dict[key, Concept]` for both models (key = `id` or `(type, name)`).
2. `added` = keys in `model_b` not in `model_a`.
3. `removed` = keys in `model_a` not in `model_b`.
4. For shared keys: `model_dump(exclude={"id"})` both, diff the dicts. Relationship `source`/`target` are reduced to their `id` before comparison.
5. Non-empty field diffs become `ConceptChange` entries.

Complexity: O(n + m) where n, m are concept counts -- single-pass set operations plus per-shared-key field comparison.

## Consequences

- **Positive**: Clean separation from `Model`; frozen output prevents accidental mutation; `to_dict()` enables JSON serialization for CI pipelines.
- **Positive**: `match_by="type_name"` supports cross-tool comparison without shared IDs.
- **Negative**: `model_dump()` comparison serializes relationship source/target as full nested dicts; the implementation must normalize these to id-only before comparison.
- **Negative**: No merge capability until a future epic addresses conflict resolution.
