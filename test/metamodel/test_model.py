"""Merged tests for test_model."""

from __future__ import annotations

import pytest

import etcion
from etcion.enums import Aspect, Layer, RelationshipCategory
from etcion.exceptions import ValidationError
from etcion.metamodel.application import (
    ApplicationComponent,
    ApplicationService,
)
from etcion.metamodel.business import (
    BusinessActor,
    BusinessFunction,
    BusinessObject,
    BusinessProcess,
    BusinessRole,
    BusinessService,
    Product,
)
from etcion.metamodel.concepts import (
    Concept,
    Element,
    Relationship,
    RelationshipConnector,
)
from etcion.metamodel.model import Model
from etcion.metamodel.relationships import (
    Assignment,
    Serving,
    Specialization,
    StructuralRelationship,
)


class ConcreteElement(Element):
    @property
    def _type_name(self) -> str:
        return "ConcreteElement"


class ConcreteRelationship(Relationship):
    category = RelationshipCategory.OTHER

    @property
    def _type_name(self) -> str:
        return "ConcreteRelationship"


class ConcreteConnector(RelationshipConnector):
    @property
    def _type_name(self) -> str:
        return "ConcreteConnector"


class TestModelInit:
    def test_empty_model(self) -> None:
        """Model() creates an empty container."""
        model = Model()
        assert len(model) == 0

    def test_model_with_concepts_list(self) -> None:
        """Model(concepts=[...]) adds all concepts."""
        e1 = ConcreteElement(name="A")
        e2 = ConcreteElement(name="B")
        model = Model(concepts=[e1, e2])
        assert len(model) == 2

    def test_model_with_none(self) -> None:
        """Model(concepts=None) creates an empty container."""
        model = Model(concepts=None)
        assert len(model) == 0


class TestModelAdd:
    def test_add_element(self) -> None:
        """model.add(element) stores the element."""
        model = Model()
        e = ConcreteElement(name="X")
        model.add(e)
        assert len(model) == 1

    def test_add_relationship(self) -> None:
        """model.add(relationship) stores the relationship."""
        model = Model()
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        model.add(rel)
        assert len(model) == 1

    def test_add_connector(self) -> None:
        """model.add(connector) stores the connector."""
        model = Model()
        c = ConcreteConnector()
        model.add(c)
        assert len(model) == 1

    def test_add_non_concept_raises_type_error(self) -> None:
        """model.add('not a concept') raises TypeError."""
        model = Model()
        with pytest.raises(TypeError):
            model.add("not a concept")  # type: ignore[arg-type]

    def test_add_dict_raises_type_error(self) -> None:
        """model.add({}) raises TypeError."""
        model = Model()
        with pytest.raises(TypeError):
            model.add({})  # type: ignore[arg-type]

    def test_add_duplicate_id_raises_value_error(self) -> None:
        """Adding two concepts with the same ID raises ValueError."""
        model = Model()
        e = ConcreteElement(name="X", id="same-id")
        e2 = ConcreteElement(name="Y", id="same-id")
        model.add(e)
        with pytest.raises(ValueError):
            model.add(e2)

    def test_type_error_message_contains_type_name(self) -> None:
        """TypeError message includes the actual type name."""
        model = Model()
        with pytest.raises(TypeError, match="dict"):
            model.add({})  # type: ignore[arg-type]

    def test_value_error_message_contains_id(self) -> None:
        """ValueError message includes the duplicate ID."""
        model = Model()
        e = ConcreteElement(name="X", id="dup-id")
        e2 = ConcreteElement(name="Y", id="dup-id")
        model.add(e)
        with pytest.raises(ValueError, match="dup-id"):
            model.add(e2)


class TestModelIter:
    def test_iter_empty(self) -> None:
        """list(Model()) == []."""
        assert list(Model()) == []

    def test_iter_returns_insertion_order(self) -> None:
        """Iteration yields concepts in insertion order."""
        model = Model()
        e1 = ConcreteElement(name="A")
        e2 = ConcreteElement(name="B")
        e3 = ConcreteElement(name="C")
        model.add(e1)
        model.add(e2)
        model.add(e3)
        assert list(model) == [e1, e2, e3]

    def test_for_loop(self) -> None:
        """for concept in model: works."""
        model = Model()
        e = ConcreteElement(name="X")
        model.add(e)
        seen = []
        for concept in model:
            seen.append(concept)
        assert seen == [e]


