"""Tests for FEAT-15.1: Relationship direction enforcement via is_permitted()."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.business import (
    BusinessObject,
    BusinessProcess,
)
from pyarchi.metamodel.relationships import Access, Assignment, Serving
from pyarchi.validation.permissions import is_permitted


class TestDirectionInIsPermitted:
    """is_permitted() returns False for wrong-direction triples."""

    def test_assignment_passive_source_rejected(self) -> None:
        assert is_permitted(Assignment, BusinessObject, BusinessProcess) is False

    def test_access_passive_source_rejected(self) -> None:
        assert is_permitted(Access, BusinessObject, BusinessProcess) is False

    def test_serving_passive_source_rejected(self) -> None:
        assert is_permitted(Serving, BusinessObject, BusinessProcess) is False


class TestDirectionModelValidate:
    """Model.validate() surfaces direction errors (depends on FEAT-15.7)."""

    def test_assignment_wrong_direction_model_error(self) -> None:
        from pyarchi.exceptions import ValidationError
        from pyarchi.metamodel.model import Model

        bo = BusinessObject(name="obj")
        bp = BusinessProcess(name="proc")
        rel = Assignment(name="bad", source=bo, target=bp)
        model = Model(concepts=[bo, bp, rel])
        errors = model.validate()
        assert len(errors) >= 1
        assert isinstance(errors[0], ValidationError)

    def test_serving_wrong_direction_model_error(self) -> None:
        from pyarchi.metamodel.model import Model

        bo = BusinessObject(name="obj")
        bp = BusinessProcess(name="proc")
        rel = Serving(name="bad", source=bo, target=bp)
        model = Model(concepts=[bo, bp, rel])
        errors = model.validate()
        assert len(errors) >= 1

    def test_access_wrong_direction_model_error(self) -> None:
        from pyarchi.metamodel.model import Model

        bo = BusinessObject(name="obj")
        bp = BusinessProcess(name="proc")
        rel = Access(name="bad", source=bo, target=bp)
        model = Model(concepts=[bo, bp, rel])
        errors = model.validate()
        assert len(errors) >= 1
