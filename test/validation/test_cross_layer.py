"""Merged tests for test_cross_layer."""

from __future__ import annotations

import pytest

from etcion.metamodel.application import (
    ApplicationComponent,
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
    BusinessFunction,
    BusinessInteraction,
    BusinessInterface,
    BusinessObject,
    BusinessProcess,
    BusinessRole,
    BusinessService,
    Contract,
)
from etcion.metamodel.relationships import Realization, Serving
from etcion.metamodel.technology import (
    Artifact,
    Node,
    TechnologyFunction,
    TechnologyInterface,
    TechnologyProcess,
    TechnologyService,
)
from etcion.validation.permissions import is_permitted


class TestApplicationServingBusiness:
    """Application external elements serve Business internal elements."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (ApplicationService, BusinessProcess),
            (ApplicationService, BusinessFunction),
            (ApplicationService, BusinessInteraction),
            (ApplicationInterface, BusinessActor),
            (ApplicationInterface, BusinessRole),
        ],
    )
    def test_permitted(self, source: type, target: type) -> None:
        assert is_permitted(Serving, source, target) is True


class TestBusinessServingApplication:
    """Business external elements serve Application internal elements."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (BusinessService, ApplicationProcess),
            (BusinessService, ApplicationFunction),
            (BusinessInterface, ApplicationComponent),
        ],
    )
    def test_permitted(self, source: type, target: type) -> None:
        assert is_permitted(Serving, source, target) is True


class TestCrossLayerServingForbidden:
    """Non-service/interface types cannot Serve cross-layer."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (BusinessProcess, ApplicationFunction),
            (ApplicationProcess, BusinessFunction),
            (BusinessActor, ApplicationComponent),
            (ApplicationComponent, BusinessRole),
        ],
    )
    def test_forbidden(self, source: type, target: type) -> None:
        assert is_permitted(Serving, source, target) is False


class TestTechnologyServingApplication:
    """Technology external elements serve Application internal elements."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (TechnologyService, ApplicationFunction),
            (TechnologyService, ApplicationProcess),
            (TechnologyInterface, ApplicationComponent),
        ],
    )
    def test_permitted(self, source: type, target: type) -> None:
        assert is_permitted(Serving, source, target) is True


class TestTechServingAppForbidden:
    """Non-service/interface Technology types cannot Serve Application."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (TechnologyProcess, ApplicationFunction),
            (Node, ApplicationComponent),
            (Artifact, ApplicationComponent),
            (TechnologyFunction, ApplicationProcess),
        ],
    )
    def test_forbidden(self, source: type, target: type) -> None:
        assert is_permitted(Serving, source, target) is False


class TestAppRealizesBusinessBehavior:
    """Application behavior elements realize Business behavior elements."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (ApplicationProcess, BusinessProcess),
            (ApplicationFunction, BusinessFunction),
            (ApplicationInteraction, BusinessInteraction),
            (ApplicationProcess, BusinessFunction),
            (ApplicationFunction, BusinessProcess),
        ],
    )
    def test_permitted(self, source: type, target: type) -> None:
        assert is_permitted(Realization, source, target) is True


class TestDataObjectRealizesBusinessObject:
    """DataObject realizes BusinessObject (and subclasses)."""

    @pytest.mark.parametrize("target", [BusinessObject, Contract])
    def test_permitted(self, target: type) -> None:
        assert is_permitted(Realization, DataObject, target) is True


class TestTechRealizesAppBehavior:
    """Technology behavior elements realize Application behavior elements."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (TechnologyProcess, ApplicationProcess),
            (TechnologyFunction, ApplicationFunction),
            (TechnologyProcess, ApplicationFunction),
        ],
    )
    def test_permitted(self, source: type, target: type) -> None:
        assert is_permitted(Realization, source, target) is True


class TestArtifactRealizesAppElements:
    """Artifact realizes DataObject and ApplicationComponent."""

    @pytest.mark.parametrize(
        "target",
        [DataObject, ApplicationComponent],
    )
    def test_permitted(self, target: type) -> None:
        assert is_permitted(Realization, Artifact, target) is True


class TestCrossLayerRealizationForbidden:
    """Realization that skips a layer or goes wrong direction is forbidden."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (TechnologyProcess, BusinessProcess),
            (Artifact, BusinessObject),
            (BusinessProcess, ApplicationProcess),
        ],
    )
    def test_forbidden(self, source: type, target: type) -> None:
        assert is_permitted(Realization, source, target) is False


class TestRealizationProhibitedTargets:
    """Realization targeting BusinessInternalActiveStructureElement is forbidden."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (ApplicationProcess, BusinessActor),
            (ApplicationFunction, BusinessActor),
            (ApplicationComponent, BusinessRole),
            (ApplicationComponent, BusinessCollaboration),
            (DataObject, BusinessActor),
            (DataObject, BusinessRole),
            (Artifact, BusinessActor),
            (TechnologyProcess, BusinessRole),
        ],
    )
    def test_prohibited(self, source: type, target: type) -> None:
        assert is_permitted(Realization, source, target) is False
