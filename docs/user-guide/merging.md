# Merging Models

Combine two model versions into one, detect conflicts, and apply structured
patches — all without mutating the originals.

## What Merging Is For

Ingestion pipelines rarely produce a complete model in a single pass. A CMDB
export, a strategy document, and an AI-extraction tool each produce a *fragment*
— a partial model covering a slice of the architecture. `merge_models()` folds a
fragment into a canonical base model, resolves conflicts according to a chosen
strategy, and reports any structural issues in the result.

Use merging when you need to:

- Incorporate incremental updates from an external source into a canonical model
- Combine models produced by different tools that may assign different IDs to the
  same concept
- Validate a proposed fragment against the base before committing it
- Automate conflict resolution with custom business rules

For a pure *comparison* of two model versions without merging them, use
[Diffing](diffing.md). For what-if impact assessment before committing a
destructive change, use [Impact Analysis](impact-analysis.md).

---

## merge_models()

### Signature

```python
def merge_models(
    base: Model,
    fragment: Model,
    *,
    strategy: Literal[
        "prefer_base", "prefer_fragment", "fail_on_conflict", "custom"
    ] = "prefer_base",
    match_by: Literal["id", "type_name"] = "id",
    resolver: Callable[[Concept, Concept, ConceptChange], Concept] | None = None,
) -> MergeResult: ...
```

Neither `base` nor `fragment` is mutated. The returned `MergeResult` always
contains an independent copy of every concept.

### Basic usage

```python
from etcion import merge_models
from etcion.metamodel.business import BusinessActor, BusinessRole
from etcion.metamodel.model import Model

# Canonical model — the source of truth.
actor = BusinessActor(id="actor-alice", name="Alice")
base = Model(concepts=[actor])

# Fragment from a new import — adds Bob and a role.
bob   = BusinessActor(id="actor-bob",   name="Bob")
role  = BusinessRole(id="role-analyst", name="Analyst")
fragment = Model(concepts=[bob, role])

result = merge_models(base, fragment)

print(len(result.merged_model))  # 3
print(result.summary())          # MergeResult: 0 conflict(s), 0 violation(s)
```

### match_by — cross-tool ID alignment

By default concepts are matched by `id`. When two tools assign different IDs to
the same real-world concept, use `match_by="type_name"` to match by
`(type_name, name)` tuple instead:

```python
base_actor = BusinessActor(id="id-from-tool-a", name="Alice")
frag_actor = BusinessActor(id="id-from-tool-b", name="Alice")

base     = Model(concepts=[base_actor])
fragment = Model(concepts=[frag_actor])

# Without match_by="type_name", these would be treated as two separate actors.
result = merge_models(base, fragment, match_by="type_name")

alice_instances = [
    c for c in result.merged_model.concepts if getattr(c, "name", None) == "Alice"
]
assert len(alice_instances) == 1   # deduplicated
```

### Merge semantics

- **Additive, not destructive.** Concepts present in `base` but absent from
  `fragment` are retained in the merged model. The fragment never deletes base
  concepts.
