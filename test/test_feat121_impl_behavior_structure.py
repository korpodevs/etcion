"""Tests for FEAT-12.1 -- Implementation Behavior and Structure concrete elements."""

from __future__ import annotations

from datetime import datetime

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    Event,
    InternalBehaviorElement,
    PassiveStructureElement,
)
from pyarchi.metamodel.implementation_migration import (
    Deliverable,
    ImplementationEvent,
    WorkPackage,
)

ALL_FEAT121 = [WorkPackage, Deliverable, ImplementationEvent]


class TestInstantiation:
    @pytest.mark.parametrize("cls", ALL_FEAT121)
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames:
    @pytest.mark.parametrize(
        ("cls", "expected"),
        [
            (WorkPackage, "WorkPackage"),
            (Deliverable, "Deliverable"),
            (ImplementationEvent, "ImplementationEvent"),
        ],
    )
    def test_type_name(self, cls: type, expected: str) -> None:
        assert cls(name="x")._type_name == expected


class TestInheritance:
    def test_workpackage_is_internal_behavior(self) -> None:
        assert issubclass(WorkPackage, InternalBehaviorElement)

    def test_deliverable_is_passive_structure(self) -> None:
        assert issubclass(Deliverable, PassiveStructureElement)

    def test_implementation_event_is_event(self) -> None:
        assert issubclass(ImplementationEvent, Event)


class TestClassVars:
    @pytest.mark.parametrize("cls", ALL_FEAT121)
    def test_layer_is_implementation_migration(self, cls: type) -> None:
        assert cls.layer is Layer.IMPLEMENTATION_MIGRATION

    @pytest.mark.parametrize(
        ("cls", "expected_aspect"),
        [
            (WorkPackage, Aspect.BEHAVIOR),
            (Deliverable, Aspect.PASSIVE_STRUCTURE),
            (ImplementationEvent, Aspect.BEHAVIOR),
        ],
    )
    def test_aspect(self, cls: type, expected_aspect: Aspect) -> None:
        assert cls.aspect is expected_aspect


class TestNotation:
    @pytest.mark.parametrize("cls", ALL_FEAT121)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#FFE0E0"

    @pytest.mark.parametrize("cls", ALL_FEAT121)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "I"

    def test_workpackage_corner_round(self) -> None:
        assert WorkPackage.notation.corner_shape == "round"

    def test_deliverable_corner_square(self) -> None:
        assert Deliverable.notation.corner_shape == "square"

    def test_implementation_event_corner_round(self) -> None:
        assert ImplementationEvent.notation.corner_shape == "round"


class TestWorkPackageTemporalFields:
    def test_start_defaults_to_none(self) -> None:
        wp = WorkPackage(name="wp")
        assert wp.start is None

    def test_end_defaults_to_none(self) -> None:
        wp = WorkPackage(name="wp")
        assert wp.end is None

    def test_start_accepts_string(self) -> None:
        wp = WorkPackage(name="wp", start="Q3 2026")
        assert wp.start == "Q3 2026"

    def test_end_accepts_string(self) -> None:
        wp = WorkPackage(name="wp", end="TBD")
        assert wp.end == "TBD"

    def test_start_accepts_datetime(self) -> None:
        dt = datetime(2026, 7, 1)
        wp = WorkPackage(name="wp", start=dt)
        assert wp.start == dt

    def test_end_accepts_datetime(self) -> None:
        dt = datetime(2026, 12, 31)
        wp = WorkPackage(name="wp", end=dt)
        assert wp.end == dt


class TestImplementationEventTime:
    def test_time_inherited_from_event(self) -> None:
        ie = ImplementationEvent(name="go-live")
        assert ie.time is None

    def test_time_accepts_string(self) -> None:
        ie = ImplementationEvent(name="go-live", time="2026-07-01")
        assert ie.time == "2026-07-01"
