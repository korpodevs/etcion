"""Tests for FEAT-15.2: Aggregation/Composition composite-source rule."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.business import BusinessActor, BusinessProcess
from pyarchi.metamodel.elements import Grouping
from pyarchi.metamodel.relationships import Aggregation, Assignment, Composition
from pyarchi.validation.permissions import is_permitted


class TestCompositeSourcePermission:
    """is_permitted() enforces composite-source when target is Relationship."""

    def test_aggregation_non_composite_source_rel_target_rejected(self) -> None:
        assert is_permitted(Aggregation, BusinessActor, Assignment) is False

    def test_aggregation_composite_source_rel_target_permitted(self) -> None:
        assert is_permitted(Aggregation, Grouping, Assignment) is True

    def test_composition_non_composite_source_rel_target_rejected(self) -> None:
        assert is_permitted(Composition, BusinessActor, Assignment) is False

    def test_composition_composite_source_rel_target_permitted(self) -> None:
        assert is_permitted(Composition, Grouping, Assignment) is True

    def test_same_type_still_works(self) -> None:
        """Existing same-type rule is not broken."""
        assert is_permitted(Aggregation, BusinessActor, BusinessActor) is True


class TestCompositeSourceModelValidate:
    """Model.validate() surfaces the violation (depends on FEAT-15.7)."""

    def test_aggregation_non_composite_source_model_error(self) -> None:
        from pyarchi.exceptions import ValidationError
        from pyarchi.metamodel.model import Model

        a = BusinessActor(name="a")
        bp = BusinessProcess(name="bp")
        inner_rel = Assignment(name="inner", source=a, target=bp)
        outer_rel = Aggregation(name="outer", source=a, target=inner_rel)
        model = Model(concepts=[a, bp, inner_rel, outer_rel])
        errors = model.validate()
        assert len(errors) >= 1
        assert isinstance(errors[0], ValidationError)
