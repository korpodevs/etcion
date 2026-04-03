# Pattern Matching and Gap Analysis

`Pattern` is a fluent builder for structural ArchiMate sub-graph templates.
You describe nodes (typed element placeholders) and edges (typed relationship
constraints), then ask a model whether that structure exists, enumerate every
occurrence of it, or find which elements are missing required connections.

## When to Use Patterns

Use patterns when you need to:

- Check whether a structural combination exists anywhere in a model
- Enumerate every occurrence of a sub-graph template
- Find elements that *should* participate in a pattern but are missing required connections (gap analysis)
- Encode architectural governance rules ("every BusinessService must be backed by an ApplicationService")
- Store and share reusable structural rules as serialized JSON

For simple type or attribute queries without structural constraints, the flat query methods on `Model` (see [Querying](querying.md)) are more direct.

Patterns require the `graph` extra:

```
pip install etcion[graph]
```

---

## Pattern Construction

### `.node()` — registering typed placeholders

Each node in a pattern has a unique string alias and a required element type.
The type can be a concrete class or an abstract base class; matching uses
`issubclass` so a node typed `BehaviorElement` will match any
`BusinessProcess`, `ApplicationFunction`, etc.

```python
from etcion.patterns import Pattern
from etcion.metamodel.business import BusinessActor, BusinessRole
from etcion.metamodel.relationships import Assignment

pattern = Pattern().node("actor", BusinessActor).node("role", BusinessRole)
```

**Exact-match attribute constraints** can be passed as keyword arguments.
Every keyword must be a field name on the element type; an unknown field
raises `ValueError` at definition time.

```python
pattern = Pattern().node("actor", BusinessActor, name="Alice")
```

This is equivalent to a literal equality filter: the pattern only matches
a `BusinessActor` whose `name` field is exactly `"Alice"`.

### `.edge()` — registering directed relationship constraints

An edge constraint binds two already-registered aliases with a relationship
type.  Both aliases must exist; calling `.edge()` before registering either
alias raises `ValueError`.

```python
pattern = (
    Pattern()
    .node("actor", BusinessActor)
    .node("role", BusinessRole)
    .edge("actor", "role", Assignment)
)
```

Direction is significant: the first alias is the source, the second is the
target, matching the `source`/`target` fields on the relationship.

All three methods return `self`, so the entire definition can be written as
a single expression:

```python
from etcion.patterns import Pattern
from etcion.metamodel.business import BusinessActor, BusinessProcess
from etcion.metamodel.relationships import Assignment

pattern = (
    Pattern()
    .node("actor", BusinessActor)
    .node("proc", BusinessProcess)
    .edge("actor", "proc", Assignment)
)
```

Read-only access to the registered structure is available via the `nodes`
and `edges` properties:

```python
pattern.nodes  # {"actor": BusinessActor, "proc": BusinessProcess}
pattern.edges  # [("actor", "proc", Assignment)]
```

---

## Matching Against Models

### `.match()` — enumerate all occurrences

`.match(model)` returns a list of `MatchResult` objects, one per distinct
subgraph match found in the model.  Each `MatchResult` maps pattern aliases
to the actual `Concept` instances from the model.

```python
from etcion.metamodel.model import Model

actor = BusinessActor(name="Alice")
proc  = BusinessProcess(name="OrderFulfillment")
rel   = Assignment(name="r1", source=actor, target=proc)
model = Model(concepts=[actor, proc, rel])

results = pattern.match(model)
print(len(results))          # 1
print(results[0]["actor"])   # <BusinessActor name='Alice'>
print(results[0]["proc"])    # <BusinessProcess name='OrderFulfillment'>
```

The returned concept references are the live model objects, not copies.
`MatchResult` supports item access by alias and `in` containment tests:

```python
match = results[0]
match["actor"]          # BusinessActor
"actor" in match        # True
```

When the same pair of model elements can be reached via multiple graph paths,
the results are deduplicated by the set of matched concept IDs so each unique
combination appears exactly once.

Edge matching uses "at least one" semantics: if a model has both a `Serving`
and an `Association` between the same pair of nodes, a pattern requesting
only `Serving` will still match.

**Abstract base classes in patterns.** The type supplied to `.node()` may be
an ABC.  The pattern below matches any `BehaviorElement` subclass:

```python
from etcion.metamodel.elements import BehaviorElement

broad_pattern = (
    Pattern()
    .node("actor", BusinessActor)
    .node("behavior", BehaviorElement)
    .edge("actor", "behavior", Assignment)
)
results = broad_pattern.match(model)  # matches BusinessProcess, ApplicationFunction, etc.
```