class TestModelGetitem:
    def test_getitem_by_id(self) -> None:
        """model[id] returns the correct concept."""
        model = Model()
        e = ConcreteElement(name="X", id="my-id")
        model.add(e)
        assert model["my-id"] is e

    def test_getitem_missing_raises_key_error(self) -> None:
        """model['nonexistent'] raises KeyError."""
        model = Model()
        with pytest.raises(KeyError):
            _ = model["nonexistent"]

    def test_getitem_identity(self) -> None:
        """model[concept.id] is concept (same object)."""
        model = Model()
        e = ConcreteElement(name="X")
        model.add(e)
        assert model[e.id] is e


class TestModelLen:
    def test_len_empty(self) -> None:
        """len(Model()) == 0."""
        assert len(Model()) == 0

    def test_len_after_adds(self) -> None:
        """len(model) reflects number of added concepts."""
        model = Model()
        model.add(ConcreteElement(name="A"))
        model.add(ConcreteElement(name="B"))
        assert len(model) == 2


class TestModelProperties:
    def test_concepts_returns_all(self) -> None:
        """model.concepts returns all concepts as a list."""
        model = Model()
        e = ConcreteElement(name="X")
        c = ConcreteConnector()
        model.add(e)
        model.add(c)
        concepts = model.concepts
        assert len(concepts) == 2
        assert e in concepts
        assert c in concepts

    def test_elements_filters_elements_only(self) -> None:
        """model.elements returns only Element instances."""
        model = Model()
        e = ConcreteElement(name="X")
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        model.add(e)
        model.add(rel)
        assert model.elements == [e]

    def test_relationships_filters_relationships_only(self) -> None:
        """model.relationships returns only Relationship instances."""
        model = Model()
        e = ConcreteElement(name="X")
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        model.add(e)
        model.add(rel)
        assert model.relationships == [rel]

    def test_elements_excludes_relationships(self) -> None:
        """model.elements does not include Relationship instances."""
        model = Model()
        src = ConcreteElement(name="src")
        tgt = ConcreteElement(name="tgt")
        rel = ConcreteRelationship(name="R", source=src, target=tgt)
        model.add(rel)
        assert model.elements == []

    def test_relationships_excludes_connectors(self) -> None:
        """model.relationships does not include RelationshipConnector instances."""
        model = Model()
        model.add(ConcreteConnector())
        assert model.relationships == []

    def test_elements_excludes_connectors(self) -> None:
        """model.elements does not include RelationshipConnector instances."""
        model = Model()
        model.add(ConcreteConnector())
        assert model.elements == []

    def test_properties_preserve_insertion_order(self) -> None:
        """elements and relationships maintain insertion order."""
        model = Model()
        e1 = ConcreteElement(name="A")
        e2 = ConcreteElement(name="B")
        model.add(e1)
        model.add(e2)
        assert model.elements == [e1, e2]


class TestModelExports:
    def test_model_in_etcion_all(self) -> None:
        """'Model' is in etcion.__all__."""
        assert "Model" in etcion.__all__

    def test_concept_in_etcion_all(self) -> None:
        """'Concept' is in etcion.__all__."""
        assert "Concept" in etcion.__all__

    def test_element_in_etcion_all(self) -> None:
        """'Element' is in etcion.__all__."""
        assert "Element" in etcion.__all__

    def test_relationship_in_etcion_all(self) -> None:
        """'Relationship' is in etcion.__all__."""
        assert "Relationship" in etcion.__all__

    def test_relationship_connector_in_etcion_all(self) -> None:
        """'RelationshipConnector' is in etcion.__all__."""
        assert "RelationshipConnector" in etcion.__all__

    def test_import_from_etcion(self) -> None:
        """from etcion import Model, Concept, Element, Relationship, RelationshipConnector."""
        from etcion import (  # noqa: PLC0415
            Concept,
            Element,
            Model,
            Relationship,
            RelationshipConnector,
        )

        assert all([Concept, Element, Relationship, RelationshipConnector, Model])


