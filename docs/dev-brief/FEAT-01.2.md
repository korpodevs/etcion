# Technical Brief: FEAT-01.2 Conformance Test Suite

**Status:** Ready for Implementation
**ADR Link:** `docs/adr/ADR-004-conformance-test-suite.md`
**Epic:** EPIC-001 -- Scope and Conformance
**Date:** 2026-03-23

---

## 1. Feature Summary

FEAT-01.2 creates `test/test_conformance.py`, the executable specification of the library's ArchiMate 3.2 conformance requirements. The file contains four test classes: `TestConformanceProfile` (passes immediately once FEAT-01.1 is done), `TestShallFeatures` (one `xfail` test per mandatory feature, each asserting that the required public API types exist on the `pyarchi` module), `TestShouldFeatures` (two `xfail` tests for Phase 2 features), and `TestMayFeatures` (one `skip` test for out-of-scope Appendix C viewpoints). The `xfail(strict=False)` pattern ensures the test suite is CI-green from day one while documenting the full scope of remaining work, and tests silently transition to passes as implementing epics are completed.

---

## 2. Story-by-Story Implementation Guide

### STORY-01.2.1: Create `test/test_conformance.py` with assertions for each `shall`-level mandatory feature

**Files to create:**
- `/home/kiera/dev/pyarchi/test/test_conformance.py`

**Content:** See Section 3 below for the complete file.

**Acceptance Criteria:**
- `test/test_conformance.py` exists.
- `TestConformanceProfile` class contains 7 test methods that all pass immediately (given FEAT-01.1 is complete).
- `TestShallFeatures` class contains 12 test methods, each decorated with `@pytest.mark.xfail(strict=False, reason="EPIC-0XX: ...")`.
- Each `shall`-level test asserts `hasattr(pyarchi, "TypeName")` for every ArchiMate type required by that feature.
- `pytest` runs without errors (xfail tests show as `x`, not `F`).

**Gotchas:**
- Import `pyarchi` at module level, not inside test methods. The module is already importable.
- Each `xfail` reason string must reference the specific epic that will implement the feature. This makes the pytest output self-documenting.
- `strict=False` is critical. With `strict=True`, an xfail test that unexpectedly passes would be reported as an error, requiring manual marker removal. `strict=False` allows the transition from xfail to xpass silently.

---

### STORY-01.2.2: Add warning-level checks for `should`-level features

**Files to modify:**
- `/home/kiera/dev/pyarchi/test/test_conformance.py` (already created in STORY-01.2.1)

**Acceptance Criteria:**
- `TestShouldFeatures` class contains 2 test methods.
- Both use `@pytest.mark.xfail(strict=False, reason="Phase 2: ...")`.
- `pytest.warns` is NOT used (explicitly rejected per ADR-004).

**Gotchas:**
- The `should` level is a specification property, not a runtime warning condition. Using `pytest.warns` would conflate spec compliance levels with Python's `warnings` module, which is a different concept entirely.

---

### STORY-01.2.3: Verify that `may`-level features do not cause test failure when absent

**Files to modify:**
- `/home/kiera/dev/pyarchi/test/test_conformance.py` (already created in STORY-01.2.1)

**Acceptance Criteria:**
- `TestMayFeatures` class contains 1 test method.
- The test uses `@pytest.mark.skip(reason="...")`, NOT `xfail`.
- Running `pytest` shows the test as `s` (skipped), not `x` (xfail) or `F` (failure).

**Gotchas:**
- `skip` is chosen over `xfail` because `may`-level features are not planned for any phase. `xfail` implies "will pass eventually," which is misleading for out-of-scope features. `skip` communicates "intentionally not tested."

---

## 3. `test/test_conformance.py` -- Complete Reference

