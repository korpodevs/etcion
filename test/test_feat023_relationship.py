"""Tests for FEAT-02.3 -- Relationship ABC."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.enums import RelationshipCategory
from pyarchi.metamodel.concepts import Concept, Element, Relationship
from pyarchi.metamodel.mixins import AttributeMixin


class ConcreteElement(Element):
    @property
    def _type_name(self) -> str:
        return "ConcreteElement"


class ConcreteRelationship(Relationship):
    category = RelationshipCategory.OTHER

    @property
    def _type_name(self) -> str:
        return "ConcreteRelationship"


class TestRelationship:
    def test_cannot_instantiate_directly(self) -> None:
        """Relationship() raises TypeError due to abstract _type_name."""
        with pytest.raises(TypeError):
            Relationship()  # type: ignore[abstract]

    def test_is_subclass_of_concept(self) -> None:
        """issubclass(Relationship, Concept) is True."""
        assert issubclass(Relationship, Concept)

    def test_concrete_relationship_is_instance_of_concept(self) -> None:
        """isinstance(concrete_rel, Concept) is True."""
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert isinstance(rel, Concept)

    def test_concrete_relationship_is_instance_of_relationship(self) -> None:
        """isinstance(concrete_rel, Relationship) is True."""
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert isinstance(rel, Relationship)

    def test_concrete_relationship_is_not_instance_of_element(self) -> None:
        """isinstance(concrete_rel, Element) is False."""
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert not isinstance(rel, Element)

    def test_source_and_target_required(self) -> None:
        """ConcreteRelationship(name='X') without source/target raises ValidationError."""
        with pytest.raises(ValidationError):
            ConcreteRelationship(name="X")  # type: ignore[call-arg]

    def test_source_and_target_preserved(self) -> None:
        """source and target fields hold the provided Concept instances."""
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert rel.source is src
        assert rel.target is tgt

    def test_is_derived_defaults_to_false(self) -> None:
        """ConcreteRelationship(...).is_derived is False."""
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert rel.is_derived is False

    def test_is_derived_can_be_set_true(self) -> None:
        """ConcreteRelationship(..., is_derived=True).is_derived is True."""
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt, is_derived=True)
        assert rel.is_derived is True

    def test_category_is_class_variable(self) -> None:
        """'category' is not in Relationship.model_fields."""
        assert "category" not in Relationship.model_fields

    def test_category_set_on_concrete_subclass(self) -> None:
        """ConcreteRelationship.category == RelationshipCategory.OTHER."""
        assert ConcreteRelationship.category == RelationshipCategory.OTHER

    def test_name_is_required(self) -> None:
        """ConcreteRelationship() without name raises ValidationError."""
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        with pytest.raises(ValidationError):
            ConcreteRelationship(source=src, target=tgt)  # type: ignore[call-arg]

    def test_name_is_preserved(self) -> None:
        """ConcreteRelationship(name='R1', ...).name == 'R1'."""
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R1", source=src, target=tgt)
        assert rel.name == "R1"

    def test_description_defaults_to_none(self) -> None:
        """ConcreteRelationship(...).description is None."""
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert rel.description is None

    def test_documentation_url_defaults_to_none(self) -> None:
        """ConcreteRelationship(...).documentation_url is None."""
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert rel.documentation_url is None

    def test_id_inherited_from_concept(self) -> None:
        """ConcreteRelationship(...).id is a non-empty string."""
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert isinstance(rel.id, str)
        assert len(rel.id) > 0

    def test_mro_mixin_before_concept(self) -> None:
        """AttributeMixin appears before Concept in Relationship.__mro__."""
        mro = Relationship.__mro__
        mixin_pos = mro.index(AttributeMixin)
        concept_pos = mro.index(Concept)
        assert mixin_pos < concept_pos
