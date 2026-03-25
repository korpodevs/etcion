"""Tests for FEAT-12.4 -- Implementation & Migration cross-layer validation rules."""

from __future__ import annotations

import warnings

import pytest

from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessRole,
)
from pyarchi.metamodel.implementation_migration import (
    Deliverable,
    ImplementationEvent,
    Plateau,
    WorkPackage,
)
from pyarchi.metamodel.relationships import (
    Access,
    Assignment,
    Realization,
    Triggering,
)
from pyarchi.validation.permissions import is_permitted


class TestRealizationDeprecation:
    """Realization(WorkPackage, Deliverable) is permitted but deprecated."""

    def test_returns_true(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            assert is_permitted(Realization, WorkPackage, Deliverable) is True

    def test_emits_deprecation_warning(self) -> None:
        with pytest.warns(DeprecationWarning, match="deprecated"):
            is_permitted(Realization, WorkPackage, Deliverable)


class TestAssignmentToWorkPackage:
    """Business internal active structure sources may assign to WorkPackage."""

    @pytest.mark.parametrize(
        "source_type",
        [BusinessActor, BusinessRole, BusinessCollaboration],
    )
    def test_permitted_sources(self, source_type: type) -> None:
        assert is_permitted(Assignment, source_type, WorkPackage) is True

    @pytest.mark.parametrize(
        "source_type",
        [Deliverable, ImplementationEvent, Plateau],
    )
    def test_forbidden_sources(self, source_type: type) -> None:
        assert is_permitted(Assignment, source_type, WorkPackage) is False


class TestTriggering:
    """ImplementationEvent may trigger/be triggered by WorkPackage or Plateau."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (ImplementationEvent, WorkPackage),
            (ImplementationEvent, Plateau),
            (WorkPackage, ImplementationEvent),
            (Plateau, ImplementationEvent),
        ],
    )
    def test_permitted_triggering(self, source: type, target: type) -> None:
        assert is_permitted(Triggering, source, target) is True


class TestAccess:
    """ImplementationEvent may access Deliverable."""

    def test_impl_event_accesses_deliverable(self) -> None:
        assert is_permitted(Access, ImplementationEvent, Deliverable) is True


class TestDeliverableRealization:
    """Deliverable may realize core structure/behavior elements."""

    def test_deliverable_realizes_work_package(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            assert is_permitted(Realization, Deliverable, WorkPackage) is True
