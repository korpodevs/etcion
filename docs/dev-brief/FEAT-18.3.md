# Technical Brief: FEAT-18.3 -- Profile Application to Model

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-030-epic018-language-customization.md` (Decisions 6, 7)
**Backlog:** STORY-18.3.1 through STORY-18.3.4
**Depends on:** FEAT-18.1, FEAT-18.2

---

## 1. Implementation Scope

### Modified File: `src/pyarchi/metamodel/model.py`

| Addition | Type | Purpose |
|---|---|---|
| `_profiles` | `list[Profile]` | Stores applied profiles |
| `_specialization_registry` | `dict[str, type[Element]]` | Maps specialization name to base Element type |
| `apply_profile(profile)` | method | Registers profile, populates registry |
| `profiles` | `@property` | Read-only access to `_profiles` |
| Validation block in `validate()` | code | Checks specialization + extended_attributes consistency |

### `__init__` Changes

```python
def __init__(self, concepts: list[Concept] | None = None) -> None:
    self._concepts: dict[str, Concept] = {}
    self._profiles: list[Profile] = []
    self._specialization_registry: dict[str, type[Element]] = {}
    if concepts is not None:
        for concept in concepts:
            self.add(concept)
```

### `apply_profile` Method

```python
def apply_profile(self, profile: Profile) -> None:
    """Register a Profile with this model.

    :raises TypeError: if *profile* is not a Profile instance.
    :raises ValueError: if a specialization name is already registered.
    """
    if not isinstance(profile, Profile):
        raise TypeError(f"Expected a Profile, got {type(profile).__name__}")
    for base_type, names in profile.specializations.items():
        for name in names:
            if name in self._specialization_registry:
                raise ValueError(
                    f"Duplicate specialization name: '{name}'"
                )
            self._specialization_registry[name] = base_type
    self._profiles.append(profile)
```

### `profiles` Property

```python
@property
def profiles(self) -> list[Profile]:
    """Read-only list of applied profiles."""
    return list(self._profiles)
```

### `validate()` Additions

Append after the existing Junction validation block, before `return errors`:

```python
# FEAT-18.3: Profile validation.
for elem in self.elements:
    # Check specialization string
    if elem.specialization is not None:
        if elem.specialization not in self._specialization_registry:
            err = ValidationError(
                f"Element '{elem.id}': specialization "
                f"'{elem.specialization}' is not declared in any profile"
            )
            if strict:
                raise err
            errors.append(err)
        else:
            expected_base = self._specialization_registry[elem.specialization]
            if not isinstance(elem, expected_base):
                err = ValidationError(
                    f"Element '{elem.id}': specialization "
                    f"'{elem.specialization}' requires base type "
                    f"{expected_base.__name__}, got {type(elem).__name__}"
                )
                if strict:
                    raise err
                errors.append(err)

    # Check extended_attributes against profile declarations
    if elem.extended_attributes:
        # Build allowed attrs for this element's type from all profiles
        allowed: dict[str, type] = {}
        for prof in self._profiles:
            for prof_type, attrs in prof.attribute_extensions.items():
                if isinstance(elem, prof_type):
                    allowed.update(attrs)
        for attr_name, attr_value in elem.extended_attributes.items():
            if attr_name not in allowed:
                err = ValidationError(
                    f"Element '{elem.id}': extended attribute "
                    f"'{attr_name}' is not declared in any profile"
                )
                if strict:
                    raise err
                errors.append(err)
            elif not isinstance(attr_value, allowed[attr_name]):
                err = ValidationError(
                    f"Element '{elem.id}': extended attribute "
                    f"'{attr_name}' expected type "
                    f"{allowed[attr_name].__name__}, "
                    f"got {type(attr_value).__name__}"
                )
                if strict:
                    raise err
                errors.append(err)
```

### Import Additions in `model.py`

```python
from pyarchi.metamodel.profiles import Profile  # top-level import
```

---

## 2. Validation Logic Summary

| Check | When | Error Type |
|---|---|---|
| `apply_profile` receives non-Profile | `apply_profile()` call | `TypeError` |
| Duplicate specialization name across profiles | `apply_profile()` call | `ValueError` |
| Element has `specialization` not in registry | `validate()` | `pyarchi.ValidationError` |
| Element `specialization` maps to wrong base type | `validate()` | `pyarchi.ValidationError` |
| Element has `extended_attributes` key not in any profile | `validate()` | `pyarchi.ValidationError` |
| Element extended attribute value has wrong type | `validate()` | `pyarchi.ValidationError` |
| Element has `extended_attributes` but no profiles applied | `validate()` | `pyarchi.ValidationError` (undeclared) |

---

## 3. Test File: `test/test_feat183_profile_application.py`

```python
"""Tests for FEAT-18.3: Model.apply_profile() and validate() profile checks."""

