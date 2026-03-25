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
    def test_collaboration_requires_two_internal_active(self) -> None:
        from pydantic import ValidationError as PydanticValidationError

        from pyarchi.metamodel.business import BusinessActor, BusinessCollaboration

        a = BusinessActor(name="a")
        with pytest.raises(PydanticValidationError):
            BusinessCollaboration(name="collab", assigned_elements=[a])



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
