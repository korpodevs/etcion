# Technical Brief: FEAT-04.6 Interaction and Collaboration Validation

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-016-epic004-generic-metamodel.md` ss5
**Epic:** EPIC-004 (final feature)

---

## Feature Summary

Validation tests for `Interaction`, `Event.time`, and forward-looking xfails for `Collaboration` and `PassiveStructureElement` assignment constraints. No new production classes. This feature also gates the `__init__.py` export update for all EPIC-004 types.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-04.2 (`Interaction`, `Event` with validator/field) | Must be done |
| FEAT-04.1 (`ActiveStructureElement`, `PassiveStructureElement`) | Must be done |
| FEAT-04.4, FEAT-04.5 (`Grouping`, `Location`) | Must be done |

## Stories

| Story | Testable Now? | Notes |
|---|---|---|
| 04.6.1 | Yes | `Interaction` >= 2 assigned elements. Validator defined in FEAT-04.2. Test with concrete subclass. |
| 04.6.2 | No -- xfail | `Collaboration` is a layer-specific type (not yet defined). Mark `xfail`. |
| 04.6.3 | No -- xfail | `PassiveStructureElement` cannot perform behavior. Requires `Assignment` relationship (EPIC-005). Mark `xfail`. |
| 04.6.4 | Yes | Single active structure -> `Interaction` raises `ValueError`. |
| 04.6.5 | Yes | `Event.time` defaults `None`, accepts `datetime` and `str`. |

## `__init__.py` Update

After all FEAT-04.x features are implemented, update `src/pyarchi/__init__.py` to export all EPIC-004 types:

```python
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    BehaviorElement,
    CompositeElement,
    Event,
    ExternalActiveStructureElement,
    ExternalBehaviorElement,
    Function,
    Grouping,
    InternalActiveStructureElement,
    InternalBehaviorElement,
    Interaction,
    Location,
    MotivationElement,
    PassiveStructureElement,
    Process,
    StructureElement,
)
```

Add all 16 names to `__all__`.

## Conformance xfail Status

All xfails in `test/test_conformance.py` test for layer-specific concrete types (`BusinessActor`, `Resource`, etc.) or relationship types. EPIC-004 introduces only generic ABCs + `Grouping` + `Location`. **No conformance xfails are removed by EPIC-004.** The layer-specific xfails remain until their respective epics ship.

The `test/test_feat012_structure.py` `_PROMOTED` set and functional outcome counts (`13 passed, 11 xfailed, 1 skipped`) are **unchanged** by EPIC-004.

## Test File: `test/test_feat046_validation.py`

```python
"""Tests for FEAT-04.6 -- Interaction and Collaboration Validation."""
from __future__ import annotations

from datetime import datetime
from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    Event,
    Interaction,
)


# ---------------------------------------------------------------------------
# Test-local concrete stubs
# ---------------------------------------------------------------------------


class _ConcreteActiveStructure(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "ConcreteActive"


class _ConcreteInteraction(Interaction):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

    @property
    def _type_name(self) -> str:
        return "ConcreteInteraction"


class _ConcreteEvent(Event):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

    @property
    def _type_name(self) -> str:
        return "ConcreteEvent"


# ---------------------------------------------------------------------------
# STORY-04.6.1 / STORY-04.6.4: Interaction >= 2 assigned elements
# ---------------------------------------------------------------------------


class TestInteractionValidation:
    def test_zero_assigned_raises(self) -> None:
        with pytest.raises(ValueError, match="requires >= 2"):
            _ConcreteInteraction(name="i")

    def test_one_assigned_raises(self) -> None:
        a = _ConcreteActiveStructure(name="a")
        with pytest.raises(ValueError, match="requires >= 2"):
            _ConcreteInteraction(name="i", assigned_elements=[a])

    def test_two_assigned_valid(self) -> None:
        a1 = _ConcreteActiveStructure(name="a1")
        a2 = _ConcreteActiveStructure(name="a2")
        i = _ConcreteInteraction(name="i", assigned_elements=[a1, a2])
        assert len(i.assigned_elements) == 2

    def test_three_assigned_valid(self) -> None:
        actors = [_ConcreteActiveStructure(name=f"a{n}") for n in range(3)]
        i = _ConcreteInteraction(name="i", assigned_elements=actors)
        assert len(i.assigned_elements) == 3


# ---------------------------------------------------------------------------
# STORY-04.6.2: Collaboration >= 2 internal active structure (xfail)
# ---------------------------------------------------------------------------


class TestCollaborationValidation:
    @pytest.mark.xfail(
        strict=False,
        reason="Collaboration is a layer-specific type, not yet defined",
    )
    def test_collaboration_requires_two_internal_active(self) -> None:
        # Placeholder -- Collaboration does not exist yet.
        from pyarchi.metamodel.elements import Collaboration  # type: ignore[attr-defined]

        pytest.fail("Collaboration class not yet implemented")


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


# ---------------------------------------------------------------------------
# STORY-04.6.5: Event.time attribute
# ---------------------------------------------------------------------------


class TestEventTime:
    def test_time_defaults_to_none(self) -> None:
        e = _ConcreteEvent(name="ev")
        assert e.time is None

    def test_time_accepts_datetime(self) -> None:
        dt = datetime(2026, 6, 15, 9, 0)
        e = _ConcreteEvent(name="ev", time=dt)
        assert e.time == dt

    def test_time_accepts_string(self) -> None:
        e = _ConcreteEvent(name="ev", time="end of Q2")
        assert e.time == "end of Q2"

    def test_time_in_model_dump(self) -> None:
        e = _ConcreteEvent(name="ev", time="2026-Q3")
        dump = e.model_dump()
        assert dump["time"] == "2026-Q3"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/elements.py src/pyarchi/__init__.py
ruff check test/test_feat046_validation.py
ruff format --check src/pyarchi/ test/test_feat046_validation.py
mypy src/pyarchi/ test/test_feat046_validation.py
pytest test/test_feat046_validation.py -v

# Confirm conformance counts unchanged
pytest test/test_conformance.py -v --tb=short -q
# Expect: 13 passed, 11 xfailed, 1 skipped

# Confirm structural test counts unchanged
pytest test/test_feat012_structure.py::TestConformanceFunctionalBehaviour -v

# Full suite
pytest
```
