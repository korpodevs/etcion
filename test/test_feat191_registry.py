"""Tests for FEAT-19.1 -- XML namespace constants and TypeRegistry."""

from __future__ import annotations

import pytest

from pyarchi.serialization.registry import (
    ARCHIMATE_NS,
    NSMAP,
    TYPE_REGISTRY,
    XSI_NS,
    TypeDescriptor,
)


class TestNamespaceConstants:
    def test_archimate_ns_is_opengroup_uri(self):
        assert "opengroup.org" in ARCHIMATE_NS
        assert "archimate" in ARCHIMATE_NS

    def test_xsi_ns(self):
        assert XSI_NS == "http://www.w3.org/2001/XMLSchema-instance"

    def test_nsmap_default_key(self):
        assert None in NSMAP
        assert NSMAP[None] == ARCHIMATE_NS


class TestTypeDescriptor:
    def test_frozen(self):
        td = TypeDescriptor(xml_tag="Foo")
        with pytest.raises(AttributeError):
            td.xml_tag = "Bar"  # type: ignore[misc]

    def test_extra_attrs_default_empty(self):
        td = TypeDescriptor(xml_tag="Foo")
        assert td.extra_attrs == {}


class TestTypeRegistry:
    def test_registry_is_not_empty(self):
        assert len(TYPE_REGISTRY) > 0

    def test_all_element_types_registered(self):
        from pyarchi.metamodel.application import DataObject
        from pyarchi.metamodel.business import BusinessActor
        from pyarchi.metamodel.elements import Grouping
        from pyarchi.metamodel.implementation_migration import Plateau
        from pyarchi.metamodel.motivation import Goal
        from pyarchi.metamodel.physical import Equipment
        from pyarchi.metamodel.strategy import Capability
        from pyarchi.metamodel.technology import Artifact

        for cls in [
            BusinessActor,
            DataObject,
            Artifact,
            Goal,
            Capability,
            Equipment,
            Plateau,
            Grouping,
        ]:
            assert cls in TYPE_REGISTRY, f"{cls.__name__} not in registry"

    def test_all_relationship_types_registered(self):
        from pyarchi.metamodel.relationships import (
            Access,
            Composition,
            Flow,
            Influence,
            Junction,
        )

        for cls in [Composition, Access, Influence, Flow, Junction]:
            assert cls in TYPE_REGISTRY, f"{cls.__name__} not in registry"

    def test_access_has_extra_attrs(self):
        from pyarchi.metamodel.relationships import Access

        desc = TYPE_REGISTRY[Access]
        assert "accessType" in desc.extra_attrs

    def test_influence_has_modifier_and_strength(self):
        from pyarchi.metamodel.relationships import Influence

        desc = TYPE_REGISTRY[Influence]
        assert "modifier" in desc.extra_attrs
        assert "strength" in desc.extra_attrs

    def test_junction_has_type_attr(self):
        from pyarchi.metamodel.relationships import Junction

        desc = TYPE_REGISTRY[Junction]
        assert "type" in desc.extra_attrs

    def test_registry_count_at_least_57(self):
        """57 concrete types: ~52 elements + ~12 relationships/junction - overlaps."""
        assert len(TYPE_REGISTRY) >= 57

    def test_xml_tag_matches_class_name_for_simple_types(self):
        from pyarchi.metamodel.business import BusinessActor

        assert TYPE_REGISTRY[BusinessActor].xml_tag == "BusinessActor"
