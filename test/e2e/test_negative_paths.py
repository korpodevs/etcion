"""Negative path integration tests — Issue #71.

Verifies that the library fails correctly and with actionable messages when
given bad input.  Each test exercises full error propagation rather than an
isolated guard in isolation.

All tests are marked ``@pytest.mark.integration``.

Behaviour contract (derived from reading source before writing tests):

5.1  Invalid relationship — ``model.validate(strict=True)`` raises
     ValidationError.  ``model.add()`` itself does NOT check permissions;
     the relationship is accepted into the concept pool and the violation is
     detected at validate-time.

5.2  Duplicate ID — ``model.add()`` raises ``ValueError`` on the second add.

5.3  Malformed XML — ``deserialize_model()`` is lenient by design (unknown
     types emit a warning; unresolved refs emit a warning and return None).
     Missing ``identifier`` produces an element with an empty-string id, which
     then collides and raises ``ValueError`` on the second add.  Unknown
     element types are skipped (warning) and do NOT raise.  Unknown
     relationship types or unresolved refs are skipped (warning) and do NOT
     raise — ``model.validate()`` is required to surface those as errors.

5.4  Viewpoint constraint — ``view.add()`` raises ``ValidationError`` when the
     concept type is not in ``permitted_concept_types``.

5.5  Profile type mismatch — ``model.validate()`` returns/raises a
     ``ValidationError`` whose message names the expected and actual types.

5.6  Circular relationship — ``analyze_impact(remove=...)`` terminates via BFS
     (visited-set prevents re-enqueuing) and does not loop infinitely.  The
     result's ``affected`` tuple contains all three elements in the cycle.
"""

from __future__ import annotations

import warnings

import pytest

from etcion import (
    ApplicationComponent,
    ApplicationService,
    Goal,
    Model,
    Node,
    Profile,
    Serving,
    ValidationError,
    View,
    Viewpoint,
    analyze_impact,
)
from etcion.enums import ContentCategory, PurposeCategory
from etcion.metamodel.concepts import Element
from etcion.metamodel.relationships import Composition
from etcion.serialization.registry import ARCHIMATE_NS, XSI_NS
from etcion.serialization.xml import deserialize_model

try:
    from lxml import etree

    _LXML_AVAILABLE = True
except ImportError:
    _LXML_AVAILABLE = False

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NS = ARCHIMATE_NS
_XSI = XSI_NS
_XML_NS = "http://www.w3.org/XML/1998/namespace"
_NSMAP: dict[str | None, str] = {None: _NS, "xsi": _XSI}


def _parse_xml(xml_string: str) -> "etree._ElementTree":
    """Parse an inline XML bytes string into an lxml ElementTree."""
    root = etree.fromstring(xml_string.encode())
    return root.getroottree()


def _minimal_model_xml(extra_elements: str = "", extra_rels: str = "") -> str:
    """Return a minimal valid Exchange Format XML document."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<model xmlns="{_NS}"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       identifier="id-model-root">
  <name xml:lang="en">Test Model</name>
  <elements>{extra_elements}</elements>
  <relationships>{extra_rels}</relationships>
</model>"""


# ===========================================================================
# 5.1  Invalid relationship rejected at validate()
# ===========================================================================


