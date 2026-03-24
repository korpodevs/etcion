"""Tests for FEAT-02.4 -- RelationshipConnector ABC."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.concepts import (
    Concept,
    Element,
    Relationship,
    RelationshipConnector,
)
from pyarchi.metamodel.mixins import AttributeMixin


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
