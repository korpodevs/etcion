#!/usr/bin/env python3
"""Quick start: build a minimal ArchiMate model and validate it.

Demonstrates creating elements, relationships, and running validation.
"""

from etcion import (
    ApplicationComponent,
    ApplicationService,
    Assignment,
    BusinessProcess,
    BusinessService,
    Model,
    Serving,
)


def main() -> None:
    # Create elements from different layers
    order_process = BusinessProcess(name="Order Handling")
    order_service = BusinessService(name="Order Service")
    crm = ApplicationComponent(name="CRM System")
    crm_api = ApplicationService(name="CRM API")

    # Create relationships (name is required on all relationships)
    biz_serve = Serving(name="enables", source=order_service, target=order_process)
    app_assign = Assignment(name="exposes", source=crm, target=crm_api)
    cross_serve = Serving(name="supports", source=crm_api, target=order_process)

    # Build the model
    model = Model(concepts=[
        order_process, order_service, crm, crm_api,
        biz_serve, app_assign, cross_serve,
    ])

    print(f"Elements:      {len(model.elements)}")
    print(f"Relationships: {len(model.relationships)}")

    # Validate against the ArchiMate 3.2 permission table
    errors = model.validate()
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print("Model is valid.")


if __name__ == "__main__":
    main()