from __future__ import annotations

from typing import Any

import pytest

from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.concepts import Element
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.profiles import Profile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _AppComponent(Element):
    @property
    def _type_name(self) -> str:
        return "ApplicationComponent"


class _TechService(Element):
    @property
    def _type_name(self) -> str:
        return "TechnologyService"


def _cloud_profile() -> Profile:
    return Profile(
        name="Cloud",
        specializations={_AppComponent: ["Microservice", "Serverless"]},
        attribute_extensions={_AppComponent: {"cost": float}},
    )


def _ops_profile() -> Profile:
    return Profile(
        name="Ops",
        specializations={_TechService: ["ManagedDB"]},
    )


# ===========================================================================
# apply_profile
# ===========================================================================


class TestApplyProfile:
    """STORY-18.3.1: Model.apply_profile() registers a profile."""

    def test_apply_single_profile(self) -> None:
        m = Model()
        p = _cloud_profile()
        m.apply_profile(p)
        assert len(m.profiles) == 1
        assert m.profiles[0].name == "Cloud"

    def test_apply_multiple_profiles(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        m.apply_profile(_ops_profile())
        assert len(m.profiles) == 2

    def test_profiles_returns_copy(self) -> None:
        """Mutating the returned list must not affect internal state."""
        m = Model()
        m.apply_profile(_cloud_profile())
        external = m.profiles
        external.clear()
        assert len(m.profiles) == 1

    def test_non_profile_raises_type_error(self) -> None:
        m = Model()
        with pytest.raises(TypeError, match="Expected a Profile"):
            m.apply_profile("not a profile")  # type: ignore[arg-type]

    def test_duplicate_specialization_name_raises_value_error(self) -> None:
        """Same specialization name in two profiles is rejected."""
        m = Model()
        p1 = Profile(name="A", specializations={_AppComponent: ["Microservice"]})
        p2 = Profile(name="B", specializations={_TechService: ["Microservice"]})
        m.apply_profile(p1)
        with pytest.raises(ValueError, match="Duplicate specialization name.*Microservice"):
            m.apply_profile(p2)

    def test_specialization_registry_populated(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        assert m._specialization_registry["Microservice"] is _AppComponent
        assert m._specialization_registry["Serverless"] is _AppComponent

    def test_model_with_no_profiles(self) -> None:
        m = Model()
        assert m.profiles == []


# ===========================================================================
# validate() -- specialization checks
# ===========================================================================


class TestValidateSpecialization:
    """STORY-18.3.3: validate() checks specialization consistency."""

    def test_valid_specialization_no_errors(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="Orders", specialization="Microservice")
        m.add(elem)
        errors = m.validate()
        spec_errors = [e for e in errors if "specialization" in str(e)]
        assert spec_errors == []

    def test_undeclared_specialization(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X", specialization="UnknownThing")
        m.add(elem)
        errors = m.validate()
        assert any("UnknownThing" in str(e) and "not declared" in str(e) for e in errors)

    def test_undeclared_specialization_strict(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X", specialization="Nope")
        m.add(elem)
        with pytest.raises(ValidationError, match="not declared"):
            m.validate(strict=True)

    def test_wrong_base_type(self) -> None:
        """Microservice is declared for _AppComponent, not _TechService."""
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _TechService(name="DB", specialization="Microservice")
        m.add(elem)
        errors = m.validate()
        assert any("requires base type" in str(e) for e in errors)

    def test_no_specialization_no_error(self) -> None:
        """Elements without specialization are fine."""
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="Plain")
        m.add(elem)
        errors = m.validate()
        spec_errors = [e for e in errors if "specialization" in str(e)]
        assert spec_errors == []

    def test_no_profiles_with_specialized_element(self) -> None:
        """Element has specialization but no profiles applied -> error."""
        m = Model()
        elem = _AppComponent(name="X", specialization="Ghost")
        m.add(elem)
        errors = m.validate()
        assert any("not declared" in str(e) for e in errors)


# ===========================================================================
# validate() -- extended_attributes checks
# ===========================================================================


class TestValidateExtendedAttributes:
    """STORY-18.3.3: validate() type-checks extended attributes."""

    def test_valid_extended_attribute(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X", extended_attributes={"cost": 9.99})
        m.add(elem)
        errors = m.validate()
        attr_errors = [e for e in errors if "extended attribute" in str(e)]
        assert attr_errors == []

    def test_undeclared_extended_attribute(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X", extended_attributes={"color": "red"})
        m.add(elem)
        errors = m.validate()
        assert any("'color' is not declared" in str(e) for e in errors)

    def test_wrong_type_extended_attribute(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X", extended_attributes={"cost": "expensive"})
        m.add(elem)
        errors = m.validate()
        assert any("expected type float" in str(e) for e in errors)

    def test_extended_attributes_strict(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X", extended_attributes={"cost": "bad"})
        m.add(elem)
        with pytest.raises(ValidationError, match="expected type float"):
            m.validate(strict=True)

    def test_no_extended_attributes_no_error(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X")
        m.add(elem)
        errors = m.validate()
        attr_errors = [e for e in errors if "extended attribute" in str(e)]
        assert attr_errors == []

    def test_extended_attributes_no_profiles(self) -> None:
        """Extended attributes present but no profiles -> all undeclared."""
        m = Model()
        elem = _AppComponent(name="X", extended_attributes={"cost": 1.0})
        m.add(elem)
        errors = m.validate()
        assert any("'cost' is not declared" in str(e) for e in errors)

    def test_attribute_from_parent_profile_type(self) -> None:
        """Profile declares extension on Element (parent); concrete subclass inherits it."""
        p = Profile(
            name="Universal",
            attribute_extensions={Element: {"priority": int}},
        )
        m = Model()
        m.apply_profile(p)
        elem = _AppComponent(name="X", extended_attributes={"priority": 5})
        m.add(elem)
        errors = m.validate()
        attr_errors = [e for e in errors if "extended attribute" in str(e)]
        assert attr_errors == []


# ===========================================================================
# Combined scenarios
# ===========================================================================


class TestCombinedScenarios:
    """Integration-level tests mixing specialization and extended attributes."""

    def test_specialized_element_with_extended_attrs(self) -> None:
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(
            name="Cart",
            specialization="Microservice",
            extended_attributes={"cost": 12.5},
        )
        m.add(elem)
        errors = m.validate()
        profile_errors = [
            e for e in errors
            if "specialization" in str(e) or "extended attribute" in str(e)
        ]
        assert profile_errors == []

    def test_multiple_profiles_compose(self) -> None:
        """Attributes from multiple profiles are all valid."""
        p1 = Profile(
            name="Cost",
            attribute_extensions={_AppComponent: {"cost": float}},
        )
        p2 = Profile(
            name="Team",
            attribute_extensions={_AppComponent: {"owner": str}},
        )
        m = Model()
        m.apply_profile(p1)
        m.apply_profile(p2)
        elem = _AppComponent(
            name="X",
            extended_attributes={"cost": 1.0, "owner": "TeamA"},
        )
        m.add(elem)
        errors = m.validate()
        attr_errors = [e for e in errors if "extended attribute" in str(e)]
        assert attr_errors == []

    def test_existing_relationship_validation_still_works(self) -> None:
        """Profile additions must not break existing validate() logic."""
        m = Model()
        m.apply_profile(_cloud_profile())
        elem = _AppComponent(name="X", specialization="Microservice")
        m.add(elem)
        # validate() returns list; should not raise
        errors = m.validate()
        assert isinstance(errors, list)
```

---

## 4. Edge Cases

| Case | Expected |
|---|---|
| `apply_profile` called after `add` | Valid -- validation is deferred to `validate()` |
| Element with specialization, no profiles | `validate()` returns error |
| Element with `extended_attributes={}` | No errors (empty dict is fine) |
| Profile declares extension on abstract `Element` | All concrete subclasses inherit the allowance via `isinstance` |
| Two profiles declare same specialization name | `ValueError` at `apply_profile()` time |

---

## 5. Files Changed Summary

| File | Action |
|---|---|
| `src/pyarchi/metamodel/model.py` | **Modify** -- add `_profiles`, `_specialization_registry`, `apply_profile()`, `profiles` property, validation block |
| `test/test_feat183_profile_application.py` | **Create** -- test file above |