@pytest.mark.integration
class TestInvalidRelationshipRejected:
    """5.1 — Serving from Goal to Node violates the permission table."""

    def test_invalid_relationship_accepted_by_add(self) -> None:
        """model.add() does not check permissions; the relationship is stored."""
        model = Model()
        goal = Goal(name="Reduce Costs")
        node = Node(name="App Server")
        model.add(goal)
        model.add(node)
        # Serving from a MotivationElement (Goal) to a technology element (Node)
        # is not listed in the permission table and will be rejected at
        # validate() time, but add() itself must not raise.
        rel = Serving(name="", source=goal, target=node)
        model.add(rel)  # must not raise
        assert rel in model.relationships

    def test_invalid_relationship_detected_by_validate(self) -> None:
        """validate() collects the violation as a ValidationError."""
        model = Model()
        goal = Goal(name="Reduce Costs")
        node = Node(name="App Server")
        model.add(goal)
        model.add(node)
        model.add(Serving(name="", source=goal, target=node))

        errors = model.validate()

        assert len(errors) >= 1
        assert all(isinstance(e, ValidationError) for e in errors)

    def test_invalid_relationship_strict_raises_immediately(self) -> None:
        """validate(strict=True) raises on the first violation with a message
        that identifies the relationship type and element types involved."""
        model = Model()
        goal = Goal(name="Reduce Costs")
        node = Node(name="App Server")
        model.add(goal)
        model.add(node)
        rel = Serving(name="", source=goal, target=node)
        model.add(rel)

        with pytest.raises(ValidationError, match="Serving") as exc_info:
            model.validate(strict=True)

        message = str(exc_info.value)
        # Message must name both element types so the user knows what to fix.
        assert "Goal" in message
        assert "Node" in message

    def test_error_message_names_relationship_id(self) -> None:
        """The error message includes the relationship's own ID."""
        model = Model()
        goal = Goal(name="Reduce Costs")
        node = Node(name="App Server")
        model.add(goal)
        model.add(node)
        rel = Serving(name="", source=goal, target=node)
        model.add(rel)

        errors = model.validate()

        assert any(rel.id in str(e) for e in errors), (
            f"Expected relationship id '{rel.id}' in error messages; got: {errors}"
        )


# ===========================================================================
# 5.2  Duplicate element ID
# ===========================================================================


@pytest.mark.integration
class TestDuplicateElementId:
    """5.2 — Adding two elements with the same ID."""

    def test_duplicate_id_raises_value_error(self) -> None:
        """model.add() raises ValueError immediately on a duplicate ID."""
        model = Model()
        comp = ApplicationComponent(name="First")
        model.add(comp)

        # Build a second element that steals the same ID.
        duplicate = ApplicationComponent(id=comp.id, name="Second")

        with pytest.raises(ValueError):
            model.add(duplicate)

    def test_duplicate_id_error_message_contains_id(self) -> None:
        """The ValueError message names the colliding ID."""
        model = Model()
        comp = ApplicationComponent(name="Original")
        model.add(comp)
        duplicate = ApplicationComponent(id=comp.id, name="Duplicate")

        with pytest.raises(ValueError, match=comp.id):
            model.add(duplicate)

    def test_model_unchanged_after_duplicate_rejection(self) -> None:
        """After a duplicate-ID rejection the model still contains exactly the
        original element under that ID."""
        model = Model()
        original = ApplicationComponent(name="Original")
        model.add(original)
        duplicate = ApplicationComponent(id=original.id, name="Duplicate")

        try:
            model.add(duplicate)
        except ValueError:
            pass

        assert model[original.id] is original
        assert len(model.elements) == 1


# ===========================================================================
# 5.3  Malformed XML import
# ===========================================================================


