"""Conformance test suite for pyarchi against the ArchiMate 3.2 specification.

Test Strategy
-------------
This file is an *executable specification* of the library's conformance
requirements.  It does not test implementation behaviour (that is the
responsibility of each epic's unit tests); it tests that the public API
surface declared by :class:`pyarchi.ConformanceProfile` actually exists.

Marker Strategy
~~~~~~~~~~~~~~~
* **TestConformanceProfile** -- No markers.  These tests pass immediately
  once ``conformance.py`` (FEAT-01.1) is implemented.
* **TestShallFeatures** -- ``@pytest.mark.xfail(strict=False)``.  Each test
  is expected to fail until the implementing epic exports the required types
  from ``pyarchi.__init__``.  ``strict=False`` means an unexpected pass
  (xpass) is tolerated, allowing tests to silently transition to green.
* **TestShouldFeatures** -- Same ``xfail`` pattern, with Phase 2 reasons.
* **TestMayFeatures** -- ``@pytest.mark.skip``.  These features are out of
  scope and should never appear as expected failures.

When an epic is complete and its types are exported from ``pyarchi.__init__``,
remove the ``xfail`` marker from the corresponding test so it appears as a
normal ``PASSED`` result in the test report.
"""

from __future__ import annotations

import dataclasses

import pytest

import pyarchi
from pyarchi import CONFORMANCE, SPEC_VERSION, ConformanceProfile

# ---------------------------------------------------------------------------
# TestConformanceProfile -- passes immediately once FEAT-01.1 is done
# ---------------------------------------------------------------------------


class TestConformanceProfile:
    """Verify the ConformanceProfile dataclass and the CONFORMANCE singleton."""

    def test_spec_version_is_3_2(self) -> None:
        assert CONFORMANCE.spec_version == "3.2"

    def test_spec_version_matches_module_constant(self) -> None:
        assert CONFORMANCE.spec_version == SPEC_VERSION

    def test_shall_features_are_true(self) -> None:
        assert CONFORMANCE.language_structure is True
        assert CONFORMANCE.generic_metamodel is True
        assert CONFORMANCE.strategy_elements is True
        assert CONFORMANCE.motivation_elements is True
        assert CONFORMANCE.business_elements is True
        assert CONFORMANCE.application_elements is True
        assert CONFORMANCE.technology_elements is True
        assert CONFORMANCE.physical_elements is True
        assert CONFORMANCE.implementation_migration_elements is True
        assert CONFORMANCE.cross_layer_relationships is True
        assert CONFORMANCE.relationship_permission_table is True
        assert CONFORMANCE.iconography_metadata is True

    def test_should_features_are_true(self) -> None:
        assert CONFORMANCE.viewpoint_mechanism is True
        assert CONFORMANCE.language_customization is True

    def test_may_features_are_false(self) -> None:
        assert CONFORMANCE.example_viewpoints is False

    def test_profile_is_frozen(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            CONFORMANCE.language_structure = False  # type: ignore[misc]

    def test_conformance_is_conformanceprofile_instance(self) -> None:
        assert isinstance(CONFORMANCE, ConformanceProfile)


# ---------------------------------------------------------------------------
# TestShallFeatures -- xfail until the implementing epic is complete
# ---------------------------------------------------------------------------


class TestShallFeatures:
    """Assert that every shall-level feature is present in the public API.

    Each test checks ``hasattr(pyarchi, "TypeName")`` for the types
    required by the corresponding :class:`ConformanceProfile` field.
    Tests are marked ``xfail(strict=False)`` until the implementing epic
    exports the types from ``pyarchi.__init__``.
    """

    def test_language_structure(self) -> None:
        assert hasattr(pyarchi, "Layer")
        assert hasattr(pyarchi, "Aspect")

    def test_generic_metamodel(self) -> None:
        assert hasattr(pyarchi, "Concept")
        assert hasattr(pyarchi, "Element")
        assert hasattr(pyarchi, "Relationship")
        assert hasattr(pyarchi, "RelationshipConnector")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-004: Strategy layer elements not yet implemented",
    )
    def test_strategy_elements(self) -> None:
        assert hasattr(pyarchi, "Resource")
        assert hasattr(pyarchi, "Capability")
        assert hasattr(pyarchi, "ValueStream")
        assert hasattr(pyarchi, "CourseOfAction")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-004: Motivation layer elements not yet implemented",
    )
    def test_motivation_elements(self) -> None:
        assert hasattr(pyarchi, "Stakeholder")
        assert hasattr(pyarchi, "Driver")
        assert hasattr(pyarchi, "Assessment")
        assert hasattr(pyarchi, "Goal")
        assert hasattr(pyarchi, "Outcome")
        assert hasattr(pyarchi, "Principle")
        assert hasattr(pyarchi, "Requirement")
        assert hasattr(pyarchi, "Constraint")
        assert hasattr(pyarchi, "Meaning")
        assert hasattr(pyarchi, "Value")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-004: Business layer elements not yet implemented",
    )
    def test_business_elements(self) -> None:
        assert hasattr(pyarchi, "BusinessActor")
        assert hasattr(pyarchi, "BusinessRole")
        assert hasattr(pyarchi, "BusinessCollaboration")
        assert hasattr(pyarchi, "BusinessInterface")
        assert hasattr(pyarchi, "BusinessProcess")
        assert hasattr(pyarchi, "BusinessFunction")
        assert hasattr(pyarchi, "BusinessInteraction")
        assert hasattr(pyarchi, "BusinessEvent")
        assert hasattr(pyarchi, "BusinessService")
        assert hasattr(pyarchi, "BusinessObject")
        assert hasattr(pyarchi, "Contract")
        assert hasattr(pyarchi, "Representation")
        assert hasattr(pyarchi, "Product")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-004: Application layer elements not yet implemented",
    )
    def test_application_elements(self) -> None:
        assert hasattr(pyarchi, "ApplicationComponent")
        assert hasattr(pyarchi, "ApplicationCollaboration")
        assert hasattr(pyarchi, "ApplicationInterface")
        assert hasattr(pyarchi, "ApplicationFunction")
        assert hasattr(pyarchi, "ApplicationInteraction")
        assert hasattr(pyarchi, "ApplicationProcess")
        assert hasattr(pyarchi, "ApplicationEvent")
        assert hasattr(pyarchi, "ApplicationService")
        assert hasattr(pyarchi, "DataObject")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-004: Technology layer elements not yet implemented",
    )
    def test_technology_elements(self) -> None:
        assert hasattr(pyarchi, "Node")
        assert hasattr(pyarchi, "Device")
        assert hasattr(pyarchi, "SystemSoftware")
        assert hasattr(pyarchi, "TechnologyCollaboration")
        assert hasattr(pyarchi, "TechnologyInterface")
        assert hasattr(pyarchi, "Path")
        assert hasattr(pyarchi, "CommunicationNetwork")
        assert hasattr(pyarchi, "TechnologyFunction")
        assert hasattr(pyarchi, "TechnologyProcess")
        assert hasattr(pyarchi, "TechnologyInteraction")
        assert hasattr(pyarchi, "TechnologyEvent")
        assert hasattr(pyarchi, "TechnologyService")
        assert hasattr(pyarchi, "Artifact")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-004: Physical layer elements not yet implemented",
    )
    def test_physical_elements(self) -> None:
        assert hasattr(pyarchi, "Equipment")
        assert hasattr(pyarchi, "Facility")
        assert hasattr(pyarchi, "DistributionNetwork")
        assert hasattr(pyarchi, "Material")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-004: Implementation & Migration elements not yet implemented",
    )
    def test_implementation_migration_elements(self) -> None:
        assert hasattr(pyarchi, "WorkPackage")
        assert hasattr(pyarchi, "Deliverable")
        assert hasattr(pyarchi, "ImplementationEvent")
        assert hasattr(pyarchi, "Plateau")
        assert hasattr(pyarchi, "Gap")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-005: Relationship types and Junction not yet implemented",
    )
    def test_cross_layer_relationships(self) -> None:
        assert hasattr(pyarchi, "Composition")
        assert hasattr(pyarchi, "Aggregation")
        assert hasattr(pyarchi, "Assignment")
        assert hasattr(pyarchi, "Realization")
        assert hasattr(pyarchi, "Serving")
        assert hasattr(pyarchi, "Access")
        assert hasattr(pyarchi, "Influence")
        assert hasattr(pyarchi, "Association")
        assert hasattr(pyarchi, "Triggering")
        assert hasattr(pyarchi, "Flow")
        assert hasattr(pyarchi, "Specialization")
        assert hasattr(pyarchi, "Junction")

    @pytest.mark.xfail(
        strict=False,
        reason="EPIC-005 (FEAT-05.11): Permission table not yet implemented",
    )
    def test_relationship_permission_table(self) -> None:
        assert hasattr(pyarchi, "is_permitted")

    def test_iconography_metadata(self) -> None:
        assert hasattr(pyarchi, "NotationMetadata")


