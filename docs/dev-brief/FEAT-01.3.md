# Technical Brief: FEAT-01.3 Undefined Type Guard

**Status:** Ready for Implementation
**ADR Link:** `docs/adr/ADR-005-undefined-type-guard.md`
**Epic:** EPIC-001 -- Scope and Conformance
**Date:** 2026-03-23

---

## 1. Feature Summary

FEAT-01.3 is primarily a design decision (codified in ADR-005) plus placeholder tests, with the actual guard implementation deferred to EPIC-002. The feature establishes that undefined ArchiMate types are prevented by two mechanisms: Python's own type system (attempting to instantiate a non-existent class raises `NameError`) and `Model.add()` input validation (passing a non-`Concept` object raises `TypeError`). Since neither `Model` nor `Concept` exist yet, FEAT-01.3 delivers the ADR and `xfail`-marked tests that will transition to passing once EPIC-002 implements the `Model` container and `Concept` abstract base class.

---

## 2. Story-by-Story Implementation Guide

### STORY-01.3.1: Implement guard logic so that attempting to use an undefined element type raises an error

**Files to create:** None.

**Action:** Verify that ADR-005 (`docs/adr/ADR-005-undefined-type-guard.md`) exists and documents the guard design. The guard logic itself is specified for the EPIC-002 implementer:

- **Primary guard:** Python's type system. `BusinessWidget(name="test")` raises `NameError` because the class does not exist. No library code is needed for this.
- **Secondary guard:** `Model.add()` performs `isinstance(concept, Concept)` and raises `TypeError` for non-Concept arguments. This is implemented in EPIC-002 FEAT-02.6.

The developer's action for this story is to:
1. Confirm ADR-005 exists at `docs/adr/ADR-005-undefined-type-guard.md`.
2. Ensure the EPIC-002 backlog references ADR-005 in the definition of done for FEAT-02.6.

**Acceptance Criteria:**
- ADR-005 exists and has status `ACCEPTED`.
- ADR-005 specifies `TypeError` (not `ValidationError`, not `ConformanceError`) as the exception for non-Concept arguments.
- ADR-005 specifies `isinstance(concept, Concept)` as the guard mechanism.
- No new source files are created.

**Gotchas:**
- Do NOT create a `guards.py` module. ADR-005 explicitly rejects this approach.
- Do NOT create a string-based type registry. ADR-005 explicitly rejects this approach.
- Do NOT use `__init_subclass__` for type registration. ADR-005 explicitly rejects this approach.

---

### STORY-01.3.2: Write tests confirming that fabricated/undefined element type names raise errors

**Files to modify:**
- `/home/kiera/dev/pyarchi/test/test_conformance.py` (append `TestUndefinedTypeGuard` class)

**Content:** See Section 3 below for the class to append.

**Acceptance Criteria:**
- `TestUndefinedTypeGuard` class exists in `test/test_conformance.py`.
- Three test methods, all decorated with `@pytest.mark.xfail(strict=False, reason="EPIC-002: Model not yet implemented")`.
- `pytest test/test_conformance.py -v -k "TestUndefinedTypeGuard"` shows all 3 tests as `x` (expected failure).
- No test causes an unexpected `FAILED` result (xfail absorbs the `AttributeError` that occurs because `pyarchi.Model` does not exist).

**Gotchas:**
- Since `pyarchi.Model` does not exist yet, these tests will fail with `AttributeError` (not `TypeError`). With `xfail(strict=False)`, any failure mode counts as an expected failure, so this is correct behavior.
- When EPIC-002 implements `Model` and `Concept`, the tests will start raising `TypeError` from `Model.add()`, at which point the `pytest.raises(TypeError)` context manager will catch it and the tests will pass. With `strict=False`, the transition from xfail to xpass is silent.
- The tests use `pyarchi.Model()` directly (not `from pyarchi import Model`) because the import would fail at collection time. Accessing via `pyarchi.Model` defers the failure to runtime inside the test body, where xfail can catch it.

---

## 3. Addition to `test/test_conformance.py`

Append the following class to the end of `test/test_conformance.py`:

```python
# ---------------------------------------------------------------------------
# TestUndefinedTypeGuard -- xfail until EPIC-002 implements Model + Concept
# ---------------------------------------------------------------------------


class TestUndefinedTypeGuard:
    """Verify that Model.add() rejects non-Concept arguments with TypeError.

    These tests are specified by ADR-005 and will pass once EPIC-002
    implements the Model container (FEAT-02.6) and Concept ABC (FEAT-02.1).
    Until then, they fail with AttributeError (pyarchi.Model does not exist)
    which is absorbed by the xfail marker.
    """

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-002: Model not yet implemented",
    )
    def test_dict_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            pyarchi.Model().add({})  # type: ignore[attr-defined]

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-002: Model not yet implemented",
    )
    def test_arbitrary_object_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            pyarchi.Model().add(object())  # type: ignore[attr-defined]

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-002: Model not yet implemented",
    )
    def test_non_concept_class_raises_type_error(self) -> None:
        class Fake:
            pass

        with pytest.raises(TypeError):
            pyarchi.Model().add(Fake())  # type: ignore[attr-defined]
```

---

## 4. Note for EPIC-002 Implementer

> **IMPORTANT: Contract for `Model.add()` (FEAT-02.6)**
>
> The following tests in `test/test_conformance.py::TestUndefinedTypeGuard`
> are `xfail` and waiting for your implementation. To make them pass,
> `Model.add()` must satisfy these exact requirements:
>
> 1. **Accept** any instance of `Concept` (or any subclass of `Concept`)
>    without raising an error.
>
> 2. **Raise `TypeError`** (not `ValidationError`, not `ConformanceError`,
>    not `NotImplementedError`) when the argument is not an instance of
>    `Concept`.
>
> 3. **Include `type(concept).__name__`** in the error message so the user
>    can identify the rejected type. Example:
>    ```
>    TypeError: Expected an instance of Concept, got dict
>    ```
>
> 4. **Use `isinstance(concept, Concept)`** as the guard check. Do not use
>    a string registry, a set of registered types, or `__init_subclass__`
>    tracking.
>
> Reference: `docs/adr/ADR-005-undefined-type-guard.md`
>
> Once `Model.add()` is implemented:
> - Remove the `xfail` markers from all three `TestUndefinedTypeGuard` tests.
> - Remove the `# type: ignore[attr-defined]` comments.
> - Add a fourth test: `test_valid_concept_is_accepted` that creates a
>   concrete `Concept` subclass instance and verifies `Model.add()` does
>   not raise.

---

## 5. Verification Checklist

Run these commands sequentially from the repository root after completing both stories. Every command must exit with code 0.

```bash
# 0. Activate the virtual environment
source .venv/bin/activate

# 1. Verify ADR-005 exists
test -f docs/adr/ADR-005-undefined-type-guard.md && echo "OK: ADR-005 exists"

# 2. Verify TestUndefinedTypeGuard class exists in test file
grep -q "class TestUndefinedTypeGuard" test/test_conformance.py && echo "OK: class exists"

# 3. Run the guard tests -- expect all 3 to xfail
pytest test/test_conformance.py -v -k "TestUndefinedTypeGuard"

# 4. Verify no guards.py module was created
test ! -f src/pyarchi/guards.py && echo "OK: no guards.py"

# 5. Full test suite -- no errors
pytest test/test_conformance.py -v

# 6. Ruff linter -- zero violations
ruff check src/ test/

# 7. Ruff formatter -- zero violations
ruff format --check src/ test/
```