```python
"""Conformance test suite for pyarchi against the ArchiMate 3.2 specification.

Test Strategy
-------------
This file is an *executable specification* of the library's conformance
requirements.  It does not test implementation behaviour (that is the
responsibility of each epic's unit tests); it tests that the public API
surface declared by :class:`pyarchi.ConformanceProfile` actually exists.

Marker Strategy
~~~~~~~~~~~~~~~
* **TestConformanceProfile** -- No markers.  These tests pass immediately
  once ``conformance.py`` (FEAT-01.1) is implemented.
* **TestShallFeatures** -- ``@pytest.mark.xfail(strict=False)``.  Each test
  is expected to fail until the implementing epic exports the required types
  from ``pyarchi.__init__``.  ``strict=False`` means an unexpected pass
  (xpass) is tolerated, allowing tests to silently transition to green.
* **TestShouldFeatures** -- Same ``xfail`` pattern, with Phase 2 reasons.
* **TestMayFeatures** -- ``@pytest.mark.skip``.  These features are out of
  scope and should never appear as expected failures.

When an epic is complete and its types are exported from ``pyarchi.__init__``,
remove the ``xfail`` marker from the corresponding test so it appears as a
normal ``PASSED`` result in the test report.
"""

from __future__ import annotations

import dataclasses

import pytest

import pyarchi
from pyarchi import CONFORMANCE, SPEC_VERSION, ConformanceProfile


# ---------------------------------------------------------------------------
# TestConformanceProfile -- passes immediately once FEAT-01.1 is done
# ---------------------------------------------------------------------------


class TestConformanceProfile:
    """Verify the ConformanceProfile dataclass and the CONFORMANCE singleton."""

    def test_spec_version_is_3_2(self) -> None:
        assert CONFORMANCE.spec_version == "3.2"

    def test_spec_version_matches_module_constant(self) -> None:
        assert CONFORMANCE.spec_version == SPEC_VERSION

    def test_shall_features_are_true(self) -> None:
        assert CONFORMANCE.language_structure is True
        assert CONFORMANCE.generic_metamodel is True
        assert CONFORMANCE.strategy_elements is True
        assert CONFORMANCE.motivation_elements is True
        assert CONFORMANCE.business_elements is True
        assert CONFORMANCE.application_elements is True
        assert CONFORMANCE.technology_elements is True
        assert CONFORMANCE.physical_elements is True
        assert CONFORMANCE.implementation_migration_elements is True
        assert CONFORMANCE.cross_layer_relationships is True
        assert CONFORMANCE.relationship_permission_table is True
        assert CONFORMANCE.iconography_metadata is True

    def test_should_features_are_true(self) -> None:
        assert CONFORMANCE.viewpoint_mechanism is True
        assert CONFORMANCE.language_customization is True

    def test_may_features_are_false(self) -> None:
        assert CONFORMANCE.example_viewpoints is False

    def test_profile_is_frozen(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            CONFORMANCE.language_structure = False  # type: ignore[misc]

    def test_conformance_is_conformanceprofile_instance(self) -> None:
        assert isinstance(CONFORMANCE, ConformanceProfile)


# ---------------------------------------------------------------------------
# TestShallFeatures -- xfail until the implementing epic is complete
# ---------------------------------------------------------------------------


class TestShallFeatures:
    """Assert that every shall-level feature is present in the public API.

    Each test checks ``hasattr(pyarchi, "TypeName")`` for the types
    required by the corresponding :class:`ConformanceProfile` field.
    Tests are marked ``xfail(strict=False)`` until the implementing epic
    exports the types from ``pyarchi.__init__``.
    """

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-003: Language structure enums not yet re-exported",
    )
    def test_language_structure(self) -> None:
        assert hasattr(pyarchi, "Layer")
        assert hasattr(pyarchi, "Aspect")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-002: Generic metamodel ABCs not yet implemented",
    )
    def test_generic_metamodel(self) -> None:
        assert hasattr(pyarchi, "Concept")
        assert hasattr(pyarchi, "Element")
        assert hasattr(pyarchi, "Relationship")
        assert hasattr(pyarchi, "RelationshipConnector")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-004: Strategy layer elements not yet implemented",
    )
    def test_strategy_elements(self) -> None:
        assert hasattr(pyarchi, "Resource")
        assert hasattr(pyarchi, "Capability")
        assert hasattr(pyarchi, "ValueStream")
        assert hasattr(pyarchi, "CourseOfAction")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-004: Motivation layer elements not yet implemented",
    )
    def test_motivation_elements(self) -> None:
        assert hasattr(pyarchi, "Stakeholder")
        assert hasattr(pyarchi, "Driver")
        assert hasattr(pyarchi, "Assessment")
        assert hasattr(pyarchi, "Goal")
        assert hasattr(pyarchi, "Outcome")
        assert hasattr(pyarchi, "Principle")
        assert hasattr(pyarchi, "Requirement")
        assert hasattr(pyarchi, "Constraint")
        assert hasattr(pyarchi, "Meaning")
        assert hasattr(pyarchi, "Value")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-004: Business layer elements not yet implemented",
    )
    def test_business_elements(self) -> None:
        assert hasattr(pyarchi, "BusinessActor")
        assert hasattr(pyarchi, "BusinessRole")
        assert hasattr(pyarchi, "BusinessCollaboration")
        assert hasattr(pyarchi, "BusinessInterface")
        assert hasattr(pyarchi, "BusinessProcess")
        assert hasattr(pyarchi, "BusinessFunction")
        assert hasattr(pyarchi, "BusinessInteraction")
        assert hasattr(pyarchi, "BusinessEvent")
        assert hasattr(pyarchi, "BusinessService")
        assert hasattr(pyarchi, "BusinessObject")
        assert hasattr(pyarchi, "Contract")
        assert hasattr(pyarchi, "Representation")
        assert hasattr(pyarchi, "Product")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-004: Application layer elements not yet implemented",
    )
    def test_application_elements(self) -> None:
        assert hasattr(pyarchi, "ApplicationComponent")
        assert hasattr(pyarchi, "ApplicationCollaboration")
        assert hasattr(pyarchi, "ApplicationInterface")
        assert hasattr(pyarchi, "ApplicationFunction")
        assert hasattr(pyarchi, "ApplicationInteraction")
        assert hasattr(pyarchi, "ApplicationProcess")
        assert hasattr(pyarchi, "ApplicationEvent")
        assert hasattr(pyarchi, "ApplicationService")
        assert hasattr(pyarchi, "DataObject")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-004: Technology layer elements not yet implemented",
    )
    def test_technology_elements(self) -> None:
        assert hasattr(pyarchi, "Node")
        assert hasattr(pyarchi, "Device")
        assert hasattr(pyarchi, "SystemSoftware")
        assert hasattr(pyarchi, "TechnologyCollaboration")
        assert hasattr(pyarchi, "TechnologyInterface")
        assert hasattr(pyarchi, "Path")
        assert hasattr(pyarchi, "CommunicationNetwork")
        assert hasattr(pyarchi, "TechnologyFunction")
        assert hasattr(pyarchi, "TechnologyProcess")
        assert hasattr(pyarchi, "TechnologyInteraction")
        assert hasattr(pyarchi, "TechnologyEvent")
        assert hasattr(pyarchi, "TechnologyService")
        assert hasattr(pyarchi, "Artifact")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-004: Physical layer elements not yet implemented",
    )
    def test_physical_elements(self) -> None:
        assert hasattr(pyarchi, "Equipment")
        assert hasattr(pyarchi, "Facility")
        assert hasattr(pyarchi, "DistributionNetwork")
        assert hasattr(pyarchi, "Material")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-004: Implementation & Migration elements not yet implemented",
    )
    def test_implementation_migration_elements(self) -> None:
        assert hasattr(pyarchi, "WorkPackage")
        assert hasattr(pyarchi, "Deliverable")
        assert hasattr(pyarchi, "ImplementationEvent")
        assert hasattr(pyarchi, "Plateau")
        assert hasattr(pyarchi, "Gap")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-005: Relationship types and Junction not yet implemented",
    )
    def test_cross_layer_relationships(self) -> None:
        assert hasattr(pyarchi, "Composition")
        assert hasattr(pyarchi, "Aggregation")
        assert hasattr(pyarchi, "Assignment")
        assert hasattr(pyarchi, "Realization")
        assert hasattr(pyarchi, "Serving")
        assert hasattr(pyarchi, "Access")
        assert hasattr(pyarchi, "Influence")
        assert hasattr(pyarchi, "Association")
        assert hasattr(pyarchi, "Triggering")
        assert hasattr(pyarchi, "Flow")
        assert hasattr(pyarchi, "Specialization")
        assert hasattr(pyarchi, "Junction")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-005 (FEAT-05.11): Permission table not yet implemented",
    )
    def test_relationship_permission_table(self) -> None:
        assert hasattr(pyarchi, "is_permitted")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-003: Notation metadata not yet implemented",
    )
    def test_iconography_metadata(self) -> None:
        assert hasattr(pyarchi, "NotationMetadata")


# ---------------------------------------------------------------------------
# TestShouldFeatures -- xfail, Phase 2
# ---------------------------------------------------------------------------


class TestShouldFeatures:
    """Assert that should-level features are present in the public API.

    These features are planned for Phase 2.  Tests use the same
    ``xfail(strict=False)`` pattern as shall-level tests.
    """

    @pytest.mark.xfail(
        strict=False,
        reason="Phase 2: Viewpoint mechanism not yet implemented",
    )
    def test_viewpoint_mechanism(self) -> None:
        assert hasattr(pyarchi, "Viewpoint")

    @pytest.mark.xfail(
        strict=False,
        reason="Phase 2: Language customization not yet implemented",
    )
    def test_language_customization(self) -> None:
        assert hasattr(pyarchi, "Profile")


# ---------------------------------------------------------------------------
# TestMayFeatures -- skip (out of scope)
# ---------------------------------------------------------------------------


class TestMayFeatures:
    """Document may-level features that are explicitly out of scope.

    These tests are skipped, not xfail, because the library does not plan
    to implement them in any phase.
    """

    @pytest.mark.skip(
        reason="Appendix C example viewpoints are out of scope for Phase 1",
    )
    def test_example_viewpoints(self) -> None:
        # Placeholder -- if implemented, would check for concrete viewpoint
        # classes such as BasicViewpoint, OrganizationViewpoint, etc.
        pass
```

