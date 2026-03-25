"""Tests for FEAT-15.3: Specialization same-type enforcement."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.business import BusinessActor, BusinessProcess
from pyarchi.metamodel.relationships import Specialization
from pyarchi.validation.permissions import is_permitted


class TestSpecializationPermission:
    def test_same_type_permitted(self) -> None:
        assert is_permitted(Specialization, BusinessActor, BusinessActor) is True

    def test_cross_type_rejected(self) -> None:
        assert is_permitted(Specialization, BusinessActor, BusinessProcess) is False


class TestSpecializationModelValidate:
    """Model.validate() catches cross-type Specialization (depends on FEAT-15.7)."""

    def test_cross_type_specialization_model_error(self) -> None:
        from pyarchi.exceptions import ValidationError
        from pyarchi.metamodel.model import Model

        ba = BusinessActor(name="actor")
        bp = BusinessProcess(name="proc")
        rel = Specialization(name="bad", source=ba, target=bp)
        model = Model(concepts=[ba, bp, rel])
        errors = model.validate()
        assert len(errors) >= 1
        assert isinstance(errors[0], ValidationError)

    def test_same_type_specialization_no_error(self) -> None:
        from pyarchi.metamodel.model import Model

        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        rel = Specialization(name="ok", source=a1, target=a2)
        model = Model(concepts=[a1, a2, rel])
        errors = model.validate()
        assert len(errors) == 0