Similarly, a relationship type such as `StructuralRelationship` matches any
concrete structural relationship (`Composition`, `Aggregation`, etc.).

### `.exists()` — fast boolean check

When you only need to know whether the pattern occurs at all, `.exists()`
is more efficient than `.match()` because it short-circuits after the first
match is found:

```python
if pattern.exists(model):
    print("Pattern found")
```

---

## Gap Analysis

### `.gaps()` — find elements missing required connections

`.gaps(model, anchor="alias")` answers the question: "For each element of
the anchor type, does it participate in a full pattern match?"  Elements that
do not appear in any successful match are returned as `GapResult` objects.

The anchor is the alias whose element type determines the candidate set.
Every model element of that type is checked; those absent from all matches
are gaps.

```python
from etcion.patterns import Pattern
from etcion.metamodel.business import BusinessService
from etcion.metamodel.application import ApplicationService
from etcion.metamodel.relationships import Serving
from etcion.metamodel.model import Model

pattern = (
    Pattern()
    .node("bsvc", BusinessService)
    .node("appsvc", ApplicationService)
    .edge("appsvc", "bsvc", Serving)
)

bsvc1   = BusinessService(name="OrderService")
bsvc2   = BusinessService(name="UnbackedService")   # no ApplicationService
appsvc  = ApplicationService(name="OrderApp")
rel     = Serving(name="r1", source=appsvc, target=bsvc1)
model   = Model(concepts=[bsvc1, bsvc2, appsvc, rel])

gaps = pattern.gaps(model, anchor="bsvc")
print(len(gaps))              # 1
print(gaps[0].element.name)   # "UnbackedService"
print(gaps[0].missing)        # ["No Serving edge from any ApplicationService"]
```

`GapResult` is a frozen dataclass with two fields:

| Field | Type | Description |
|---|---|---|
| `element` | `Concept` | The anchor-type element that has no complete match |
| `missing` | `list[str]` | Human-readable descriptions of absent connections |

`.gaps()` returns an empty list when every element of the anchor type
participates in at least one full match, or when the model contains no
elements of that type.

In Jupyter notebooks, `GapResult._repr_html_()` renders a styled summary
block showing the element name and missing connections.

**Implementation note.** Gap analysis uses set subtraction (ADR-042): all
elements of the anchor type are collected, then elements appearing in any
successful `.match()` result are subtracted.  This is O(E + M) where E is
the number of anchor-type elements and M is the number of full matches.
Callers choose which alias to anchor on; the anchor should be the element
type you want to audit.

---

## Cardinality Constraints

Cardinality constraints impose minimum or maximum edge counts on a matched
node, independent of the structural topology.  They are checked as a
post-filter after the isomorphism step.

### `.min_edges()` — require at least N edges

```python
from etcion.metamodel.application import ApplicationComponent
from etcion.metamodel.relationships import Composition

pattern = (
    Pattern()
    .node("comp", ApplicationComponent)
    .min_edges("comp", Composition, count=2, direction="outgoing")
)
```

This pattern matches only `ApplicationComponent` instances that have two or
more outgoing `Composition` relationships.

The `direction` parameter accepts `"incoming"`, `"outgoing"`, or `"any"`
(the default).  `count` defaults to `1`.

### `.max_edges()` — allow at most N edges

```python
pattern = (
    Pattern()
    .node("comp", ApplicationComponent)
    .max_edges("comp", Composition, count=1, direction="outgoing")
)
```

`count` is a required keyword argument for `.max_edges()`.

Cardinality constraints can be combined with structural edges:

```python
from etcion.metamodel.business import BusinessActor
from etcion.metamodel.business import BusinessRole
from etcion.metamodel.relationships import Assignment

# Actor who is assigned to exactly one role — no more, no fewer.
pattern = (
    Pattern()
    .node("actor", BusinessActor)
    .node("role", BusinessRole)
    .edge("actor", "role", Assignment)
    .min_edges("actor", Assignment, count=1, direction="outgoing")
    .max_edges("actor", Assignment, count=1, direction="outgoing")
)
```

---

## Attribute Predicates

### `.where()` — arbitrary lambda predicates

`.where(alias, predicate)` registers a callable `(Concept) -> bool` on a
node alias.  Multiple `.where()` calls on the same alias are ANDed:

```python
pattern = (
    Pattern()
    .node("actor", BusinessActor)
    .where("actor", lambda e: e.name is not None and e.name.startswith("CRM"))
    .where("actor", lambda e: e.description is not None)
)
```

Lambda predicates are evaluated during the isomorphism step: a model node
must pass all registered predicates to be considered a valid match for that
alias.

`.where()` predicates **cannot be serialized** via `.to_dict()`.  When
portability or persistence is required, use `.where_attr()` instead.

### `.where_attr()` — serializable declarative predicates

Introduced in v0.8.0 (ADR-048), `.where_attr()` registers a predicate
as a `(attr_name, operator, value)` triple.  The predicate is fully
serializable and round-trips through `.to_dict()` / `.from_dict()`.

```python
pattern = (
    Pattern()
    .node("service", ApplicationService)
    .where_attr("service", "risk_score", "==", "high")
)
```

**Supported operators:**

| Operator | Semantics |
|---|---|
| `"=="` | equality |
| `"!="` | inequality |
| `"<"` | less than |
| `"<="` | less than or equal |
| `">"` | greater than |
| `">="` | greater than or equal |
| `"in"` | membership in an iterable value |
| `"not_in"` | non-membership in an iterable value |

**Attribute resolution.** At match time the predicate reads
`concept.extended_attributes.get(attr_name)` first.  If the key is absent
from `extended_attributes` it falls back to `getattr(concept, attr_name, None)`,
allowing both profile-level extended attributes and direct model fields to
be targeted.

**Combining with `.where()`.** Both predicate types can be registered on
the same alias.  All predicates — lambda and declarative — are ANDed together:

```python
from etcion.metamodel.application import ApplicationService

pattern = (
    Pattern()
    .node("svc", ApplicationService)
    .where_attr("svc", "risk_score", "==", "high")
    .where_attr("svc", "region", "in", ["EU", "APAC"])
    .where("svc", lambda e: e.description is not None)
)
```

**Membership operators** require the value to be an iterable (e.g. a list):

```python
pattern = (
    Pattern()
    .node("actor", BusinessActor)
    .where_attr("actor", "clearance_level", "not_in", ["PUBLIC", "INTERNAL"])
)
```

---

## Pattern Composition

`.compose(other)` merges two patterns into a new one, combining their nodes,
edges, constraints, predicates, and cardinality.  Neither input is mutated.

```python
actor_pattern = (
    Pattern()
    .node("actor", BusinessActor)
    .node("role", BusinessRole)
    .edge("actor", "role", Assignment)
)

governance_pattern = (
    Pattern()
    .node("actor", BusinessActor)
    .min_edges("actor", Assignment, count=1, direction="outgoing")
)

combined = actor_pattern.compose(governance_pattern)
results = combined.match(model)
```

Shared aliases must map to the same type in both patterns; a type conflict
raises `ValueError`.  When both patterns define constraints or predicates for
the same alias, they are merged (ANDed for predicates, unioned for keyword
constraints).

Composition is useful for building reusable pattern fragments — for example,
a base structural fragment and a separate cardinality or attribute filter —
and assembling them into a complete rule without duplication.

---

## Serialization

Patterns can be serialized to a plain Python dictionary suitable for JSON
encoding and reconstructed from that form.

### `.to_dict()` — serialize a pattern

```python
import json
from etcion.patterns import Pattern
from etcion.metamodel.business import BusinessActor, BusinessProcess
from etcion.metamodel.relationships import Assignment

pattern = (
    Pattern()
    .node("actor", BusinessActor)
    .node("proc", BusinessProcess)
    .edge("actor", "proc", Assignment)
    .where_attr("actor", "cost_centre", "==", "IT-42")
)

data = pattern.to_dict()
print(json.dumps(data, indent=2))
```

The output schema:

```json
{
  "version": 1,
  "nodes": {
    "actor": {
      "type": "BusinessActor",
      "has_lambda_predicates": true
    },
    "proc": {
      "type": "BusinessProcess"
    }
  },
  "edges": [
    { "source": "actor", "target": "proc", "type": "Assignment" }
  ],
  "attr_predicates": [
    { "alias": "actor", "attr_name": "cost_centre", "operator": "==", "value": "IT-42" }
  ]
}
```

Keyword constraints passed to `.node()` are serialized under `"constraints"`.
Cardinality constraints appear in a `"cardinality"` key when present (omitted
when empty).

