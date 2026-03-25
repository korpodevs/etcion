"""Tests for FEAT-12.2 -- Plateau composite element."""

from __future__ import annotations

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import CompositeElement
from pyarchi.metamodel.implementation_migration import Plateau, WorkPackage


class TestInstantiation:
    def test_can_instantiate(self) -> None:
        p = Plateau(name="Target Architecture")
        assert p.name == "Target Architecture"

    def test_type_name(self) -> None:
        assert Plateau(name="x")._type_name == "Plateau"


class TestInheritance:
    def test_is_composite_element(self) -> None:
        assert issubclass(Plateau, CompositeElement)

    def test_isinstance_composite_element(self) -> None:
        assert isinstance(Plateau(name="x"), CompositeElement)


class TestClassVars:
    def test_layer(self) -> None:
        assert Plateau.layer is Layer.IMPLEMENTATION_MIGRATION

    def test_aspect(self) -> None:
        assert Plateau.aspect is Aspect.COMPOSITE


class TestNotation:
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
