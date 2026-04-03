# ADR-048: Serializable Pattern Predicates via Pattern.where_attr()

**Status:** ACCEPTED
**Date:** 2026-04-02
**Scope:** Pattern predicate vocabulary, serialization contract, and Pattern.to_dict()/from_dict() extension — GitHub Issue #53

## Context

`Pattern.where()` accepts arbitrary Python lambdas for attribute-level filtering.
Lambdas are powerful but opaque: they cannot be stored in a rule repository,
written to a configuration file, transmitted over the wire, or reconstructed
from a serialized form.

The most common predicate types — equality, comparison, and membership tests
against `extended_attributes` values — follow a regular structure that can be
expressed declaratively as `(attr_name, operator, value)` triples.

Issue #53 requires a `where_attr()` method that captures these common predicates
in a serializable form while leaving complex, bespoke logic as lambda-only via
the existing `.where()`.

### Constraints from issue discussion

- **Patterns are analytical instruments**, not model data.  Pattern
  serialization must be independent of model serialization (model_to_dict /
  serialize_model) and must never be embedded in model persistence.
- The serialized form is intended for rule repositories, audit logs, and
  configuration files only.
- Full round-trip fidelity is required for `where_attr` predicates only.
  Lambda predicates registered via `.where()` are excluded from serialization
  with a marker in `to_dict()` output (but no warning at call time, as the
  warning would fire at every `to_dict()` call for patterns that intentionally
  mix both styles).

## Decision

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Add `Pattern.where_attr(alias, attr_name, operator, value)` that registers a declarative predicate in a new `_attr_predicates` dict, separate from the existing `_predicates` dict of lambdas. | Keeps the two kinds of predicates structurally distinct, making serialization straightforward without inspecting callables. |
| 2 | Supported operators: `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not_in` (8 total). | Covers the declared acceptance criteria and mirrors the most common filter patterns found in rule repositories. `in`/`not_in` test membership in an iterable value. |
| 3 | `where_attr` predicates are evaluated in `_build_matcher` as part of the same `predicates` list delivered to the `node_match` callback, ANDed with any lambda predicates on the same alias. | Uniform execution path; no changes to the subgraph-isomorphism core. |
| 4 | `to_dict()` includes a new top-level `"attr_predicates"` key serializing every `where_attr` predicate as `{"alias", "attr_name", "operator", "value"}` dicts. Lambda predicates are indicated by a `"has_lambda_predicates"` marker key per node in the `"nodes"` section. | Consumers can detect whether a deserialized pattern is fully reconstructable or has opaque predicates. |
| 5 | `from_dict()` reconstructs `where_attr` predicates via `where_attr()` calls.  Lambda predicates cannot be reconstructed; the `has_lambda_predicates` marker is silently ignored during reconstruction (the caller is responsible for re-attaching lambdas). | Consistent with the existing docstring note; no silent data loss. |
| 6 | `AttrPredicate` is introduced as a `dataclass(frozen=True)` holding `(alias, attr_name, operator, value)`.  It is not part of the public API surface (`__all__` is not extended); it is an implementation detail supporting serialization. | Keeps the public API minimal; `where_attr()` is the only new public method. |
| 7 | Predicate evaluation reads `concept.extended_attributes.get(attr_name)` (consistent with the existing example in issue #53 and in `model.py`), but also falls back to `getattr(concept, attr_name, None)` so that direct model fields can also be targeted. | Flexible without surprising the majority case. |
| 8 | Pattern serialization is standalone (`Pattern.to_dict()` / `Pattern.from_dict()`). It is never called by the model serialization layer. | Enforces the "analytical instrument" separation required by the issue discussion. |

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|-----------------|
| Extend `.where()` to accept a tuple `(attr, op, value)` in addition to callables | Overloads a single method with two unrelated signatures; type-checker cannot distinguish the two modes; makes the serializable path implicit rather than explicit. |
| Store `where_attr` predicates as lambda wrappers in `_predicates` with a side-channel dict for serialization | Doubles the storage; predicates would fire twice; keeping two data structures in sync is fragile. |
| Use `operator` module functions as the serialized form | `operator.eq` etc. cannot round-trip through JSON without an eval()-based registry, which is a security concern. |
| Add a `PredicateSpec` union type accepted by `.where()` | Pydantic-style over-engineering for a method that currently accepts a plain callable; introduces a new public type for a simple feature. |
| Emit a runtime `warnings.warn` on every `to_dict()` call when lambda predicates are present | Would fire in every round-trip test and in interactive usage even when the caller is fully aware of the limitation; a structural marker is sufficient. |

## Consequences

- **Positive**: The most common predicate types are now portable — they can be stored in JSON rule repositories and reconstructed with full fidelity.
- **Positive**: `where_attr` and `where` compose naturally; a single node can have both, all ANDed together.
- **Positive**: No breaking changes to the existing `.where()` API or to `to_dict()`/`from_dict()` consumers (the new keys are additive).
- **Negative**: Patterns that mix lambda and `where_attr` predicates are only partially serializable.  The `has_lambda_predicates` marker signals this but does not prevent information loss.
- **Negative**: `where_attr` currently targets `extended_attributes` or direct fields only; computed/derived attributes require a lambda via `.where()`.
