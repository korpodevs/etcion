"""Tests for Issue #52: Declarative value constraints on Profile attribute extensions.

TDD — these tests are written BEFORE implementation.

Stages covered:
  1. Profile construction accepting dict constraints + validation of constraint keys
  2. Model.validate() enforcement of constraints (allowed, min/max, required)
  3. JSON serialization round-trip of constraints
  4. XML serialization round-trip of constraints
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from etcion.exceptions import ValidationError
from etcion.metamodel.concepts import Element
from etcion.metamodel.model import Model
from etcion.metamodel.profiles import Profile

# ---------------------------------------------------------------------------
# Shared stubs
# ---------------------------------------------------------------------------


class _AppSvc(Element):
    @property
    def _type_name(self) -> str:
        return "ApplicationService"


class _AppComponent(Element):
    @property
    def _type_name(self) -> str:
        return "ApplicationComponent"


# ===========================================================================
# Stage 1 — Profile construction: dict constraint form
# ===========================================================================


class TestProfileConstructionWithDictConstraints:
    """Profile accepts the extended dict-form for attribute_extensions values."""

    def test_bare_type_form_still_accepted(self) -> None:
        """Backward-compatibility: {'attr': type} continues to work."""
        p = Profile(
            name="Plain",
            attribute_extensions={_AppSvc: {"cost": float}},
        )
        assert p.attribute_extensions[_AppSvc]["cost"] is float

    def test_dict_form_with_type_only(self) -> None:
        """{'attr': {'type': float}} is accepted and normalized."""
        p = Profile(
            name="DictOnly",
            attribute_extensions={_AppSvc: {"cost": {"type": float}}},
        )
        assert _AppSvc in p.attribute_extensions

    def test_dict_form_with_allowed_constraint(self) -> None:
        """{'type': str, 'allowed': [...]} is accepted."""
        p = Profile(
            name="WithAllowed",
            attribute_extensions={
                _AppSvc: {
                    "risk_score": {"type": str, "allowed": ["low", "medium", "high", "critical"]}
                }
            },
        )
        assert _AppSvc in p.attribute_extensions

    def test_dict_form_with_min_constraint(self) -> None:
        """{'type': float, 'min': 0.0} is accepted."""
        p = Profile(
            name="WithMin",
            attribute_extensions={_AppSvc: {"tco": {"type": float, "min": 0.0}}},
        )
        assert _AppSvc in p.attribute_extensions

    def test_dict_form_with_max_constraint(self) -> None:
        """{'type': float, 'max': 100.0} is accepted."""
        p = Profile(
            name="WithMax",
            attribute_extensions={_AppSvc: {"score": {"type": float, "max": 100.0}}},
        )
        assert _AppSvc in p.attribute_extensions

    def test_dict_form_with_min_and_max(self) -> None:
        """{'type': float, 'min': 0.0, 'max': 1.0} is accepted."""
        p = Profile(
            name="WithRange",
            attribute_extensions={_AppSvc: {"ratio": {"type": float, "min": 0.0, "max": 1.0}}},
        )
        assert _AppSvc in p.attribute_extensions

    def test_dict_form_with_required_constraint(self) -> None:
        """{'type': str, 'required': True} is accepted."""
        p = Profile(
            name="WithRequired",
            attribute_extensions={_AppSvc: {"owner": {"type": str, "required": True}}},
        )
        assert _AppSvc in p.attribute_extensions

    def test_dict_form_all_constraints_together(self) -> None:
        """The full example from the issue description is accepted."""
        p = Profile(
            name="RiskManagement",
            attribute_extensions={
                _AppSvc: {
                    "risk_score": {"type": str, "allowed": ["low", "medium", "high", "critical"]},
                    "tco": {"type": float, "min": 0.0},
                    "owner": {"type": str, "required": True},
                }
            },
        )
        assert _AppSvc in p.attribute_extensions

    def test_dict_form_missing_type_key_rejected(self) -> None:
        """A dict without the 'type' key must be rejected at construction time."""
        with pytest.raises(PydanticValidationError, match="'type'"):
            Profile(
                name="Bad",
                attribute_extensions={_AppSvc: {"score": {"allowed": ["a", "b"]}}},
            )

    def test_dict_form_unrecognized_constraint_key_rejected(self) -> None:
        """Unknown constraint keys are rejected at construction time."""
        with pytest.raises(PydanticValidationError, match="unrecognized constraint"):
            Profile(
                name="Bad",
                attribute_extensions={_AppSvc: {"score": {"type": str, "regex": r"\d+"}}},
            )

    def test_allowed_must_be_a_list(self) -> None:
        """'allowed' value must be a list."""
        with pytest.raises(PydanticValidationError, match="allowed"):
            Profile(
                name="Bad",
                attribute_extensions={_AppSvc: {"risk": {"type": str, "allowed": "low"}}},
            )

    def test_min_must_be_numeric(self) -> None:
        """'min' value must be numeric (int or float)."""
        with pytest.raises(PydanticValidationError, match="min"):
            Profile(
                name="Bad",
                attribute_extensions={_AppSvc: {"score": {"type": float, "min": "zero"}}},
            )

    def test_max_must_be_numeric(self) -> None:
        """'max' value must be numeric (int or float)."""
        with pytest.raises(PydanticValidationError, match="max"):
            Profile(
                name="Bad",
                attribute_extensions={_AppSvc: {"score": {"type": float, "max": "hundred"}}},
            )

    def test_required_must_be_bool(self) -> None:
        """'required' value must be a bool."""
        with pytest.raises(PydanticValidationError, match="required"):
            Profile(
                name="Bad",
                attribute_extensions={_AppSvc: {"owner": {"type": str, "required": "yes"}}},
            )

    def test_min_greater_than_max_rejected(self) -> None:
        """min > max is a nonsensical constraint and must be rejected."""
        with pytest.raises(PydanticValidationError, match="min.*max|max.*min"):
            Profile(
                name="Bad",
                attribute_extensions={_AppSvc: {"score": {"type": float, "min": 10.0, "max": 1.0}}},
            )

    def test_field_name_conflict_still_rejected_in_dict_form(self) -> None:
        """Existing field collision check applies to the dict form too."""
        with pytest.raises(PydanticValidationError, match="'name' conflicts"):
            Profile(
                name="Bad",
                attribute_extensions={_AppSvc: {"name": {"type": str, "required": True}}},
            )


# ===========================================================================
# Stage 2 — Model.validate() constraint enforcement
# ===========================================================================


class TestValidateAllowedConstraint:
    """validate() rejects values not in the allowed list."""

    def _make_model(self, value: object) -> Model:
        profile = Profile(
            name="Risk",
            attribute_extensions={
                _AppSvc: {
                    "risk_score": {"type": str, "allowed": ["low", "medium", "high", "critical"]}
                }
            },
        )
        m = Model()
        m.apply_profile(profile)
        elem = _AppSvc(name="PaymentService", extended_attributes={"risk_score": value})
        m.add(elem)
        return m

    def test_allowed_value_passes(self) -> None:
        m = self._make_model("high")
        errors = m.validate()
        constraint_errors = [e for e in errors if "risk_score" in str(e)]
        assert constraint_errors == []

    def test_disallowed_value_fails(self) -> None:
        m = self._make_model("extreme")
        errors = m.validate()
        assert any("risk_score" in str(e) and "allowed" in str(e) for e in errors)

    def test_disallowed_value_strict(self) -> None:
        m = self._make_model("extreme")
        with pytest.raises(ValidationError, match="allowed"):
            m.validate(strict=True)

    def test_error_message_contains_value(self) -> None:
        m = self._make_model("extreme")
        errors = m.validate()
        assert any("'extreme'" in str(e) or "extreme" in str(e) for e in errors)

    def test_error_message_contains_allowed_list(self) -> None:
        m = self._make_model("extreme")
        errors = m.validate()
        assert any("low" in str(e) or "critical" in str(e) for e in errors)


class TestValidateMinConstraint:
    """validate() rejects values below the declared minimum."""

    def _make_model(self, value: object) -> Model:
        profile = Profile(
            name="Cost",
            attribute_extensions={_AppSvc: {"tco": {"type": float, "min": 0.0}}},
        )
        m = Model()
        m.apply_profile(profile)
        elem = _AppSvc(name="SomeService", extended_attributes={"tco": value})
        m.add(elem)
        return m

    def test_value_at_min_passes(self) -> None:
        m = self._make_model(0.0)
        errors = m.validate()
        constraint_errors = [e for e in errors if "tco" in str(e)]
        assert constraint_errors == []

    def test_value_above_min_passes(self) -> None:
        m = self._make_model(1000.0)
        errors = m.validate()
        constraint_errors = [e for e in errors if "tco" in str(e)]
        assert constraint_errors == []

    def test_value_below_min_fails(self) -> None:
        m = self._make_model(-1.0)
        errors = m.validate()
        assert any("tco" in str(e) and "min" in str(e) for e in errors)

    def test_value_below_min_strict(self) -> None:
        m = self._make_model(-1.0)
        with pytest.raises(ValidationError, match="min"):
            m.validate(strict=True)


class TestValidateMaxConstraint:
    """validate() rejects values above the declared maximum."""

    def _make_model(self, value: object) -> Model:
        profile = Profile(
            name="Score",
            attribute_extensions={_AppSvc: {"score": {"type": float, "max": 100.0}}},
        )
        m = Model()
        m.apply_profile(profile)
        elem = _AppSvc(name="SomeService", extended_attributes={"score": value})
        m.add(elem)
        return m

    def test_value_at_max_passes(self) -> None:
        m = self._make_model(100.0)
        errors = m.validate()
        constraint_errors = [e for e in errors if "score" in str(e)]
        assert constraint_errors == []

    def test_value_below_max_passes(self) -> None:
        m = self._make_model(42.0)
        errors = m.validate()
        constraint_errors = [e for e in errors if "score" in str(e)]
        assert constraint_errors == []

    def test_value_above_max_fails(self) -> None:
        m = self._make_model(101.0)
        errors = m.validate()
        assert any("score" in str(e) and "max" in str(e) for e in errors)

    def test_value_above_max_strict(self) -> None:
        m = self._make_model(101.0)
        with pytest.raises(ValidationError, match="max"):
            m.validate(strict=True)


class TestValidateMinMaxRange:
    """validate() checks both bounds when min and max are declared."""

    def _make_model(self, value: object) -> Model:
        profile = Profile(
            name="Ratio",
            attribute_extensions={_AppSvc: {"ratio": {"type": float, "min": 0.0, "max": 1.0}}},
        )
        m = Model()
        m.apply_profile(profile)
        elem = _AppSvc(name="SomeService", extended_attributes={"ratio": value})
        m.add(elem)
        return m

    def test_mid_range_passes(self) -> None:
        m = self._make_model(0.5)
        errors = m.validate()
        constraint_errors = [e for e in errors if "ratio" in str(e)]
        assert constraint_errors == []

    def test_below_range_fails(self) -> None:
        m = self._make_model(-0.1)
        errors = m.validate()
        assert any("ratio" in str(e) for e in errors)

    def test_above_range_fails(self) -> None:
        m = self._make_model(1.1)
        errors = m.validate()
        assert any("ratio" in str(e) for e in errors)


class TestValidateRequiredConstraint:
    """validate() reports missing attributes when required=True."""

    def _profile(self) -> Profile:
        return Profile(
            name="OwnerRequired",
            attribute_extensions={_AppSvc: {"owner": {"type": str, "required": True}}},
        )

    def test_attribute_present_passes(self) -> None:
        m = Model()
        m.apply_profile(self._profile())
        elem = _AppSvc(name="Svc", extended_attributes={"owner": "TeamA"})
        m.add(elem)
        errors = m.validate()
        constraint_errors = [e for e in errors if "owner" in str(e)]
        assert constraint_errors == []

    def test_attribute_absent_fails(self) -> None:
        m = Model()
        m.apply_profile(self._profile())
        elem = _AppSvc(name="Svc")  # no extended_attributes
        m.add(elem)
        errors = m.validate()
        assert any("owner" in str(e) and "required" in str(e) for e in errors)

    def test_attribute_absent_strict(self) -> None:
        m = Model()
        m.apply_profile(self._profile())
        elem = _AppSvc(name="Svc")
        m.add(elem)
        with pytest.raises(ValidationError, match="required"):
            m.validate(strict=True)

    def test_required_false_and_absent_is_fine(self) -> None:
        """required=False (or omitted) must not produce an error for absent attrs."""
        profile = Profile(
            name="OptionalOwner",
            attribute_extensions={_AppSvc: {"owner": {"type": str, "required": False}}},
        )
        m = Model()
        m.apply_profile(profile)
        elem = _AppSvc(name="Svc")
        m.add(elem)
        errors = m.validate()
        constraint_errors = [e for e in errors if "owner" in str(e)]
        assert constraint_errors == []


class TestValidateMultipleConstraintsComposed:
    """Constraints from the same and different profiles compose correctly."""

    def test_all_constraints_pass(self) -> None:
        profile = Profile(
            name="RiskManagement",
            attribute_extensions={
                _AppSvc: {
                    "risk_score": {"type": str, "allowed": ["low", "medium", "high", "critical"]},
                    "tco": {"type": float, "min": 0.0},
                    "owner": {"type": str, "required": True},
                }
            },
        )
        m = Model()
        m.apply_profile(profile)
        elem = _AppSvc(
            name="PaymentGateway",
            extended_attributes={"risk_score": "high", "tco": 50000.0, "owner": "FinanceTeam"},
        )
        m.add(elem)
        errors = m.validate()
        constraint_errors = [
            e
            for e in errors
            if any(k in str(e) for k in ["risk_score", "tco", "owner"])
        ]
        assert constraint_errors == []

    def test_multiple_violations_all_reported(self) -> None:
        """All constraint violations are collected, not just the first."""
        profile = Profile(
            name="RiskManagement",
            attribute_extensions={
                _AppSvc: {
                    "risk_score": {"type": str, "allowed": ["low", "medium", "high", "critical"]},
                    "tco": {"type": float, "min": 0.0},
                }
            },
        )
        m = Model()
        m.apply_profile(profile)
        elem = _AppSvc(
            name="BadService",
            extended_attributes={"risk_score": "extreme", "tco": -100.0},
        )
        m.add(elem)
        errors = m.validate()
        attr_errors = [
            e for e in errors if "risk_score" in str(e) or "tco" in str(e)
        ]
        assert len(attr_errors) >= 2

    def test_bare_type_profile_still_validates_as_before(self) -> None:
        """Backward compat: profiles with bare types still get type-checked only."""
        profile = Profile(
            name="Legacy",
            attribute_extensions={_AppSvc: {"cost": float}},
        )
        m = Model()
        m.apply_profile(profile)
        elem = _AppSvc(name="Svc", extended_attributes={"cost": "not-a-float"})
        m.add(elem)
        errors = m.validate()
        assert any("expected type float" in str(e) for e in errors)


# ===========================================================================
# Stage 3 — JSON serialization round-trip of constraints
# ===========================================================================


class TestJsonConstraintRoundTrip:
    """Constraints survive model_to_dict -> model_from_dict."""

    def _constrained_profile(self) -> Profile:
        return Profile(
            name="RiskManagement",
            attribute_extensions={
                _AppSvc: {
                    "risk_score": {"type": str, "allowed": ["low", "medium", "high", "critical"]},
                    "tco": {"type": float, "min": 0.0},
                    "owner": {"type": str, "required": True},
                }
            },
        )

    def _constrained_model(self) -> Model:
        from etcion.metamodel.application import ApplicationService

        profile = Profile(
            name="RiskManagement",
            attribute_extensions={
                ApplicationService: {
                    "risk_score": {"type": str, "allowed": ["low", "medium", "high", "critical"]},
                    "tco": {"type": float, "min": 0.0},
                    "owner": {"type": str, "required": True},
                }
            },
        )
        m = Model()
        m.apply_profile(profile)
        elem = ApplicationService(
            name="PaymentGateway",
            extended_attributes={"risk_score": "high", "tco": 50000.0, "owner": "FinanceTeam"},
        )
        m.add(elem)
        return m

    def test_constraint_dict_serialized_to_json(self) -> None:
        """model_to_dict includes constraint keys in the profile's attribute_extensions."""
        from etcion.serialization.json import model_to_dict

        m = self._constrained_model()
        data = model_to_dict(m)
        profiles = data["profiles"]
        assert len(profiles) == 1
        attr_ext = profiles[0]["attribute_extensions"]
        # At least one element type should have constraint-carrying entries
        assert len(attr_ext) > 0

    def test_allowed_constraint_survives_json_round_trip(self) -> None:
        """After round-trip, validate() still catches an 'allowed' violation."""
        from etcion.metamodel.application import ApplicationService
        from etcion.serialization.json import model_from_dict, model_to_dict

        m = self._constrained_model()
        data = model_to_dict(m)
        restored = model_from_dict(data)

        # Inject a bad element and validate
        bad_elem = ApplicationService(
            name="BadService",
            extended_attributes={"risk_score": "extreme", "tco": 1.0, "owner": "X"},
        )
        restored.add(bad_elem)
        errors = restored.validate()
        assert any("risk_score" in str(e) and "allowed" in str(e) for e in errors)

    def test_min_constraint_survives_json_round_trip(self) -> None:
        """After round-trip, validate() still catches a 'min' violation."""
        from etcion.metamodel.application import ApplicationService
        from etcion.serialization.json import model_from_dict, model_to_dict

        m = self._constrained_model()
        data = model_to_dict(m)
        restored = model_from_dict(data)

        bad_elem = ApplicationService(
            name="BadService",
            extended_attributes={"risk_score": "low", "tco": -999.0, "owner": "X"},
        )
        restored.add(bad_elem)
        errors = restored.validate()
        assert any("tco" in str(e) and "min" in str(e) for e in errors)

    def test_required_constraint_survives_json_round_trip(self) -> None:
        """After round-trip, validate() still catches a 'required' violation."""
        from etcion.metamodel.application import ApplicationService
        from etcion.serialization.json import model_from_dict, model_to_dict

        m = self._constrained_model()
        data = model_to_dict(m)
        restored = model_from_dict(data)

        bad_elem = ApplicationService(
            name="BadService",
            extended_attributes={"risk_score": "low", "tco": 100.0},
            # missing 'owner'
        )
        restored.add(bad_elem)
        errors = restored.validate()
        assert any("owner" in str(e) and "required" in str(e) for e in errors)

    def test_json_round_trip_passes_validate_for_valid_model(self) -> None:
        """validate() produces no errors after round-trip for a valid model."""
        from etcion.serialization.json import model_from_dict, model_to_dict

        m = self._constrained_model()
        data = model_to_dict(m)
        restored = model_from_dict(data)
        errors = restored.validate()
        assert errors == []

    def test_json_idempotency_with_constraints(self) -> None:
        """model_to_dict(model_from_dict(model_to_dict(m))) == model_to_dict(m)."""
        import json

        from etcion.serialization.json import model_from_dict, model_to_dict

        m = self._constrained_model()
        d1 = model_to_dict(m)
        restored = model_from_dict(d1)
        d2 = model_to_dict(restored)
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


