"""Tests for FEAT-02.6 -- Model container."""

from __future__ import annotations

import pytest

import pyarchi
from pyarchi.enums import RelationshipCategory
from pyarchi.metamodel.concepts import (
    Concept,
    Element,
    Relationship,
    RelationshipConnector,
)
from pyarchi.metamodel.model import Model


class ConcreteElement(Element):
    @property
    def _type_name(self) -> str:
        return "ConcreteElement"


class ConcreteRelationship(Relationship):
    category = RelationshipCategory.OTHER

    @property
    def _type_name(self) -> str:
        return "ConcreteRelationship"


class ConcreteConnector(RelationshipConnector):
    @property
    def _type_name(self) -> str:
        return "ConcreteConnector"


class TestModelInit:
    def test_empty_model(self) -> None:
        """Model() creates an empty container."""
        model = Model()
        assert len(model) == 0

    def test_model_with_concepts_list(self) -> None:
        """Model(concepts=[...]) adds all concepts."""
        e1 = ConcreteElement(name="A")
        e2 = ConcreteElement(name="B")
        model = Model(concepts=[e1, e2])
        assert len(model) == 2

    def test_model_with_none(self) -> None:
        """Model(concepts=None) creates an empty container."""
        model = Model(concepts=None)
        assert len(model) == 0


class TestModelAdd:
    def test_add_element(self) -> None:
        """model.add(element) stores the element."""
        model = Model()
        e = ConcreteElement(name="X")
        model.add(e)
        assert len(model) == 1

    def test_add_relationship(self) -> None:
        """model.add(relationship) stores the relationship."""
        model = Model()
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        model.add(rel)
        assert len(model) == 1

    def test_add_connector(self) -> None:
        """model.add(connector) stores the connector."""
        model = Model()
        c = ConcreteConnector()
        model.add(c)
        assert len(model) == 1

    def test_add_non_concept_raises_type_error(self) -> None:
        """model.add('not a concept') raises TypeError."""
        model = Model()
        with pytest.raises(TypeError):
            model.add("not a concept")  # type: ignore[arg-type]

    def test_add_dict_raises_type_error(self) -> None:
        """model.add({}) raises TypeError."""
        model = Model()
        with pytest.raises(TypeError):
            model.add({})  # type: ignore[arg-type]

    def test_add_duplicate_id_raises_value_error(self) -> None:
        """Adding two concepts with the same ID raises ValueError."""
        model = Model()
        e = ConcreteElement(name="X", id="same-id")
        e2 = ConcreteElement(name="Y", id="same-id")
        model.add(e)
        with pytest.raises(ValueError):
            model.add(e2)

    def test_type_error_message_contains_type_name(self) -> None:
        """TypeError message includes the actual type name."""
        model = Model()
        with pytest.raises(TypeError, match="dict"):
            model.add({})  # type: ignore[arg-type]

    def test_value_error_message_contains_id(self) -> None:
        """ValueError message includes the duplicate ID."""
        model = Model()
        e = ConcreteElement(name="X", id="dup-id")
        e2 = ConcreteElement(name="Y", id="dup-id")
        model.add(e)
        with pytest.raises(ValueError, match="dup-id"):
            model.add(e2)


class TestModelIter:
    def test_iter_empty(self) -> None:
        """list(Model()) == []."""
        assert list(Model()) == []

    def test_iter_returns_insertion_order(self) -> None:
        """Iteration yields concepts in insertion order."""
        model = Model()
        e1 = ConcreteElement(name="A")
        e2 = ConcreteElement(name="B")
        e3 = ConcreteElement(name="C")
        model.add(e1)
        model.add(e2)
        model.add(e3)
        assert list(model) == [e1, e2, e3]

    def test_for_loop(self) -> None:
        """for concept in model: works."""
        model = Model()
        e = ConcreteElement(name="X")
        model.add(e)
        seen = []
        for concept in model:
            seen.append(concept)
        assert seen == [e]


