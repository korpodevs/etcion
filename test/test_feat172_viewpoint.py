from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from pyarchi.enums import ContentCategory, PurposeCategory
from pyarchi.metamodel.business import BusinessActor, BusinessProcess
from pyarchi.metamodel.concepts import Concept
from pyarchi.metamodel.viewpoints import Viewpoint


@pytest.fixture
def basic_viewpoint() -> Viewpoint:
    return Viewpoint(
        name="Test VP",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset({BusinessActor}),
    )


class TestViewpointConstruction:
    def test_minimal_construction(self, basic_viewpoint: Viewpoint) -> None:
        assert basic_viewpoint.name == "Test VP"
        assert basic_viewpoint.purpose == PurposeCategory.DESIGNING
        assert basic_viewpoint.content == ContentCategory.DETAILS
        assert BusinessActor in basic_viewpoint.permitted_concept_types

    def test_optional_fields_default(self, basic_viewpoint: Viewpoint) -> None:
        assert basic_viewpoint.representation_description is None
        assert basic_viewpoint.concerns == []

    def test_with_representation_description(self) -> None:
        vp = Viewpoint(
            name="VP",
            purpose=PurposeCategory.INFORMING,
            content=ContentCategory.OVERVIEW,
            permitted_concept_types=frozenset({BusinessActor}),
            representation_description="Shows actors only",
        )
        assert vp.representation_description == "Shows actors only"

    def test_missing_name_raises(self) -> None:
        with pytest.raises(PydanticValidationError):
            Viewpoint(
                purpose=PurposeCategory.DESIGNING,
                content=ContentCategory.DETAILS,
                permitted_concept_types=frozenset({BusinessActor}),
            )  # type: ignore[call-arg]

    def test_missing_purpose_raises(self) -> None:
        with pytest.raises(PydanticValidationError):
            Viewpoint(
                name="VP",
                content=ContentCategory.DETAILS,
                permitted_concept_types=frozenset({BusinessActor}),
            )  # type: ignore[call-arg]


class TestViewpointImmutability:
    def test_frozen_name(self, basic_viewpoint: Viewpoint) -> None:
        with pytest.raises(PydanticValidationError):
            basic_viewpoint.name = "Changed"  # type: ignore[misc]

    def test_frozen_permitted_types(self, basic_viewpoint: Viewpoint) -> None:
        with pytest.raises(PydanticValidationError):
            basic_viewpoint.permitted_concept_types = frozenset()  # type: ignore[misc]


class TestViewpointIsNotConcept:
    def test_not_a_concept(self, basic_viewpoint: Viewpoint) -> None:
        assert not isinstance(basic_viewpoint, Concept)

    def test_no_id_field(self) -> None:
        assert "id" not in Viewpoint.model_fields


class TestCustomViewpoints:
    def test_user_defined_viewpoint_accepted(self) -> None:
        vp = Viewpoint(
            name="My Custom VP",
            purpose=PurposeCategory.DECIDING,
            content=ContentCategory.COHERENCE,
            permitted_concept_types=frozenset({BusinessActor, BusinessProcess}),
        )
        assert len(vp.permitted_concept_types) == 2
