"""Merged tests: test_feat141_phase2_exports, test_feat203_exports."""

from __future__ import annotations

import pytest

import etcion

_PHASE2_TYPES: list[str] = [
    # Strategy layer (EPIC-006)
    "StrategyStructureElement",
    "StrategyBehaviorElement",
    "Resource",
    "Capability",
    "ValueStream",
    "CourseOfAction",
    # Business layer (EPIC-007)
    "BusinessInternalActiveStructureElement",
    "BusinessInternalBehaviorElement",
    "BusinessPassiveStructureElement",
    "BusinessActor",
    "BusinessRole",
    "BusinessCollaboration",
    "BusinessInterface",
    "BusinessProcess",
    "BusinessFunction",
    "BusinessInteraction",
    "BusinessEvent",
    "BusinessService",
    "BusinessObject",
    "Contract",
    "Representation",
    "Product",
    # Application layer (EPIC-008)
    "ApplicationInternalActiveStructureElement",
    "ApplicationInternalBehaviorElement",
    "ApplicationComponent",
    "ApplicationCollaboration",
    "ApplicationInterface",
    "ApplicationFunction",
    "ApplicationInteraction",
    "ApplicationProcess",
    "ApplicationEvent",
    "ApplicationService",
    "DataObject",
    # Technology layer (EPIC-009)
    "TechnologyInternalActiveStructureElement",
    "TechnologyInternalBehaviorElement",
    "Node",
    "Device",
    "SystemSoftware",
    "TechnologyCollaboration",
    "TechnologyInterface",
    "Path",
    "CommunicationNetwork",
    "TechnologyFunction",
    "TechnologyProcess",
    "TechnologyInteraction",
    "TechnologyEvent",
    "TechnologyService",
    "Artifact",
    # Physical layer (EPIC-010)
    "PhysicalActiveStructureElement",
    "PhysicalPassiveStructureElement",
    "Equipment",
    "Facility",
    "DistributionNetwork",
    "Material",
    # Motivation layer (EPIC-011)
    "Stakeholder",
    "Driver",
    "Assessment",
    "Goal",
    "Outcome",
    "Principle",
    "Requirement",
    "Constraint",
    "Meaning",
    "Value",
    # Implementation & Migration layer (EPIC-012)
    "WorkPackage",
    "Deliverable",
    "ImplementationEvent",
    "Plateau",
    "Gap",
]


class TestPhase2Exports:
    @pytest.mark.parametrize("name", _PHASE2_TYPES)
    def test_public_api_export(self, name: str) -> None:
        import etcion

        attr = getattr(etcion, name, None)
        assert attr is not None, f"{name} not exported from etcion"

    @pytest.mark.parametrize("name", _PHASE2_TYPES)
    def test_in_all(self, name: str) -> None:
        import etcion

        assert name in etcion.__all__, f"{name} missing from etcion.__all__"

    def test_phase2_count(self) -> None:
        assert len(_PHASE2_TYPES) == 69


PHASE_3_EXPORTS = [
    "Viewpoint",
    "View",
    "Concern",
    "Profile",
    "PurposeCategory",
    "ContentCategory",
]


class TestPhase3Exports:
    @pytest.mark.parametrize("name", PHASE_3_EXPORTS)
    def test_symbol_importable_from_etcion(self, name: str) -> None:
        assert hasattr(etcion, name), f"{name} not found in etcion namespace"

    @pytest.mark.parametrize("name", PHASE_3_EXPORTS)
    def test_symbol_in_all(self, name: str) -> None:
        assert name in etcion.__all__, f"{name} not in etcion.__all__"

    def test_no_serialization_functions_in_all(self) -> None:
        forbidden = {
            "serialize_model",
            "deserialize_model",
            "write_model",
            "read_model",
            "model_to_dict",
            "model_from_dict",
        }
        leaked = forbidden & set(etcion.__all__)
        assert leaked == set(), f"Serialization functions leaked into __all__: {leaked}"
