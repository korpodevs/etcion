# Merge

Model merge operations for incremental ingestion and diff application.

> **User Guide:** [Merging](../user-guide/merging.md)

---

## Overview

`etcion.merge` provides two functions for combining models:

- `merge_models()` — merges a *fragment* model into a *base* model using a configurable conflict
  resolution strategy.
- `apply_diff()` — applies a `ModelDiff` as a patch to an existing model.

Neither function mutates its inputs. Both return a `MergeResult` containing the merged model,
any conflicts detected, and any structural violations (dangling relationship endpoints).

---

## Functions

### `merge_models`

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
) -> MergeResult
```

Merge `fragment` into `base`, returning a new `MergeResult`.

Internally uses `diff_models()` to detect differences, then applies the chosen resolution
strategy for each conflict. The merge is **additive**: concepts that exist in `base` but not
in `fragment` are retained in the result. Concepts added by `fragment` are included. Concepts
modified in `fragment` relative to `base` are resolved according to `strategy`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base` | `Model` | | The canonical ("receiving") model. Not mutated. |
| `fragment` | `Model` | | The model fragment (delta) to merge in. Not mutated. |
| `strategy` | `str` | `"prefer_base"` | Conflict resolution strategy. See below. |
| `match_by` | `str` | `"id"` | Key used to identify the *same* concept across models. `"id"` matches by concept ID; `"type_name"` matches by `(type_name, name)` tuple, useful when models come from different tools with different ID schemes. |
| `resolver` | `Callable \| None` | `None` | Callable invoked per conflict when `strategy="custom"`. Signature: `(base_concept, fragment_concept, change) -> winning_concept`. Any exception raised by the resolver is re-raised with the conflicting concept ID appended. Required when `strategy="custom"`. |

**Conflict resolution strategies**

| Strategy | Behaviour |
|----------|-----------|
| `"prefer_base"` | Keep the base version; record the conflict in `MergeResult.conflicts`. |
| `"prefer_fragment"` | Use the fragment version; record the conflict. |
| `"fail_on_conflict"` | Raise `ValueError` at the first conflict encountered. |
| `"custom"` | Delegate to the `resolver` callable. Requires `resolver` to be provided. |

**Returns** `MergeResult`.

**Raises**

- `ValueError` — if `strategy="fail_on_conflict"` and any conflict is detected.
- `ValueError` — if `strategy="custom"` and `resolver` is `None`.

---

### `apply_diff`

```python
def apply_diff(
    model: Model,
    diff: ModelDiff,
) -> MergeResult
```

Apply a `ModelDiff` as a patch to `model`.

Returns a new `MergeResult` without mutating the original model.

- `diff.added` — concepts are added to the result model.
- `diff.removed` — concepts are removed from the result model.
- `diff.modified` — field-level changes are applied to matching concepts.

Removals are applied before additions, so an addition can safely overwrite a removed concept.

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `Model` | The model to patch. Not mutated. |
| `diff` | `ModelDiff` | A `ModelDiff` (from `etcion.comparison`) describing the patch. |

**Returns** `MergeResult`.

- Dangling relationship endpoints caused by removals are reported as `violations`.
- References in `diff.modified` to concept IDs absent from `model` are reported as `conflicts`.

---

## Classes

### `MergeResult`

```python
@dataclass(frozen=True)
class MergeResult:
    merged_model: Model
    conflicts: tuple[ConceptChange, ...] = ()
    violations: tuple[Violation, ...] = ()
```

Immutable result returned by `merge_models()` and `apply_diff()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `merged_model` | `Model` | The new model produced by combining base and fragment. |
| `conflicts` | `tuple[ConceptChange, ...]` | Concepts that existed in both models with differing field values. Populated even when a strategy resolved them. |
| `violations` | `tuple[Violation, ...]` | Structural violations detected after merging (e.g. dangling relationship endpoints). |

**Dunder methods**

| Method | Returns | Description |
|--------|---------|-------------|
| `__bool__` | `bool` | `True` when there are unresolved conflicts (`len(self.conflicts) > 0`). |
| `__str__` | `str` | Same as `summary()`. |

#### `summary`

```python
def summary(self) -> str
```

Return a human-readable one-line summary.

**Returns** `str` — e.g. `"MergeResult: 2 conflict(s), 0 violation(s)"`.

---

#### `to_dict`

```python
def to_dict(self) -> dict[str, Any]
```

Return a JSON-serializable dict per ADR-046.

Includes `_schema_version: "1.0"` for forward compatibility. All nested objects are
reduced to primitive types so that `json.dumps(result.to_dict())` succeeds without a
custom encoder.

**Returns** `dict` with keys `_schema_version`, `merged_model_summary`, `conflicts`,
and `violations`.

---

## Example

```python
from etcion.merge import merge_models, apply_diff

# Merge a fragment into a base model
result = merge_models(base, fragment, strategy="prefer_fragment")
if result:  # True when there are conflicts
    for c in result.conflicts:
        print(f"Conflict on {c.concept_id}: {list(c.changes.keys())}")
for v in result.violations:
    print(f"Violation: {v.reason}")
merged = result.merged_model

# Custom conflict resolution
def pick_longer_name(base_c, frag_c, change):
    if "name" in change.changes:
        return frag_c if len(frag_c.name) > len(base_c.name) else base_c
    return base_c

result = merge_models(
    base, fragment,
    strategy="custom",
    resolver=pick_longer_name,
)

# Apply a diff as a patch
from etcion.comparison import diff_models
diff = diff_models(old_model, new_model)
result = apply_diff(old_model, diff)
print(result.summary())
```

---

## See also

- [`etcion.comparison`](comparison.md) — `diff_models()` and `ModelDiff`
- [`etcion.impact`](impact.md) — `analyze_impact()` with `merge=` for what-if merge analysis