class TestModelValidateBasic:
    def test_empty_model_returns_empty(self) -> None:
        model = Model()
        assert model.validate() == []

    def test_valid_model_returns_empty(self) -> None:
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        rel = Specialization(name="s", source=a1, target=a2)
        model = Model(concepts=[a1, a2, rel])
        assert model.validate() == []

    def test_invalid_relationship_returns_error(self) -> None:
        ba = BusinessActor(name="actor")
        bp = BusinessProcess(name="proc")
        rel = Specialization(name="bad", source=ba, target=bp)  # cross-type
        model = Model(concepts=[ba, bp, rel])
        errors = model.validate()
        assert len(errors) == 1
        assert isinstance(errors[0], ValidationError)

    def test_multiple_errors_collected(self) -> None:
        ba = BusinessActor(name="actor")
        bp = BusinessProcess(name="proc")
        br = BusinessRole(name="role")
        r1 = Specialization(name="r1", source=ba, target=bp)
        r2 = Specialization(name="r2", source=bp, target=br)
        model = Model(concepts=[ba, bp, br, r1, r2])
        errors = model.validate()
        assert len(errors) == 2


class TestModelValidateStrict:
    def test_strict_raises_on_first(self) -> None:
        ba = BusinessActor(name="actor")
        bp = BusinessProcess(name="proc")
        br = BusinessRole(name="role")
        r1 = Specialization(name="r1", source=ba, target=bp)
        r2 = Specialization(name="r2", source=bp, target=br)
        model = Model(concepts=[ba, bp, br, r1, r2])
        with pytest.raises(ValidationError):
            model.validate(strict=True)

    def test_strict_no_error_returns_empty(self) -> None:
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        rel = Specialization(name="s", source=a1, target=a2)
        model = Model(concepts=[a1, a2, rel])
        assert model.validate(strict=True) == []


class TestModelValidateErrorMessage:
    def test_error_contains_relationship_info(self) -> None:
        ba = BusinessActor(name="actor")
        bp = BusinessProcess(name="proc")
        rel = Specialization(name="bad", source=ba, target=bp)
        model = Model(concepts=[ba, bp, rel])
        errors = model.validate()
        msg = str(errors[0])
        assert "Specialization" in msg
        assert "BusinessActor" in msg
        assert "BusinessProcess" in msg


@pytest.fixture
def model() -> Model:
    m = Model()
    m.add(BusinessActor(name="Alice"))
    m.add(BusinessActor(name="Bob"))
    m.add(BusinessRole(name="Manager"))
    m.add(BusinessFunction(name="Hiring"))
    m.add(BusinessObject(name="Contract Doc"))
    m.add(BusinessService(name="HR Service"))
    m.add(ApplicationComponent(name="CRM System"))
    m.add(ApplicationService(name="CRM API"))
    m.add(Product(name="Enterprise Suite"))
    return m


# -- elements_of_type ---------------------------------------------------------


class TestElementsOfType:
    def test_exact_type(self, model: Model) -> None:
        result = model.elements_of_type(BusinessActor)
        assert len(result) == 2
        assert all(isinstance(e, BusinessActor) for e in result)

    def test_subclass_included(self, model: Model) -> None:
        """BusinessObject is parent of Contract; but here we just check
        that isinstance-based matching works with the hierarchy."""
        from etcion.metamodel.concepts import Element

        result = model.elements_of_type(Element)
        assert len(result) == len(model.elements)

    def test_no_matches(self, model: Model) -> None:
        from etcion.metamodel.technology import Node

        assert model.elements_of_type(Node) == []

    def test_returns_list(self, model: Model) -> None:
        result = model.elements_of_type(BusinessActor)
        assert isinstance(result, list)


# -- elements_by_layer --------------------------------------------------------


class TestElementsByLayer:
    def test_business_layer(self, model: Model) -> None:
        result = model.elements_by_layer(Layer.BUSINESS)
        names = {e.name for e in result}
        assert "Alice" in names
        assert "Manager" in names
        assert "Enterprise Suite" in names  # Product is Business layer
        assert "CRM System" not in names

    def test_application_layer(self, model: Model) -> None:
        result = model.elements_by_layer(Layer.APPLICATION)
        names = {e.name for e in result}
        assert names == {"CRM System", "CRM API"}

    def test_empty_layer(self, model: Model) -> None:
        assert model.elements_by_layer(Layer.TECHNOLOGY) == []


# -- elements_by_aspect -------------------------------------------------------


class TestElementsByAspect:
    def test_active_structure(self, model: Model) -> None:
        result = model.elements_by_aspect(Aspect.ACTIVE_STRUCTURE)
        names = {e.name for e in result}
        assert "Alice" in names
        assert "Manager" in names
        assert "CRM System" in names

    def test_behavior(self, model: Model) -> None:
        result = model.elements_by_aspect(Aspect.BEHAVIOR)
        names = {e.name for e in result}
        assert "Hiring" in names
        assert "HR Service" in names
        assert "CRM API" in names

    def test_passive_structure(self, model: Model) -> None:
        result = model.elements_by_aspect(Aspect.PASSIVE_STRUCTURE)
        assert len(result) == 1
        assert result[0].name == "Contract Doc"

    def test_composite(self, model: Model) -> None:
        result = model.elements_by_aspect(Aspect.COMPOSITE)
        assert len(result) == 1
        assert result[0].name == "Enterprise Suite"


