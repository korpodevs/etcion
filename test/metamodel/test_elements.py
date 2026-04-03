"""Merged tests for test_elements."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

import pytest

from etcion.enums import Aspect, Layer, RelationshipCategory
from etcion.metamodel.concepts import Concept, Element, Relationship
from etcion.metamodel.elements import (
    ActiveStructureElement,
    BehaviorElement,
    CompositeElement,
    Event,
    ExternalActiveStructureElement,
    ExternalBehaviorElement,
    Function,
    Grouping,
    Interaction,
    InternalActiveStructureElement,
    InternalBehaviorElement,
    Location,
    MotivationElement,
    PassiveStructureElement,
    Process,
    StructureElement,
)
from test.metamodel.conftest import StubActiveStructure, StubEvent, StubInteraction


class TestStructureElementHierarchyABC:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [
            StructureElement,
            ActiveStructureElement,
            InternalActiveStructureElement,
            ExternalActiveStructureElement,
            PassiveStructureElement,
        ],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestStructureElementInheritance:
    """Verify issubclass relationships."""

    def test_structure_element_is_element(self) -> None:
        assert issubclass(StructureElement, Element)

    def test_active_structure_is_structure(self) -> None:
        assert issubclass(ActiveStructureElement, StructureElement)

    def test_internal_active_is_active(self) -> None:
        assert issubclass(InternalActiveStructureElement, ActiveStructureElement)

    def test_external_active_is_active(self) -> None:
        assert issubclass(ExternalActiveStructureElement, ActiveStructureElement)

    def test_passive_is_structure(self) -> None:
        assert issubclass(PassiveStructureElement, StructureElement)

    def test_passive_is_not_active(self) -> None:
        assert not issubclass(PassiveStructureElement, ActiveStructureElement)


class TestBehaviorElementHierarchyABC:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [
            BehaviorElement,
            InternalBehaviorElement,
            Process,
            Function,
            Interaction,
            ExternalBehaviorElement,
            Event,
        ],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestBehaviorElementInheritance:
    """Verify issubclass relationships."""

    def test_behavior_is_element(self) -> None:
        assert issubclass(BehaviorElement, Element)

    def test_internal_behavior_is_behavior(self) -> None:
        assert issubclass(InternalBehaviorElement, BehaviorElement)

    def test_process_is_internal_behavior(self) -> None:
        assert issubclass(Process, InternalBehaviorElement)

    def test_function_is_internal_behavior(self) -> None:
        assert issubclass(Function, InternalBehaviorElement)

    def test_interaction_is_internal_behavior(self) -> None:
        assert issubclass(Interaction, InternalBehaviorElement)

    def test_external_behavior_is_behavior(self) -> None:
        assert issubclass(ExternalBehaviorElement, BehaviorElement)

    def test_event_is_behavior(self) -> None:
        assert issubclass(Event, BehaviorElement)


class TestInteractionValidatorOnConcreteSubclass:
    """Interaction.model_validator fires on concrete subclass only."""

    class StubInteraction(Interaction):
        layer: ClassVar[Layer] = Layer.BUSINESS
        aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

        @property
        def _type_name(self) -> str:
            return "ConcreteInteraction"

    class StubActiveStructure(ActiveStructureElement):
        layer: ClassVar[Layer] = Layer.BUSINESS
        aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

        @property
        def _type_name(self) -> str:
            return "ConcreteActiveStructure"

    def test_fewer_than_two_raises_validation_error(self) -> None:
        actor = self.StubActiveStructure(name="a1")
        with pytest.raises(ValueError, match="requires >= 2"):
            self.StubInteraction(name="i", assigned_elements=[actor])

    def test_zero_assigned_raises_validation_error(self) -> None:
        with pytest.raises(ValueError, match="requires >= 2"):
            self.StubInteraction(name="i")

    def test_two_assigned_is_valid(self) -> None:
        a1 = self.StubActiveStructure(name="a1")
        a2 = self.StubActiveStructure(name="a2")
        interaction = self.StubInteraction(name="i", assigned_elements=[a1, a2])
        assert len(interaction.assigned_elements) == 2


class TestEventTimeField:
    """Event.time is present on concrete subclass."""

    class StubEvent(Event):
        layer: ClassVar[Layer] = Layer.BUSINESS
        aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

        @property
        def _type_name(self) -> str:
            return "ConcreteEvent"

    def test_time_defaults_to_none(self) -> None:
        e = self.StubEvent(name="ev")
        assert e.time is None

    def test_time_accepts_datetime(self) -> None:
        dt = datetime(2026, 1, 1, 12, 0)
        e = self.StubEvent(name="ev", time=dt)
        assert e.time == dt

    def test_time_accepts_string(self) -> None:
        e = self.StubEvent(name="ev", time="Q3 2026")
        assert e.time == "Q3 2026"


class TestMotivationCompositeABC:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize("cls", [MotivationElement, CompositeElement])
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestMotivationCompositeInheritance:
    def test_motivation_is_element(self) -> None:
        assert issubclass(MotivationElement, Element)

    def test_composite_is_element(self) -> None:
        assert issubclass(CompositeElement, Element)

    def test_motivation_is_not_composite(self) -> None:
        assert not issubclass(MotivationElement, CompositeElement)

    def test_composite_is_not_motivation(self) -> None:
        assert not issubclass(CompositeElement, MotivationElement)


class TestGroupingInstantiation:
    def test_can_instantiate(self) -> None:
        g = Grouping(name="g")
        assert g.name == "g"

    def test_members_defaults_to_empty_list(self) -> None:
        g = Grouping(name="g")
        assert g.members == []

    def test_type_name(self) -> None:
        g = Grouping(name="g")
        assert g._type_name == "Grouping"


class TestGroupingClassification:
    def test_layer(self) -> None:
        assert Grouping.layer is Layer.IMPLEMENTATION_MIGRATION

    def test_aspect(self) -> None:
        assert Grouping.aspect is Aspect.COMPOSITE


class TestGroupingInheritance:
    def test_is_composite_element(self) -> None:
        assert isinstance(Grouping(name="g"), CompositeElement)

    def test_is_element(self) -> None:
        assert isinstance(Grouping(name="g"), Element)

    def test_is_concept(self) -> None:
        assert isinstance(Grouping(name="g"), Concept)


class TestGroupingMembers:
    """Grouping accepts both Element and Relationship members."""

    class _StubElement(Element):
        layer: ClassVar[Layer] = Layer.BUSINESS
        aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

        @property
        def _type_name(self) -> str:
            return "Stub"

    class _StubRelationship(Relationship):
        category: ClassVar[RelationshipCategory] = RelationshipCategory.OTHER

        @property
        def _type_name(self) -> str:
            return "StubRel"

    def test_accepts_element_member(self) -> None:
        elem = self._StubElement(name="e")
        g = Grouping(name="g", members=[elem])
        assert len(g.members) == 1

    def test_accepts_relationship_member(self) -> None:
        elem = self._StubElement(name="e")
        rel = self._StubRelationship(name="r", source=elem, target=elem)
        g = Grouping(name="g", members=[rel])
        assert len(g.members) == 1

    def test_accepts_mixed_members(self) -> None:
        elem = self._StubElement(name="e")
        rel = self._StubRelationship(name="r", source=elem, target=elem)
        g = Grouping(name="g", members=[elem, rel])
        assert len(g.members) == 2


class TestLocationInstantiation:
    def test_can_instantiate(self) -> None:
        loc = Location(name="HQ")
        assert loc.name == "HQ"

    def test_type_name(self) -> None:
        loc = Location(name="HQ")
        assert loc._type_name == "Location"


class TestLocationClassification:
    def test_aspect(self) -> None:
        assert Location.aspect is Aspect.COMPOSITE

    def test_no_layer_attribute(self) -> None:
        assert not hasattr(Location, "layer")

    def test_layer_access_raises_attribute_error(self) -> None:
        with pytest.raises(AttributeError):
            _ = Location.layer  # type: ignore[attr-defined]


class TestLocationInheritance:
    def test_is_composite_element(self) -> None:
        assert isinstance(Location(name="x"), CompositeElement)

    def test_is_element(self) -> None:
        assert isinstance(Location(name="x"), Element)

    def test_is_concept(self) -> None:
        assert isinstance(Location(name="x"), Concept)


# ---------------------------------------------------------------------------
# STORY-04.6.1 / STORY-04.6.4: Interaction >= 2 assigned elements
# ---------------------------------------------------------------------------


class TestInteractionValidation:
    def test_zero_assigned_raises(self) -> None:
        with pytest.raises(ValueError, match="requires >= 2"):
            StubInteraction(name="i")

    def test_one_assigned_raises(self) -> None:
        a = StubActiveStructure(name="a")
        with pytest.raises(ValueError, match="requires >= 2"):
            StubInteraction(name="i", assigned_elements=[a])

    def test_two_assigned_valid(self) -> None:
        a1 = StubActiveStructure(name="a1")
        a2 = StubActiveStructure(name="a2")
        i = StubInteraction(name="i", assigned_elements=[a1, a2])
        assert len(i.assigned_elements) == 2

    def test_three_assigned_valid(self) -> None:
        actors = [StubActiveStructure(name=f"a{n}") for n in range(3)]
        i = StubInteraction(name="i", assigned_elements=actors)
        assert len(i.assigned_elements) == 3


# ---------------------------------------------------------------------------
# STORY-04.6.2: Collaboration >= 2 internal active structure (xfail)
# ---------------------------------------------------------------------------


class TestCollaborationValidation:
    def test_collaboration_requires_two_internal_active(self) -> None:
        from pydantic import ValidationError as PydanticValidationError

        from etcion.metamodel.business import BusinessActor, BusinessCollaboration

        a = BusinessActor(name="a")
        with pytest.raises(PydanticValidationError):
            BusinessCollaboration(name="collab", assigned_elements=[a])


# ---------------------------------------------------------------------------
# STORY-04.6.5: Event.time attribute
# ---------------------------------------------------------------------------


class TestEventTime:
    def test_time_defaults_to_none(self) -> None:
        e = StubEvent(name="ev")
        assert e.time is None

    def test_time_accepts_datetime(self) -> None:
        dt = datetime(2026, 6, 15, 9, 0)
        e = StubEvent(name="ev", time=dt)
        assert e.time == dt

    def test_time_accepts_string(self) -> None:
        e = StubEvent(name="ev", time="end of Q2")
        assert e.time == "end of Q2"

    def test_time_in_model_dump(self) -> None:
        e = StubEvent(name="ev", time="2026-Q3")
        dump = e.model_dump()
        assert dump["time"] == "2026-Q3"
