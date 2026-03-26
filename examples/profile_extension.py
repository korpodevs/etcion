#!/usr/bin/env python3
"""Profile extension: create a profile with specializations and extended attributes.

Demonstrates Profile creation, apply_profile, and validation of profile constraints.
"""

from pyarchi import (
    ApplicationComponent,
    Model,
    Profile,
)


def main() -> None:
    # Define a cloud-focused profile
    cloud_profile = Profile(
        name="Cloud Extensions",
        specializations={
            ApplicationComponent: ["Microservice", "API Gateway", "Message Broker"],
        },
        attribute_extensions={
            ApplicationComponent: {"cloud_provider": str, "region": str},
        },
    )
    print(f"Profile: {cloud_profile.name}")
    print(f"Specializations: {cloud_profile.specializations}")

    # Build a model and apply the profile
    model = Model()
    model.apply_profile(cloud_profile)

    # Create elements with specializations and extended attributes
    order_svc = ApplicationComponent(
        name="Order Service",
        specialization="Microservice",
        extended_attributes={"cloud_provider": "AWS", "region": "eu-west-1"},
    )
    gateway = ApplicationComponent(
        name="API Gateway",
        specialization="API Gateway",
        extended_attributes={"cloud_provider": "AWS", "region": "us-east-1"},
    )

    model.add(order_svc)
    model.add(gateway)

    # Validate -- should pass
    errors = model.validate()
    print(f"\nValid model errors: {len(errors)}")

    # Now create an element with an undeclared specialization
    bad = ApplicationComponent(name="Bad Service", specialization="Lambda")
    model.add(bad)

    errors = model.validate()
    print(f"After adding undeclared specialization: {len(errors)} error(s)")
    for err in errors:
        print(f"  {err}")


if __name__ == "__main__":
    main()