---

## 4. xfail Marker Removal Policy

When an epic is completed and its types are exported from `pyarchi.__init__`, the developer implementing that epic must:

1. **Remove** the `@pytest.mark.xfail(...)` decorator from the corresponding test method in `test/test_conformance.py`.
2. **Verify** that the test now passes as a normal `PASSED` result (not `XPASS`).
3. **Update** `docs/BACKLOG.md` to mark the corresponding FEAT-01.2 story as complete if all tests in that class have had their markers removed.

Forgetting to remove the marker is harmless -- `strict=False` means an xpass is tolerated and does not break CI. However, cleanup is recommended for test report clarity. Each epic's definition of done should include a checklist item: "Remove xfail markers from `test/test_conformance.py` for conformance tests that now pass."

The mapping from test methods to implementing epics is:

| Test Method | Implementing Epic |
|---|---|
| `test_language_structure` | EPIC-003 |
| `test_generic_metamodel` | EPIC-002 |
| `test_strategy_elements` | EPIC-004 |
| `test_motivation_elements` | EPIC-004 |
| `test_business_elements` | EPIC-004 |
| `test_application_elements` | EPIC-004 |
| `test_technology_elements` | EPIC-004 |
| `test_physical_elements` | EPIC-004 |
| `test_implementation_migration_elements` | EPIC-004 |
| `test_cross_layer_relationships` | EPIC-005 |
| `test_relationship_permission_table` | EPIC-005 (FEAT-05.11) |
| `test_iconography_metadata` | EPIC-003 |
| `test_viewpoint_mechanism` | Phase 2 |
| `test_language_customization` | Phase 2 |

---

## 5. Verification Checklist

Run these commands sequentially from the repository root after completing all three stories. Every command must exit with code 0.

```bash
# 0. Activate the virtual environment
source .venv/bin/activate

# 1. Verify test file exists
test -f test/test_conformance.py && echo "OK: file exists"

# 2. Run pytest -- expect TestConformanceProfile tests to PASS,
#    TestShallFeatures/TestShouldFeatures tests to XFAIL,
#    TestMayFeatures test to SKIP
pytest test/test_conformance.py -v

# 3. Verify TestConformanceProfile passes (no xfail, no skip)
pytest test/test_conformance.py -v -k "TestConformanceProfile" --tb=short

# 4. Count test outcomes (informational)
pytest test/test_conformance.py -v --tb=no 2>&1 | tail -1

# 5. Ruff linter -- zero violations
ruff check src/ test/

# 6. Ruff formatter -- zero violations
ruff format --check src/ test/

# 7. Full test suite -- no errors
pytest
```
