# Patterns

Sub-graph pattern matching, gap analysis, and model validation rules.

> **User Guide:** [Patterns](../user-guide/patterns.md)

---

## Overview

`etcion.patterns` provides a fluent API for describing typed ArchiMate sub-graph templates and
searching for them inside a `Model`. A `Pattern` declares typed node *aliases* and directed *edges*
between them; calling `Pattern.match()` returns every subgraph in the model that is structurally
compatible with the template.

The module also ships three validation-rule classes — `PatternValidationRule`,
`AntiPatternRule`, and `RequiredPatternRule` — that integrate directly with
`Model.add_validation_rule()`.

Requires the `graph` extra for matching operations:

```
pip install etcion[graph]
```

---

## Classes

### `Pattern`

```python
class Pattern:
    def __init__(self, *, viewpoint: Viewpoint | None = None) -> None
```

Fluent builder for a typed ArchiMate sub-graph pattern.

Nodes (element type placeholders) are registered with `.node()`, directed edge
constraints with `.edge()`.  Optional attribute predicates can be layered on top
with `.where()` (lambda) or `.where_attr()` (declarative/serializable).
Cardinality constraints are added with `.min_edges()` and `.max_edges()`.

**Constructor parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `viewpoint` | `Viewpoint \| None` | `None` | When provided, every node and edge type is validated against the viewpoint's `permitted_concept_types` at definition time. |

**Properties**

| Property | Type | Description |
|----------|------|-------------|
| `nodes` | `dict[str, type]` | Read-only copy of registered alias → element-type mappings. |
| `edges` | `list[tuple[str, str, type]]` | Read-only copy of `(source_alias, target_alias, rel_type)` tuples. |

#### `node`

```python
def node(self, alias: str, element_type: type, **constraints: object) -> Pattern
```

Register a typed node placeholder.

| Parameter | Type | Description |
|-----------|------|-------------|
| `alias` | `str` | Unique identifier for this placeholder within the pattern. |
| `element_type` | `type` | A subclass of `Element` or `RelationshipConnector`. Abstract base classes are accepted for broad matching. |
| `**constraints` | `object` | Optional exact-match attribute constraints (e.g. `name="Alice"`). Keys must be valid field names on `element_type`. |

**Returns** `Pattern` — `self`, for method chaining.

**Raises**

- `ValueError` — if `alias` is already registered, or a constraint key is not a recognised field.
- `TypeError` — if `element_type` is not a subclass of `Element` or `RelationshipConnector`.
- `ValueError` — if `viewpoint` is set and `element_type` is not permitted.

---

#### `edge`

```python
def edge(self, source_alias: str, target_alias: str, rel_type: type) -> Pattern
```

Register a typed directed edge constraint.

| Parameter | Type | Description |
|-----------|------|-------------|
| `source_alias` | `str` | Alias of the source node (must already be registered). |
| `target_alias` | `str` | Alias of the target node (must already be registered). |
| `rel_type` | `type` | A subclass of `Relationship`. |

**Returns** `Pattern` — `self`, for method chaining.

**Raises**

- `ValueError` — if either alias is not registered.
- `TypeError` — if `rel_type` is not a subclass of `Relationship`.
- `ValueError` — if `viewpoint` is set and `rel_type` is not permitted.

---

#### `where`

```python
def where(self, alias: str, predicate: Callable[[Concept], bool]) -> Pattern
```

Register an arbitrary predicate filter for a pattern node.

Multiple `where` calls on the same alias are ANDed together.

| Parameter | Type | Description |
|-----------|------|-------------|
| `alias` | `str` | The alias to constrain. Must already be registered. |
| `predicate` | `Callable[[Concept], bool]` | Returns `True` to allow a match. |

**Returns** `Pattern` — `self`, for method chaining.

**Raises** `ValueError` — if `alias` is not registered.

!!! note
    Lambda predicates are **not** included when serializing via `to_dict()`.
    Reattach them manually after `from_dict()`.

---

#### `where_attr`

```python
def where_attr(
    self,
    alias: str,
    attr_name: str,
    operator: str,
    value: object,
) -> Pattern
```

Register a declarative, serializable predicate for a pattern node.

Unlike `where`, this encodes the predicate as a `(attr_name, operator, value)` triple
that round-trips through `to_dict()` / `from_dict()`.

At match time, `concept.extended_attributes.get(attr_name)` is checked first,
falling back to `getattr(concept, attr_name, None)`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `alias` | `str` | The alias to constrain. Must already be registered. |
| `attr_name` | `str` | Name of the attribute to compare. |
| `operator` | `str` | One of `"=="`, `"!="`, `"<"`, `"<="`, `">"`, `">="`, `"in"`, `"not_in"`. |
| `value` | `object` | Value to compare against. For `"in"` / `"not_in"`, must be an iterable. |

**Returns** `Pattern` — `self`, for method chaining.

**Raises** `ValueError` — if `alias` is not registered or `operator` is not supported.

---

#### `min_edges`

