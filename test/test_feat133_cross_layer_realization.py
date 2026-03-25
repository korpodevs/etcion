"""Tests for FEAT-13.3 -- Cross-layer Realization permission rules."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.application import (
    ApplicationComponent,
    ApplicationFunction,
    ApplicationInteraction,
    ApplicationProcess,
    DataObject,
)
from pyarchi.metamodel.business import (
    BusinessFunction,
    BusinessInteraction,
    BusinessObject,
    BusinessProcess,
    Contract,
)
from pyarchi.metamodel.relationships import Realization
from pyarchi.metamodel.technology import (
    Artifact,
    TechnologyFunction,
    TechnologyProcess,
)
from pyarchi.validation.permissions import is_permitted


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