# -- elements_by_name ---------------------------------------------------------


class TestElementsByName:
    def test_substring_match(self, model: Model) -> None:
        result = model.elements_by_name("CRM")
        assert len(result) == 2

    def test_substring_no_match(self, model: Model) -> None:
        assert model.elements_by_name("zzz_nonexistent") == []

    def test_substring_case_sensitive(self, model: Model) -> None:
        result = model.elements_by_name("crm")
        assert result == []

    def test_regex_mode(self, model: Model) -> None:
        result = model.elements_by_name(r"^Business", regex=True)
        assert result == []  # names are "Alice", "Bob", etc., not "BusinessActor"

    def test_regex_case_insensitive(self, model: Model) -> None:
        result = model.elements_by_name(r"(?i)crm", regex=True)
        assert len(result) == 2

    def test_regex_pattern(self, model: Model) -> None:
        result = model.elements_by_name(r"Al(ice|ex)", regex=True)
        assert len(result) == 1
        assert result[0].name == "Alice"

    def test_elements_with_none_name_skipped(self) -> None:
        m = Model()
        m.add(BusinessActor(name="Alice"))
        m.add(BusinessActor(name=""))  # name is empty string (falsy), skipped by filter
        result = m.elements_by_name("Alice")
        assert len(result) == 1


# -- composition (replaces chained QueryBuilder tests) ------------------------


class TestComposition:
    def test_layer_then_name(self, model: Model) -> None:
        """Compose elements_by_layer + list comprehension for name filter."""
        biz = model.elements_by_layer(Layer.BUSINESS)
        result = [e for e in biz if e.name and "Service" in e.name]
        assert len(result) == 1
        assert result[0].name == "HR Service"

    def test_type_then_aspect(self, model: Model) -> None:
        from etcion.metamodel.concepts import Element

        active = model.elements_by_aspect(Aspect.ACTIVE_STRUCTURE)
        biz_active = [e for e in active if getattr(type(e), "layer", None) is Layer.BUSINESS]
        names = {e.name for e in biz_active}
        assert "Alice" in names
        assert "CRM System" not in names


@pytest.fixture
def populated_model() -> Model:
    """Build a small model:

    actor --Assignment--> role
    role  --Assignment--> service
    component --Serving--> app_service
    component --Serving--> service
    """
    actor = BusinessActor(name="Alice")
    role = BusinessRole(name="Manager")
    service = BusinessService(name="HR Service")
    component = ApplicationComponent(name="CRM")
    app_service = ApplicationService(name="CRM API")

    a1 = Assignment(source=actor, target=role, name="a1")
    a2 = Assignment(source=role, target=service, name="a2")
    s1 = Serving(source=component, target=app_service, name="s1")
    s2 = Serving(source=component, target=service, name="s2")

    m = Model()
    for c in [actor, role, service, component, app_service, a1, a2, s1, s2]:
        m.add(c)
    return m


def _by_name(model: Model, name: str):
    """Helper to find an element by name."""
    return next(e for e in model.elements if e.name == name)


# -- connected_to -------------------------------------------------------------


class TestConnectedTo:
    def test_returns_relationships_for_source(self, populated_model: Model) -> None:
        component = _by_name(populated_model, "CRM")
        result = populated_model.connected_to(component)
        assert len(result) == 2
        assert all(isinstance(r, Serving) for r in result)

    def test_returns_relationships_for_target(self, populated_model: Model) -> None:
        role = _by_name(populated_model, "Manager")
        result = populated_model.connected_to(role)
        # role is target of a1, source of a2
        assert len(result) == 2

    def test_returns_relationships_for_both_directions(self, populated_model: Model) -> None:
        service = _by_name(populated_model, "HR Service")
        result = populated_model.connected_to(service)
        # service is target of a2 and s2
        assert len(result) == 2

    def test_isolated_element(self) -> None:
        m = Model()
        actor = BusinessActor(name="Lonely")
        m.add(actor)
        assert m.connected_to(actor) == []

    def test_identity_not_equality(self, populated_model: Model) -> None:
        """A different object with the same name should not match."""
        impostor = BusinessActor(name="Alice")
        assert populated_model.connected_to(impostor) == []

    def test_returns_list(self, populated_model: Model) -> None:
        actor = _by_name(populated_model, "Alice")
        assert isinstance(populated_model.connected_to(actor), list)


