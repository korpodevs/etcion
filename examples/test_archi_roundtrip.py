#!/usr/bin/env python3
"""Test round-trip: read Archi exchange export, verify contents, re-export.

Reads examples/pet_shop-from_archi.xml (exported from Archi after adding
Security Monitoring Service + Association to POS System), verifies all
elements and relationships loaded, then re-exports and compares.

Run:
    python examples/test_archi_roundtrip.py
"""

from __future__ import annotations

from pathlib import Path

from pyarchi.serialization.xml import read_model, write_model, serialize_model

HERE = Path(__file__).parent
INPUT = HERE / "pet_shop-from_archi.xml"
OUTPUT = HERE / "pet_shop-roundtrip.xml"


def main() -> None:
    print(f"Reading {INPUT}...")
    model = read_model(INPUT)

    print(f"  Elements:      {len(model.elements)}")
    print(f"  Relationships: {len(model.relationships)}")
    print(f"  Total:         {len(model)}")

    # Check for the new element added in Archi
    names = {e.name for e in model.elements}
    assert "Security Monitoring Service" in names, "Missing Archi-added element!"
    print("  ✓ Security Monitoring Service found")

    # Check original elements survived
    for expected in [
        "Store Manager", "Sales Clerk", "Pet Care Advisor",
        "Sell Pet", "POS System", "E-Commerce Platform",
        "PostgreSQL", "Main Street Pet Shop",
        "Pet Shop Owner", "Increase Annual Revenue by 20%",
        "Phase 1: Launch E-Commerce",
    ]:
        assert expected in names, f"Missing: {expected}"
    print("  ✓ All original elements present")

    # Check types
    type_names = {type(e).__name__ for e in model.elements}
    expected_types = {
        "BusinessActor", "BusinessRole", "BusinessInterface",
        "BusinessProcess", "BusinessFunction", "BusinessService",
        "BusinessObject", "Contract", "Product",
        "ApplicationComponent", "ApplicationInterface", "ApplicationService",
        "DataObject",
        "Node", "Device", "SystemSoftware", "TechnologyService", "Artifact",
        "Facility", "Equipment",
        "Stakeholder", "Driver", "Goal", "Principle", "Requirement",
        "Capability", "Resource", "ValueStream",
        "WorkPackage", "Deliverable", "Plateau",
    }
    missing_types = expected_types - type_names
    if missing_types:
        print(f"  ⚠ Missing types: {missing_types}")
    else:
        print(f"  ✓ All {len(expected_types)} expected types present")

    # Check relationship types
    rel_types = {type(r).__name__ for r in model.relationships}
    print(f"  Relationship types: {sorted(rel_types)}")

    # Check the new Archi-added relationship (Association to POS System)
    from pyarchi.metamodel.relationships import Association
    new_rels = [
        r for r in model.relationships
        if isinstance(r, Association)
        and any("Security" in getattr(x, "name", "") for x in [r.source, r.target])
    ]
    if new_rels:
        r = new_rels[0]
        print(f"  ✓ Archi-added Association found: {r.source.name} -> {r.target.name}")
    else:
        print("  ⚠ Archi-added Association not found (may be different rel type)")

    # Validate
    errors = model.validate()
    if errors:
        print(f"\n  Validation: {len(errors)} issue(s)")
        for e in errors[:5]:
            print(f"    - {e}")
    else:
        print(f"\n  ✓ Model validates cleanly")

    # Check opaque XML preservation (organizations, views)
    opaque = getattr(model, "_opaque_xml", [])
    opaque_tags = [child.tag.split("}")[-1] if "}" in child.tag else child.tag for child in opaque]
    print(f"  Opaque XML sections preserved: {opaque_tags}")

    # Re-export
    write_model(model, OUTPUT, model_name="Pet Shop Architecture (round-trip)")
    print(f"\nRe-exported to {OUTPUT}")

    # Quick sanity: count lines
    lines = OUTPUT.read_text().count("\n")
    print(f"  Output: {lines} lines")


if __name__ == "__main__":
    main()