class TestModelGetitem:
    def test_getitem_by_id(self) -> None:
        """model[id] returns the correct concept."""
        model = Model()
        e = ConcreteElement(name="X", id="my-id")
        model.add(e)
        assert model["my-id"] is e

    def test_getitem_missing_raises_key_error(self) -> None:
        """model['nonexistent'] raises KeyError."""
        model = Model()
        with pytest.raises(KeyError):
            _ = model["nonexistent"]

    def test_getitem_identity(self) -> None:
        """model[concept.id] is concept (same object)."""
        model = Model()
        e = ConcreteElement(name="X")
        model.add(e)
        assert model[e.id] is e


class TestModelLen:
    def test_len_empty(self) -> None:
        """len(Model()) == 0."""
        assert len(Model()) == 0

    def test_len_after_adds(self) -> None:
        """len(model) reflects number of added concepts."""
        model = Model()
        model.add(ConcreteElement(name="A"))
        model.add(ConcreteElement(name="B"))
        assert len(model) == 2


class TestModelProperties:
    def test_concepts_returns_all(self) -> None:
        """model.concepts returns all concepts as a list."""
        model = Model()
        e = ConcreteElement(name="X")
        c = ConcreteConnector()
        model.add(e)
        model.add(c)
        concepts = model.concepts
        assert len(concepts) == 2
        assert e in concepts
        assert c in concepts

    def test_elements_filters_elements_only(self) -> None:
        """model.elements returns only Element instances."""
        model = Model()
        e = ConcreteElement(name="X")
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        model.add(e)
        model.add(rel)
        assert model.elements == [e]

    def test_relationships_filters_relationships_only(self) -> None:
        """model.relationships returns only Relationship instances."""
        model = Model()
        e = ConcreteElement(name="X")
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        model.add(e)
        model.add(rel)
        assert model.relationships == [rel]

    def test_elements_excludes_relationships(self) -> None:
        """model.elements does not include Relationship instances."""
        model = Model()
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        model.add(rel)
        assert model.elements == []

    def test_relationships_excludes_connectors(self) -> None:
        """model.relationships does not include RelationshipConnector instances."""
        model = Model()
        model.add(ConcreteConnector())
        assert model.relationships == []

    def test_elements_excludes_connectors(self) -> None:
        """model.elements does not include RelationshipConnector instances."""
        model = Model()
        model.add(ConcreteConnector())
        assert model.elements == []

    def test_properties_preserve_insertion_order(self) -> None:
        """elements and relationships maintain insertion order."""
        model = Model()
        e1 = ConcreteElement(name="A")
        e2 = ConcreteElement(name="B")
        model.add(e1)
        model.add(e2)
        assert model.elements == [e1, e2]


class TestModelExports:
    def test_model_in_pyarchi_all(self) -> None:
        """'Model' is in pyarchi.__all__."""
        assert "Model" in pyarchi.__all__

    def test_concept_in_pyarchi_all(self) -> None:
        """'Concept' is in pyarchi.__all__."""
        assert "Concept" in pyarchi.__all__

    def test_element_in_pyarchi_all(self) -> None:
        """'Element' is in pyarchi.__all__."""
        assert "Element" in pyarchi.__all__

    def test_relationship_in_pyarchi_all(self) -> None:
        """'Relationship' is in pyarchi.__all__."""
        assert "Relationship" in pyarchi.__all__

    def test_relationship_connector_in_pyarchi_all(self) -> None:
        """'RelationshipConnector' is in pyarchi.__all__."""
        assert "RelationshipConnector" in pyarchi.__all__

    def test_import_from_pyarchi(self) -> None:
        """from pyarchi import Model, Concept, Element, Relationship, RelationshipConnector."""
        from pyarchi import (  # noqa: PLC0415
            Concept,
            Element,
            Model,
            Relationship,
            RelationshipConnector,
        )

        assert all([Concept, Element, Relationship, RelationshipConnector, Model])
