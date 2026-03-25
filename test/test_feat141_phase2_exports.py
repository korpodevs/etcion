"""Tests for FEAT-14.1 -- Phase 2 public API exports."""

from __future__ import annotations

import pytest

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
        import pyarchi

        attr = getattr(pyarchi, name, None)
        assert attr is not None, f"{name} not exported from pyarchi"

    @pytest.mark.parametrize("name", _PHASE2_TYPES)
    def test_in_all(self, name: str) -> None:
        import pyarchi

        assert name in pyarchi.__all__, f"{name} missing from pyarchi.__all__"

    def test_phase2_count(self) -> None:
        assert len(_PHASE2_TYPES) == 69
