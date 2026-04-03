# Profiles

ArchiMate Profiles customize the language by declaring specialization names and extended attributes for existing element types.

## Creating a Profile

A `Profile` declares specializations and attribute extensions keyed by element type:

```python
from etcion import Profile, ApplicationComponent

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
from etcion import Model

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

## Declarative Constraints

Attribute extensions accept either a bare Python type (backward-compatible) or a constraint dict. The constraint dict form lets you express validation rules inline when defining the profile, without writing custom validation code.

A constraint dict must include a `"type"` key. The optional keys `"allowed"`, `"min"`, `"max"`, and `"required"` are described below.

```python
from etcion import Profile, ApplicationService

risk_profile = Profile(
    name="RiskManagement",
    attribute_extensions={
        ApplicationService: {
            # bare type — backward-compatible, no extra constraints
            "owner": str,
            # constraint dict form
            "risk_score": {"type": str, "allowed": ["low", "medium", "high", "critical"]},
            "tco": {"type": float, "min": 0.0},
            "sla_hours": {"type": int, "min": 1, "max": 720},
            "review_owner": {"type": str, "required": True},
        },
    },
)
```

### `allowed` Constraint

Restricts the attribute value to a fixed set of permitted values:

```python
from etcion import Profile, ApplicationComponent

env_profile = Profile(
    name="Environments",
    attribute_extensions={
        ApplicationComponent: {
            "environment": {
                "type": str,
                "allowed": ["dev", "staging", "prod"],
            },
        },
    },
)
```

When an element sets `environment` to a value outside that list, `model.validate()` returns an error:

```
"Element 'id-123': extended attribute 'environment' value 'uat' is not in the allowed list ['dev', 'staging', 'prod']"
```

### `min` and `max` Constraints

Enforce inclusive numeric bounds. Either bound may be omitted to create a one-sided range:

```python
from etcion import Profile, ApplicationService

sla_profile = Profile(
    name="SLA",
    attribute_extensions={
        ApplicationService: {
            "response_ms": {"type": int, "min": 0, "max": 5000},
            "replicas":    {"type": int, "min": 1},
        },
    },
)
```

Violations produce errors of the form:

```
"Element 'id-456': extended attribute 'response_ms' value 9999 is above max 5000"
"Element 'id-789': extended attribute 'replicas' value 0 is below min 1"
```

`min` must not be greater than `max`; `Profile(...)` raises `ValueError` at construction time if this invariant is broken.

### `required` Constraint

Marks an attribute as mandatory. Every element of the declared type must carry the attribute (non-`None`) or `model.validate()` reports an error:

```python
from etcion import Profile, ApplicationService

ownership_profile = Profile(
    name="Ownership",
    attribute_extensions={
        ApplicationService: {
            "owner": {"type": str, "required": True},
        },
    },
)
```

An element that omits `owner` from `extended_attributes` produces:

```
"Element 'id-101': extended attribute 'owner' is required but missing"
```

### Combined Example

All three constraint kinds can be combined on a single attribute:

```python
from etcion import Model, Profile, ApplicationService

profile = Profile(
    name="FullConstraints",
    attribute_extensions={
        ApplicationService: {
            "risk_score":  {"type": str, "required": True, "allowed": ["low", "medium", "high", "critical"]},
            "tco":         {"type": float, "min": 0.0},
            "sla_hours":   {"type": int, "min": 1, "max": 720},
        },
    },
)

model = Model()
model.apply_profile(profile)

svc = ApplicationService(
    name="Payments",
    extended_attributes={
        "risk_score": "critical",
        "tco": 12500.0,
        "sla_hours": 24,
    },
)
model.add(svc)

errors = model.validate()
assert errors == []
```

## Validation

Profile constraints are enforced by `model.validate()`:

```python
errors = model.validate()
# Possible errors:
# - "specialization 'Foo' is not declared in any profile"
# - "extended attribute 'bar' is not declared in any profile"
# - "extended attribute 'region' expected type str, got int"
# - "extended attribute 'environment' value 'uat' is not in the allowed list [...]"
# - "extended attribute 'replicas' value 0 is below min 1"
# - "extended attribute 'response_ms' value 9999 is above max 5000"
# - "extended attribute 'owner' is required but missing"
```

Pass `strict=True` to raise on the first error instead of collecting all errors:

```python
model.validate(strict=True)  # raises ValidationError on first violation
```

See also: [`examples/profile_extension.py`](../examples/index.md)
