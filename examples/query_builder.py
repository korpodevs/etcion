#!/usr/bin/env python3
"""Query builder: filter elements by type, layer, and name; traverse relationships.

Demonstrates Model query methods (no QueryBuilder class -- methods are on Model directly).
"""

from pyarchi import (
    ApplicationComponent,
    ApplicationService,
    Assignment,
    BusinessActor,
    BusinessProcess,
    BusinessService,
    Layer,
    Model,
    Serving,
)


def main() -> None:
    # Build a model
    actor = BusinessActor(name="Customer")
    manager = BusinessActor(name="Account Manager")
    process = BusinessProcess(name="Order Handling")
    biz_svc = BusinessService(name="Order Service")
    app = ApplicationComponent(name="CRM System")
    api = ApplicationService(name="CRM API")

    serve = Serving(name="supports", source=api, target=process)
    assign = Assignment(name="exposes", source=app, target=api)

    model = Model(concepts=[actor, manager, process, biz_svc, app, api, serve, assign])

    # Filter by type
    actors = model.elements_of_type(BusinessActor)
    print(f"BusinessActors: {[a.name for a in actors]}")

    # Filter by layer
    biz = model.elements_by_layer(Layer.BUSINESS)
    print(f"Business layer: {[e.name for e in biz]}")

    # Filter by name (substring)
    orders = model.elements_by_name("Order")
    print(f"Name contains 'Order': {[e.name for e in orders]}")

    # Relationship traversal
    targets = model.targets_of(app)
    print(f"Targets of '{app.name}': {[t.name for t in targets]}")

    sources = model.sources_of(process)
    print(f"Sources of '{process.name}': {[s.name for s in sources]}")

    connected = model.connected_to(api)
    print(f"Relationships involving '{api.name}': {len(connected)}")


if __name__ == "__main__":
    main()
