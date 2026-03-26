#!/usr/bin/env python3
"""Viewpoint filter: apply a predefined viewpoint to a model.

Demonstrates VIEWPOINT_CATALOGUE, View creation, and type gates.
"""

from pyarchi import (
    ApplicationComponent,
    BusinessActor,
    BusinessInterface,
    BusinessRole,
    Model,
    Serving,
    VIEWPOINT_CATALOGUE,
    View,
)


def main() -> None:
    # Build a model with business and application elements
    actor = BusinessActor(name="Customer")
    role = BusinessRole(name="Buyer")
    iface = BusinessInterface(name="Web Portal")
    app = ApplicationComponent(name="CRM System")
    serve = Serving(name="serves", source=iface, target=actor)

    model = Model(concepts=[actor, role, iface, app, serve])

    # Load the Organization viewpoint from the catalogue
    org_vp = VIEWPOINT_CATALOGUE["Organization"]
    print(f"Viewpoint: {org_vp.name}")
    print(f"Purpose:   {org_vp.purpose.value}")
    print(f"Permitted types: {len(org_vp.permitted_concept_types)}")

    # Create a view and add permitted concepts
    view = View(governing_viewpoint=org_vp, underlying_model=model)

    for concept in model:
        try:
            view.add(concept)
            print(f"  Added: {type(concept).__name__} '{getattr(concept, 'name', concept.id)}'")
        except Exception as e:
            print(f"  Rejected: {type(concept).__name__} -- {e}")

    print(f"\nView contains {len(view.concepts)} concepts")
    print(f"\nAvailable viewpoints: {len(VIEWPOINT_CATALOGUE)}")


if __name__ == "__main__":
    main()