```python
def min_edges(
    self,
    alias: str,
    rel_type: type,
    *,
    count: int = 1,
    direction: str = "any",
) -> Pattern
```

Require at least `count` edges of `rel_type` on the node bound to `alias`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `alias` | `str` | | The alias to constrain. |
| `rel_type` | `type` | | A subclass of `Relationship` to count. |
| `count` | `int` | `1` | Minimum number of edges required (inclusive). |
| `direction` | `str` | `"any"` | `"incoming"`, `"outgoing"`, or `"any"`. |

**Returns** `Pattern` — `self`, for method chaining.

**Raises** `ValueError` — if `alias` is not registered.

---

#### `max_edges`

```python
def max_edges(
    self,
    alias: str,
    rel_type: type,
    *,
    count: int,
    direction: str = "any",
) -> Pattern
```

Require at most `count` edges of `rel_type` on the node bound to `alias`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `alias` | `str` | | The alias to constrain. |
| `rel_type` | `type` | | A subclass of `Relationship` to count. |
| `count` | `int` | | Maximum number of edges allowed (inclusive). |
| `direction` | `str` | `"any"` | `"incoming"`, `"outgoing"`, or `"any"`. |

**Returns** `Pattern` — `self`, for method chaining.

**Raises** `ValueError` — if `alias` is not registered.

---

#### `compose`

```python
def compose(self, other: Pattern) -> Pattern
```

Return a new `Pattern` that is the union of `self` and `other`.

Nodes, edges, keyword constraints, predicates, and cardinality are all merged.
Shared aliases must map to the same type in both patterns.
Neither input pattern is mutated.

| Parameter | Type | Description |
|-----------|------|-------------|
| `other` | `Pattern` | The second pattern to merge with this one. |

**Returns** `Pattern` — a new combined pattern.

**Raises** `ValueError` — if a shared alias maps to different types in the two patterns.

---

#### `match`

```python
def match(self, model: Model) -> list[MatchResult]
```

Find all subgraph matches of this pattern within `model`.

Uses `networkx.algorithms.isomorphism.DiGraphMatcher` with subgraph monomorphism
semantics (`>=` edge-count). Returned `MatchResult` objects map pattern aliases to
the *actual* `Concept` instances from the model (identity-preserving, not copies).
Duplicate mappings (same set of matched concept IDs) are deduplicated.

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `Model` | The model to search. |

**Returns** `list[MatchResult]` — one entry per distinct subgraph match, or an empty list.

**Raises** `ImportError` — if `networkx` is not installed.

---

#### `exists`

```python
def exists(self, model: Model) -> bool
```

Return `True` if this pattern matches at least one subgraph in `model`.

Short-circuits on the first match found.

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `Model` | The model to search. |

**Returns** `bool`.

**Raises** `ImportError` — if `networkx` is not installed.

---

#### `gaps`

```python
def gaps(self, model: Model, *, anchor: str) -> list[GapResult]
```

Find elements of the anchor type that are missing required connections.

All elements of the anchor type are collected from `model`. Elements that appear in
at least one successful `match()` are subtracted; the remainder are "gaps." For each
gap element, missing connection descriptions are generated by inspecting edge
constraints and cardinality rules.

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `Model` | The model to search. |
| `anchor` | `str` | Pattern alias whose element type determines the candidate set. |

**Returns** `list[GapResult]` — one entry per unmatched element, empty when all participate.

**Raises**

- `ValueError` — if `anchor` is not a registered alias.
- `ImportError` — if `networkx` is not installed.

---

#### `to_networkx`

```python
def to_networkx(self) -> networkx.MultiDiGraph
```

Convert this pattern to a `networkx.MultiDiGraph`.

Node attributes: `type` (Python class), `constraints` (dict), `predicates` (list of callables).
Edge attributes: `type` (relationship class).

The attribute schema mirrors `Model.to_networkx()` so that `GraphMatcher` callbacks
use identical attribute access on both graphs.

**Returns** `networkx.MultiDiGraph`.

**Raises** `ImportError` — if `networkx` is not installed.

---

#### `to_dict`

```python
def to_dict(self) -> dict[str, Any]
```

Serialize this pattern to a plain Python dict suitable for JSON encoding.

Lambda predicates registered via `where()` are **not** included. Declarative
predicates from `where_attr()` are included under the `"attr_predicates"` key.

**Returns** `dict[str, Any]` with keys `"version"`, `"nodes"`, `"edges"`,
and optionally `"cardinality"` and `"attr_predicates"`.

---

#### `from_dict`

```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> Pattern
```

Reconstruct a `Pattern` from a dict produced by `to_dict()`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict[str, Any]` | A dict with the schema emitted by `to_dict()`. |

**Returns** `Pattern`.

**Raises** `ValueError` — if a type name in `data` is not found in the metamodel type registry,
or an alias referenced in `attr_predicates` is not declared in `nodes`.

---

### `MatchResult`

```python
@dataclass(frozen=True)
class MatchResult:
    mapping: dict[str, Concept]
