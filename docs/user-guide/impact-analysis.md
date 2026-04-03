# Impact Analysis and What-If Modeling

`analyze_impact()` computes the blast radius of a hypothetical change to a
model without modifying it. You describe an operation — removing an element,
merging two elements, replacing one with another, or adding/removing a
relationship — and receive an `ImpactResult` that shows which concepts are
affected, which relationships would break, and what the model would look like
after the change.

## When to Use Impact Analysis

Use impact analysis when you need to:

- Preview which elements would be affected before committing a destructive
  change
- Plan multi-step migrations by chaining several what-if scenarios together
- Detect ArchiMate permission violations that a merge or replace operation
  would introduce
- Feed a before/after comparison into `diff_models()` without touching the
  original model
- Produce a JSON-serializable report of the change for downstream tooling

For straightforward structural queries without a hypothetical change, the flat
query methods on `Model` (see [Querying](querying.md)) are more direct. For
comparing two existing model versions, use [Diffing](diffing.md).

Impact analysis requires the `graph` extra:

```
pip install etcion[graph]
```

---

## analyze_impact()

```python
from etcion import analyze_impact

result = analyze_impact(model, remove=some_element)
```

### Signature

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
) -> ImpactResult: ...
```

Exactly one scenario parameter (`remove`, `merge`, `replace`,
`add_relationship`, or `remove_relationship`) must be provided. Passing none
raises `ValueError`. The `max_depth` and `follow_types` parameters apply only
to the `remove` scenario.

The original model is never modified. `ImpactResult.resulting_model` is always
a new `Model` instance with independent copies of all surviving concepts.

### Basic remove example

```python
from etcion import analyze_impact
from etcion.metamodel.business import BusinessActor, BusinessProcess
from etcion.metamodel.model import Model
from etcion.metamodel.relationships import Assignment

actor = BusinessActor(id="a1", name="Alice")
process = BusinessProcess(id="p1", name="Order Processing")
rel = Assignment(id="rel-1", name="", source=actor, target=process)
model = Model(concepts=[actor, process, rel])

result = analyze_impact(model, remove=actor)

print(len(result))                       # 1 — process is affected
print([ic.concept.name for ic in result.affected])   # ["Order Processing"]
print([r.id for r in result.broken_relationships])   # ["rel-1"]
```

---

## Scenario Types

### remove

Computes a bidirectional BFS from the removed element, so impact propagates
along both incoming and outgoing relationships.

```python
result = analyze_impact(model, remove=actor)
```

The removed element itself does not appear in `result.affected`. All
relationships that referenced it as source or target appear in
`result.broken_relationships`. The `resulting_model` excludes the element and
all broken relationships.

### merge

Collapses a list of elements into a single target. Every relationship that
touches any element in the merge list is rewired to point at the target instead.
Duplicate rewired relationships are deduplicated by `(type, source_id,
target_id)`. Each deduplicated relationship is then checked against the
ArchiMate 3.2 permission table; impermissible relationships appear in
`result.violations` rather than in the resulting model.

```python
from etcion.metamodel.business import BusinessActor, BusinessRole
from etcion.metamodel.relationships import Association

actor_a = BusinessActor(id="a1", name="A")
actor_b = BusinessActor(id="b1", name="B")
target  = BusinessActor(id="t1", name="T")
role    = BusinessRole(id="r1", name="R")
rel_a   = Association(id="rel-ar", name="", source=actor_a, target=role)
rel_b   = Association(id="rel-br", name="", source=actor_b, target=role)
model   = Model(concepts=[actor_a, actor_b, target, role, rel_a, rel_b])

# Merge A and B into T.  Both A→R and B→R rewire to T→R;
# deduplication keeps only one T→R in the result.
result = analyze_impact(model, merge=([actor_a, actor_b], target))
```

The target may be one of the merged elements, in which case it is kept and all
others are removed.

### replace

A convenience shorthand for the common case of swapping one element for
another. `replace=(old, new)` is equivalent to `merge([old], new)` and is
subject to the same rewiring, deduplication, and permission-checking logic.

```python
old_component = ApplicationComponent(id="comp1", name="LegacyComp")
new_component = ApplicationComponent(id="comp2", name="ModernComp")

result = analyze_impact(model, replace=(old_component, new_component))
```

### add_relationship

Reports the impact of hypothetically adding a new relationship to the model.
The source and target elements of the new relationship appear in
`result.affected` at depth 1. The resulting model contains all original
concepts plus the new relationship.

```python
from etcion.metamodel.relationships import Serving

