# ADR-004: Conformance Test Suite

## Status

ACCEPTED

## Date

2026-03-23

## Context

ADR-003 establishes `ConformanceProfile` as the library's machine-readable declaration of which ArchiMate 3.2 features it commits to implementing. However, a declaration without verification is meaningless. `CONFORMANCE.business_elements = True` is only credible if there is a test that checks whether the public API actually exports the types that constitute Business layer elements.

A dedicated conformance test file is needed, separate from the unit tests that will accompany each epic's implementation, for two reasons:

1. **Specification-level tests vs. implementation-level tests**: Unit tests for EPIC-002 will verify that `BusinessActor` can be instantiated, has the correct fields, and validates correctly. Conformance tests verify a higher-level invariant: "the library exports a type called `BusinessActor` that is accessible via `etcion.BusinessActor`." These are different concerns. A conformance test can be written today (before `BusinessActor` exists) and will fail until EPIC-002 is complete. A unit test cannot be written until the class exists.
2. **Living specification**: The conformance test file serves as an executable specification of the ArchiMate 3.2 standard's requirements on the library. Reading `test/test_conformance.py` tells a contributor exactly what public API surface the library must expose to be conformant.

The phasing problem is central to this decision. Most `shall`-level features will not be implemented until EPIC-002 through EPIC-005. The conformance tests must be structured so that:

- They exist now (FEAT-01.2), documenting the full scope of required features.
- They fail gracefully now, without blocking CI or making the test suite appear broken.
- They transition to hard failures (or passes) as each epic is completed.

This requires careful use of pytest markers to distinguish between tests that should pass now, tests that are expected to fail now but will pass later, and tests that are intentionally skipped.

## Decision

### Test File Location

All conformance tests live in `test/test_conformance.py`. This is a single file, not a sub-directory, because conformance tests are assertion-only checks (no complex fixtures, no parameterization) that together total fewer than 200 lines.

### Test Structure: Three Test Classes

The file is organized into three test classes, one per conformance level:

1. **`TestConformanceProfile`** -- Verifies the `CONFORMANCE` singleton itself: correct attribute values, correct types, frozen immutability. These tests pass immediately once FEAT-01.1 (`conformance.py`) is implemented.

2. **`TestShallFeatures`** -- One test function per `shall`-level conformance attribute. Each test checks that the public API members required by that feature exist. For example, `test_business_elements` asserts that `etcion.BusinessActor`, `etcion.BusinessRole`, etc. are importable.

3. **`TestShouldFeatures`** -- Tests for `should`-level features (viewpoint mechanism, language customization).

4. **`TestMayFeatures`** -- Tests for `may`-level features (Appendix C example viewpoints).

### `shall`-Level Tests: Direct Assertions, `xfail` Until Implemented

Each `shall`-level test performs direct attribute existence checks:

```python
@pytest.mark.xfail(reason="EPIC-002: Business layer elements not yet implemented", strict=False)
def test_business_elements(self) -> None:
    assert hasattr(etcion, "BusinessActor")
    assert hasattr(etcion, "BusinessRole")
    assert hasattr(etcion, "BusinessCollaboration")
    # ... all Business layer types
```

The `pytest.mark.xfail(strict=False)` marker is the correct mechanism:

- When the feature is absent, the test is an **expected failure (xfail)** -- it appears in the test report as `x` (expected failure), not `F` (failure). It does not block CI.
- When the feature is implemented, the test passes and appears as `X` (unexpected pass, also called xpass). With `strict=False`, this is not an error -- the test simply transitions from expected-fail to pass.
- The `reason` string documents which epic will implement the feature, making the test report self-explanatory.

The alternative of using `strict=True` was rejected because it would cause the test to fail when the feature IS implemented (xpass becomes an error with strict=True), requiring a manual marker removal step. `strict=False` allows the transition to happen automatically.

### `should`-Level Tests: `xfail` with Phase 2 Reason

`should`-level features (viewpoint mechanism, language customization) use the same `xfail(strict=False)` pattern with reason strings indicating Phase 2 targeting:

```python
@pytest.mark.xfail(reason="Phase 2: Viewpoint mechanism not yet implemented", strict=False)
def test_viewpoint_mechanism(self) -> None:
    assert hasattr(etcion, "Viewpoint")
```

Using `pytest.warns(UserWarning)` was explicitly rejected. `pytest.warns` is designed to test that code emits Python `warnings.warn()` calls. It is not a mechanism for marking tests as "recommended but not required." The `should`/`may` distinction is about the test's importance to the project, not about runtime warning behavior.

### `may`-Level Tests: `skip`

`may`-level features use `pytest.mark.skip(reason="...")`:

```python
@pytest.mark.skip(reason="Appendix C example viewpoints are out of scope")
def test_example_viewpoints(self) -> None:
    assert hasattr(etcion, "BasicViewpoint")
```

`skip` is chosen over `xfail` because these features are not planned. They should not appear as expected failures in the test report (which implies they will eventually pass). `skip` communicates "this is documented but intentionally not implemented."

### Test Naming Convention

Test function names follow the pattern `test_<conformance_attribute>` to create a one-to-one mapping between `ConformanceProfile` fields and test functions. This makes CI output self-explanatory:

```
test_conformance.py::TestShallFeatures::test_language_structure    XFAIL
test_conformance.py::TestShallFeatures::test_business_elements     XFAIL
test_conformance.py::TestConformanceProfile::test_shall_defaults   PASSED
```

### `TestConformanceProfile` Assertions

This class verifies the `CONFORMANCE` object itself, independent of whether implementing code exists:

- All `shall`-level fields are `True`.
- All `should`-level fields are `True`.
- `example_viewpoints` (the sole `may` field) is `False`.
- `spec_version` equals `"3.2"`.
- `spec_version` equals `etcion.SPEC_VERSION` (consistency check).
- The dataclass is frozen: assigning to any field raises `FrozenInstanceError`.

These tests pass as soon as FEAT-01.1 is implemented and remain green permanently.

### Marker Removal Policy

When an epic is completed and all types for a `shall`-level feature are exported from `etcion.__init__`, the implementer must remove the `xfail` marker from the corresponding conformance test. This is documented as a checklist item in each epic's definition of done. Forgetting to remove the marker is harmless (`strict=False` tolerates xpass), but the marker should be removed for test report clarity.

## Alternatives Considered

### `pytest.warns` for `should`-Level Tests

Using `pytest.warns(UserWarning)` to check that the library emits a warning when a `should`-level feature is accessed but not implemented. This was rejected because:

1. `pytest.warns` tests runtime behavior of code that emits `warnings.warn()`. It does not test feature presence or absence.
2. It would require the library to actively detect and warn about missing features, adding runtime overhead and complexity for a marginal benefit.
3. The `should` compliance level is a property of the specification, not a runtime condition. Encoding it as a pytest marker is the correct abstraction.

### Custom `@conformance_check` Decorator

A custom decorator that wraps test functions with compliance-level metadata and custom reporting. This was rejected because:

1. It adds framework code that must be maintained, tested, and documented.
2. `pytest.mark.xfail` and `pytest.mark.skip` are standard, well-understood mechanisms that achieve the same result with zero custom code.
3. Contributors do not need to learn a custom API; they already know pytest markers.

### Separate Test Files per Compliance Level

Splitting into `test/test_conformance_shall.py`, `test/test_conformance_should.py`, and `test/test_conformance_may.py`. This was rejected because the total test count is small (approximately 20 test functions) and the class-based grouping within a single file provides sufficient organization. Three files would scatter related tests without adding navigational benefit.

### Parametrized Tests with a Feature Registry

Using `@pytest.mark.parametrize` with a list of `(feature_name, expected_types)` tuples instead of individual test functions. This was rejected because:

1. Parametrized tests produce less readable failure messages: `test_feature[business_elements]` is less informative than `test_business_elements` with a descriptive docstring listing the expected types.
2. Each feature has a different set of assertions (different types to check), making the parametrize fixture awkward: the test body would need a dispatch table or conditional logic.
3. Individual test functions allow per-feature `xfail` reasons referencing different epics.

## Consequences

### Positive

- **Living specification**: The test file is an executable document of ArchiMate 3.2 conformance requirements. Reading it tells a contributor exactly what the library must export.
- **CI-safe from day one**: `xfail(strict=False)` and `skip` markers ensure the test suite is green even before implementing epics, while still documenting the full scope of required work.
- **Automatic transition**: As each epic is completed, conformance tests silently transition from `xfail` to `pass` without requiring test code changes (though marker cleanup is recommended).
- **Self-explanatory CI output**: Test names map directly to `ConformanceProfile` attributes, and `xfail` reason strings reference the implementing epic. A CI failure report immediately tells the reader which spec requirement is unfulfilled and which epic is responsible.
- **No custom framework**: The entire strategy uses standard pytest markers, requiring zero custom test infrastructure.

### Negative

- **`xfail` marker maintenance**: Each conformance test starts with an `xfail` marker that should be removed when the implementing epic is complete. If markers are not cleaned up, the test report shows `XPASS` instead of `PASSED`, which is noisy but not harmful. Mitigated by including marker removal in each epic's definition of done.
- **Tests are assertion-only, not behavioral**: Conformance tests check that types exist (`hasattr`), not that they behave correctly. A conformance test will pass if `etcion.BusinessActor` is a re-exported class, even if that class has no fields or validation. Behavioral correctness is the responsibility of each epic's unit tests, not the conformance suite.
- **Tight coupling to `__init__.py` exports**: Conformance tests assert against `etcion.<TypeName>`, meaning every conformance-required type must be re-exported from `__init__.py`. This is intentional (the public API surface IS the conformance surface), but it means the `__init__.py` re-export list must grow in lockstep with implementation.

## Compliance

This ADR provides the architectural rationale for each story in FEAT-01.2:

| Story | Decision Implemented |
|---|---|
| STORY-01.2.1 | `test/test_conformance.py` with `TestShallFeatures` class; one `xfail` test per `shall`-level attribute asserting public API type existence |
| STORY-01.2.2 | `TestShouldFeatures` class with `xfail(strict=False)` markers referencing Phase 2; `pytest.warns` explicitly rejected |
| STORY-01.2.3 | `TestMayFeatures` class with `pytest.mark.skip`; skipped tests do not cause failure when features are absent |