# -- sources_of ---------------------------------------------------------------


class TestSourcesOf:
    def test_single_source(self, populated_model: Model) -> None:
        role = _by_name(populated_model, "Manager")
        result = populated_model.sources_of(role)
        assert len(result) == 1
        assert result[0].name == "Alice"

    def test_multiple_sources(self, populated_model: Model) -> None:
        service = _by_name(populated_model, "HR Service")
        result = populated_model.sources_of(service)
        names = {c.name for c in result}
        assert names == {"Manager", "CRM"}

    def test_no_sources(self, populated_model: Model) -> None:
        actor = _by_name(populated_model, "Alice")
        assert populated_model.sources_of(actor) == []

    def test_returns_concepts_not_relationships(self, populated_model: Model) -> None:
        role = _by_name(populated_model, "Manager")
        result = populated_model.sources_of(role)
        from etcion.metamodel.concepts import Concept, Relationship

        assert all(isinstance(c, Concept) for c in result)
        assert not any(isinstance(c, Relationship) for c in result)


# -- targets_of ---------------------------------------------------------------


class TestTargetsOf:
    def test_single_target(self, populated_model: Model) -> None:
        actor = _by_name(populated_model, "Alice")
        result = populated_model.targets_of(actor)
        assert len(result) == 1
        assert result[0].name == "Manager"

    def test_multiple_targets(self, populated_model: Model) -> None:
        component = _by_name(populated_model, "CRM")
        result = populated_model.targets_of(component)
        names = {c.name for c in result}
        assert names == {"CRM API", "HR Service"}

    def test_no_targets(self, populated_model: Model) -> None:
        api = _by_name(populated_model, "CRM API")
        assert populated_model.targets_of(api) == []

    def test_composition_with_of_type(self, populated_model: Model) -> None:
        """STORY-23.2.5 equivalent: targets_of(actor) filtered by type."""
        actor = _by_name(populated_model, "Alice")
        targets = populated_model.targets_of(actor)
        roles = [t for t in targets if isinstance(t, BusinessRole)]
        assert len(roles) == 1
        assert roles[0].name == "Manager"


# -- empty model edge case ----------------------------------------------------


class TestEmptyModel:
    def test_connected_to_empty(self) -> None:
        m = Model()
        actor = BusinessActor(name="Ghost")
        assert m.connected_to(actor) == []

    def test_sources_of_empty(self) -> None:
        m = Model()
        actor = BusinessActor(name="Ghost")
        assert m.sources_of(actor) == []

    def test_targets_of_empty(self) -> None:
        m = Model()
        actor = BusinessActor(name="Ghost")
        assert m.targets_of(actor) == []


@pytest.fixture
def full_model() -> Model:
    """A model with mixed elements and relationships.

    Elements:
        actor, role, biz_service, biz_obj (Business layer)
        component, app_service (Application layer)

    Relationships:
        actor --Assignment--> role
        role  --Assignment--> biz_service
        component --Serving--> app_service
        component --Serving--> biz_service
    """
    actor = BusinessActor(name="Alice")
    role = BusinessRole(name="Manager")
    biz_service = BusinessService(name="HR Service")
    biz_obj = BusinessObject(name="Policy Doc")
    component = ApplicationComponent(name="CRM")
    app_service = ApplicationService(name="CRM API")

    a1 = Assignment(source=actor, target=role, name="assign-1")
    a2 = Assignment(source=role, target=biz_service, name="assign-2")
    s1 = Serving(source=component, target=app_service, name="serve-1")
    s2 = Serving(source=component, target=biz_service, name="serve-2")

    m = Model()
    for c in [actor, role, biz_service, biz_obj, component, app_service, a1, a2, s1, s2]:
        m.add(c)
    return m


def _elem(model: Model, name: str):
    return next(e for e in model.elements if e.name == name)


# -- relationships_of_type ----------------------------------------------------