new_rel = Serving(id="rel-new", name="", source=app_component, target=app_service)
result = analyze_impact(model, add_relationship=new_rel)
```

### remove_relationship

Reports the impact of hypothetically removing a relationship. The source and
target elements appear in `result.affected` at depth 1. The removed
relationship appears in `result.broken_relationships`. The resulting model
retains all elements but omits the relationship.

```python
result = analyze_impact(model, remove_relationship=some_rel)
```

---

## ImpactResult

`ImpactResult` is a frozen dataclass. Its fields are immutable tuples.

| Field | Type | Description |
|---|---|---|
| `affected` | `tuple[ImpactedConcept, ...]` | All concepts reachable from the changed concept within the traversal depth |
| `broken_relationships` | `tuple[Relationship, ...]` | Relationships that would become dangling after the operation |
| `resulting_model` | `Model \| None` | The model as it would look after the operation |
| `violations` | `tuple[Violation, ...]` | ArchiMate permission violations introduced by a merge or replace operation |

`ImpactResult` supports `len()` and boolean evaluation:

```python
result = analyze_impact(model, remove=actor)

if result:
    print(f"{len(result)} concept(s) affected")
else:
    print("No impact — isolated element")
```

### ImpactedConcept

Each entry in `result.affected` is an `ImpactedConcept`:

| Field | Type | Description |
|---|---|---|
| `concept` | `Concept` | The affected concept |
| `depth` | `int` | Graph distance from the changed concept (1 = direct neighbour) |
| `path` | `tuple[str, ...]` | Ordered relationship IDs traversed to reach this concept |

```python
for ic in result.affected:
    print(ic.concept.name, "at depth", ic.depth, "via", ic.path)
```

### Grouping methods

#### .by_layer()

Groups affected concepts by their ArchiMate layer:

```python
from etcion.enums import Layer

groups = result.by_layer()

for layer, concepts in groups.items():
    label = layer.value if layer is not None else "no layer"
    print(f"{label}: {[ic.concept.name for ic in concepts]}")
```

Concepts whose type has no `layer` class attribute (such as relationships used
as graph nodes) are grouped under the `None` key. Layer keys that have no
affected concepts are omitted entirely.

```python
# Example output for a remove that touches Business and Application elements:
# business: ["Order Processing", "Customer Role"]
# application: ["Order Service"]
```

#### .by_depth()

Groups affected concepts by traversal depth:

```python
groups = result.by_depth()

direct = groups.get(1, [])      # immediately connected
indirect = groups.get(2, [])    # two hops away

print("Direct impact:", [ic.concept.name for ic in direct])
print("Indirect impact:", [ic.concept.name for ic in indirect])
```

---

## Broken Relationship Reporting

Any relationship whose source or target is the removed (or merged-out) element
appears in `result.broken_relationships`. Only relationships that directly
touch the removed element are reported; unrelated relationships in the same
model are not included.

```python
result = analyze_impact(model, remove=actor)

for rel in result.broken_relationships:
    print(
        f"Broken: {type(rel).__name__} "
        f"{rel.source.name} -> {rel.target.name} (id={rel.id})"
    )
```

Broken relationships are excluded from `result.resulting_model` automatically.

For `remove_relationship`, the removed relationship itself is placed in
`broken_relationships`:

```python
result = analyze_impact(model, remove_relationship=rel)
assert rel in result.broken_relationships
# Both endpoints survive in resulting_model
assert actor.id in {c.id for c in result.resulting_model}
```

---

## chain_impacts()

`chain_impacts()` aggregates multiple `ImpactResult` instances into a single
combined result. Use it when you want a unified summary across several
independent what-if operations applied to the same base model.

```python
from etcion import analyze_impact, chain_impacts

result_a = analyze_impact(model, remove=element_a)
result_b = analyze_impact(model, remove=element_b)

combined = chain_impacts(result_a, result_b)
print(f"{len(combined)} total affected concepts")
```

When the same concept appears in multiple results, `chain_impacts()` keeps the
entry with the minimum depth. The `resulting_model` of the last argument
becomes the combined result's `resulting_model`. All `broken_relationships` and
`violations` from every input are collected.

`chain_impacts()` with no arguments returns an empty `ImpactResult`.

### Multi-step migration planning

For sequential changes — where each step operates on the model produced by the
previous step — pass `result.resulting_model` as the model for the next call:

```python
# Step 1: remove the legacy gateway
result1 = analyze_impact(model, remove=legacy_gateway)

# Step 2: replace the adapter in the intermediate model
adapter_copy = result1.resulting_model["adapter-1"]
result2 = analyze_impact(result1.resulting_model, replace=(adapter_copy, modern_adapter))

