"""Tests for FEAT-02.1 -- Concept ABC."""

from __future__ import annotations

import uuid

import pytest

from pyarchi.metamodel.concepts import Concept


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
