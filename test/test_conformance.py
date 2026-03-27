"""Conformance test suite for etcion against the ArchiMate 3.2 specification.

Test Strategy
-------------
This file is an *executable specification* of the library's conformance
requirements.  It does not test implementation behaviour (that is the
responsibility of each epic's unit tests); it tests that the public API
surface declared by :class:`etcion.ConformanceProfile` actually exists.

Marker Strategy
~~~~~~~~~~~~~~~
* **TestConformanceProfile** -- No markers.  These tests pass immediately
  once ``conformance.py`` (FEAT-01.1) is implemented.
* **TestShallFeatures** -- ``@pytest.mark.xfail(strict=False)``.  Each test
  is expected to fail until the implementing epic exports the required types
  from ``etcion.__init__``.  ``strict=False`` means an unexpected pass
  (xpass) is tolerated, allowing tests to silently transition to green.
* **TestShouldFeatures** -- Same ``xfail`` pattern, with Phase 2 reasons.
* **TestMayFeatures** -- ``@pytest.mark.skip``.  These features are out of
  scope and should never appear as expected failures.

When an epic is complete and its types are exported from ``etcion.__init__``,
remove the ``xfail`` marker from the corresponding test so it appears as a
normal ``PASSED`` result in the test report.
"""

from __future__ import annotations

import dataclasses

import pytest

import etcion
from etcion import CONFORMANCE, SPEC_VERSION, ConformanceProfile

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

    Each test checks ``hasattr(etcion, "TypeName")`` for the types
    required by the corresponding :class:`ConformanceProfile` field.
    Tests are marked ``xfail(strict=False)`` until the implementing epic
    exports the types from ``etcion.__init__``.
    """

    def test_language_structure(self) -> None:
        assert hasattr(etcion, "Layer")
        assert hasattr(etcion, "Aspect")

    def test_generic_metamodel(self) -> None:
        assert hasattr(etcion, "Concept")
        assert hasattr(etcion, "Element")
        assert hasattr(etcion, "Relationship")
        assert hasattr(etcion, "RelationshipConnector")

    def test_strategy_elements(self) -> None:
        assert hasattr(etcion, "Resource")
        assert hasattr(etcion, "Capability")
        assert hasattr(etcion, "ValueStream")
        assert hasattr(etcion, "CourseOfAction")

    def test_motivation_elements(self) -> None:
        assert hasattr(etcion, "Stakeholder")
        assert hasattr(etcion, "Driver")
        assert hasattr(etcion, "Assessment")
        assert hasattr(etcion, "Goal")
        assert hasattr(etcion, "Outcome")
        assert hasattr(etcion, "Principle")
        assert hasattr(etcion, "Requirement")
        assert hasattr(etcion, "Constraint")
        assert hasattr(etcion, "Meaning")
        assert hasattr(etcion, "Value")

    def test_business_elements(self) -> None:
        assert hasattr(etcion, "BusinessActor")
        assert hasattr(etcion, "BusinessRole")
        assert hasattr(etcion, "BusinessCollaboration")
        assert hasattr(etcion, "BusinessInterface")
        assert hasattr(etcion, "BusinessProcess")
        assert hasattr(etcion, "BusinessFunction")
        assert hasattr(etcion, "BusinessInteraction")
        assert hasattr(etcion, "BusinessEvent")
        assert hasattr(etcion, "BusinessService")
        assert hasattr(etcion, "BusinessObject")
        assert hasattr(etcion, "Contract")
        assert hasattr(etcion, "Representation")
        assert hasattr(etcion, "Product")

    def test_application_elements(self) -> None:
        assert hasattr(etcion, "ApplicationComponent")
        assert hasattr(etcion, "ApplicationCollaboration")
        assert hasattr(etcion, "ApplicationInterface")
        assert hasattr(etcion, "ApplicationFunction")
        assert hasattr(etcion, "ApplicationInteraction")
        assert hasattr(etcion, "ApplicationProcess")
        assert hasattr(etcion, "ApplicationEvent")
        assert hasattr(etcion, "ApplicationService")
        assert hasattr(etcion, "DataObject")

    def test_technology_elements(self) -> None:
        assert hasattr(etcion, "Node")
        assert hasattr(etcion, "Device")
        assert hasattr(etcion, "SystemSoftware")
        assert hasattr(etcion, "TechnologyCollaboration")
        assert hasattr(etcion, "TechnologyInterface")
        assert hasattr(etcion, "Path")
        assert hasattr(etcion, "CommunicationNetwork")
        assert hasattr(etcion, "TechnologyFunction")
        assert hasattr(etcion, "TechnologyProcess")
        assert hasattr(etcion, "TechnologyInteraction")
        assert hasattr(etcion, "TechnologyEvent")
        assert hasattr(etcion, "TechnologyService")
        assert hasattr(etcion, "Artifact")

    def test_physical_elements(self) -> None:
        assert hasattr(etcion, "Equipment")
        assert hasattr(etcion, "Facility")
        assert hasattr(etcion, "DistributionNetwork")
        assert hasattr(etcion, "Material")

    def test_implementation_migration_elements(self) -> None:
        assert hasattr(etcion, "WorkPackage")
        assert hasattr(etcion, "Deliverable")
        assert hasattr(etcion, "ImplementationEvent")
        assert hasattr(etcion, "Plateau")
        assert hasattr(etcion, "Gap")

    def test_cross_layer_relationships(self) -> None:
        assert hasattr(etcion, "Composition")
        assert hasattr(etcion, "Aggregation")
        assert hasattr(etcion, "Assignment")
        assert hasattr(etcion, "Realization")
        assert hasattr(etcion, "Serving")
        assert hasattr(etcion, "Access")
        assert hasattr(etcion, "Influence")
        assert hasattr(etcion, "Association")
        assert hasattr(etcion, "Triggering")
        assert hasattr(etcion, "Flow")
        assert hasattr(etcion, "Specialization")
        assert hasattr(etcion, "Junction")

    def test_relationship_permission_table(self) -> None:
        assert hasattr(etcion, "is_permitted")

    def test_iconography_metadata(self) -> None:
        assert hasattr(etcion, "NotationMetadata")


# ---------------------------------------------------------------------------
# TestShouldFeatures -- xfail, Phase 2
# ---------------------------------------------------------------------------


class TestShouldFeatures:
    """Assert that should-level features are present in the public API.

    These features are planned for Phase 2.  Tests use the same
    ``xfail(strict=False)`` pattern as shall-level tests.
    """

    def test_viewpoint_mechanism(self) -> None:
        assert hasattr(etcion, "Viewpoint")

    def test_language_customization(self) -> None:
        assert hasattr(etcion, "Profile")


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
    Until then, they fail with AttributeError (etcion.Model does not exist)
    which is absorbed by the xfail marker.
    """

    def test_dict_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            etcion.Model().add({})  # type: ignore[arg-type]

    def test_arbitrary_object_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            etcion.Model().add(object())  # type: ignore[arg-type]

    def test_non_concept_class_raises_type_error(self) -> None:
        class Fake:
            pass

        with pytest.raises(TypeError):
            etcion.Model().add(Fake())  # type: ignore[arg-type]