# ===========================================================================
# Stage 4 — XML serialization round-trip of constraints
# ===========================================================================


class TestXmlConstraintRoundTrip:
    """Constraints survive serialize_model -> deserialize_model."""

    def _constrained_model(self) -> Model:
        from etcion.metamodel.application import ApplicationService

        profile = Profile(
            name="RiskManagement",
            attribute_extensions={
                ApplicationService: {
                    "risk_score": {"type": str, "allowed": ["low", "medium", "high", "critical"]},
                    "tco": {"type": float, "min": 0.0},
                    "owner": {"type": str, "required": True},
                }
            },
        )
        m = Model()
        m.apply_profile(profile)
        elem = ApplicationService(
            name="PaymentGateway",
            extended_attributes={"risk_score": "high", "tco": 50000.0, "owner": "FinanceTeam"},
        )
        m.add(elem)
        return m

    def test_allowed_constraint_survives_xml_round_trip(self) -> None:
        """After XML round-trip, validate() still catches an 'allowed' violation."""
        from etcion.metamodel.application import ApplicationService
        from etcion.serialization.xml import deserialize_model, serialize_model

        m = self._constrained_model()
        tree = serialize_model(m)
        restored = deserialize_model(tree)

        bad_elem = ApplicationService(
            name="BadService",
            extended_attributes={"risk_score": "extreme", "tco": 1.0, "owner": "X"},
        )
        restored.add(bad_elem)
        errors = restored.validate()
        assert any("risk_score" in str(e) and "allowed" in str(e) for e in errors)

    def test_min_constraint_survives_xml_round_trip(self) -> None:
        """After XML round-trip, validate() still catches a 'min' violation."""
        from etcion.metamodel.application import ApplicationService
        from etcion.serialization.xml import deserialize_model, serialize_model

        m = self._constrained_model()
        tree = serialize_model(m)
        restored = deserialize_model(tree)

        bad_elem = ApplicationService(
            name="BadService",
            extended_attributes={"risk_score": "low", "tco": -999.0, "owner": "X"},
        )
        restored.add(bad_elem)
        errors = restored.validate()
        assert any("tco" in str(e) and "min" in str(e) for e in errors)

    def test_required_constraint_survives_xml_round_trip(self) -> None:
        """After XML round-trip, validate() still catches a 'required' violation."""
        from etcion.metamodel.application import ApplicationService
        from etcion.serialization.xml import deserialize_model, serialize_model

        m = self._constrained_model()
        tree = serialize_model(m)
        restored = deserialize_model(tree)

        bad_elem = ApplicationService(
            name="BadService",
            extended_attributes={"risk_score": "low", "tco": 100.0},
            # missing 'owner'
        )
        restored.add(bad_elem)
        errors = restored.validate()
        assert any("owner" in str(e) and "required" in str(e) for e in errors)

    def test_xml_round_trip_passes_validate_for_valid_model(self) -> None:
        """validate() produces no errors after XML round-trip for a valid model."""
        from etcion.serialization.xml import deserialize_model, serialize_model

        m = self._constrained_model()
        tree = serialize_model(m)
        restored = deserialize_model(tree)
        errors = restored.validate()
        assert errors == []

    def test_xml_write_read_round_trip(self) -> None:
        """write_model -> read_model preserves constraints so validate() passes."""
        import tempfile
        from pathlib import Path

        from etcion.serialization.xml import read_model, write_model

        m = self._constrained_model()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "constrained.xml"
            write_model(m, path)
            restored = read_model(path)

        errors = restored.validate()
        assert errors == []
