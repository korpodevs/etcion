#!/usr/bin/env python3
"""Model diff: compare two model versions and inspect changes.

Demonstrates diff_models, ModelDiff, ConceptChange, and FieldChange.
"""

from etcion import (
    ApplicationComponent,
    ApplicationService,
    Assignment,
    BusinessProcess,
    Model,
    Serving,
    diff_models,
)


def main() -> None:
    # Version 1: original model
    app = ApplicationComponent(name="CRM System")
    api = ApplicationService(name="CRM API")
    process = BusinessProcess(name="Order Handling")
    assign = Assignment(name="exposes", source=app, target=api)
    serve = Serving(name="supports", source=api, target=process)

    v1 = Model(concepts=[app, api, process, assign, serve])

    # Version 2: rename a service, add a new component
    api_v2 = ApplicationService(id=api.id, name="CRM REST API")
    new_app = ApplicationComponent(name="Billing System")

    v2 = Model(concepts=[
        app, api_v2, process, new_app,
        assign,
        Serving(name="supports", source=api_v2, target=process),
    ])

    # Compare
    diff = diff_models(v1, v2)
    print(diff.summary())

    # Inspect additions
    for concept in diff.added:
        print(f"  + {type(concept).__name__}: {getattr(concept, 'name', concept.id)}")

    # Inspect removals
    for concept in diff.removed:
        print(f"  - {type(concept).__name__}: {getattr(concept, 'name', concept.id)}")

    # Inspect modifications
    for change in diff.modified:
        print(f"  ~ {change.concept_type} ({change.concept_id}):")
        for field_name, fc in change.changes.items():
            print(f"      {field_name}: {fc.old!r} -> {fc.new!r}")

    # Serialize to dict
    print(f"\nDiff as dict keys: {list(diff.to_dict().keys())}")


if __name__ == "__main__":
    main()
