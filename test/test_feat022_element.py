"""Tests for FEAT-02.2 -- Element ABC."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.metamodel.concepts import Concept, Element
from pyarchi.metamodel.mixins import AttributeMixin


class ConcreteElement(Element):
    @property
    def _type_name(self) -> str:
        return "ConcreteElement"


class TestElement:
    def test_cannot_instantiate_directly(self) -> None:
        """Element() raises TypeError due to abstract _type_name."""
        with pytest.raises(TypeError):
            Element()  # type: ignore[abstract]

    def test_is_subclass_of_concept(self) -> None:
        """issubclass(Element, Concept) is True."""
        assert issubclass(Element, Concept)

    def test_concrete_element_is_instance_of_concept(self) -> None:
        """isinstance(ConcreteElement(name='X'), Concept) is True."""
        assert isinstance(ConcreteElement(name="X"), Concept)

    def test_concrete_element_is_instance_of_element(self) -> None:
        """isinstance(ConcreteElement(name='X'), Element) is True."""
        assert isinstance(ConcreteElement(name="X"), Element)

    def test_name_is_required(self) -> None:
        """ConcreteElement() without name raises ValidationError."""
        with pytest.raises(ValidationError):
            ConcreteElement()  # type: ignore[call-arg]

    def test_name_is_preserved(self) -> None:
        """ConcreteElement(name='Alice').name == 'Alice'."""
        assert ConcreteElement(name="Alice").name == "Alice"

    def test_description_defaults_to_none(self) -> None:
        """ConcreteElement(name='X').description is None."""
        assert ConcreteElement(name="X").description is None

    def test_description_is_preserved(self) -> None:
        """ConcreteElement(name='X', description='D').description == 'D'."""
        assert ConcreteElement(name="X", description="D").description == "D"

    def test_documentation_url_defaults_to_none(self) -> None:
        """ConcreteElement(name='X').documentation_url is None."""
        assert ConcreteElement(name="X").documentation_url is None

    def test_documentation_url_is_preserved(self) -> None:
        """ConcreteElement(name='X', documentation_url='http://x').documentation_url."""
        c = ConcreteElement(name="X", documentation_url="http://x")
        assert c.documentation_url == "http://x"

    def test_id_inherited_from_concept(self) -> None:
        """ConcreteElement(name='X').id is a non-empty string."""
        c = ConcreteElement(name="X")
        assert isinstance(c.id, str)
        assert len(c.id) > 0

    def test_mro_mixin_before_concept(self) -> None:
        """AttributeMixin appears before Concept in Element.__mro__."""
        mro = Element.__mro__
        mixin_pos = mro.index(AttributeMixin)
        concept_pos = mro.index(Concept)
        assert mixin_pos < concept_pos
