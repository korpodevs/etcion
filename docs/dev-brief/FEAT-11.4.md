# Technical Brief: FEAT-11.4 Motivation Cross-Layer Validation Rules

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-023-epic011-motivation-elements.md`
**Epic:** EPIC-011

---

## Feature Summary

Add permission table entries to `src/pyarchi/validation/permissions.py` for three cross-layer Motivation relationship rules. No changes to element classes.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-11.1, 11.2, 11.3 (all 10 Motivation concrete classes) | Must be done first |
| EPIC-005 (`permissions.py`, `is_permitted()`) | Done |
| EPIC-007 (`BusinessActor`, `BusinessRole`, `BusinessCollaboration`) | Done |
| EPIC-005 (`Assignment`, `Realization`, `Influence`) | Done |
| ADR-023 Decision 7 | Accepted |

## Stories -> Acceptance

| Story | Rule | Acceptance |
|---|---|---|
| 11.4.1 | Assignment to Stakeholder | Only `BusinessActor`, `BusinessRole`, `BusinessCollaboration` permitted as source |
| 11.4.2 | Realization of Requirement | Core structure/behavior elements permitted as source |
| 11.4.3 | Influence between motivation and core | `Influence` permitted from any motivation element to any core element and vice versa |
| 11.4.4 | Test | `is_permitted(Assignment, ApplicationComponent, Stakeholder)` returns `False` |
| 11.4.5 | Test | `is_permitted(Assignment, BusinessActor, Stakeholder)` returns `True` |
| 11.4.6 | Test | `is_permitted(Influence, Assessment, Goal)` returns `True` |

## Implementation

### Changes to `src/pyarchi/validation/permissions.py`

Add new imports and populate `_PERMITTED_TRIPLES` with the cross-layer entries. The exact set of triples depends on which core element types exist at implementation time. At minimum:

**Assignment to Stakeholder** (3 triples):

| Source | Relationship | Target |
|---|---|---|
| `BusinessActor` | `Assignment` | `Stakeholder` |
| `BusinessRole` | `Assignment` | `Stakeholder` |
| `BusinessCollaboration` | `Assignment` | `Stakeholder` |

**Realization of Requirement** (source: any concrete structure or behavior element that exists in the codebase). The implementer should collect all concrete subclasses of `StructureElement` and `BehaviorElement` that have a `_type_name` property, and add `(Realization, <source>, Requirement)` for each.

**Influence** (motivation <-> core): Add `(Influence, <motivation_type>, <core_type>)` and `(Influence, <core_type>, <motivation_type>)` for each pair of concrete motivation element and concrete core element.

> **Implementation note:** If the number of triples becomes large, consider a helper function that generates the frozenset programmatically from class hierarchies rather than hand-enumerating every triple. Alternatively, add a rule-based check in `is_permitted()` before the triple lookup (e.g., `if rel_type is Assignment and issubclass(target_type, Stakeholder): return issubclass(source_type, BusinessInternalActiveStructureElement)`). The implementer should choose the approach that best fits the existing `is_permitted()` architecture.

## Test File: `test/test_feat114_motivation_cross_layer.py`

```python
"""Tests for FEAT-11.4 -- Motivation cross-layer validation rules."""
from __future__ import annotations

import pytest

from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessRole,
)
from pyarchi.metamodel.motivation import (
    Assessment,
    Constraint,
    Driver,
    Goal,
    Meaning,
    Outcome,
    Principle,
    Requirement,
    Stakeholder,
    Value,
)
from pyarchi.metamodel.relationships import Assignment, Influence, Realization
from pyarchi.validation.permissions import is_permitted

ALL_MOTIVATION = [
    Stakeholder, Driver, Assessment,
    Goal, Outcome, Principle, Requirement, Constraint,
    Meaning, Value,
]


class TestAssignmentToStakeholder:
    """Only Business active structure sources may target Stakeholder."""

    @pytest.mark.parametrize(
        "source_type",
        [BusinessActor, BusinessRole, BusinessCollaboration],
    )
    def test_permitted_sources(self, source_type: type) -> None:
        assert is_permitted(Assignment, source_type, Stakeholder) is True

    @pytest.mark.parametrize(
        "source_type",
        [Goal, Driver, Assessment, Requirement],
    )
    def test_forbidden_motivation_sources(self, source_type: type) -> None:
        assert is_permitted(Assignment, source_type, Stakeholder) is False


class TestRealizationOfRequirement:
    """Core structure/behavior elements may realize Requirement."""

    def test_business_actor_realizes_requirement(self) -> None:
        assert is_permitted(Realization, BusinessActor, Requirement) is True

    @pytest.mark.parametrize(
        "source_type",
        [Goal, Driver, Assessment, Stakeholder],
    )
    def test_motivation_cannot_realize_requirement(self, source_type: type) -> None:
        assert is_permitted(Realization, source_type, Requirement) is False


class TestInfluence:
    """Influence permitted between motivation elements."""

    def test_assessment_influences_goal(self) -> None:
        assert is_permitted(Influence, Assessment, Goal) is True

    def test_driver_influences_requirement(self) -> None:
        assert is_permitted(Influence, Driver, Requirement) is True

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (Stakeholder, Goal),
            (Goal, Principle),
            (Outcome, Constraint),
            (Meaning, Value),
        ],
    )
    def test_motivation_to_motivation_influence(
        self, source: type, target: type
    ) -> None:
        assert is_permitted(Influence, source, target) is True
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/validation/permissions.py test/test_feat114_motivation_cross_layer.py
ruff format --check src/pyarchi/validation/permissions.py test/test_feat114_motivation_cross_layer.py
mypy src/pyarchi/validation/permissions.py test/test_feat114_motivation_cross_layer.py
pytest test/test_feat114_motivation_cross_layer.py -v
pytest  # full suite, no regressions
```
