"""Tests for FEAT-15.5: BusinessCollaboration assigned_elements validator."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from pyarchi.metamodel.business import BusinessActor, BusinessCollaboration


class TestBusinessCollaborationValidator:
    def test_zero_assigned_raises(self) -> None:
        with pytest.raises(PydanticValidationError):
            BusinessCollaboration(name="collab")

    def test_one_assigned_raises(self) -> None:
        a = BusinessActor(name="a")
        with pytest.raises(PydanticValidationError):
            BusinessCollaboration(name="collab", assigned_elements=[a])

    def test_two_assigned_succeeds(self) -> None:
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        bc = BusinessCollaboration(name="collab", assigned_elements=[a1, a2])
        assert len(bc.assigned_elements) == 2

    def test_three_assigned_succeeds(self) -> None:
        actors = [BusinessActor(name=f"a{i}") for i in range(3)]
        bc = BusinessCollaboration(name="collab", assigned_elements=actors)
        assert len(bc.assigned_elements) == 3
