"""Tests for FEAT-13.4 -- Cross-layer Realization prohibition rules."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.application import (
    ApplicationComponent,
    ApplicationFunction,
    ApplicationProcess,
    DataObject,
)
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessRole,
)
from pyarchi.metamodel.relationships import Realization
from pyarchi.metamodel.technology import (
    Artifact,
    TechnologyProcess,
)
from pyarchi.validation.permissions import is_permitted


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
