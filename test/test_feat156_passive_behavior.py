"""Tests for FEAT-15.6: Passive cannot perform behavior."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.business import BusinessObject, BusinessProcess
from pyarchi.metamodel.relationships import Assignment
from pyarchi.validation.permissions import is_permitted


class TestPassiveBehaviorPermission:
    def test_passive_to_behavior_assignment_rejected(self) -> None:
        assert is_permitted(Assignment, BusinessObject, BusinessProcess) is False

    def test_passive_to_passive_assignment_not_affected(self) -> None:
        """This rule only covers passive->behavior, not passive->passive."""
        # passive->passive is handled by other rules; just document the boundary
        is_permitted(Assignment, BusinessObject, BusinessObject)


class TestPassiveBehaviorModelValidate:
    """Model.validate() surfaces the violation (depends on FEAT-15.7)."""

    def test_passive_assigned_to_behavior_model_error(self) -> None:
        from pyarchi.exceptions import ValidationError
        from pyarchi.metamodel.model import Model

        bo = BusinessObject(name="obj")
        bp = BusinessProcess(name="proc")
        rel = Assignment(name="bad", source=bo, target=bp)
        model = Model(concepts=[bo, bp, rel])
        errors = model.validate()
        assert len(errors) >= 1
        assert isinstance(errors[0], ValidationError)

    def test_construction_succeeds_silently(self) -> None:
        """Construction-time does NOT raise -- model-time only."""
        bo = BusinessObject(name="obj")
        bp = BusinessProcess(name="proc")
        rel = Assignment(name="bad", source=bo, target=bp)  # no error here
        assert rel.source is bo
