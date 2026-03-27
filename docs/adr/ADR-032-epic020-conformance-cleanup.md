# ADR-032: EPIC-020 -- Conformance Cleanup and Phase 3 Public API

## Status

PROPOSED

## Date

2026-03-25

## Context

EPIC-020 is a wiring and cleanup epic. No new domain types, modules, or classes are introduced. The metamodel is complete through EPIC-018 (language customization) and the serialization layer shipped in EPIC-019. What remains is:

1. Two conformance xfails in `test_conformance.py` (`test_viewpoint_mechanism`, `test_language_customization`) that exist only because the implementing types have not yet been exported from `etcion.__init__`.
2. Six deferred-validation xfails across Phase 1 test files (`test_feat052`, `test_feat053`, `test_feat054`, `test_feat058`, `test_feat046`) that were stubbed under ADR-017 ss6 and never rewritten after the validation engine (EPIC-015) shipped.
3. Phase 3 types (`Viewpoint`, `View`, `Concern`, `Profile`, `PurposeCategory`, `ContentCategory`) missing from `__init__.py` exports.
4. The `test_feat012_structure.py::test_functional_outcome` assertion counts are stale.

Prior decisions accepted without re-litigation:

- Exports follow the pattern established in ADR-026 (EPIC-014): domain types added to `__init__.py` imports and `__all__`.
- Serialization functions are NOT exported to `__init__` (ADR-031 Decision 11); users import from `etcion.serialization.xml` / `etcion.serialization.json` directly.
- `TestShouldFeaturesMarkers` currently enforces that ALL methods in `TestShouldFeatures` carry `xfail`. This meta-test must be updated when the xfails are removed.

## Decisions

### 1. Conformance xfail Removal Strategy

| Test | Blocking dependency | Resolution |
|---|---|---|
| `TestShouldFeatures.test_viewpoint_mechanism` | `Viewpoint` not in `etcion.__init__` | Export `Viewpoint` from `viewpoints.py`; remove `xfail` decorator |
| `TestShouldFeatures.test_language_customization` | `Profile` not in `etcion.__init__` | Export `Profile` from `profiles.py`; remove `xfail` decorator |

Both tests assert `hasattr(etcion, "TypeName")`. No behavioral changes are required -- the classes already exist and are fully tested. Once exported, the tests pass as-is.

Consequence: `TestShouldFeaturesMarkers` in `test_feat012_structure.py` must be restructured. It currently asserts that every method in `TestShouldFeatures` has an `xfail` marker. After this epic, zero methods will have `xfail`. The marker class either gains a `_PROMOTED` set (mirroring `TestShallFeaturesMarkers`) or is replaced with assertions that no xfail decorators remain.

### 2. Deferred Validation xfail Disposition

These xfails were created in Phase 1 (ADR-017 ss6) as forward stubs for model-level validation. The validation engine (EPIC-015) has since shipped with its own comprehensive test suite. The disposition depends on whether each stub is now redundant.

| File | xfail test | Action | Rationale |
|---|---|---|---|
| `test_feat052_structural.py` | 2 tests in `TestDeferredValidation` | Rewrite to use `Model.validate()` or remove if covered by `test_feat15x` | FEAT-15.1/15.2 shipped model-level structural validation |
| `test_feat053_serving.py` | 1 test in `TestDeferredValidation` | Same | FEAT-15.1 covers serving direction |
| `test_feat054_access.py` | 1 test in `TestDeferredValidation` | Same | FEAT-15.1 covers access direction |
| `test_feat058_specialization.py` | 1 test in `TestDeferredValidation` | Same | FEAT-15.3 covers same-type constraint |
| `test_feat046_validation.py` | 1 test in `TestPassiveCannotPerformBehavior` | Same | FEAT-15.6 covers passive-structure assignment |

Principle: if an equivalent assertion already exists in the FEAT-15.x test suite, the old stub is deleted outright. If the stub tests a scenario not covered by FEAT-15.x, it is rewritten to construct a `Model`, add concepts, call `model.validate()`, and assert the expected `ValidationError`. No xfail markers survive this epic.

### 3. Phase 3 Exports

| Symbol | Source module | Kind |
|---|---|---|
| `Viewpoint` | `etcion.metamodel.viewpoints` | Class |
| `View` | `etcion.metamodel.viewpoints` | Class |
| `Concern` | `etcion.metamodel.viewpoints` | Class |
| `Profile` | `etcion.metamodel.profiles` | Class |
| `PurposeCategory` | `etcion.enums` | Enum |
| `ContentCategory` | `etcion.enums` | Enum |

These are appended to the existing `__init__.py` imports and `__all__` list, grouped under a `# Phase 3` comment following the established pattern.

Serialization public functions (`serialize_model`, `deserialize_model`, `write_model`, `read_model`, `model_to_dict`, `model_from_dict`) are explicitly excluded from `__init__.py` per ADR-031 Decision 11.

### 4. Outcome Test Update

`test_feat012_structure.py::test_functional_outcome` runs `pytest test/test_conformance.py` as a subprocess and asserts specific pass/xfail/skip counts. Current expectation: `22 passed, 2 xfailed, 1 skipped`. After this epic: all conformance xfails are removed, so the expected output becomes `24 passed, 1 skipped` (the single `@pytest.mark.skip` on `TestMayFeatures.test_example_viewpoints` is unchanged).

The `_PROMOTED` set in `TestShallFeaturesMarkers` is already complete -- all `TestShallFeatures` methods are promoted. No changes needed there.

### 5. No New Modules or Classes

This epic creates no new files under `src/etcion/`. All work is confined to:

- `src/etcion/__init__.py` (import additions)
- `test/test_conformance.py` (xfail removal)
- `test/test_feat012_structure.py` (marker class and outcome count updates)
- `test/test_feat05x` and `test/test_feat046_validation.py` (xfail removal or rewrite)

## Consequences

### Positive

- The conformance test suite reaches full green (zero xfails, zero unexpected failures), providing a clean baseline for any future Phase 4 work.
- All Phase 3 types are discoverable via `etcion.__init__` and IDE autocompletion.
- Eliminating stale xfail stubs removes false confidence -- tests that were silently passing as xfail-strict-false are either confirmed covered or explicitly rewritten.

### Negative

- Deleting old deferred-validation stubs removes historical traceability of the ADR-017 ss6 deferral decision. This is acceptable because ADR-017 itself documents the rationale, and the FEAT-15.x tests now own the validation assertions.
- The `test_functional_outcome` subprocess test is brittle by nature (it asserts exact counts). Any future test additions to `test_conformance.py` will require updating the expected counts again.