@pytest.mark.integration
@pytest.mark.skipif(not _LXML_AVAILABLE, reason="lxml not installed")
class TestMalformedXmlImport:
    """5.3 — Various malformed Exchange Format documents."""

    def test_missing_identifier_causes_empty_id_collision(self) -> None:
        """An <element> node without an 'identifier' attribute deserializes to
        an element whose id is the empty string.  If two such nodes exist in
        the document, the second add() raises ValueError because both map to
        the same empty-string id."""
        xml = _minimal_model_xml(
            extra_elements="""
              <element xsi:type="ApplicationComponent">
                <name xml:lang="en">No ID First</name>
              </element>
              <element xsi:type="ApplicationComponent">
                <name xml:lang="en">No ID Second</name>
              </element>
            """
        )
        tree = _parse_xml(xml)
        # Two elements with empty-string id => second add() must raise ValueError.
        with pytest.raises(ValueError, match="Duplicate"):
            deserialize_model(tree)

    def test_single_missing_identifier_succeeds_with_empty_id(self) -> None:
        """A single element with no identifier still deserializes (id becomes
        empty string).  No exception is raised because there is no collision."""
        xml = _minimal_model_xml(
            extra_elements="""
              <element xsi:type="ApplicationComponent">
                <name xml:lang="en">No ID</name>
              </element>
            """
        )
        tree = _parse_xml(xml)
        model = deserialize_model(tree)
        assert len(model.elements) == 1
        # The element's id is the empty string (stripped "id-" prefix of "").
        assert model.elements[0].id == ""

    def test_unknown_element_type_is_skipped_with_warning(self) -> None:
        """An element with an unrecognised xsi:type emits a warning and is
        silently dropped — no exception is raised and the model is returned."""
        xml = _minimal_model_xml(
            extra_elements="""
              <element identifier="id-abc123" xsi:type="NonExistentConcept">
                <name xml:lang="en">Ghost</name>
              </element>
            """
        )
        tree = _parse_xml(xml)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = deserialize_model(tree)

        assert len(model.elements) == 0
        warning_messages = [str(w.message) for w in caught]
        assert any("NonExistentConcept" in m for m in warning_messages), (
            f"Expected warning about unknown type; got: {warning_messages}"
        )

    def test_unknown_element_type_warning_is_actionable(self) -> None:
        """The warning for an unknown element type names the unknown type."""
        xml = _minimal_model_xml(
            extra_elements="""
              <element identifier="id-xyz" xsi:type="QuantumEntanglement">
                <name xml:lang="en">Qubit</name>
              </element>
            """
        )
        tree = _parse_xml(xml)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            deserialize_model(tree)

        messages = [str(w.message) for w in caught if issubclass(w.category, UserWarning)]
        assert any("QuantumEntanglement" in m for m in messages)

    def test_relationship_referencing_nonexistent_element_is_skipped(self) -> None:
        """A relationship whose source or target ID cannot be resolved is
        silently skipped (warning emitted) and is absent from the model."""
        xml = _minimal_model_xml(
            extra_elements="""
              <element identifier="id-real-comp" xsi:type="ApplicationComponent">
                <name xml:lang="en">Real Component</name>
              </element>
            """,
            extra_rels="""
              <relationship identifier="id-orphan-rel"
                            xsi:type="Serving"
                            source="id-real-comp"
                            target="id-does-not-exist"/>
            """,
        )
        tree = _parse_xml(xml)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = deserialize_model(tree)

        assert len(model.relationships) == 0, (
            "Orphaned relationship must be dropped, not added to the model"
        )
        warning_messages = [str(w.message) for w in caught]
        assert any("id-orphan-rel" in m or "Unresolved" in m for m in warning_messages), (
            f"Expected warning about unresolved reference; got: {warning_messages}"
        )

    def test_unknown_relationship_type_is_skipped_with_warning(self) -> None:
        """A relationship with an unknown xsi:type emits a warning and is
        excluded from the deserialized model."""
        xml = _minimal_model_xml(
            extra_elements="""
              <element identifier="id-src" xsi:type="ApplicationComponent">
                <name xml:lang="en">Source</name>
              </element>
              <element identifier="id-tgt" xsi:type="ApplicationComponent">
                <name xml:lang="en">Target</name>
              </element>
            """,
            extra_rels="""
              <relationship identifier="id-bad-rel"
                            xsi:type="MagicalDependency"
                            source="id-src"
                            target="id-tgt"/>
            """,
        )
        tree = _parse_xml(xml)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = deserialize_model(tree)

        assert len(model.relationships) == 0
        messages = [str(w.message) for w in caught]
        assert any("MagicalDependency" in m for m in messages)


# ===========================================================================
# 5.4  Viewpoint constraint violation
# ===========================================================================