Lambda predicates registered via `.where()` are **not** serialized.  If a
node has lambda predicates, a `"has_lambda_predicates": true` marker appears
in the node entry so consumers can detect that the deserialized pattern is
not fully equivalent to the original.

### `.from_dict()` — reconstruct a pattern

```python
reconstructed = Pattern.from_dict(data)
results = reconstructed.match(model)
```

`from_dict()` rebuilds nodes, edges, cardinality, and `where_attr` predicates
with full fidelity.  Lambda predicates cannot be reconstructed; re-attach them
manually after loading if required:

```python
reconstructed = Pattern.from_dict(data)
reconstructed.where("actor", lambda e: e.description is not None)
```

Type names in the serialized form are matched against the metamodel type
registry.  An unknown type name raises `ValueError`.

**Round-trip example:**

```python
original = (
    Pattern()
    .node("actor", BusinessActor)
    .where_attr("actor", "region", "in", ["EU", "US"])
)
data = original.to_dict()
restored = Pattern.from_dict(data)

# Both produce the same results on the same model.
assert original.match(model) == restored.match(model)
```

---

## Pattern-Based Validation Rules

Three built-in classes adapt `Pattern` into the `ValidationRule` protocol so
patterns can be registered on a model and run as part of `model.validate()`.

### `PatternValidationRule` — require a pattern to be present

`PatternValidationRule` reports one `ValidationError` when the pattern is
**absent** from the model.  This is the "required structure" rule: the model
must contain at least one instance of the pattern.

```python
from etcion.patterns import Pattern, PatternValidationRule
from etcion.metamodel.business import BusinessActor, BusinessProcess
from etcion.metamodel.relationships import Assignment

pattern = (
    Pattern()
    .node("actor", BusinessActor)
    .node("proc", BusinessProcess)
    .edge("actor", "proc", Assignment)
)

rule = PatternValidationRule(
    pattern=pattern,
    description="Model must contain at least one BusinessActor assigned to a BusinessProcess",
)
model.add_validation_rule(rule)
errors = model.validate()
```

If the pattern exists, `.validate()` returns an empty list.  If it is absent,
a single `ValidationError` whose message is the `description` string is returned.

### `AntiPatternRule` — forbid a pattern

`AntiPatternRule` is the inverse: it reports one `ValidationError` **per
match** when the pattern **is present**.  Use this to enforce "this structure
must never appear":

```python
from etcion.patterns import AntiPatternRule

direct_assign_rule = AntiPatternRule(
    pattern=direct_assign_pattern,
    description="Actors must not be directly assigned to processes — use a Role intermediary",
)
model.add_validation_rule(direct_assign_rule)
errors = model.validate()
# One ValidationError per offending occurrence; each error names the matched elements.
```

Each error message includes the `description` and an `alias=name` summary of
the matched elements, for example:
`"Actors must not be directly assigned to processes (matched: actor=Alice, proc=OrderFulfillment)"`.

### `RequiredPatternRule` — require every element to participate

`RequiredPatternRule` wraps `.gaps()`: every element of the anchor type that
does not participate in a full match produces a separate `ValidationError`.
This is the strongest governance rule: "every X must have Y."

```python
from etcion.patterns import Pattern, RequiredPatternRule
from etcion.metamodel.business import BusinessService
from etcion.metamodel.application import ApplicationService
from etcion.metamodel.relationships import Serving

backing_pattern = (
    Pattern()
    .node("bsvc", BusinessService)
    .node("appsvc", ApplicationService)
    .edge("appsvc", "bsvc", Serving)
)

rule = RequiredPatternRule(
    pattern=backing_pattern,
    anchor="bsvc",
    description="Every BusinessService must be backed by an ApplicationService",
)
model.add_validation_rule(rule)
errors = model.validate()
# One ValidationError per unbacked BusinessService; each error names the element
# and lists its missing connections.
```

The `anchor` must be a registered alias in the pattern; an unknown alias
raises `ValueError` at construction time, not at validate time.

**Combining all three rule types on a single model:**

```python
model.add_validation_rule(PatternValidationRule(
    pattern=required_pattern,
    description="Required pattern A must exist",
))
model.add_validation_rule(AntiPatternRule(
    pattern=forbidden_pattern,
    description="Forbidden pattern B must not exist",
))
model.add_validation_rule(RequiredPatternRule(
    pattern=coverage_pattern,
    anchor="svc",
    description="Every service must satisfy coverage pattern C",
))

errors = model.validate()
```

All three can also be combined with the built-in ArchiMate permission
checker and any custom `ValidationRule` implementations.

