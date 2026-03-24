"""Tests for FEAT-03.2 -- Aspect Enum."""

from __future__ import annotations

import pyarchi
from pyarchi.enums import Aspect


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

    def test_aspect_importable_from_pyarchi(self) -> None:
        """Aspect is re-exported from the top-level pyarchi package."""
        from pyarchi import Aspect as TopLevelAspect

        assert TopLevelAspect is Aspect

    def test_aspect_in_pyarchi_all(self) -> None:
        """Aspect appears in pyarchi.__all__."""
        assert "Aspect" in pyarchi.__all__

    def test_enum_not_str_equal(self) -> None:
        """Aspect uses enum.Enum, not StrEnum -- members do not equal plain strings."""
        assert Aspect.BEHAVIOR != "Behavior"
