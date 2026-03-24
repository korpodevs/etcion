"""Tests for FEAT-03.4 -- Classification Metadata on Elements.

STORY-03.4.1 has no production code changes.  The ClassVar[Layer] and
ClassVar[Aspect] contract is established by ADR-014 and proven viable by the
pattern tests below.

STORY-03.4.2 provides two test classes:
1. TestClassVarClassificationPattern -- proves the mechanism works using a
   test-local concrete Element subclass.
2. TestAllConcreteElementsHaveClassification -- discovers all concrete Element
   subclasses at runtime and asserts each has layer and aspect.  Marked xfail
   until EPIC-004 introduces concrete element classes.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.concepts import Element

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
