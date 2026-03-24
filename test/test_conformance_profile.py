"""Acceptance tests for FEAT-01.1: ConformanceProfile.

Covers four stories:
  STORY-01.1.1 — ConformanceProfile dataclass definition and frozen immutability
  STORY-01.1.2 — All 16 fields: 1 spec_version, 12 shall-level, 2 should-level,
                  1 may-level
  STORY-01.1.3 — Re-exports from pyarchi.__init__ and SPEC_VERSION consistency
  STORY-01.1.4 — may-level field defaults False; constructing new instance with
                  True works
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
CONFORMANCE_MODULE = REPO_ROOT / "src" / "pyarchi" / "conformance.py"

# ===========================================================================
# STORY-01.1.1 — ConformanceProfile dataclass definition and frozen immutability
# ===========================================================================


class TestConformanceModuleExists:
    def test_conformance_py_exists(self) -> None:
        assert CONFORMANCE_MODULE.exists(), "src/pyarchi/conformance.py must exist"


class TestConformanceImport:
    def test_import_from_conformance_module(self) -> None:
        from pyarchi.conformance import CONFORMANCE, ConformanceProfile  # noqa: PLC0415

        assert ConformanceProfile is not None
        assert CONFORMANCE is not None

    def test_conformance_singleton_is_instance_of_profile(self) -> None:
        from pyarchi.conformance import CONFORMANCE, ConformanceProfile  # noqa: PLC0415

        assert isinstance(CONFORMANCE, ConformanceProfile)

    def test_conformance_profile_is_frozen_dataclass(self) -> None:
        from pyarchi.conformance import CONFORMANCE  # noqa: PLC0415

        with pytest.raises(dataclasses.FrozenInstanceError):
            CONFORMANCE.language_structure = False  # type: ignore[misc]


# ===========================================================================
# STORY-01.1.2 — All 16 fields with correct names and defaults
# ===========================================================================


class TestConformanceProfileFieldCount:
    def test_has_exactly_16_fields(self) -> None:
        from pyarchi.conformance import ConformanceProfile  # noqa: PLC0415

        assert len(dataclasses.fields(ConformanceProfile)) == 16


class TestSpecVersionField:
    def test_spec_version_field_exists(self) -> None:
        from pyarchi.conformance import ConformanceProfile  # noqa: PLC0415

        field_names = {f.name for f in dataclasses.fields(ConformanceProfile)}
        assert "spec_version" in field_names

    def test_spec_version_is_str_type(self) -> None:
        from pyarchi.conformance import ConformanceProfile  # noqa: PLC0415

        field_map = {f.name: f for f in dataclasses.fields(ConformanceProfile)}
        assert field_map["spec_version"].type is str or field_map["spec_version"].type == "str"

    def test_spec_version_defaults_to_3_2(self) -> None:
        from pyarchi.conformance import CONFORMANCE  # noqa: PLC0415

        assert CONFORMANCE.spec_version == "3.2"


class TestShallLevelFields:
    """All 12 shall-level boolean fields must be present and default True."""

    SHALL_FIELDS: list[str] = [
        "language_structure",
        "generic_metamodel",
        "strategy_elements",
        "motivation_elements",
        "business_elements",
        "application_elements",
        "technology_elements",
        "physical_elements",
        "implementation_migration_elements",
        "cross_layer_relationships",
        "relationship_permission_table",
        "iconography_metadata",
    ]

    def test_all_shall_fields_present(self) -> None:
        from pyarchi.conformance import ConformanceProfile  # noqa: PLC0415

        field_names = {f.name for f in dataclasses.fields(ConformanceProfile)}
        for name in self.SHALL_FIELDS:
            assert name in field_names, f"shall-level field '{name}' is missing"

    def test_all_shall_fields_default_true(self) -> None:
        from pyarchi.conformance import CONFORMANCE  # noqa: PLC0415

        for name in self.SHALL_FIELDS:
            value = getattr(CONFORMANCE, name)
            assert value is True, f"shall-level field '{name}' must default to True, got {value!r}"


class TestShouldLevelFields:
    """Both should-level boolean fields must be present and default True."""

    SHOULD_FIELDS: list[str] = [
        "viewpoint_mechanism",
        "language_customization",
    ]

    def test_all_should_fields_present(self) -> None:
        from pyarchi.conformance import ConformanceProfile  # noqa: PLC0415

        field_names = {f.name for f in dataclasses.fields(ConformanceProfile)}
        for name in self.SHOULD_FIELDS:
            assert name in field_names, f"should-level field '{name}' is missing"

    def test_all_should_fields_default_true(self) -> None:
        from pyarchi.conformance import CONFORMANCE  # noqa: PLC0415

        for name in self.SHOULD_FIELDS:
            value = getattr(CONFORMANCE, name)
            assert value is True, f"should-level field '{name}' must default to True, got {value!r}"


class TestMayLevelField:
    def test_example_viewpoints_field_present(self) -> None:
        from pyarchi.conformance import ConformanceProfile  # noqa: PLC0415

        field_names = {f.name for f in dataclasses.fields(ConformanceProfile)}
        assert "example_viewpoints" in field_names

    def test_example_viewpoints_defaults_false(self) -> None:
        from pyarchi.conformance import CONFORMANCE  # noqa: PLC0415

        assert CONFORMANCE.example_viewpoints is False


# ===========================================================================
# STORY-01.1.3 — Re-exports from pyarchi.__init__ and SPEC_VERSION consistency
# ===========================================================================


class TestInitReexports:
    def test_import_conformance_profile_from_pyarchi(self) -> None:
        from pyarchi import ConformanceProfile  # noqa: PLC0415

        assert ConformanceProfile is not None

    def test_import_conformance_singleton_from_pyarchi(self) -> None:
        from pyarchi import CONFORMANCE  # noqa: PLC0415

        assert CONFORMANCE is not None

    def test_conformance_profile_in_all(self) -> None:
        import pyarchi  # noqa: PLC0415

        assert "ConformanceProfile" in pyarchi.__all__

    def test_conformance_singleton_in_all(self) -> None:
        import pyarchi  # noqa: PLC0415

        assert "CONFORMANCE" in pyarchi.__all__

    def test_conformance_spec_version_equals_spec_version(self) -> None:
        import pyarchi  # noqa: PLC0415

        assert pyarchi.CONFORMANCE.spec_version == pyarchi.SPEC_VERSION

    def test_spec_version_value_is_3_2(self) -> None:
        import pyarchi  # noqa: PLC0415

        assert pyarchi.SPEC_VERSION == "3.2"
        assert pyarchi.CONFORMANCE.spec_version == "3.2"


# ===========================================================================
# STORY-01.1.4 — may-level field: False default, constructible with True
# ===========================================================================


class TestMayLevelFieldBehavior:
    def test_example_viewpoints_is_false_on_singleton(self) -> None:
        from pyarchi.conformance import CONFORMANCE  # noqa: PLC0415

        assert CONFORMANCE.example_viewpoints is False

    def test_new_instance_with_example_viewpoints_true(self) -> None:
        from pyarchi.conformance import ConformanceProfile  # noqa: PLC0415

        custom = ConformanceProfile(example_viewpoints=True)
        assert custom.example_viewpoints is True

    def test_singleton_not_mutated_by_new_instance(self) -> None:
        from pyarchi.conformance import CONFORMANCE, ConformanceProfile  # noqa: PLC0415

        ConformanceProfile(example_viewpoints=True)
        assert CONFORMANCE.example_viewpoints is False
