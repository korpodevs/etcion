# Technical Brief: FEAT-11.2 Motivation Goal-Oriented Elements

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-023-epic011-motivation-elements.md`
**Epic:** EPIC-011

---

## Feature Summary

Add five concrete classes to `src/pyarchi/metamodel/motivation.py`: `Goal`, `Outcome`, `Principle`, `Requirement`, `Constraint`, all extending `MotivationElement` directly. Wire `NotationMetadata` with `badge_letter="M"` and `layer_color="#CCCCFF"` on all five.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-11.1 (`motivation.py` exists, `MotivationElement` has ClassVars) | Must be done first |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-023 Decisions 2, 3, 5, 6 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 11.2.1 | `Goal(MotivationElement)` | `_type_name == "Goal"` |
| 11.2.2 | `Outcome(MotivationElement)` | `_type_name == "Outcome"` |
| 11.2.3 | `Principle(MotivationElement)` | `_type_name == "Principle"` |
| 11.2.4 | `Requirement(MotivationElement)` | `_type_name == "Requirement"` |
| 11.2.5 | `Constraint(MotivationElement)` | `_type_name == "Constraint"` |
| 11.2.6 | ClassVars | All five: `layer is Layer.MOTIVATION`, `aspect is Aspect.MOTIVATION` (inherited) |
| 11.2.7 | `NotationMetadata` | All five: `layer_color="#CCCCFF"`, `badge_letter="M"` |
| 11.2.8 | Test | All five instantiate without error |
| 11.2.9 | Test | `Goal` and `Outcome` are distinct types |
| 11.2.10 | Test | `Principle`, `Requirement`, `Constraint` are distinct types |

## Implementation

### Additions to `src/pyarchi/metamodel/motivation.py`

```python
class Goal(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Goal"


class Outcome(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Outcome"


class Principle(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Principle"


class Requirement(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Requirement"


class Constraint(MotivationElement):
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="round",
        layer_color="#CCCCFF",
        badge_letter="M",
    )

    @property
    def _type_name(self) -> str:
        return "Constraint"
```

## Test File: `test/test_feat112_motivation_goal_oriented.py`

```python
"""Tests for FEAT-11.2 -- Motivation Goal-Oriented concrete elements."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import MotivationElement
from pyarchi.metamodel.motivation import (
    Constraint,
    Goal,
    Outcome,
    Principle,
    Requirement,
)

ALL_GOAL_ORIENTED = [Goal, Outcome, Principle, Requirement, Constraint]


class TestInstantiation:
    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames:
    @pytest.mark.parametrize(
        ("cls", "expected"),
        [
            (Goal, "Goal"),
            (Outcome, "Outcome"),
            (Principle, "Principle"),
            (Requirement, "Requirement"),
            (Constraint, "Constraint"),
        ],
    )
    def test_type_name(self, cls: type, expected: str) -> None:
        assert cls(name="x")._type_name == expected


class TestInheritance:
    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_is_motivation_element(self, cls: type) -> None:
        assert issubclass(cls, MotivationElement)

    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_extends_motivation_element_directly(self, cls: type) -> None:
        assert cls.__bases__ == (MotivationElement,)


class TestDistinctTypes:
    def test_goal_and_outcome_are_distinct(self) -> None:
        assert Goal is not Outcome
        assert not issubclass(Goal, Outcome)
        assert not issubclass(Outcome, Goal)

    def test_principle_requirement_constraint_are_distinct(self) -> None:
        triple = [Principle, Requirement, Constraint]
        for i, a in enumerate(triple):
            for j, b in enumerate(triple):
                if i != j:
                    assert a is not b
                    assert not issubclass(a, b)


class TestClassVars:
    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_layer_is_motivation(self, cls: type) -> None:
        assert cls.layer is Layer.MOTIVATION

    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_aspect_is_motivation(self, cls: type) -> None:
        assert cls.aspect is Aspect.MOTIVATION


class TestNotation:
    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#CCCCFF"

    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "M"

    @pytest.mark.parametrize("cls", ALL_GOAL_ORIENTED)
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/motivation.py test/test_feat112_motivation_goal_oriented.py
ruff format --check src/pyarchi/metamodel/motivation.py test/test_feat112_motivation_goal_oriented.py
mypy src/pyarchi/metamodel/motivation.py test/test_feat112_motivation_goal_oriented.py
pytest test/test_feat112_motivation_goal_oriented.py -v
pytest  # full suite, no regressions
```
