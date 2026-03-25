"""Tests for FEAT-13.1 -- Business-Application cross-layer Serving rules."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.application import (
    ApplicationComponent,
    ApplicationFunction,
    ApplicationInterface,
    ApplicationProcess,
    ApplicationService,
)
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessFunction,
    BusinessInteraction,
    BusinessInterface,
    BusinessProcess,
    BusinessRole,
    BusinessService,
)
from pyarchi.metamodel.relationships import Serving
from pyarchi.validation.permissions import is_permitted


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