@pytest.mark.integration
class TestViewpointConstraintViolation:
    """5.4 — Adding a concept to a View that doesn't permit its type."""

    def _make_app_only_viewpoint(self) -> Viewpoint:
        return Viewpoint(
            name="Application Layer Only",
            purpose=PurposeCategory.DESIGNING,
            content=ContentCategory.DETAILS,
            permitted_concept_types=frozenset({ApplicationComponent, ApplicationService}),
        )

    def test_forbidden_type_raises_validation_error(self) -> None:
        """A Goal cannot be added to a viewpoint that only permits application
        layer types — ValidationError is raised immediately."""
        model = Model()
        goal = Goal(name="Reduce TCO")
        model.add(goal)

        vp = self._make_app_only_viewpoint()
        view = View(governing_viewpoint=vp, underlying_model=model)

        with pytest.raises(ValidationError):
            view.add(goal)

    def test_error_message_names_rejected_type(self) -> None:
        """The ValidationError message must name the rejected concept type so
        the developer knows which type is not permitted."""
        model = Model()
        goal = Goal(name="Reduce TCO")
        model.add(goal)

        vp = self._make_app_only_viewpoint()
        view = View(governing_viewpoint=vp, underlying_model=model)

        with pytest.raises(ValidationError, match="Goal"):
            view.add(goal)

    def test_error_message_names_viewpoint(self) -> None:
        """The ValidationError message must name the governing viewpoint."""
        model = Model()
        goal = Goal(name="Reduce TCO")
        model.add(goal)

        vp = self._make_app_only_viewpoint()
        view = View(governing_viewpoint=vp, underlying_model=model)

        with pytest.raises(ValidationError, match="Application Layer Only"):
            view.add(goal)

    def test_permitted_type_succeeds(self) -> None:
        """Sanity check: a permitted type does not raise."""
        model = Model()
        comp = ApplicationComponent(name="Billing Service")
        model.add(comp)

        vp = self._make_app_only_viewpoint()
        view = View(governing_viewpoint=vp, underlying_model=model)

        view.add(comp)  # must not raise
        assert comp in view.concepts

    def test_concept_not_in_model_raises_validation_error(self) -> None:
        """Attempting to add a concept that is permitted by type but not present
        in the underlying model also raises ValidationError."""
        model = Model()
        comp = ApplicationComponent(name="Orphan Component")
        # Intentionally NOT added to model.

        vp = self._make_app_only_viewpoint()
        view = View(governing_viewpoint=vp, underlying_model=model)

        with pytest.raises(ValidationError, match=comp.id):
            view.add(comp)


# ===========================================================================
# 5.5  Profile type mismatch
# ===========================================================================


@pytest.mark.integration
class TestProfileTypeMismatch:
    """5.5 — Extended attribute value that violates the declared type constraint."""

    def test_type_mismatch_detected_by_validate(self) -> None:
        """A float attribute set to a string value must appear as a
        ValidationError when validate() runs."""
        # Declare a profile: ApplicationComponent has a 'tco' attribute of type float.
        profile = Profile(
            name="CostProfile",
            attribute_extensions={
                ApplicationComponent: {"tco": float},
            },
        )
        model = Model()
        model.apply_profile(profile)

        # Create an element that violates the declared type.
        comp = ApplicationComponent(
            name="Billing",
            extended_attributes={"tco": "not-a-float"},  # type mismatch
        )
        model.add(comp)

        errors = model.validate()

        assert len(errors) >= 1
        type_errors = [e for e in errors if "tco" in str(e)]
        assert type_errors, f"Expected a type-mismatch error for 'tco'; got: {errors}"

    def test_type_mismatch_error_message_is_actionable(self) -> None:
        """The error message must name the attribute, the expected type, and the
        actual type so the user has enough information to fix the problem."""
        profile = Profile(
            name="CostProfile",
            attribute_extensions={
                ApplicationComponent: {"tco": float},
            },
        )
        model = Model()
        model.apply_profile(profile)
        comp = ApplicationComponent(
            name="Billing",
            extended_attributes={"tco": "not-a-float"},
        )
        model.add(comp)

        errors = model.validate()
        tco_error = next((e for e in errors if "tco" in str(e)), None)
        assert tco_error is not None

        message = str(tco_error)
        # Must name the attribute.
        assert "tco" in message
        # Must name the expected type.
        assert "float" in message
        # Must name the actual type.
        assert "str" in message

    def test_type_mismatch_strict_raises_immediately(self) -> None:
        """validate(strict=True) raises ValidationError on the first mismatch."""
        profile = Profile(
            name="CostProfile",
            attribute_extensions={
                ApplicationComponent: {"tco": float},
            },
        )
        model = Model()
        model.apply_profile(profile)
        comp = ApplicationComponent(
            name="Billing",
            extended_attributes={"tco": "not-a-float"},
        )
        model.add(comp)

        with pytest.raises(ValidationError):
            model.validate(strict=True)

    def test_correct_type_passes_validation(self) -> None:
        """Sanity check: a correctly-typed attribute produces no errors."""
        profile = Profile(
            name="CostProfile",
            attribute_extensions={
                ApplicationComponent: {"tco": float},
            },
        )
        model = Model()
        model.apply_profile(profile)
        comp = ApplicationComponent(
            name="Billing",
            extended_attributes={"tco": 42.5},
        )
        model.add(comp)

        errors = model.validate()
        tco_errors = [e for e in errors if "tco" in str(e)]
        assert not tco_errors

    def test_undeclared_attribute_flagged_as_error(self) -> None:
        """An extended_attribute key that is not declared in any profile produces
        a ValidationError naming the undeclared attribute."""
        profile = Profile(
            name="CostProfile",
            attribute_extensions={
                ApplicationComponent: {"tco": float},
            },
        )
        model = Model()
        model.apply_profile(profile)
        # Add an attribute that was never declared in the profile.
        comp = ApplicationComponent(
            name="Billing",
            extended_attributes={"mystery_field": "unknown"},
        )
        model.add(comp)

        errors = model.validate()
        assert any("mystery_field" in str(e) for e in errors), (
            f"Expected error about undeclared 'mystery_field'; got: {errors}"
        )


