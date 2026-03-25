"""Tests for FEAT-15.7: Model.validate() method."""

from __future__ import annotations

import pytest

from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessObject,
    BusinessProcess,
    BusinessRole,
)
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Assignment, Specialization


class TestModelValidateBasic:
    def test_empty_model_returns_empty(self) -> None:
        model = Model()
        assert model.validate() == []

    def test_valid_model_returns_empty(self) -> None:
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        rel = Specialization(name="s", source=a1, target=a2)
        model = Model(concepts=[a1, a2, rel])
        assert model.validate() == []

    def test_invalid_relationship_returns_error(self) -> None:
        ba = BusinessActor(name="actor")
        bp = BusinessProcess(name="proc")
        rel = Specialization(name="bad", source=ba, target=bp)  # cross-type
        model = Model(concepts=[ba, bp, rel])
        errors = model.validate()
        assert len(errors) == 1
        assert isinstance(errors[0], ValidationError)

    def test_multiple_errors_collected(self) -> None:
        ba = BusinessActor(name="actor")
        bp = BusinessProcess(name="proc")
        br = BusinessRole(name="role")
        r1 = Specialization(name="r1", source=ba, target=bp)
        r2 = Specialization(name="r2", source=bp, target=br)
        model = Model(concepts=[ba, bp, br, r1, r2])
        errors = model.validate()
        assert len(errors) == 2


class TestModelValidateStrict:
    def test_strict_raises_on_first(self) -> None:
        ba = BusinessActor(name="actor")
        bp = BusinessProcess(name="proc")
        br = BusinessRole(name="role")
        r1 = Specialization(name="r1", source=ba, target=bp)
        r2 = Specialization(name="r2", source=bp, target=br)
        model = Model(concepts=[ba, bp, br, r1, r2])
        with pytest.raises(ValidationError):
            model.validate(strict=True)

    def test_strict_no_error_returns_empty(self) -> None:
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        rel = Specialization(name="s", source=a1, target=a2)
        model = Model(concepts=[a1, a2, rel])
        assert model.validate(strict=True) == []


class TestModelValidateErrorMessage:
    def test_error_contains_relationship_info(self) -> None:
        ba = BusinessActor(name="actor")
        bp = BusinessProcess(name="proc")
        rel = Specialization(name="bad", source=ba, target=bp)
        model = Model(concepts=[ba, bp, rel])
        errors = model.validate()
        msg = str(errors[0])
        assert "Specialization" in msg
        assert "BusinessActor" in msg
        assert "BusinessProcess" in msg