- **Relationships are transitive.** If the fragment contains element A, element
  B, and a relationship A → B, all three are included in the merged model,
  provided both endpoints are present. Relationships whose endpoints are missing
  from both models become violations (see [Violations](#violations)).
- **No mutation.** `merge_models()` returns a new `MergeResult`; `base` and
  `fragment` are unchanged after the call.

---

## Conflict Resolution Strategies

A *conflict* occurs when the same concept ID exists in both models with
different field values. The `strategy` parameter controls what happens.

### prefer_base (default)

The base version of the concept is kept. The conflict is recorded in
`result.conflicts` but does not affect the merge outcome.

```python
base_actor = BusinessActor(id="actor-1", name="Alice")
frag_actor = BusinessActor(id="actor-1", name="Alicia")

base     = Model(concepts=[base_actor])
fragment = Model(concepts=[frag_actor])

result = merge_models(base, fragment, strategy="prefer_base")

print(result.merged_model["actor-1"].name)  # Alice
print(len(result.conflicts))                # 1
```

### prefer_fragment

The fragment version of the concept is used. Useful when the fragment is the
authoritative update source and the base is stale.

```python
result = merge_models(base, fragment, strategy="prefer_fragment")

print(result.merged_model["actor-1"].name)  # Alicia
print(len(result.conflicts))                # 1
```

The conflict is still recorded so callers can audit what was overwritten.

### fail_on_conflict

Raises `ValueError` at the first conflict encountered. Use this in CI/CD
pipelines to enforce that incoming fragments contain no surprises.

```python
from etcion import merge_models

try:
    result = merge_models(base, fragment, strategy="fail_on_conflict")
except ValueError as exc:
    print(exc)  # Conflict on concept 'actor-1': fields ['name'] differ ...
```

### custom

Delegates resolution to a callable you supply via `resolver`. The callable
receives `(base_concept, fragment_concept, change)` and must return the
`Concept` that should appear in the merged model. The returned concept may be
either of the two inputs or a new copy derived from both.

```python
from etcion.comparison import ConceptChange
from etcion.metamodel.concepts import Concept

def last_write_wins(
    base_concept: Concept,
    frag_concept: Concept,
    change: ConceptChange,
) -> Concept:
    # Business rule: fragment is always the latest authoritative update.
    return frag_concept

result = merge_models(base, fragment, strategy="custom", resolver=last_write_wins)
```

Combining fields from both sides:

```python
def combine_names(
    base_concept: Concept,
    frag_concept: Concept,
    change: ConceptChange,
) -> Concept:
    combined = f"{base_concept.name} / {frag_concept.name}"
    return base_concept.model_copy(update={"name": combined})

result = merge_models(base, fragment, strategy="custom", resolver=combine_names)
print(result.merged_model["actor-1"].name)  # Alice / Alicia
```

Passing `strategy="custom"` without a `resolver` raises `ValueError`
immediately:

```python
# Raises: strategy='custom' requires a resolver callback; pass resolver=<callable>
merge_models(base, fragment, strategy="custom")
```

Any exception raised inside the resolver is re-raised with the conflicting
concept ID prepended to the message, so the stack trace always identifies which
concept triggered the failure.

---

## MergeResult

`merge_models()` and `apply_diff()` both return a `MergeResult`. It is a
frozen dataclass — all fields are immutable after construction.

### Fields

| Field | Type | Description |
|---|---|---|
| `merged_model` | `Model` | The new model produced by combining base and fragment |
| `conflicts` | `tuple[ConceptChange, ...]` | Concepts with differing field values in both inputs; populated regardless of which strategy was used |
| `violations` | `tuple[Violation, ...]` | Dangling relationship endpoints detected after merging |

### Boolean evaluation and summary

`bool(result)` is `True` when there are unresolved conflicts:

```python
result = merge_models(base, fragment)

if result:
    print(f"Review required: {len(result.conflicts)} conflict(s)")
else:
    print("Clean merge")
```

`result.summary()` returns a one-line human-readable string:

```python
print(result.summary())
# MergeResult: 1 conflict(s), 0 violation(s)
```

`str(result)` delegates to `summary()`.

### to_dict() — JSON export

`to_dict()` returns a JSON-serializable dict conforming to the ADR-046 data
export contract. `json.dumps(result.to_dict())` always succeeds without a
custom encoder.

```python
import json

result = merge_models(base, fragment)
print(json.dumps(result.to_dict(), indent=2))
```

The dict has the following top-level keys:

| Key | Description |
|---|---|
| `_schema_version` | Always `"1.0"` |
| `merged_model_summary` | Dict with `element_count` and `relationship_count` |
| `conflicts` | List of `{concept_id, concept_type, changed_fields}` dicts |
| `violations` | List of `{relationship_id, reason}` dicts |

### Jupyter rendering

`MergeResult` implements `_repr_html_()`, so it renders as a styled HTML
summary in Jupyter notebooks automatically:

```python
result = merge_models(base, fragment)
result  # displays a colour-coded HTML table in Jupyter
```

Clean merges render a green banner with the element count. Merges with
conflicts or violations render colour-coded tables for each.

---

## apply_diff()

`apply_diff()` applies a `ModelDiff` as a patch to an existing model. Where
`merge_models()` computes the diff internally and applies it in one step,
`apply_diff()` lets you work with a diff you already have — for example, one
produced by `diff_models()`, loaded from storage, or constructed programmatically.

### Signature

```python
def apply_diff(
    model: Model,
    diff: ModelDiff,
) -> MergeResult: ...
```

The original `model` is never mutated. The returned `MergeResult` contains an
independent copy.

### Basic usage

```python
from etcion.comparison import diff_models
from etcion.merge import apply_diff

diff = diff_models(model_a, model_b)
result = apply_diff(model_a, diff)
```

### Patch semantics

`apply_diff()` applies the three sections of a `ModelDiff` in order:

1. **`diff.removed`** — concepts with matching IDs are removed from the working
   set first.
2. **`diff.added`** — new concepts are inserted, potentially overwriting any
   concept removed in step 1 that shares the same ID.
3. **`diff.modified`** — field-level changes are applied to the matching concept
   via `model_copy(update=...)`.

```python
from etcion.comparison import ConceptChange, FieldChange, ModelDiff
from etcion.merge import apply_diff
from etcion.metamodel.business import BusinessActor
from etcion.metamodel.model import Model

alice = BusinessActor(id="a1", name="Alice")
model = Model(concepts=[alice])

# Rename Alice to Alicia via a hand-crafted diff.
change = ConceptChange(
    concept_id="a1",
    concept_type="BusinessActor",
    changes={"name": FieldChange(field="name", old="Alice", new="Alicia")},
)
diff = ModelDiff(added=(), removed=(), modified=(change,))

result = apply_diff(model, diff)
print(result.merged_model["a1"].name)  # Alicia
```

### Round-trip: apply_diff(A, diff_models(A, B)) ~= B

`diff_models(A, B)` followed by `apply_diff(A, diff)` produces a model whose
concept IDs match those of B:

```python
from etcion.comparison import diff_models
from etcion.merge import apply_diff

diff   = diff_models(model_a, model_b)
result = apply_diff(model_a, diff)

result_ids   = {c.id for c in result.merged_model.concepts}
expected_ids = {c.id for c in model_b.concepts}
assert result_ids == expected_ids
```

Note that this is an *ID equality*, not a field equality: if B contains
concepts absent from A (with new IDs), those appear in the result; if A
contains concepts absent from B, those are removed.

### Conflicts in apply_diff()

If `diff.modified` references a concept ID that does not exist in the model
(for example, because an earlier diff step removed it), that `ConceptChange` is
recorded as a conflict rather than applied:

```python
result = apply_diff(model, diff)

if result.conflicts:
    for change in result.conflicts:
        print(f"Could not apply change to '{change.concept_id}' — concept not found")
```

---

## Violations

A `Violation` is produced whenever a relationship in the merged model has a
dangling endpoint — a source or target that does not appear in the merged
concept set. This can happen when:

- The fragment contains a relationship pointing to an element that exists in
  neither the base nor the fragment (a genuinely ghost endpoint).
- `apply_diff()` removes an element that is still referenced by a relationship.

Violations do not prevent the merge from completing. The relationship is simply
excluded from `result.merged_model` and recorded in `result.violations`.

```python
from etcion.impact import Violation
from etcion.metamodel.business import BusinessActor
from etcion.metamodel.relationships import Association
from etcion.metamodel.model import Model

actor_a = BusinessActor(id="actor-a", name="A")
ghost   = BusinessActor(id="ghost",   name="Ghost")
rel     = Association(id="rel-ghost", name="ghostlink", source=actor_a, target=ghost)

# ghost is NOT added to the fragment.
fragment = Model(concepts=[actor_a, rel])
base     = Model(concepts=[actor_a])

result = merge_models(base, fragment)

print(len(result.violations))               # 1
print(result.violations[0].reason)
# Relationship 'rel-ghost' has a dangling endpoint in the merged model
# (source='actor-a', target='ghost')
```

`Violation` has two fields:

| Field | Type | Description |
|---|---|---|
| `relationship` | `Relationship` | The relationship with the dangling endpoint |
| `reason` | `str` | Human-readable description of the missing endpoint |

---

## Common Patterns

### Incremental ingestion pipeline

Each fragment source feeds into the canonical model in sequence. Because
`merged_model` is an independent copy, you can safely chain calls:

```python
from etcion import merge_models

model = base_model

for fragment in [cmdb_fragment, strategy_fragment, ai_fragment]:
    result = merge_models(model, fragment, strategy="prefer_fragment")

    if result.violations:
        print(f"WARNING: {len(result.violations)} dangling relationship(s) from fragment")
        for v in result.violations:
            print(" -", v.reason)

    model = result.merged_model

print(f"Final model: {len(model)} concept(s)")
```

### Strict CI/CD validation

Reject fragments that conflict with the canonical model in a pipeline step:

```python
from etcion import merge_models

try:
    result = merge_models(canonical, incoming_fragment, strategy="fail_on_conflict")
except ValueError as exc:
    # Exit non-zero to fail the pipeline.
    raise SystemExit(f"Fragment rejected: {exc}") from exc

print("Fragment accepted — no conflicts")
```

### Audit trail via to_dict()

Persist a JSON record of every merge for audit or rollback purposes:

```python
import json

result = merge_models(base, fragment)
audit_record = result.to_dict()

with open("merge_audit.json", "w") as f:
    json.dump(audit_record, f, indent=2)
```

### Stored diff as a patch

Save a diff to disk, then replay it against any compatible model:

```python
import json
from etcion.comparison import ConceptChange, FieldChange, ModelDiff, diff_models
from etcion.merge import apply_diff

# Compute and serialise the diff.
diff = diff_models(model_v1, model_v2)
with open("patch.json", "w") as f:
    json.dump(diff.to_dict(), f, indent=2)

# Later — replay the patch against model_v1.
result = apply_diff(model_v1, diff)
```

### Detect conflict without resolving

Pass `strategy="prefer_base"` and inspect `result.conflicts` to audit what the
fragment would change before deciding whether to accept it:

```python
result = merge_models(canonical, incoming, strategy="prefer_base")

if result.conflicts:
    print(f"{len(result.conflicts)} conflict(s) detected:")
    for change in result.conflicts:
        print(f"  {change.concept_type} '{change.concept_id}':")
        for field, fc in change.changes.items():
            print(f"    {field}: {fc.old!r} -> {fc.new!r}")
    # Decide whether to promote to prefer_fragment or reject.
```

---

## API Summary

| Symbol | Kind | Description |
|---|---|---|
| `merge_models(base, fragment, *, strategy, match_by, resolver)` | function | Merge a fragment into a base model; returns `MergeResult` |
| `apply_diff(model, diff)` | function | Apply a `ModelDiff` patch to a model; returns `MergeResult` |
| `MergeResult` | frozen dataclass | Holds `merged_model`, `conflicts`, and `violations` |
| `MergeResult.summary()` | method | One-line human-readable summary of conflict and violation counts |
| `MergeResult.to_dict()` | method | JSON-serializable dict conforming to the ADR-046 export contract |
| `MergeResult.__bool__()` | method | `True` when `conflicts` is non-empty |
| `ConceptChange` | frozen dataclass | A concept present in both models with differing field values |
| `FieldChange` | frozen dataclass | A single field-level change (`field`, `old`, `new`) |
| `Violation` | frozen dataclass | A dangling relationship endpoint in the merged model |

See also: [API Reference](../api/index.md), [Diffing](diffing.md),
[Impact Analysis](impact-analysis.md)
