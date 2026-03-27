"""Merged tests for test_concepts."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from etcion.enums import RelationshipCategory
from etcion.metamodel.concepts import (
    Concept,
    Element,
    Relationship,
    RelationshipConnector,
)
from etcion.metamodel.mixins import AttributeMixin


# Minimal concrete subclass for testing — defined in test file only
class ConcreteConcept(Concept):
    @property
    def _type_name(self) -> str:
        return "ConcreteConcept"


class TestConcept:
    def test_cannot_instantiate_directly(self) -> None:
        """Concept() raises TypeError due to abstract _type_name."""
        with pytest.raises(TypeError):
            Concept()  # type: ignore[abstract]

    def test_id_defaults_to_uuid_string(self) -> None:
        """ConcreteConcept().id is a valid UUID4 string."""
        c = ConcreteConcept()
        # Must be parseable as a UUID
        parsed = uuid.UUID(c.id)
        assert str(parsed) == c.id

    def test_default_ids_are_unique(self) -> None:
        """Two independently created instances have distinct IDs."""
        a = ConcreteConcept()
        b = ConcreteConcept()
        assert a.id != b.id

    def test_custom_id_is_preserved(self) -> None:
        """ConcreteConcept(id='my-custom-id').id == 'my-custom-id'."""
        c = ConcreteConcept(id="my-custom-id")
        assert c.id == "my-custom-id"

    def test_archi_standard_id_format_accepted(self) -> None:
        """Archi-prefixed id string is accepted without modification."""
        archi_id = "id-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        c = ConcreteConcept(id=archi_id)
        assert c.id == archi_id

    def test_type_name_property_returns_string(self) -> None:
        """ConcreteConcept()._type_name == 'ConcreteConcept'."""
        c = ConcreteConcept()
        assert c._type_name == "ConcreteConcept"

    def test_is_instance_of_concept(self) -> None:
        """isinstance(ConcreteConcept(), Concept) is True."""
        c = ConcreteConcept()
        assert isinstance(c, Concept)

    def test_model_config_allows_arbitrary_types(self) -> None:
        """Concept.model_config['arbitrary_types_allowed'] is True."""
        assert Concept.model_config.get("arbitrary_types_allowed") is True


class ConcreteElement_1(Element):
    @property
    def _type_name(self) -> str:
        return "ConcreteElement_1"


class TestElement:
    def test_cannot_instantiate_directly(self) -> None:
        """Element() raises TypeError due to abstract _type_name."""
        with pytest.raises(TypeError):
            Element()  # type: ignore[abstract]

    def test_is_subclass_of_concept(self) -> None:
        """issubclass(Element, Concept) is True."""
        assert issubclass(Element, Concept)

    def test_concrete_element_is_instance_of_concept(self) -> None:
        """isinstance(ConcreteElement_1(name='X'), Concept) is True."""
        assert isinstance(ConcreteElement_1(name="X"), Concept)

    def test_concrete_element_is_instance_of_element(self) -> None:
        """isinstance(ConcreteElement_1(name='X'), Element) is True."""
        assert isinstance(ConcreteElement_1(name="X"), Element)

    def test_name_is_required(self) -> None:
        """ConcreteElement_1() without name raises ValidationError."""
        with pytest.raises(ValidationError):
            ConcreteElement_1()  # type: ignore[call-arg]

    def test_name_is_preserved(self) -> None:
        """ConcreteElement_1(name='Alice').name == 'Alice'."""
        assert ConcreteElement_1(name="Alice").name == "Alice"

    def test_description_defaults_to_none(self) -> None:
        """ConcreteElement_1(name='X').description is None."""
        assert ConcreteElement_1(name="X").description is None

    def test_description_is_preserved(self) -> None:
        """ConcreteElement_1(name='X', description='D').description == 'D'."""
        assert ConcreteElement_1(name="X", description="D").description == "D"

    def test_documentation_url_defaults_to_none(self) -> None:
        """ConcreteElement_1(name='X').documentation_url is None."""
        assert ConcreteElement_1(name="X").documentation_url is None

    def test_documentation_url_is_preserved(self) -> None:
        """ConcreteElement_1(name='X', documentation_url='http://x').documentation_url."""
        c = ConcreteElement_1(name="X", documentation_url="http://x")
        assert c.documentation_url == "http://x"

    def test_id_inherited_from_concept(self) -> None:
        """ConcreteElement_1(name='X').id is a non-empty string."""
        c = ConcreteElement_1(name="X")
        assert isinstance(c.id, str)
        assert len(c.id) > 0

    def test_mro_mixin_before_concept(self) -> None:
        """AttributeMixin appears before Concept in Element.__mro__."""
        mro = Element.__mro__
        mixin_pos = mro.index(AttributeMixin)
        concept_pos = mro.index(Concept)
        assert mixin_pos < concept_pos


class ConcreteElement_2(Element):
    @property
    def _type_name(self) -> str:
        return "ConcreteElement_2"


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
        src = ConcreteElement_2(name="src")
        tgt = ConcreteElement_2(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert isinstance(rel, Concept)

    def test_concrete_relationship_is_instance_of_relationship(self) -> None:
        """isinstance(concrete_rel, Relationship) is True."""
        src = ConcreteElement_2(name="src")
        tgt = ConcreteElement_2(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert isinstance(rel, Relationship)

    def test_concrete_relationship_is_not_instance_of_element(self) -> None:
        """isinstance(concrete_rel, Element) is False."""
        src = ConcreteElement_2(name="src")
        tgt = ConcreteElement_2(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert not isinstance(rel, Element)

    def test_source_and_target_required(self) -> None:
        """ConcreteRelationship(name='X') without source/target raises ValidationError."""
        with pytest.raises(ValidationError):
            ConcreteRelationship(name="X")  # type: ignore[call-arg]

    def test_source_and_target_preserved(self) -> None:
        """source and target fields hold the provided Concept instances."""
        src = ConcreteElement_2(name="src")
        tgt = ConcreteElement_2(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert rel.source is src
        assert rel.target is tgt

    def test_is_derived_defaults_to_false(self) -> None:
        """ConcreteRelationship(...).is_derived is False."""
        src = ConcreteElement_2(name="src")
        tgt = ConcreteElement_2(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert rel.is_derived is False

    def test_is_derived_can_be_set_true(self) -> None:
        """ConcreteRelationship(..., is_derived=True).is_derived is True."""
        src = ConcreteElement_2(name="src")
        tgt = ConcreteElement_2(name="tgt")
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
        src = ConcreteElement_2(name="src")
        tgt = ConcreteElement_2(name="tgt")
        with pytest.raises(ValidationError):
            ConcreteRelationship(source=src, target=tgt)  # type: ignore[call-arg]

    def test_name_is_preserved(self) -> None:
        """ConcreteRelationship(name='R1', ...).name == 'R1'."""
        src = ConcreteElement_2(name="src")
        tgt = ConcreteElement_2(name="tgt")
        rel = ConcreteRelationship(name="R1", source=src, target=tgt)
        assert rel.name == "R1"

    def test_description_defaults_to_none(self) -> None:
        """ConcreteRelationship(...).description is None."""
        src = ConcreteElement_2(name="src")
        tgt = ConcreteElement_2(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert rel.description is None

    def test_documentation_url_defaults_to_none(self) -> None:
        """ConcreteRelationship(...).documentation_url is None."""
        src = ConcreteElement_2(name="src")
        tgt = ConcreteElement_2(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert rel.documentation_url is None

    def test_id_inherited_from_concept(self) -> None:
        """ConcreteRelationship(...).id is a non-empty string."""
        src = ConcreteElement_2(name="src")
        tgt = ConcreteElement_2(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        assert isinstance(rel.id, str)
        assert len(rel.id) > 0

    def test_mro_mixin_before_concept(self) -> None:
        """AttributeMixin appears before Concept in Relationship.__mro__."""
        mro = Relationship.__mro__
        mixin_pos = mro.index(AttributeMixin)
        concept_pos = mro.index(Concept)
        assert mixin_pos < concept_pos


class ConcreteConnector(RelationshipConnector):
    @property
    def _type_name(self) -> str:
        return "ConcreteConnector"


class TestRelationshipConnector:
    def test_cannot_instantiate_directly(self) -> None:
        """RelationshipConnector() raises TypeError due to abstract _type_name."""
        with pytest.raises(TypeError):
            RelationshipConnector()  # type: ignore[abstract]

    def test_is_subclass_of_concept(self) -> None:
        """issubclass(RelationshipConnector, Concept) is True."""
        assert issubclass(RelationshipConnector, Concept)

    def test_is_not_subclass_of_relationship(self) -> None:
        """issubclass(RelationshipConnector, Relationship) is False."""
        assert not issubclass(RelationshipConnector, Relationship)

    def test_is_not_subclass_of_element(self) -> None:
        """issubclass(RelationshipConnector, Element) is False."""
        assert not issubclass(RelationshipConnector, Element)

    def test_concrete_connector_is_instance_of_concept(self) -> None:
        """isinstance(ConcreteConnector(), Concept) is True."""
        assert isinstance(ConcreteConnector(), Concept)

    def test_concrete_connector_is_not_instance_of_relationship(self) -> None:
        """isinstance(ConcreteConnector(), Relationship) is False."""
        assert not isinstance(ConcreteConnector(), Relationship)

    def test_id_inherited_from_concept(self) -> None:
        """ConcreteConnector().id is a non-empty string."""
        c = ConcreteConnector()
        assert isinstance(c.id, str)
        assert len(c.id) > 0

    def test_no_name_field(self) -> None:
        """'name' is not in RelationshipConnector.model_fields."""
        assert "name" not in RelationshipConnector.model_fields

    def test_no_description_field(self) -> None:
        """'description' is not in RelationshipConnector.model_fields."""
        assert "description" not in RelationshipConnector.model_fields

    def test_no_documentation_url_field(self) -> None:
        """'documentation_url' is not in RelationshipConnector.model_fields."""
        assert "documentation_url" not in RelationshipConnector.model_fields

    def test_no_attribute_mixin_in_mro(self) -> None:
        """AttributeMixin is not in RelationshipConnector.__mro__."""
        assert AttributeMixin not in RelationshipConnector.__mro__
