"""Tests for FEAT-13.2 -- Application-Technology cross-layer Serving rules."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.application import (
    ApplicationComponent,
    ApplicationFunction,
    ApplicationProcess,
)
from pyarchi.metamodel.relationships import Serving
from pyarchi.metamodel.technology import (
    Artifact,
    Node,
    TechnologyFunction,
    TechnologyInterface,
    TechnologyProcess,
    TechnologyService,
)
from pyarchi.validation.permissions import is_permitted


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
