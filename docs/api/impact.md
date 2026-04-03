# Impact Analysis

What-if impact modeling: remove, merge, replace, and relationship operations.

> **User Guide:** [Impact Analysis](../user-guide/impact-analysis.md)

---

## Overview

`etcion.impact` provides a graph-based impact analysis engine that answers what-if questions
about a model. Given a `Model` and a hypothetical change operation, `analyze_impact()` performs
a bidirectional BFS on the underlying `networkx` graph and returns an `ImpactResult` describing
all affected concepts, broken relationships, and (for merge operations) ArchiMate permission
violations.

Requires the `graph` extra:

```
pip install etcion[graph]
```

---

## Functions

### `analyze_impact`

```python
def analyze_impact(
    model: Model,
    *,
    remove: Concept | None = None,
    merge: tuple[list[Concept], Concept] | None = None,
    replace: tuple[Concept, Concept] | None = None,
    add_relationship: Relationship | None = None,
    remove_relationship: Relationship | None = None,
    max_depth: int | None = None,
    follow_types: set[type[Relationship]] | None = None,
) -> ImpactResult
```

Analyse the impact of a what-if change operation on `model`.

Exactly one change-operation parameter must be provided. Operations are mutually exclusive;
the precedence order is: `replace` > `merge` > `add_relationship` > `remove_relationship` > `remove`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `Model` | | The model to analyse. |
| `remove` | `Concept \| None` | `None` | Hypothetically remove this concept. Performs bidirectional BFS; all reachable concepts are reported as affected. Broken relationships (those touching the removed element) are identified. |
| `merge` | `tuple[list[Concept], Concept] \| None` | `None` | A `(merged_list, target)` tuple. All concepts in `merged_list` are collapsed into `target`. Relationships are rewired, deduplicated by `(type, source_id, target_id)`, and permission-checked against ArchiMate 3.2 Appendix B. |
| `replace` | `tuple[Concept, Concept] \| None` | `None` | A `(old, new)` tuple. Equivalent to `merge([old], new)`. Transfers all relationships from `old` to `new` and runs the same permission-checking pipeline. |
| `add_relationship` | `Relationship \| None` | `None` | Hypothetically add this relationship. The resulting model includes the new relationship; source and target elements are reported as affected at depth 1. |
| `remove_relationship` | `Relationship \| None` | `None` | Hypothetically remove this relationship. The resulting model excludes it; source and target are reported as affected at depth 1 and the relationship appears in `broken_relationships`. |
| `max_depth` | `int \| None` | `None` | Maximum BFS traversal depth (`remove` operation only). `None` means unlimited. |
| `follow_types` | `set[type[Relationship]] \| None` | `None` | Restrict BFS traversal to these relationship types (`remove` operation only). `None` follows all types. |

**Returns** `ImpactResult`.

**Raises**

- `ValueError` — if no change-operation parameter is provided.
- `ImportError` — if `networkx` is not installed.

---

### `chain_impacts`

```python
def chain_impacts(*impacts: ImpactResult) -> ImpactResult
```

Combine multiple `ImpactResult` instances into one chained result.

Unions `affected` sets across all impacts, deduplicating by concept ID and keeping
the entry with the minimum depth. Collects all `broken_relationships` and `violations`
from every input. The `resulting_model` of the *last* impact becomes the chained result's
`resulting_model`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `*impacts` | `ImpactResult` | Zero or more impact results to combine. |

**Returns** `ImpactResult` — the union of all inputs. Returns an empty `ImpactResult()` when called with no arguments.

---

## Classes

### `ImpactResult`

```python
@dataclass(frozen=True)
class ImpactResult:
    affected: tuple[ImpactedConcept, ...] = ()
    broken_relationships: tuple[Relationship, ...] = ()
    resulting_model: Model | None = None
    violations: tuple[Violation, ...] = ()
```

Immutable result returned by `analyze_impact()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `affected` | `tuple[ImpactedConcept, ...]` | All concepts reachable from the changed concept within the requested traversal depth. |
| `broken_relationships` | `tuple[Relationship, ...]` | Relationships that become dangling after the operation (source or target removed or, for merge, relationships that fail permission checks). |
| `resulting_model` | `Model \| None` | The model as it would look after the operation. `None` if not computed. |
| `violations` | `tuple[Violation, ...]` | ArchiMate rule violations introduced by the operation. Populated for `merge` and `replace` operations. |

**Dunder methods**

| Method | Returns | Description |
|--------|---------|-------------|
| `__len__` | `int` | Number of affected concepts. |
| `__bool__` | `bool` | `True` if any concepts were affected. |

#### `by_layer`

```python
def by_layer(self) -> dict[Layer | None, list[ImpactedConcept]]
```

Group affected concepts by their class-level `layer` ClassVar.

Concepts whose type has no `layer` attribute (e.g. Relationships) are grouped under
the `None` key.

**Returns** `dict[Layer | None, list[ImpactedConcept]]`.

---

#### `by_depth`

```python
def by_depth(self) -> dict[int, list[ImpactedConcept]]
```

Group affected concepts by traversal depth.

**Returns** `dict[int, list[ImpactedConcept]]`.

---

#### `to_dict`

```python
def to_dict(self) -> dict[str, Any]
```

Return a JSON-serializable dict representation.

Includes `_schema_version: "1.0"` per ADR-046. All nested objects are reduced to
primitive types so that `json.dumps(result.to_dict())` succeeds without a custom encoder.

**Returns** `dict` with keys `_schema_version`, `affected`, `broken_relationships`, `violations`.

---

### `ImpactedConcept`

```python
@dataclass(frozen=True)
class ImpactedConcept:
    concept: Concept
    depth: int
    path: tuple[str, ...] = ()
```

A concept affected by an impact analysis operation.

| Attribute | Type | Description |
|-----------|------|-------------|
| `concept` | `Concept` | The affected concept. |
| `depth` | `int` | Graph distance from the changed concept. `0` = the concept itself (when directly included), `1` = direct neighbour, etc. |
| `path` | `tuple[str, ...]` | Ordered tuple of relationship IDs representing the traversal path from the changed concept to this one. |

---

### `Violation`

```python
@dataclass(frozen=True)
class Violation:
    relationship: Relationship
    reason: str
```

A permission rule violation introduced by a merge or model-merge operation.

| Attribute | Type | Description |
|-----------|------|-------------|
| `relationship` | `Relationship` | The relationship that violates an ArchiMate permission rule after rewiring. |
| `reason` | `str` | Human-readable description of why the relationship is impermissible. |

---

## Example

```python
from etcion.impact import analyze_impact, chain_impacts

# What if we remove the CRM component?
result = analyze_impact(model, remove=crm)
print(f"{len(result)} concept(s) affected")
for ic in result.affected:
    print(f"  depth={ic.depth}  {type(ic.concept).__name__}: {ic.concept.name}")

# What if we merge two application components?
result = analyze_impact(model, merge=([legacy_crm, new_crm], new_crm))
for v in result.violations:
    print("Violation:", v.reason)

# Chain two operations
r1 = analyze_impact(model, remove=component_a)
r2 = analyze_impact(model, remove=component_b)
combined = chain_impacts(r1, r2)

# Group by ArchiMate layer
for layer, concepts in combined.by_layer().items():
    print(layer, [ic.concept.name for ic in concepts])
```
