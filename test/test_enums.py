"""Merged tests for test_enums."""

from __future__ import annotations

from typing import ClassVar

import pytest

import etcion
from etcion.enums import Aspect, Layer, RelationshipCategory
from etcion.metamodel.concepts import Element


class TestLayerEnum:
    def test_layer_has_seven_members(self) -> None:
        """Layer enum contains exactly seven members."""
        assert len(Layer) == 7

    def test_all_member_names_present(self) -> None:
        """All seven ArchiMate layer names are accessible as Layer.<NAME>."""
        expected = {
            "STRATEGY",
            "MOTIVATION",
            "BUSINESS",
            "APPLICATION",
            "TECHNOLOGY",
            "PHYSICAL",
            "IMPLEMENTATION_MIGRATION",
        }
        assert {m.name for m in Layer} == expected

    def test_strategy_value(self) -> None:
        assert Layer.STRATEGY.value == "Strategy"

    def test_motivation_value(self) -> None:
        assert Layer.MOTIVATION.value == "Motivation"

    def test_business_value(self) -> None:
        assert Layer.BUSINESS.value == "Business"

    def test_application_value(self) -> None:
        assert Layer.APPLICATION.value == "Application"

    def test_technology_value(self) -> None:
        assert Layer.TECHNOLOGY.value == "Technology"

    def test_physical_value(self) -> None:
        assert Layer.PHYSICAL.value == "Physical"

    def test_implementation_migration_value(self) -> None:
        assert Layer.IMPLEMENTATION_MIGRATION.value == "Implementation and Migration"

    def test_layer_importable_from_etcion(self) -> None:
        """Layer is re-exported from the top-level etcion package."""
        from etcion import Layer as TopLevelLayer

        assert TopLevelLayer is Layer

    def test_layer_in_etcion_all(self) -> None:
        """Layer appears in etcion.__all__."""
        assert "Layer" in etcion.__all__

    def test_enum_not_str_equal(self) -> None:
        """Layer uses enum.Enum, not StrEnum -- members do not equal plain strings."""
        assert Layer.BUSINESS != "Business"


class TestAspectEnum:
    def test_aspect_has_five_members(self) -> None:
        """Aspect enum contains exactly five members."""
        assert len(Aspect) == 5

    def test_all_member_names_present(self) -> None:
        """All five ArchiMate aspect names are accessible as Aspect.<NAME>."""
        expected = {
            "ACTIVE_STRUCTURE",
            "BEHAVIOR",
            "PASSIVE_STRUCTURE",
            "MOTIVATION",
            "COMPOSITE",
        }
        assert {m.name for m in Aspect} == expected

    def test_active_structure_value(self) -> None:
        assert Aspect.ACTIVE_STRUCTURE.value == "Active Structure"

    def test_behavior_value(self) -> None:
        assert Aspect.BEHAVIOR.value == "Behavior"

    def test_passive_structure_value(self) -> None:
        assert Aspect.PASSIVE_STRUCTURE.value == "Passive Structure"

    def test_motivation_value(self) -> None:
        assert Aspect.MOTIVATION.value == "Motivation"

    def test_composite_value(self) -> None:
        assert Aspect.COMPOSITE.value == "Composite"

    def test_aspect_importable_from_etcion(self) -> None:
        """Aspect is re-exported from the top-level etcion package."""
        from etcion import Aspect as TopLevelAspect

        assert TopLevelAspect is Aspect

    def test_aspect_in_etcion_all(self) -> None:
        """Aspect appears in etcion.__all__."""
        assert "Aspect" in etcion.__all__

    def test_enum_not_str_equal(self) -> None:
        """Aspect uses enum.Enum, not StrEnum -- members do not equal plain strings."""
        assert Aspect.BEHAVIOR != "Behavior"


# ---------------------------------------------------------------------------
# Test-local helper: a minimal concrete Element subclass
# ---------------------------------------------------------------------------


class _StubElement(Element):
    """Minimal concrete Element for testing the ClassVar pattern.

    This class exists only in the test module.  It is NOT part of the
    production codebase.
    """

    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "StubElement"


# ---------------------------------------------------------------------------
# TestClassVarClassificationPattern -- proves the mechanism works
# ---------------------------------------------------------------------------