class TestRelationshipsOfType:
    def test_serving_only(self, full_model: Model) -> None:
        result = full_model.relationships_of_type(Serving)
        assert len(result) == 2
        assert all(isinstance(r, Serving) for r in result)

    def test_assignment_only(self, full_model: Model) -> None:
        result = full_model.relationships_of_type(Assignment)
        assert len(result) == 2

    def test_superclass_includes_subclasses(self, full_model: Model) -> None:
        result = full_model.relationships_of_type(StructuralRelationship)
        # Assignment is a StructuralRelationship
        assert len(result) == 2
        assert all(isinstance(r, Assignment) for r in result)

    def test_base_relationship_returns_all(self, full_model: Model) -> None:
        result = full_model.relationships_of_type(Relationship)
        assert len(result) == 4

    def test_no_matches(self, full_model: Model) -> None:
        from etcion.metamodel.relationships import Composition

        assert full_model.relationships_of_type(Composition) == []

    def test_returns_list(self, full_model: Model) -> None:
        assert isinstance(full_model.relationships_of_type(Serving), list)


# -- rejected story compositions (STORY-23.3.2, 23.3.3) -----------------------


class TestCompositionPatterns:
    def test_filter_by_category(self, full_model: Model) -> None:
        """STORY-23.3.2 equivalent via comprehension."""
        structural = [
            r for r in full_model.relationships if r.category == RelationshipCategory.STRUCTURAL
        ]
        assert len(structural) == 2  # both Assignments

    def test_between_types(self, full_model: Model) -> None:
        """STORY-23.3.3 equivalent: Serving rels from AppComponent to AppService."""
        result = [
            r
            for r in full_model.relationships_of_type(Serving)
            if isinstance(r.source, ApplicationComponent)
            and isinstance(r.target, ApplicationService)
        ]
        assert len(result) == 1
        assert result[0].name == "serve-1"


# -- EPIC-023 integration tests -----------------------------------------------


class TestIntegration:
    """End-to-end tests composing multiple EPIC-023 methods."""

    def test_find_actors_serving_a_service(self, full_model: Model) -> None:
        """Who ultimately serves HR Service?  Traverse sources_of."""
        service = _elem(full_model, "HR Service")
        sources = full_model.sources_of(service)
        names = {c.name for c in sources}
        # role (via Assignment) and component (via Serving)
        assert names == {"Manager", "CRM"}

    def test_elements_of_type_then_targets(self, full_model: Model) -> None:
        """For each BusinessActor, find their targets."""
        actors = full_model.elements_of_type(BusinessActor)
        assert len(actors) == 1
        targets = full_model.targets_of(actors[0])
        assert len(targets) == 1
        assert targets[0].name == "Manager"

    def test_layer_filter_plus_connected(self, full_model: Model) -> None:
        """Find all Application-layer elements and their relationships.

        Application-layer elements: component (CRM) and app_service (CRM API).
        connected_to(component)    -> [s1, s2]
        connected_to(app_service)  -> [s1]
        all_rels before dedup      -> [s1, s2, s1]
        After dedup by object identity: {s1, s2} -> 2 unique relationships.
        """
        app_elems = full_model.elements_by_layer(Layer.APPLICATION)
        all_rels = []
        for elem in app_elems:
            all_rels.extend(full_model.connected_to(elem))
        # Deduplicate by object identity (s1 appears twice but is the same object)
        unique_rels = list({id(r): r for r in all_rels}.values())
        assert len(unique_rels) == 2  # s1 and s2

    def test_name_search_then_traverse(self, full_model: Model) -> None:
        """Find elements by name, then traverse."""
        crm_elems = full_model.elements_by_name("CRM")
        assert len(crm_elems) == 2  # CRM and CRM API
        component = next(e for e in crm_elems if e.name == "CRM")
        targets = full_model.targets_of(component)
        assert len(targets) == 2

    def test_aspect_filter(self, full_model: Model) -> None:
        """Passive structure elements in business layer."""
        passive = full_model.elements_by_aspect(Aspect.PASSIVE_STRUCTURE)
        biz_passive = [e for e in passive if getattr(type(e), "layer", None) is Layer.BUSINESS]
        assert len(biz_passive) == 1
        assert biz_passive[0].name == "Policy Doc"

    def test_all_eight_methods_exist(self, full_model: Model) -> None:
        """Smoke test: all 8 ADR-036 methods are callable."""
        assert callable(full_model.elements_of_type)
        assert callable(full_model.elements_by_layer)
        assert callable(full_model.elements_by_aspect)
        assert callable(full_model.elements_by_name)
        assert callable(full_model.relationships_of_type)
        assert callable(full_model.connected_to)
        assert callable(full_model.sources_of)
        assert callable(full_model.targets_of)