# Step 3: summarise all impact across the migration
migration_summary = chain_impacts(result1, result2)
print(f"Migration touches {len(migration_summary)} concept(s)")
print(f"Broken across all steps: {len(migration_summary.broken_relationships)}")
print(f"Violations introduced: {len(migration_summary.violations)}")
```

Because `resulting_model` is a deep copy, each call to `analyze_impact()` is
independent of the previous one. Mutating the original model after the first
call does not affect any intermediate results.

---

## follow_types — filtering traversal

The `follow_types` parameter restricts BFS traversal to relationships of the
specified types. It applies only to the `remove` scenario.

```python
from etcion.metamodel.relationships import Serving, Realization

# Only propagate impact along Serving and Realization edges
result = analyze_impact(
    model,
    remove=actor,
    follow_types={Serving, Realization},
)
```

`follow_types` uses `issubclass` semantics, so passing an abstract base class
matches all concrete subtypes:

```python
from etcion.metamodel.relationships import StructuralRelationship

# Follows Composition, Aggregation, Association, Assignment, and Realization
result = analyze_impact(model, remove=actor, follow_types={StructuralRelationship})
```

When `follow_types=None` (the default), all relationship types are traversed.
Passing an empty set (`follow_types=set()`) means no edges are followed and
`result.affected` will be empty.

Broken relationships are always computed from the full model graph regardless
of `follow_types`. A relationship that touches the removed element but whose
type is excluded from traversal still appears in `broken_relationships`.

### max_depth

Limit traversal depth with `max_depth`:

```python
# Only report concepts up to 2 hops away
result = analyze_impact(model, remove=actor, max_depth=2)
```

`max_depth=None` (the default) means unlimited depth.

---

## Violation Detection

Merge and replace operations can introduce ArchiMate permission violations when
rewired relationships connect element types that the specification does not
permit. Each impermissible rewired relationship produces a `Violation` and is
excluded from `result.resulting_model`.

```python
from etcion.impact import Violation

for v in result.violations:
    print(v.reason)
    # e.g. "Serving(BusinessActor -> ApplicationService) is not permitted
    #        by ArchiMate 3.2 Appendix B"
```

A `Violation` has two fields:

| Field | Type | Description |
|---|---|---|
| `relationship` | `Relationship` | The rewired relationship that failed the permission check |
| `reason` | `str` | Human-readable description of why the relationship is impermissible |

To validate the resulting model after an impact operation:

```python
result = analyze_impact(model, replace=(old_element, new_element))

if result.violations:
    print(f"WARNING: {len(result.violations)} permission violation(s)")
    for v in result.violations:
        print(" -", v.reason)

# The resulting_model contains only permitted relationships
errors = result.resulting_model.validate()
```

---

## Common Patterns

### Export as JSON

`ImpactResult.to_dict()` returns a JSON-serializable dict:

```python
import json

result = analyze_impact(model, remove=actor)
print(json.dumps(result.to_dict(), indent=2))
```

The dict includes a `_schema_version` key alongside `affected`,
`broken_relationships`, and `violations`.

### Integrate with diff_models()

Because `resulting_model` is an independent copy, you can pass it directly to
`diff_models()` to produce a structured before/after comparison:

```python
from etcion import analyze_impact, diff_models

result = analyze_impact(model, remove=actor)
diff = diff_models(model, result.resulting_model)

print(diff.summary())
# e.g. "ModelDiff: 0 added, 2 removed, 0 modified"
```

### Inspect impact in Jupyter

`ImpactResult` implements `_repr_html_()`, so it renders as a styled table
automatically in Jupyter notebooks. Assign the result to the last expression in
a cell:

```python
result = analyze_impact(model, remove=actor)
result  # renders an HTML table in Jupyter
```

---

## API Summary

| Symbol | Kind | Description |
|---|---|---|
| `analyze_impact(model, *, ...)` | function | Entry point for all what-if operations |
| `chain_impacts(*impacts)` | function | Combine multiple `ImpactResult` instances |
| `ImpactResult` | frozen dataclass | Holds `affected`, `broken_relationships`, `resulting_model`, `violations` |
| `ImpactedConcept` | frozen dataclass | Wraps a concept with `depth` and `path` metadata |
| `Violation` | frozen dataclass | Records a permission violation introduced by merge/replace |
| `ImpactResult.by_layer()` | method | Group `affected` by `Layer` enum value |
| `ImpactResult.by_depth()` | method | Group `affected` by traversal depth integer |
| `ImpactResult.to_dict()` | method | Return a JSON-serializable dict representation |

See also: [API Reference — Impact](../api/index.md), [Diffing](diffing.md),
[Validation](validation.md)
