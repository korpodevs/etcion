"""Merged tests for test_implementation_migration."""

from __future__ import annotations

import warnings
from datetime import datetime

import pytest
from pydantic import ValidationError

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessRole,
)
from pyarchi.metamodel.concepts import Element
from pyarchi.metamodel.elements import (
    CompositeElement,
    Event,
    InternalBehaviorElement,
    PassiveStructureElement,
)
from pyarchi.metamodel.implementation_migration import (
    Deliverable,
    Gap,
    ImplementationEvent,
    Plateau,
    WorkPackage,
)
from pyarchi.metamodel.relationships import (
    Access,
    Assignment,
    Realization,
    Triggering,
)
from pyarchi.validation.permissions import is_permitted

ALL_FEAT121 = [WorkPackage, Deliverable, ImplementationEvent]


class TestInstantiation_1:
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


class TestInheritance_1:
    def test_workpackage_is_internal_behavior(self) -> None:
        assert issubclass(WorkPackage, InternalBehaviorElement)

    def test_deliverable_is_passive_structure(self) -> None:
        assert issubclass(Deliverable, PassiveStructureElement)

    def test_implementation_event_is_event(self) -> None:
        assert issubclass(ImplementationEvent, Event)


class TestClassVars_1:
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


class TestNotation_1:
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


class TestInstantiation_2:
    def test_can_instantiate(self) -> None:
        p = Plateau(name="Target Architecture")
        assert p.name == "Target Architecture"

    def test_type_name(self) -> None:
        assert Plateau(name="x")._type_name == "Plateau"


class TestInheritance_2:
    def test_is_composite_element(self) -> None:
        assert issubclass(Plateau, CompositeElement)

    def test_isinstance_composite_element(self) -> None:
        assert isinstance(Plateau(name="x"), CompositeElement)


class TestClassVars_2:
    def test_layer(self) -> None:
        assert Plateau.layer is Layer.IMPLEMENTATION_MIGRATION

    def test_aspect(self) -> None:
        assert Plateau.aspect is Aspect.COMPOSITE


class TestNotation_2:
    def test_layer_color(self) -> None:
        assert Plateau.notation.layer_color == "#FFE0E0"

    def test_badge_letter(self) -> None:
        assert Plateau.notation.badge_letter == "I"

    def test_corner_shape(self) -> None:
        assert Plateau.notation.corner_shape == "square"


class TestMembers:
    def test_members_defaults_to_empty(self) -> None:
        p = Plateau(name="x")
        assert p.members == []

    def test_accepts_core_element_as_member(self) -> None:
        wp = WorkPackage(name="Build phase 1")
        p = Plateau(name="Target", members=[wp])
        assert len(p.members) == 1
        assert p.members[0] is wp

    def test_accepts_multiple_members(self) -> None:
        wp1 = WorkPackage(name="Phase 1")
        wp2 = WorkPackage(name="Phase 2")
        p = Plateau(name="x", members=[wp1, wp2])
        assert len(p.members) == 2

    def test_members_list_is_independent_per_instance(self) -> None:
        p1 = Plateau(name="a")
        p2 = Plateau(name="b")
        p1.members.append(WorkPackage(name="wp"))
        assert len(p2.members) == 0


@pytest.fixture()
def plateau_a() -> Plateau:
    return Plateau(name="Baseline")


@pytest.fixture()
def plateau_b() -> Plateau:
    return Plateau(name="Target")


class TestInstantiation_3:
    def test_can_instantiate(self, plateau_a: Plateau, plateau_b: Plateau) -> None:
        g = Gap(name="Migration Gap", plateau_a=plateau_a, plateau_b=plateau_b)
        assert g.name == "Migration Gap"

    def test_type_name(self, plateau_a: Plateau, plateau_b: Plateau) -> None:
        g = Gap(name="x", plateau_a=plateau_a, plateau_b=plateau_b)
        assert g._type_name == "Gap"


class TestInheritance_3:
    def test_is_element(self) -> None:
        assert issubclass(Gap, Element)

    def test_is_not_composite_element(self) -> None:
        assert not issubclass(Gap, CompositeElement)


class TestClassVars_3:
    def test_layer(self) -> None:
        assert Gap.layer is Layer.IMPLEMENTATION_MIGRATION

    def test_aspect(self) -> None:
        assert Gap.aspect is Aspect.COMPOSITE


class TestNotation_3:
    def test_layer_color(self) -> None:
        assert Gap.notation.layer_color == "#FFE0E0"

    def test_badge_letter(self) -> None:
        assert Gap.notation.badge_letter == "I"

    def test_corner_shape(self) -> None:
        assert Gap.notation.corner_shape == "square"


class TestMandatoryPlateaus:
    def test_missing_both_raises(self) -> None:
        with pytest.raises(ValidationError):
            Gap(name="x")  # type: ignore[call-arg]

    def test_missing_plateau_a_raises(self, plateau_b: Plateau) -> None:
        with pytest.raises(ValidationError):
            Gap(name="x", plateau_b=plateau_b)  # type: ignore[call-arg]

    def test_missing_plateau_b_raises(self, plateau_a: Plateau) -> None:
        with pytest.raises(ValidationError):
            Gap(name="x", plateau_a=plateau_a)  # type: ignore[call-arg]

    def test_plateau_references_stored(self, plateau_a: Plateau, plateau_b: Plateau) -> None:
        g = Gap(name="x", plateau_a=plateau_a, plateau_b=plateau_b)
        assert g.plateau_a is plateau_a
        assert g.plateau_b is plateau_b

    def test_same_plateau_for_both_allowed(self, plateau_a: Plateau) -> None:
        """Spec does not forbid same plateau for both references."""
        g = Gap(name="x", plateau_a=plateau_a, plateau_b=plateau_a)
        assert g.plateau_a is g.plateau_b


class TestRealizationDeprecation:
    """Realization(WorkPackage, Deliverable) is permitted but deprecated."""

    def test_returns_true(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            assert is_permitted(Realization, WorkPackage, Deliverable) is True

    def test_emits_deprecation_warning(self) -> None:
        with pytest.warns(DeprecationWarning, match="deprecated"):
            is_permitted(Realization, WorkPackage, Deliverable)


class TestAssignmentToWorkPackage:
    """Business internal active structure sources may assign to WorkPackage."""

    @pytest.mark.parametrize(
        "source_type",
        [BusinessActor, BusinessRole, BusinessCollaboration],
    )
    def test_permitted_sources(self, source_type: type) -> None:
        assert is_permitted(Assignment, source_type, WorkPackage) is True

    @pytest.mark.parametrize(
        "source_type",
        [Deliverable, ImplementationEvent, Plateau],
    )
    def test_forbidden_sources(self, source_type: type) -> None:
        assert is_permitted(Assignment, source_type, WorkPackage) is False


class TestTriggering:
    """ImplementationEvent may trigger/be triggered by WorkPackage or Plateau."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (ImplementationEvent, WorkPackage),
            (ImplementationEvent, Plateau),
            (WorkPackage, ImplementationEvent),
            (Plateau, ImplementationEvent),
        ],
    )
    def test_permitted_triggering(self, source: type, target: type) -> None:
        assert is_permitted(Triggering, source, target) is True


class TestAccess:
    """ImplementationEvent may access Deliverable."""

    def test_impl_event_accesses_deliverable(self) -> None:
        assert is_permitted(Access, ImplementationEvent, Deliverable) is True


class TestDeliverableRealization:
    """Deliverable may realize core structure/behavior elements."""

    def test_deliverable_realizes_work_package(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            assert is_permitted(Realization, Deliverable, WorkPackage) is True
