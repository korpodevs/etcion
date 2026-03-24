"""Tests for FEAT-05.1 -- RelationshipCategory Enum (ratification)."""

from __future__ import annotations

from pyarchi.enums import RelationshipCategory


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
