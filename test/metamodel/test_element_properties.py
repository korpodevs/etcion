"""Data-driven element registry: parametrized property tests over all concrete types.

Covers the five repeated property checks that were duplicated across all six
layer test files:
1. Type name matches class name
2. Layer class variable is correct
3. Aspect class variable is correct
4. Notation layer_color is correct
5. Notation badge_letter is correct
6. Notation corner_shape is correct
7. Element can be instantiated with a name
8. Instantiated element gets a UUID

Classes that require more than ``name=`` to instantiate (Collaborations and
Interactions) use a factory callable instead of bare ``cls(name="x")``.
Layer-specific behaviour tests (validators, time fields, etc.) stay in each
layer's own test file.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pytest

from etcion.enums import Aspect, Layer
from etcion.metamodel.application import (
    ApplicationCollaboration,
    ApplicationComponent,
    ApplicationEvent,
    ApplicationFunction,
    ApplicationInteraction,
    ApplicationInterface,
    ApplicationProcess,
    ApplicationService,
    DataObject,
)
from etcion.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessEvent,
    BusinessFunction,
    BusinessInteraction,
    BusinessInterface,
    BusinessObject,
    BusinessProcess,
    BusinessRole,
    BusinessService,
    Contract,
    Product,
    Representation,
)
from etcion.metamodel.implementation_migration import (
    Deliverable,
    Gap,
    ImplementationEvent,
    Plateau,
    WorkPackage,
)
from etcion.metamodel.motivation import (
    Assessment,
    Constraint,
    Driver,
    Goal,
    Meaning,
    Outcome,
    Principle,
    Requirement,
    Stakeholder,
    Value,
)
from etcion.metamodel.physical import (
    DistributionNetwork,
    Equipment,
    Facility,
    Material,
)
from etcion.metamodel.strategy import (
    Capability,
    CourseOfAction,
    Resource,
    ValueStream,
)
from etcion.metamodel.technology import (
    Artifact,
    CommunicationNetwork,
    Device,
    Node,
    Path,
    SystemSoftware,
    TechnologyCollaboration,
    TechnologyEvent,
    TechnologyFunction,
    TechnologyInteraction,
    TechnologyInterface,
    TechnologyProcess,
    TechnologyService,
)

# ---------------------------------------------------------------------------
# Factory helpers for elements that need assigned_elements
# ---------------------------------------------------------------------------


def _make_business_collaboration() -> BusinessCollaboration:
    a1 = BusinessActor(name="a1")
    a2 = BusinessActor(name="a2")
    return BusinessCollaboration(name="x", assigned_elements=[a1, a2])


def _make_business_interaction() -> BusinessInteraction:
    a1 = BusinessActor(name="a1")
    a2 = BusinessActor(name="a2")
    return BusinessInteraction(name="x", assigned_elements=[a1, a2])


def _make_application_collaboration() -> ApplicationCollaboration:
    c1 = ApplicationComponent(name="c1")
    c2 = ApplicationComponent(name="c2")
    return ApplicationCollaboration(name="x", assigned_elements=[c1, c2])


def _make_application_interaction() -> ApplicationInteraction:
    c1 = ApplicationComponent(name="c1")
    c2 = ApplicationComponent(name="c2")
    return ApplicationInteraction(name="x", assigned_elements=[c1, c2])


def _make_technology_collaboration() -> TechnologyCollaboration:
    n1 = Node(name="n1")
    n2 = Node(name="n2")
    return TechnologyCollaboration(name="x", assigned_elements=[n1, n2])


def _make_technology_interaction() -> TechnologyInteraction:
    n1 = Node(name="n1")
    n2 = Node(name="n2")
    return TechnologyInteraction(name="x", assigned_elements=[n1, n2])


def _make_gap() -> Gap:
    pa = Plateau(name="pa")
    pb = Plateau(name="pb")
    return Gap(name="x", plateau_a=pa, plateau_b=pb)


# ---------------------------------------------------------------------------
# ElementSpec registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ElementSpec:
    """Properties expected for a single concrete element class.

    Attributes:
        cls:          The concrete element class under test.
        type_name:    Expected value of ``instance._type_name``.
        layer:        Expected ``cls.layer`` enum value.
        aspect:       Expected ``cls.aspect`` enum value.
        layer_color:  Expected ``cls.notation.layer_color`` hex string.
        badge_letter: Expected ``cls.notation.badge_letter`` character.
        corner_shape: Expected ``cls.notation.corner_shape`` string.
        factory:      Optional callable that creates an instance when the
                      class cannot be constructed with just ``name="x"``.
    """

    cls: type
    type_name: str
    layer: Layer
    aspect: Aspect
    layer_color: str
    badge_letter: str
    corner_shape: str
    factory: Callable[[], object] | None = None


# Business layer — color #FFFFB5, badge "B"
_B_COLOR = "#FFFFB5"
_B_BADGE = "B"

# Application layer — color #B5FFFF, badge "A"
_A_COLOR = "#B5FFFF"
_A_BADGE = "A"

# Technology & Physical layer (shared green) — badge "T" / "P"
_T_COLOR = "#C9E7B7"

# Motivation layer — color #CCCCFF, badge "M"
_M_COLOR = "#CCCCFF"
_M_BADGE = "M"

# Strategy layer — color #F5DEAA, badge "S"
_S_COLOR = "#F5DEAA"
_S_BADGE = "S"

# Implementation & Migration layer — color #FFE0E0, badge "I"
_I_COLOR = "#FFE0E0"
_I_BADGE = "I"


ELEMENT_SPECS: list[ElementSpec] = [
    # ------------------------------------------------------------------
    # Business — Active Structure
    # ------------------------------------------------------------------
    ElementSpec(
        BusinessActor,
        "BusinessActor",
        Layer.BUSINESS,
        Aspect.ACTIVE_STRUCTURE,
        _B_COLOR,
        _B_BADGE,
        "square",
    ),
    ElementSpec(
        BusinessRole,
        "BusinessRole",
        Layer.BUSINESS,
        Aspect.ACTIVE_STRUCTURE,
        _B_COLOR,
        _B_BADGE,
        "square",
    ),
    ElementSpec(
        BusinessCollaboration,
        "BusinessCollaboration",
        Layer.BUSINESS,
        Aspect.ACTIVE_STRUCTURE,
        _B_COLOR,
        _B_BADGE,
        "square",
        factory=_make_business_collaboration,
    ),
    ElementSpec(
        BusinessInterface,
        "BusinessInterface",
        Layer.BUSINESS,
        Aspect.ACTIVE_STRUCTURE,
        _B_COLOR,
        _B_BADGE,
        "square",
    ),
    # Business — Behavior
    ElementSpec(
        BusinessProcess,
        "BusinessProcess",
        Layer.BUSINESS,
        Aspect.BEHAVIOR,
        _B_COLOR,
        _B_BADGE,
        "round",
    ),
    ElementSpec(
        BusinessFunction,
        "BusinessFunction",
        Layer.BUSINESS,
        Aspect.BEHAVIOR,
        _B_COLOR,
        _B_BADGE,
        "round",
    ),
    ElementSpec(
        BusinessInteraction,
        "BusinessInteraction",
        Layer.BUSINESS,
        Aspect.BEHAVIOR,
        _B_COLOR,
        _B_BADGE,
        "round",
        factory=_make_business_interaction,
    ),
    ElementSpec(
        BusinessEvent,
        "BusinessEvent",
        Layer.BUSINESS,
        Aspect.BEHAVIOR,
        _B_COLOR,
        _B_BADGE,
        "round",
    ),
    ElementSpec(
        BusinessService,
        "BusinessService",
        Layer.BUSINESS,
        Aspect.BEHAVIOR,
        _B_COLOR,
        _B_BADGE,
        "round",
    ),
    # Business — Passive Structure
    ElementSpec(
        BusinessObject,
        "BusinessObject",
        Layer.BUSINESS,
        Aspect.PASSIVE_STRUCTURE,
        _B_COLOR,
        _B_BADGE,
        "square",
    ),
    ElementSpec(
        Contract,
        "Contract",
        Layer.BUSINESS,
        Aspect.PASSIVE_STRUCTURE,
        _B_COLOR,
        _B_BADGE,
        "square",
    ),
    ElementSpec(
        Representation,
        "Representation",
        Layer.BUSINESS,
        Aspect.PASSIVE_STRUCTURE,
        _B_COLOR,
        _B_BADGE,
        "square",
    ),
    # Business — Composite
    ElementSpec(
        Product,
        "Product",
        Layer.BUSINESS,
        Aspect.COMPOSITE,
        _B_COLOR,
        _B_BADGE,
        "square",
    ),
    # ------------------------------------------------------------------
    # Application — Active Structure
    # ------------------------------------------------------------------
    ElementSpec(
        ApplicationComponent,
        "ApplicationComponent",
        Layer.APPLICATION,
        Aspect.ACTIVE_STRUCTURE,
        _A_COLOR,
        _A_BADGE,
        "square",
    ),
    ElementSpec(
        ApplicationCollaboration,
        "ApplicationCollaboration",
        Layer.APPLICATION,
        Aspect.ACTIVE_STRUCTURE,
        _A_COLOR,
        _A_BADGE,
        "square",
        factory=_make_application_collaboration,
    ),
    ElementSpec(
        ApplicationInterface,
        "ApplicationInterface",
        Layer.APPLICATION,
        Aspect.ACTIVE_STRUCTURE,
        _A_COLOR,
        _A_BADGE,
        "square",
    ),
    # Application — Behavior
    ElementSpec(
        ApplicationFunction,
        "ApplicationFunction",
        Layer.APPLICATION,
        Aspect.BEHAVIOR,
        _A_COLOR,
        _A_BADGE,
        "round",
    ),
    ElementSpec(
        ApplicationInteraction,
        "ApplicationInteraction",
        Layer.APPLICATION,
        Aspect.BEHAVIOR,
        _A_COLOR,
        _A_BADGE,
        "round",
        factory=_make_application_interaction,
    ),
    ElementSpec(
        ApplicationProcess,
        "ApplicationProcess",
        Layer.APPLICATION,
        Aspect.BEHAVIOR,
        _A_COLOR,
        _A_BADGE,
        "round",
    ),
    ElementSpec(
        ApplicationEvent,
        "ApplicationEvent",
        Layer.APPLICATION,
        Aspect.BEHAVIOR,
        _A_COLOR,
        _A_BADGE,
        "round",
    ),
    ElementSpec(
        ApplicationService,
        "ApplicationService",
        Layer.APPLICATION,
        Aspect.BEHAVIOR,
        _A_COLOR,
        _A_BADGE,
        "round",
    ),
    # Application — Passive Structure
    ElementSpec(
        DataObject,
        "DataObject",
        Layer.APPLICATION,
        Aspect.PASSIVE_STRUCTURE,
        _A_COLOR,
        _A_BADGE,
        "square",
    ),
    # ------------------------------------------------------------------
    # Technology — Active Structure
    # ------------------------------------------------------------------
    ElementSpec(Node, "Node", Layer.TECHNOLOGY, Aspect.ACTIVE_STRUCTURE, _T_COLOR, "T", "square"),
    ElementSpec(
        Device, "Device", Layer.TECHNOLOGY, Aspect.ACTIVE_STRUCTURE, _T_COLOR, "T", "square"
    ),
    ElementSpec(
        SystemSoftware,
        "SystemSoftware",
        Layer.TECHNOLOGY,
        Aspect.ACTIVE_STRUCTURE,
        _T_COLOR,
        "T",
        "square",
    ),
    ElementSpec(
        TechnologyCollaboration,
        "TechnologyCollaboration",
        Layer.TECHNOLOGY,
        Aspect.ACTIVE_STRUCTURE,
        _T_COLOR,
        "T",
        "square",
        factory=_make_technology_collaboration,
    ),
    ElementSpec(
        TechnologyInterface,
        "TechnologyInterface",
        Layer.TECHNOLOGY,
        Aspect.ACTIVE_STRUCTURE,
        _T_COLOR,
        "T",
        "square",
    ),
    ElementSpec(Path, "Path", Layer.TECHNOLOGY, Aspect.ACTIVE_STRUCTURE, _T_COLOR, "T", "square"),
    ElementSpec(
        CommunicationNetwork,
        "CommunicationNetwork",
        Layer.TECHNOLOGY,
        Aspect.ACTIVE_STRUCTURE,
        _T_COLOR,
        "T",
        "square",
    ),
    # Technology — Behavior
    ElementSpec(
        TechnologyFunction,
        "TechnologyFunction",
        Layer.TECHNOLOGY,
        Aspect.BEHAVIOR,
        _T_COLOR,
        "T",
        "round",
    ),
    ElementSpec(
        TechnologyProcess,
        "TechnologyProcess",
        Layer.TECHNOLOGY,
        Aspect.BEHAVIOR,
        _T_COLOR,
        "T",
        "round",
    ),
    ElementSpec(
        TechnologyInteraction,
        "TechnologyInteraction",
        Layer.TECHNOLOGY,
        Aspect.BEHAVIOR,
        _T_COLOR,
        "T",
        "round",
        factory=_make_technology_interaction,
    ),
    ElementSpec(
        TechnologyEvent,
        "TechnologyEvent",
        Layer.TECHNOLOGY,
        Aspect.BEHAVIOR,
        _T_COLOR,
        "T",
        "round",
    ),
    ElementSpec(
        TechnologyService,
        "TechnologyService",
        Layer.TECHNOLOGY,
        Aspect.BEHAVIOR,
        _T_COLOR,
        "T",
        "round",
    ),
    # Technology — Passive Structure
    ElementSpec(
        Artifact,
        "Artifact",
        Layer.TECHNOLOGY,
        Aspect.PASSIVE_STRUCTURE,
        _T_COLOR,
        "T",
        "square",
    ),
    # ------------------------------------------------------------------
    # Physical — Active Structure
    # ------------------------------------------------------------------
    ElementSpec(
        Equipment, "Equipment", Layer.PHYSICAL, Aspect.ACTIVE_STRUCTURE, _T_COLOR, "P", "square"
    ),
    ElementSpec(
        Facility, "Facility", Layer.PHYSICAL, Aspect.ACTIVE_STRUCTURE, _T_COLOR, "P", "square"
    ),
    ElementSpec(
        DistributionNetwork,
        "DistributionNetwork",
        Layer.PHYSICAL,
        Aspect.ACTIVE_STRUCTURE,
        _T_COLOR,
        "P",
        "square",
    ),
    # Physical — Passive Structure
    ElementSpec(
        Material,
        "Material",
        Layer.PHYSICAL,
        Aspect.PASSIVE_STRUCTURE,
        _T_COLOR,
        "P",
        "square",
    ),
    # ------------------------------------------------------------------
    # Motivation
    # ------------------------------------------------------------------
    ElementSpec(
        Stakeholder,
        "Stakeholder",
        Layer.MOTIVATION,
        Aspect.MOTIVATION,
        _M_COLOR,
        _M_BADGE,
        "round",
    ),
    ElementSpec(Driver, "Driver", Layer.MOTIVATION, Aspect.MOTIVATION, _M_COLOR, _M_BADGE, "round"),
    ElementSpec(
        Assessment,
        "Assessment",
        Layer.MOTIVATION,
        Aspect.MOTIVATION,
        _M_COLOR,
        _M_BADGE,
        "round",
    ),
    ElementSpec(Goal, "Goal", Layer.MOTIVATION, Aspect.MOTIVATION, _M_COLOR, _M_BADGE, "round"),
    ElementSpec(
        Outcome, "Outcome", Layer.MOTIVATION, Aspect.MOTIVATION, _M_COLOR, _M_BADGE, "round"
    ),
    ElementSpec(
        Principle,
        "Principle",
        Layer.MOTIVATION,
        Aspect.MOTIVATION,
        _M_COLOR,
        _M_BADGE,
        "round",
    ),
    ElementSpec(
        Requirement,
        "Requirement",
        Layer.MOTIVATION,
        Aspect.MOTIVATION,
        _M_COLOR,
        _M_BADGE,
        "round",
    ),
    ElementSpec(
        Constraint,
        "Constraint",
        Layer.MOTIVATION,
        Aspect.MOTIVATION,
        _M_COLOR,
        _M_BADGE,
        "round",
    ),
    ElementSpec(
        Meaning, "Meaning", Layer.MOTIVATION, Aspect.MOTIVATION, _M_COLOR, _M_BADGE, "round"
    ),
    ElementSpec(Value, "Value", Layer.MOTIVATION, Aspect.MOTIVATION, _M_COLOR, _M_BADGE, "round"),
    # ------------------------------------------------------------------
    # Strategy
    # ------------------------------------------------------------------
    ElementSpec(
        Resource,
        "Resource",
        Layer.STRATEGY,
        Aspect.ACTIVE_STRUCTURE,
        _S_COLOR,
        _S_BADGE,
        "square",
    ),
    ElementSpec(
        Capability,
        "Capability",
        Layer.STRATEGY,
        Aspect.BEHAVIOR,
        _S_COLOR,
        _S_BADGE,
        "round",
    ),
    ElementSpec(
        ValueStream,
        "ValueStream",
        Layer.STRATEGY,
        Aspect.BEHAVIOR,
        _S_COLOR,
        _S_BADGE,
        "round",
    ),
    ElementSpec(
        CourseOfAction,
        "CourseOfAction",
        Layer.STRATEGY,
        Aspect.BEHAVIOR,
        _S_COLOR,
        _S_BADGE,
        "round",
    ),
    # ------------------------------------------------------------------
    # Implementation & Migration
    # ------------------------------------------------------------------
    ElementSpec(
        WorkPackage,
        "WorkPackage",
        Layer.IMPLEMENTATION_MIGRATION,
        Aspect.BEHAVIOR,
        _I_COLOR,
        _I_BADGE,
        "round",
    ),
    ElementSpec(
        Deliverable,
        "Deliverable",
        Layer.IMPLEMENTATION_MIGRATION,
        Aspect.PASSIVE_STRUCTURE,
        _I_COLOR,
        _I_BADGE,
        "square",
    ),
    ElementSpec(
        ImplementationEvent,
        "ImplementationEvent",
        Layer.IMPLEMENTATION_MIGRATION,
        Aspect.BEHAVIOR,
        _I_COLOR,
        _I_BADGE,
        "round",
    ),
    ElementSpec(
        Plateau,
        "Plateau",
        Layer.IMPLEMENTATION_MIGRATION,
        Aspect.COMPOSITE,
        _I_COLOR,
        _I_BADGE,
        "square",
    ),
    ElementSpec(
        Gap,
        "Gap",
        Layer.IMPLEMENTATION_MIGRATION,
        Aspect.COMPOSITE,
        _I_COLOR,
        _I_BADGE,
        "square",
        factory=_make_gap,
    ),
]


def _make_instance(spec: ElementSpec) -> object:
    """Return a concrete instance using the factory or default constructor."""
    if spec.factory is not None:
        return spec.factory()
    return spec.cls(name="x")


def _spec_id(spec: ElementSpec) -> str:
    return spec.cls.__name__


# ---------------------------------------------------------------------------
# Parametrized test class
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("spec", ELEMENT_SPECS, ids=_spec_id)
class TestElementProperties:
    """Generic property checks parametrized over every concrete element type."""

    def test_type_name(self, spec: ElementSpec) -> None:
        instance = _make_instance(spec)
        assert instance._type_name == spec.type_name  # type: ignore[union-attr]

    def test_layer(self, spec: ElementSpec) -> None:
        assert spec.cls.layer is spec.layer

    def test_aspect(self, spec: ElementSpec) -> None:
        assert spec.cls.aspect is spec.aspect

    def test_notation_layer_color(self, spec: ElementSpec) -> None:
        assert spec.cls.notation.layer_color == spec.layer_color

    def test_notation_badge_letter(self, spec: ElementSpec) -> None:
        assert spec.cls.notation.badge_letter == spec.badge_letter

    def test_notation_corner_shape(self, spec: ElementSpec) -> None:
        assert spec.cls.notation.corner_shape == spec.corner_shape

    def test_instantiation_with_name(self, spec: ElementSpec) -> None:
        instance = _make_instance(spec)
        assert instance is not None

    def test_instance_has_uuid(self, spec: ElementSpec) -> None:
        instance = _make_instance(spec)
        uid = getattr(instance, "id", None)
        assert uid is not None
