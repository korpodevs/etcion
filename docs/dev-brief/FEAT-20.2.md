# Technical Brief: FEAT-20.2 -- Resolve Deferred Validation xfails

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-032-epic020-conformance-cleanup.md` (Decision 2)
**Depends on:** Nothing (independent of FEAT-20.1 and FEAT-20.3)

## Scope

Remove or delete all remaining `xfail` stubs from Phase 1 test files. These were created under ADR-017 ss6 as forward placeholders. The FEAT-15.x validation engine now covers each scenario.

## Disposition Matrix

| File | Class | xfail Method | FEAT-15.x Coverage | Action |
|---|---|---|---|---|
| `test/test_feat052_structural.py:121` | `TestDeferredValidation` | `test_assignment_wrong_direction_raises` | `test_feat151_direction.py::test_assignment_wrong_direction_model_error` (line 31) | **DELETE** |
| `test/test_feat052_structural.py:128` | `TestDeferredValidation` | `test_aggregation_relationship_target_non_composite_source_raises` | `test_feat152_composite_source.py::test_aggregation_non_composite_source_model_error` (line 36) | **DELETE** |
| `test/test_feat053_serving.py:101` | `TestDeferredValidation` | `test_serving_wrong_direction_raises` | `test_feat151_direction.py::test_serving_wrong_direction_model_error` (line 43) | **DELETE** |
| `test/test_feat054_access.py:105` | `TestDeferredValidation` | `test_access_wrong_direction_raises` | `test_feat151_direction.py::test_access_wrong_direction_model_error` (line 53) | **DELETE** |
| `test/test_feat058_specialization.py:108` | `TestDeferredValidation` | `test_cross_type_specialization_raises` | `test_feat153_specialization_same_type.py::test_cross_type_specialization_model_error` (line 23) | **DELETE** |
| `test/test_feat046_validation.py:102` | `TestPassiveCannotPerformBehavior` | `test_passive_assigned_to_behavior_raises` | `test_feat156_passive_behavior.py::test_passive_assigned_to_behavior_model_error` (line 25) | **DELETE** |

All six xfail stubs have exact equivalents in the FEAT-15.x test suite. Every stub is deleted outright. No rewrites are needed.

## Exact Deletions

### `test/test_feat052_structural.py`

Delete lines 110-129 (comment block, blank line, entire `TestDeferredValidation` class):

```
# ---------------------------------------------------------------------------
# Validation xfails (model-level, deferred per ADR-017 ss6)
# ---------------------------------------------------------------------------


class TestDeferredValidation:
    @pytest.mark.xfail(
        strict=False,
        reason="Model-level validation deferred (ADR-017 ss6 / FEAT-05.10/11)",
    )
    def test_assignment_wrong_direction_raises(self) -> None:
        pytest.fail("Model-level validation not yet implemented")

    @pytest.mark.xfail(
        strict=False,
        reason="Model-level validation deferred (ADR-017 ss6 / FEAT-05.10/11)",
    )
    def test_aggregation_relationship_target_non_composite_source_raises(self) -> None:
        pytest.fail("Model-level validation not yet implemented")
```

### `test/test_feat053_serving.py`

Delete lines 90-102 (comment block, blank line, entire `TestDeferredValidation` class):

```
# ---------------------------------------------------------------------------
# Validation xfails
# ---------------------------------------------------------------------------


class TestDeferredValidation:
    @pytest.mark.xfail(
        strict=False,
        reason="Serving direction validation deferred to model-level (ADR-017 ss6)",
    )
    def test_serving_wrong_direction_raises(self) -> None:
        pytest.fail("Model-level validation not yet implemented")
```

### `test/test_feat054_access.py`

Delete lines 94-106 (comment block, blank line, entire `TestDeferredValidation` class):

```
# ---------------------------------------------------------------------------
# Validation xfails
# ---------------------------------------------------------------------------


class TestDeferredValidation:
    @pytest.mark.xfail(
        strict=False,
        reason="Access direction validation deferred to model-level (ADR-017 ss6)",
    )
    def test_access_wrong_direction_raises(self) -> None:
        pytest.fail("Model-level validation not yet implemented")
```

### `test/test_feat058_specialization.py`

Delete lines 97-109 (comment block, blank line, entire `TestDeferredValidation` class):

```
# ---------------------------------------------------------------------------
# Validation xfails (model-level, deferred per ADR-017 ss6)
# ---------------------------------------------------------------------------


class TestDeferredValidation:
    @pytest.mark.xfail(
        strict=False,
        reason="Same-type constraint deferred to model-level validation (ADR-017 ss6)",
    )
    def test_cross_type_specialization_raises(self) -> None:
        pytest.fail("Model-level validation not yet implemented")
```

### `test/test_feat046_validation.py`

Delete lines 91-104 (comment block, blank line, entire `TestPassiveCannotPerformBehavior` class):

```
# ---------------------------------------------------------------------------
# STORY-04.6.3: PassiveStructureElement cannot perform behavior (xfail)
# ---------------------------------------------------------------------------


class TestPassiveCannotPerformBehavior:
    @pytest.mark.xfail(
        strict=False,
        reason="Assignment relationship not yet defined (EPIC-005)",
    )
    def test_passive_assigned_to_behavior_raises(self) -> None:
        # Placeholder -- requires Assignment relationship from EPIC-005.
        pytest.fail("Assignment relationship not yet implemented")
```

## Post-Deletion Validation

No xfail markers should remain in any `test_feat0*.py` file:

```bash
grep -rn "xfail" test/test_feat0*.py   # Expect: zero matches
```

## Not In Scope

| File | Reason |
|---|---|
| `test/test_feat059_junction.py::TestDeferredValidation` | Already a live test (no xfail marker). No action needed. |
| `test/test_feat046_validation.py::TestCollaborationValidation` | Already a live test (no xfail marker). No action needed. |

## Verification

```bash
pytest test/test_feat052_structural.py test/test_feat053_serving.py \
       test/test_feat054_access.py test/test_feat058_specialization.py \
       test/test_feat046_validation.py -v
# Expect: all remaining tests pass, zero xfail, zero skip
```
