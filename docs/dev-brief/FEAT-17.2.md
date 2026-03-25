# Technical Brief: FEAT-17.2 -- Viewpoint Class

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-029-epic017-viewpoint-mechanism.md`
**Spec:** ArchiMate 3.2, Section 13.2
**Depends on:** FEAT-17.1 (enums)

## Scope

| Artifact | Location |
|---|---|
| `Viewpoint` | `src/pyarchi/metamodel/viewpoints.py` |

## Class Structure

```python
from pydantic import BaseModel, ConfigDict

class Viewpoint(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    name: str
    purpose: PurposeCategory
    content: ContentCategory
    permitted_concept_types: frozenset[type[Concept]]
    representation_description: str | None = None
    concerns: list[Concern] = []
```

NOT a `Concept` subclass. No `id`, no `_type_name`.

## Fields

| Field | Type | Required | Default | Frozen |
|---|---|---|---|---|
| `name` | `str` | Yes | -- | Yes |
| `purpose` | `PurposeCategory` | Yes | -- | Yes |
| `content` | `ContentCategory` | Yes | -- | Yes |
| `permitted_concept_types` | `frozenset[type[Concept]]` | Yes | -- | Yes |
| `representation_description` | `str \| None` | No | `None` | Yes |
| `concerns` | `list[Concern]` | No | `[]` | Yes |

## Validation

- `name` is required (Pydantic enforces non-optional `str`).
- `frozen=True` prevents mutation after construction.
- `permitted_concept_types` holds class references, not instances.

## Test File: `test/test_feat172_viewpoint.py`

```python
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

    def test_no_id_field(self, basic_viewpoint: Viewpoint) -> None:
        assert not hasattr(basic_viewpoint, "id") or "id" not in basic_viewpoint.model_fields


class TestCustomViewpoints:
    def test_user_defined_viewpoint_accepted(self) -> None:
        vp = Viewpoint(
            name="My Custom VP",
            purpose=PurposeCategory.DECIDING,
            content=ContentCategory.COHERENCE,
            permitted_concept_types=frozenset({BusinessActor, BusinessProcess}),
        )
        assert len(vp.permitted_concept_types) == 2
```