# ---------------------------------------------------------------------------
# TestShouldFeatures -- xfail, Phase 2
# ---------------------------------------------------------------------------


class TestShouldFeatures:
    """Assert that should-level features are present in the public API.

    These features are planned for Phase 2.  Tests use the same
    ``xfail(strict=False)`` pattern as shall-level tests.
    """

    @pytest.mark.xfail(
        strict=False,
        reason="Phase 2: Viewpoint mechanism not yet implemented",
    )
    def test_viewpoint_mechanism(self) -> None:
        assert hasattr(pyarchi, "Viewpoint")

    @pytest.mark.xfail(
        strict=False,
        reason="Phase 2: Language customization not yet implemented",
    )
    def test_language_customization(self) -> None:
        assert hasattr(pyarchi, "Profile")


# ---------------------------------------------------------------------------
# TestMayFeatures -- skip (out of scope)
# ---------------------------------------------------------------------------


class TestMayFeatures:
    """Document may-level features that are explicitly out of scope.

    These tests are skipped, not xfail, because the library does not plan
    to implement them in any phase.
    """

    @pytest.mark.skip(
        reason="Appendix C example viewpoints are out of scope for Phase 1",
    )
    def test_example_viewpoints(self) -> None:
        # Placeholder -- if implemented, would check for concrete viewpoint
        # classes such as BasicViewpoint, OrganizationViewpoint, etc.
        pass


# ---------------------------------------------------------------------------
# TestUndefinedTypeGuard -- xfail until EPIC-002 implements Model + Concept
# ---------------------------------------------------------------------------


class TestUndefinedTypeGuard:
    """Verify that Model.add() rejects non-Concept arguments with TypeError.

    These tests are specified by ADR-005 and will pass once EPIC-002
    implements the Model container (FEAT-02.6) and Concept ABC (FEAT-02.1).
    Until then, they fail with AttributeError (pyarchi.Model does not exist)
    which is absorbed by the xfail marker.
    """

    def test_dict_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            pyarchi.Model().add({})  # type: ignore[arg-type]

    def test_arbitrary_object_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            pyarchi.Model().add(object())  # type: ignore[arg-type]

    def test_non_concept_class_raises_type_error(self) -> None:
        class Fake:
            pass

        with pytest.raises(TypeError):
            pyarchi.Model().add(Fake())  # type: ignore[arg-type]
