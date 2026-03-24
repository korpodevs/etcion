"""Tests for FEAT-03.1 -- Layer Enum."""

from __future__ import annotations

import pyarchi
from pyarchi.enums import Layer


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

    def test_layer_importable_from_pyarchi(self) -> None:
        """Layer is re-exported from the top-level pyarchi package."""
        from pyarchi import Layer as TopLevelLayer

        assert TopLevelLayer is Layer

    def test_layer_in_pyarchi_all(self) -> None:
        """Layer appears in pyarchi.__all__."""
        assert "Layer" in pyarchi.__all__

    def test_enum_not_str_equal(self) -> None:
        """Layer uses enum.Enum, not StrEnum -- members do not equal plain strings."""
        assert Layer.BUSINESS != "Business"
