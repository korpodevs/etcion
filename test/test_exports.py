"""Merged tests: test_feat141_phase2_exports, test_feat203_exports."""

from __future__ import annotations

import pytest

import etcion

ALL_PUBLIC_TYPES: list[str] = [
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
    # Views layer (EPIC-phase3)
    "Viewpoint",
    "View",
    "Concern",
    "Profile",
    "PurposeCategory",
    "ContentCategory",
]


@pytest.mark.parametrize("name", ALL_PUBLIC_TYPES)
def test_public_export(name: str) -> None:
    assert hasattr(etcion, name), f"{name} not importable from etcion"
    assert name in etcion.__all__, f"{name} not in etcion.__all__"


def test_no_serialization_functions_in_all() -> None:
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
