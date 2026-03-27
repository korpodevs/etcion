# ADR-038: Plugin and Extension System (EPIC-025)

## Context

Users may want to extend etcion beyond the ArchiMate 3.2 spec: custom element types, custom relationship types, or custom validation rules. The library already provides several extension mechanisms introduced by earlier epics:

| Mechanism | Epic | What it allows |
|---|---|---|
| `Profile` (specialization names + extended attrs) | EPIC-018 / ADR-030 | Tag elements with domain-specific names; attach extra key-value attributes to existing types |
| Custom `Viewpoint` instances | EPIC-017 / ADR-029 | Restrict which concept types appear in a view; no code changes needed |
| `Association` relationship | EPIC-005 / ADR-017 | Arbitrary directed/undirected linkage between any two concepts |
| `Element` subclassing | -- | Users can subclass `Element` directly; however, the subclass is **not** integrated with `TYPE_REGISTRY` or `_PERMISSION_TABLE` |

EPIC-025 proposes three features: a type registry API (`FEAT-25.1`), custom validation rules (`FEAT-25.2`), and serialization format plugins (`FEAT-25.3`). The question is whether the complexity is justified.

## Decision

**Defer full implementation. Document existing extension points. Add only a minimal registration hook.**

### Rationale (decision table)

| Concern | Full plugin system | Minimal hook + docs | Chosen |
|---|---|---|---|
| Spec compliance risk | High -- custom types bypass Appendix B validation; models become non-portable | Low -- Profiles preserve spec-legal models | Minimal |
| Maintenance burden | High -- cache invalidation, entry-point discovery, plugin lifecycle | Low -- one public function + docstring | Minimal |
| User demand | Speculative (no known requests) | Sufficient for observed patterns | Minimal |
| Interoperability | Custom types cannot round-trip through other ArchiMate tools | Profiles and Associations round-trip via Exchange Format | Minimal |
| Escape hatch exists | -- | Users can already subclass `Element` + mutate `TYPE_REGISTRY` dict directly | Minimal |

### What ships

1. **Document existing extension points** in a user guide section (FEAT-25.1 partially satisfied).
2. **`register_element_type(cls, xml_tag, ...)`** -- a single public function in `etcion.serialization.registry` that:
   - Validates `cls` is a concrete `Element` subclass (has `_type_name`).
   - Adds a `TypeDescriptor` entry to `TYPE_REGISTRY`.
   - Resets `_cache = None` in `etcion.validation.permissions` so the permission table rebuilds on next `is_permitted()` call.
   - Emits a `UserWarning` stating the type is non-standard and models containing it may not be portable.
3. **`register_permission_rule(rule: PermissionRule)`** -- appends to `_PERMISSION_TABLE`, resets `_cache = None`. Same non-portability warning.
4. **`ValidationRule` protocol + `Model.add_validation_rule()`** -- lightweight; no plugin discovery, no entry points. A `Protocol` with `def validate(model) -> list[ValidationError]` is trivial and useful without framework complexity.

### What does NOT ship

| Excluded | Reason |
|---|---|
| `TypeRegistry` as a class (STORY-25.1.1) | `TYPE_REGISTRY` dict + `register_element_type()` function is sufficient |
| `@TypeRegistry.register` decorator (STORY-25.1.2) | Decorators obscure registration order; explicit call preferred |
| `unregister()` (STORY-25.1.3) | YAGNI -- no known use case for runtime type removal |
| `SerializationPlugin` protocol (FEAT-25.3) | Entry-point discovery adds `importlib.metadata` dependency and framework-level complexity for zero known consumers |
| `setuptools` entry-point discovery (STORY-25.3.2) | See above |

### Cache invalidation strategy

Both `register_element_type()` and `register_permission_rule()` set `etcion.validation.permissions._cache = None`. The next `is_permitted()` call triggers `_build_cache()`, which is O(R * S * T) over the permission table -- acceptable for a one-time cost after registration.

`TYPE_REGISTRY` is a plain `dict`; insertion is O(1) with no cache to invalidate.

## Consequences

- **Positive**: Users get a documented, supported path to extend the metamodel without monkey-patching internal dicts. The `ValidationRule` protocol enables custom model checks (e.g., "all elements must have documentation").
- **Positive**: No framework complexity, no entry-point scanning, no plugin lifecycle management.
- **Negative**: Users who want fully custom serialization formats must implement them outside etcion.
- **Negative**: Custom element types will produce Exchange Format XML that other tools may reject.
- **Revisit trigger**: If three or more users request serialization plugins or entry-point discovery, revisit FEAT-25.3.