```

A single subgraph match produced by `Pattern.match()`.

Stores a `{alias: concept}` mapping. Concept references are identity-preserving (not copies).

| Attribute | Type | Description |
|-----------|------|-------------|
| `mapping` | `dict[str, Concept]` | Maps each pattern alias to the matched `Concept` instance. |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `__getitem__` | `(alias: str) -> Concept` | Return the concept bound to `alias`. Raises `KeyError` if absent. |
| `__contains__` | `(alias: object) -> bool` | `True` if `alias` is present. |
| `to_dict` | `() -> dict[str, Any]` | JSON-serializable representation. Includes `_schema_version: "1.0"` per ADR-046. |

---

### `GapResult`

```python
@dataclass(frozen=True)
class GapResult:
    element: Concept
    missing: list[str]
```

An element that should participate in a pattern but is missing required connections.

| Attribute | Type | Description |
|-----------|------|-------------|
| `element` | `Concept` | The anchor-position concept that has no complete match. |
| `missing` | `list[str]` | Human-readable descriptions of absent connections (e.g. `"No Serving edge to any ApplicationService"`). |

---

### `CardinalityConstraint`

```python
@dataclass(frozen=True)
class CardinalityConstraint:
    alias: str
    rel_type: type
    min_count: int | None = None
    max_count: int | None = None
    direction: str = "any"
```

Specifies a minimum or maximum edge count for a pattern node.

Created internally by `Pattern.min_edges()` and `Pattern.max_edges()`.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `alias` | `str` | | Pattern alias of the node to constrain. |
| `rel_type` | `type` | | `Relationship` subclass to count. |
| `min_count` | `int \| None` | `None` | Minimum edges required (inclusive). `None` = no lower bound. |
| `max_count` | `int \| None` | `None` | Maximum edges allowed (inclusive). `None` = no upper bound. |
| `direction` | `str` | `"any"` | `"incoming"`, `"outgoing"`, or `"any"`. |

---

### `PatternValidationRule`

```python
class PatternValidationRule:
    def __init__(self, pattern: Pattern, description: str) -> None
```

Adapter that registers a `Pattern` as a `Model` validation rule.

When `validate()` is called, it checks whether the pattern *exists* in the model.
If not found, returns a single `ValidationError` with the provided description.

| Parameter | Type | Description |
|-----------|------|-------------|
| `pattern` | `Pattern` | The pattern to check for presence. |
| `description` | `str` | Error message when the pattern is absent. |

#### `validate`

```python
def validate(self, model: Model) -> list[ValidationError]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `Model` | The model to inspect. |

**Returns** `list[ValidationError]` — empty if the pattern is found; a single-element list otherwise.

---

### `AntiPatternRule`

```python
class AntiPatternRule:
    def __init__(self, pattern: Pattern, description: str) -> None
```

Validation rule that fails when the pattern **is** found in the model.

Each match produces a separate `ValidationError` whose message includes `description`
and the names of the offending elements.

| Parameter | Type | Description |
|-----------|------|-------------|
| `pattern` | `Pattern` | The pattern whose presence is forbidden. |
| `description` | `str` | Error message included in every error raised. |

#### `validate`

```python
def validate(self, model: Model) -> list[ValidationError]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `Model` | The model to inspect. |

**Returns** `list[ValidationError]` — empty when the anti-pattern is absent; one error per match otherwise.

---

### `RequiredPatternRule`

```python
class RequiredPatternRule:
    def __init__(self, pattern: Pattern, *, anchor: str, description: str) -> None
```

Validation rule requiring every element of the anchor type to participate in the pattern.

Wraps `Pattern.gaps()` — each gap element becomes a `ValidationError`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `pattern` | `Pattern` | The pattern that each anchor-type element must satisfy. |
| `anchor` | `str` | Alias of the pattern node whose element type is the candidate set. |
| `description` | `str` | Error message prefix for each gap element. |

**Raises** `ValueError` — at construction time if `anchor` is not a registered alias in `pattern`.

#### `validate`

```python
def validate(self, model: Model) -> list[ValidationError]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `Model` | The model to inspect. |

**Returns** `list[ValidationError]` — empty when every anchor-type element participates in a match; one error per gap element otherwise.

---

## Example

```python
from etcion.metamodel.business import BusinessActor, BusinessRole
from etcion.metamodel.relationships import Assignment
from etcion.patterns import Pattern, RequiredPatternRule

pattern = (
    Pattern()
    .node("actor", BusinessActor)
    .node("role", BusinessRole)
    .edge("actor", "role", Assignment)
)

# Find all matches
matches = pattern.match(model)
for m in matches:
    print(m["actor"].name, "->", m["role"].name)

# Governance: every actor must have an assignment
rule = RequiredPatternRule(
    pattern=pattern,
    anchor="actor",
    description="Every BusinessActor must be assigned to a role",
)
model.add_validation_rule(rule)
errors = model.validate()
```