class TestClassVarClassificationPattern:
    """Demonstrate that ClassVar[Layer] and ClassVar[Aspect] work correctly
    on a Pydantic-based Element subclass.

    These tests validate STORY-03.4.1's contract: the ClassVar pattern is
    viable for classification metadata on concrete element classes.
    """

    def test_layer_is_correct_enum_member(self) -> None:
        assert _StubElement.layer is Layer.BUSINESS

    def test_aspect_is_correct_enum_member(self) -> None:
        assert _StubElement.aspect is Aspect.ACTIVE_STRUCTURE

    def test_layer_is_layer_instance(self) -> None:
        assert isinstance(_StubElement.layer, Layer)

    def test_aspect_is_aspect_instance(self) -> None:
        assert isinstance(_StubElement.aspect, Aspect)

    def test_layer_not_in_model_fields(self) -> None:
        """ClassVar[Layer] must not appear in Pydantic model_fields."""
        assert "layer" not in _StubElement.model_fields

    def test_aspect_not_in_model_fields(self) -> None:
        """ClassVar[Aspect] must not appear in Pydantic model_fields."""
        assert "aspect" not in _StubElement.model_fields

    def test_layer_excluded_from_model_dump(self) -> None:
        """ClassVar values must not leak into model_dump() output."""
        instance = _StubElement(name="test")
        dump = instance.model_dump()
        assert "layer" not in dump

    def test_aspect_excluded_from_model_dump(self) -> None:
        """ClassVar values must not leak into model_dump() output."""
        instance = _StubElement(name="test")
        dump = instance.model_dump()
        assert "aspect" not in dump

    def test_layer_accessible_on_instance(self) -> None:
        """layer is accessible via instance attribute lookup (MRO)."""
        instance = _StubElement(name="test")
        assert instance.layer is Layer.BUSINESS

    def test_aspect_accessible_on_instance(self) -> None:
        """aspect is accessible via instance attribute lookup (MRO)."""
        instance = _StubElement(name="test")
        assert instance.aspect is Aspect.ACTIVE_STRUCTURE


# ---------------------------------------------------------------------------
# TestAllConcreteElementsHaveClassification -- xfail until EPIC-004
# ---------------------------------------------------------------------------


class TestAllConcreteElementsHaveClassification:
    """Discover all concrete Element subclasses and assert each defines
    layer: Layer and aspect: Aspect.

    This test is marked xfail because no concrete Element subclasses exist
    in production code yet (they are introduced in EPIC-004).  When EPIC-004
    ships, remove the xfail marker.
    """

    def test_all_concrete_elements_have_classification(self) -> None:
        """Every concrete Element subclass must have layer and aspect."""
        concrete_classes: list[type[Element]] = []

        def _collect_subclasses(cls: type[Element]) -> None:
            for sub in cls.__subclasses__():
                # A concrete class is one that can be instantiated --
                # it implements _type_name (not abstract).
                try:
                    # Check if _type_name is still abstract
                    if not getattr(sub._type_name.fget, "__isabstractmethod__", False):  # type: ignore[attr-defined]
                        concrete_classes.append(sub)
                except AttributeError:
                    pass
                _collect_subclasses(sub)

        _collect_subclasses(Element)  # type: ignore[type-abstract]

        # Filter out test-local stubs (classes defined in test modules)
        production_classes = [
            cls for cls in concrete_classes if not cls.__module__.startswith("test")
        ]

        # Must have at least one concrete class for this test to be meaningful
        assert len(production_classes) > 0, (
            "No concrete Element subclasses found in production code. "
            "This test will pass once EPIC-004 defines concrete element types."
        )

        missing_layer: list[str] = []
        missing_aspect: list[str] = []

        _LAYER_EXCEPTIONS: set[str] = {"Location"}  # ADR-016 ss3: cross-layer

        for cls in production_classes:
            if cls.__name__ not in _LAYER_EXCEPTIONS:
                if not (hasattr(cls, "layer") and isinstance(cls.layer, Layer)):
                    missing_layer.append(cls.__name__)
            if not (hasattr(cls, "aspect") and isinstance(cls.aspect, Aspect)):
                missing_aspect.append(cls.__name__)

        assert missing_layer == [], (
            f"Concrete Element subclasses missing layer: ClassVar[Layer]: {missing_layer}"
        )
        assert missing_aspect == [], (
            f"Concrete Element subclasses missing aspect: ClassVar[Aspect]: {missing_aspect}"
        )


class TestRelationshipCategoryMembers:
    """All four required members exist with correct values."""

    def test_structural(self) -> None:
        assert RelationshipCategory.STRUCTURAL.value == "Structural"

    def test_dependency(self) -> None:
        assert RelationshipCategory.DEPENDENCY.value == "Dependency"

    def test_dynamic(self) -> None:
        assert RelationshipCategory.DYNAMIC.value == "Dynamic"

    def test_other(self) -> None:
        assert RelationshipCategory.OTHER.value == "Other"

    def test_exactly_four_members(self) -> None:
        assert len(RelationshipCategory) == 4

    def test_iterable(self) -> None:
        names = {m.name for m in RelationshipCategory}
        assert names == {"STRUCTURAL", "DEPENDENCY", "DYNAMIC", "OTHER"}