# ===========================================================================
# 5.6  Circular relationship detection
# ===========================================================================


@pytest.mark.integration
class TestCircularRelationshipDetection:
    """5.6 — analyze_impact() must terminate on a cycle and report all members.

    Cycle: A --Serving--> B --Serving--> C --Serving--> A
    (Using ApplicationService elements, which legally serve each other per the
    permission table rule S3: Serving(ApplicationService, ApplicationService).)
    """

    def _build_cycle_model(
        self,
    ) -> "tuple[Model, ApplicationService, ApplicationService, ApplicationService]":
        """Construct a three-node Serving cycle and return (model, a, b, c)."""
        from etcion import ApplicationService

        model = Model()
        a = ApplicationService(name="Alpha")
        b = ApplicationService(name="Beta")
        c = ApplicationService(name="Gamma")
        model.add(a)
        model.add(b)
        model.add(c)
        model.add(Serving(name="A->B", source=a, target=b))
        model.add(Serving(name="B->C", source=b, target=c))
        model.add(Serving(name="C->A", source=c, target=a))
        return model, a, b, c

    def test_analyze_impact_terminates_on_cycle(self) -> None:
        """analyze_impact() must return (not loop forever) when the model
        contains a directed cycle."""
        model, a, _b, _c = self._build_cycle_model()

        # This must complete without hanging or raising RecursionError.
        result = analyze_impact(model, remove=a)
        # If we reach here, the function terminated correctly.
        assert result is not None

    def test_all_cycle_members_reported_as_affected(self) -> None:
        """When impact is analysed from element A in a 3-cycle, elements B and C
        must appear in the affected set (the BFS reaches both via the cycle)."""
        model, a, b, c = self._build_cycle_model()

        result = analyze_impact(model, remove=a)

        affected_ids = {ic.concept.id for ic in result.affected}
        assert b.id in affected_ids, "B must be reachable from A via the Serving edge"
        assert c.id in affected_ids, "C must be reachable from A via the cycle path"

    def test_removed_element_not_in_affected(self) -> None:
        """The element being removed is not included in its own affected set."""
        model, a, _b, _c = self._build_cycle_model()

        result = analyze_impact(model, remove=a)

        affected_ids = {ic.concept.id for ic in result.affected}
        assert a.id not in affected_ids

    def test_cycle_validate_reports_no_errors_for_legal_rels(self) -> None:
        """Sanity check: the three Serving(ApplicationService->ApplicationService)
        relationships are all permitted — validate() returns no errors."""
        model, _a, _b, _c = self._build_cycle_model()

        errors = model.validate()
        assert errors == [], f"Cycle model should be valid; got: {errors}"

    def test_deep_cycle_does_not_raise_recursion_error(self) -> None:
        """A longer cycle (10 nodes) must not cause a RecursionError."""
        from etcion import ApplicationService as AS

        model = Model()
        nodes = [AS(name=f"S{i}") for i in range(10)]
        for n in nodes:
            model.add(n)
        # Chain: 0->1->2->...->9->0
        for i in range(10):
            model.add(Serving(name=f"edge-{i}", source=nodes[i], target=nodes[(i + 1) % 10]))

        result = analyze_impact(model, remove=nodes[0])
        # All other 9 nodes should be reachable.
        affected_ids = {ic.concept.id for ic in result.affected}
        for n in nodes[1:]:
            assert n.id in affected_ids