---

## Common Patterns

### Application backing for business services

```python
from etcion.patterns import Pattern, RequiredPatternRule
from etcion.metamodel.business import BusinessService
from etcion.metamodel.application import ApplicationService
from etcion.metamodel.relationships import Serving

backing_pattern = (
    Pattern()
    .node("bsvc", BusinessService)
    .node("appsvc", ApplicationService)
    .edge("appsvc", "bsvc", Serving)
)

gaps = backing_pattern.gaps(model, anchor="bsvc")
for gap in gaps:
    print(f"{gap.element.name}: {gap.missing}")
```

### Actor–role–process assignment chain

```python
from etcion.metamodel.business import BusinessActor, BusinessRole, BusinessProcess
from etcion.metamodel.relationships import Assignment

chain = (
    Pattern()
    .node("actor", BusinessActor)
    .node("role", BusinessRole)
    .node("proc", BusinessProcess)
    .edge("actor", "role", Assignment)
    .edge("role", "proc", Assignment)
)

results = chain.match(model)
```

### Broad structural query with ABC

```python
from etcion.metamodel.elements import BehaviorElement
from etcion.metamodel.business import BusinessActor
from etcion.metamodel.relationships import Assignment

# Match any actor-to-behavior assignment regardless of behavior subtype.
any_behavior = (
    Pattern()
    .node("actor", BusinessActor)
    .node("behavior", BehaviorElement)
    .edge("actor", "behavior", Assignment)
)

if any_behavior.exists(model):
    print("Found at least one actor-to-behavior assignment")
```

### Attribute-filtered governance rule

```python
from etcion.patterns import Pattern, RequiredPatternRule
from etcion.metamodel.application import ApplicationService
from etcion.metamodel.technology import TechnologyService
from etcion.metamodel.relationships import Serving

# High-risk ApplicationServices must be served by a TechnologyService.
high_risk_backing = (
    Pattern()
    .node("appsvc", ApplicationService)
    .node("techsvc", TechnologyService)
    .edge("techsvc", "appsvc", Serving)
    .where_attr("appsvc", "risk_score", "==", "high")
)

rule = RequiredPatternRule(
    pattern=high_risk_backing,
    anchor="appsvc",
    description="High-risk ApplicationServices must be backed by a TechnologyService",
)
model.add_validation_rule(rule)
```

---

## API Summary

| Member | Kind | Description |
|---|---|---|
| `Pattern()` | constructor | Create an empty pattern; optionally pass `viewpoint=` to restrict permitted types |
| `.node(alias, type, **constraints)` | method | Register a typed node placeholder |
| `.edge(src, tgt, rel_type)` | method | Register a directed edge constraint |
| `.where(alias, predicate)` | method | Attach an arbitrary lambda predicate to a node |
| `.where_attr(alias, attr, op, value)` | method | Attach a serializable declarative predicate |
| `.min_edges(alias, rel_type, *, count, direction)` | method | Require at least N edges of a given type |
| `.max_edges(alias, rel_type, *, count, direction)` | method | Allow at most N edges of a given type |
| `.compose(other)` | method | Merge two patterns into a new combined pattern |
| `.match(model)` | method | Return all `MatchResult` instances found in the model |
| `.exists(model)` | method | Return `True` if at least one match is found |
| `.gaps(model, *, anchor)` | method | Return `GapResult` for each unmatched anchor-type element |
| `.to_dict()` | method | Serialize to a JSON-compatible dict |
| `Pattern.from_dict(data)` | classmethod | Reconstruct a pattern from a serialized dict |
| `.nodes` | property | Read-only `{alias: type}` dict |
| `.edges` | property | Read-only list of `(src_alias, tgt_alias, rel_type)` tuples |
| `MatchResult` | dataclass | Mapping of alias to matched `Concept`; supports `result["alias"]` |
| `MatchResult.to_dict()` | method | JSON-serializable representation of a single match result |
| `GapResult` | dataclass | Frozen pair of `element` and `missing` descriptions |
| `PatternValidationRule` | class | `ValidationRule` that fails when a pattern is absent |
| `AntiPatternRule` | class | `ValidationRule` that fails when a pattern is present |
| `RequiredPatternRule` | class | `ValidationRule` that calls `.gaps()` and fails per unmatched element |

All pattern and rule classes are importable from `etcion.patterns`.

See also: [Querying](querying.md) · [Validation](validation.md) · [API Reference — Patterns](../api/index.md)
