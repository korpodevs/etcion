# Profiles

ArchiMate Profiles customize the language by declaring specialization names and extended attributes for existing element types.

## Creating a Profile

A `Profile` declares specializations and attribute extensions keyed by element type:

```python
from pyarchi import Profile, ApplicationComponent

cloud_profile = Profile(
    name="Cloud Extensions",
    specializations={
        ApplicationComponent: ["Microservice", "API Gateway", "Message Broker"],
    },
    attribute_extensions={
        ApplicationComponent: {"cloud_provider": str, "region": str},
    },
)
```

## Applying a Profile

Register a profile with a model using `apply_profile()`:

```python
from pyarchi import Model

model = Model()
model.apply_profile(cloud_profile)
```

Applied profiles are available via `model.profiles`.

## Specializations

Once a profile is applied, elements can declare a specialization string:

```python
service = ApplicationComponent(
    name="Order Service",
    specialization="Microservice",
)
model.add(service)
```

`model.validate()` checks that the specialization name is declared in an applied profile and that the element type matches the profile's base type.

## Extended Attributes

Profiles can declare additional attributes for element types. Set them via `extended_attributes`:

```python
service = ApplicationComponent(
    name="Order Service",
    specialization="Microservice",
    extended_attributes={"cloud_provider": "AWS", "region": "eu-west-1"},
)
model.add(service)
```

Validation checks that:

- Each extended attribute name is declared in an applied profile
- Each attribute value matches the declared type

## Validation

Profile constraints are enforced by `model.validate()`:

```python
errors = model.validate()
# Possible errors:
# - "specialization 'Foo' is not declared in any profile"
# - "extended attribute 'bar' is not declared in any profile"
# - "extended attribute 'region' expected type str, got int"
```

See also: [`examples/profile_extension.py`](../examples/index.md)
