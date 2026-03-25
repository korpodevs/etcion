from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from pyarchi.enums import ContentCategory, PurposeCategory
from pyarchi.metamodel.business import BusinessActor, BusinessProcess
from pyarchi.metamodel.concepts import Concept
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.motivation import Stakeholder
from pyarchi.metamodel.viewpoints import Concern, View, Viewpoint


@pytest.fixture
def stakeholder() -> Stakeholder:
    return Stakeholder(name="CTO")


@pytest.fixture
def viewpoint() -> Viewpoint:
    return Viewpoint(
        name="Business VP",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset({BusinessActor, BusinessProcess}),
    )


class TestConcernConstruction:
    def test_minimal(self) -> None:
        c = Concern(description="Data privacy compliance")
        assert c.description == "Data privacy compliance"
        assert c.stakeholders == []
        assert c.viewpoints == []

    def test_with_stakeholder_and_viewpoint(
        self, stakeholder: Stakeholder, viewpoint: Viewpoint
    ) -> None:
        c = Concern(
            description="Operational efficiency",
            stakeholders=[stakeholder],
            viewpoints=[viewpoint],
        )
        assert len(c.stakeholders) == 1
        assert len(c.viewpoints) == 1
        assert c.stakeholders[0] is stakeholder
        assert c.viewpoints[0] is viewpoint

    def test_missing_description_raises(self) -> None:
        with pytest.raises(PydanticValidationError):
            Concern()  # type: ignore[call-arg]


class TestConcernIsNotConcept:
    def test_not_a_concept(self) -> None:
        c = Concern(description="test")
        assert not isinstance(c, Concept)


class TestConcernMutability:
    def test_append_stakeholder(self, stakeholder: Stakeholder) -> None:
        c = Concern(description="test")
        c.stakeholders.append(stakeholder)
        assert len(c.stakeholders) == 1

    def test_append_viewpoint(self, viewpoint: Viewpoint) -> None:
        c = Concern(description="test")
        c.viewpoints.append(viewpoint)
        assert len(c.viewpoints) == 1


class TestStakeholderConcernViewpointNavigation:
    def test_end_to_end_chain(self, stakeholder: Stakeholder, viewpoint: Viewpoint) -> None:
        """Stakeholder -> Concern -> Viewpoint -> View navigation."""
        concern = Concern(
            description="System reliability",
            stakeholders=[stakeholder],
            viewpoints=[viewpoint],
        )

        actor = BusinessActor(name="Alice")
        m = Model()
        m.add(actor)
        m.add(stakeholder)

        view = View(
            governing_viewpoint=viewpoint,
            underlying_model=m,
        )
        view.add(actor)

        # Navigate the chain
        found_viewpoints = concern.viewpoints
        assert viewpoint in found_viewpoints

        found_stakeholders = concern.stakeholders
        assert stakeholder in found_stakeholders

        # Verify the view is governed by a viewpoint reachable from the concern
        assert view.governing_viewpoint in found_viewpoints
        assert len(view.concepts) == 1

    def test_reverse_navigation_via_comprehension(
        self, stakeholder: Stakeholder, viewpoint: Viewpoint
    ) -> None:
        """Find all concerns for a given stakeholder by filtering a collection."""
        c1 = Concern(
            description="Privacy",
            stakeholders=[stakeholder],
            viewpoints=[viewpoint],
        )
        c2 = Concern(description="Unrelated")
        all_concerns = [c1, c2]

        stakeholder_concerns = [c for c in all_concerns if stakeholder in c.stakeholders]
        assert stakeholder_concerns == [c1]


class TestViewpointConcernsBidirectional:
    def test_viewpoint_concerns_field(self, viewpoint: Viewpoint) -> None:
        """Viewpoint.concerns populated at construction time."""
        concern = Concern(description="test")
        vp = Viewpoint(
            name="VP with concerns",
            purpose=PurposeCategory.INFORMING,
            content=ContentCategory.OVERVIEW,
            permitted_concept_types=frozenset({BusinessActor}),
            concerns=[concern],
        )
        assert concern in vp.concerns
