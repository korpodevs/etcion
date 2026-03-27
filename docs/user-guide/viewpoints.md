# Viewpoints

ArchiMate viewpoints define perspectives on a model, constraining which concept types may appear.

## Viewpoint

A `Viewpoint` declares a name, purpose, content category, and a set of permitted concept types:

```python
from etcion import Viewpoint, PurposeCategory, ContentCategory
from etcion import BusinessActor, BusinessRole, Serving, Association

my_viewpoint = Viewpoint(
    name="Org Structure",
    purpose=PurposeCategory.DESIGNING,
    content=ContentCategory.COHERENCE,
    permitted_concept_types=frozenset({
        BusinessActor, BusinessRole, Serving, Association,
    }),
)
```

## View

A `View` projects a model through a viewpoint. Adding a concept enforces two gates:

1. **Type gate** -- the concept's type must be in the viewpoint's `permitted_concept_types`
2. **Membership gate** -- the concept must exist in the underlying model

```python
from etcion import View, Model, BusinessActor

model = Model(concepts=[actor, role, serving])

view = View(governing_viewpoint=my_viewpoint, underlying_model=model)
view.add(actor)   # OK if BusinessActor is permitted
view.add(role)    # OK if BusinessRole is permitted
```

Adding a concept whose type is not permitted raises `ValidationError`.

## Concern

`Concern` links stakeholders to viewpoints, forming the navigation path: Stakeholder -> Concern -> Viewpoint -> View.

```python
from etcion import Concern, Stakeholder

cto = Stakeholder(name="CTO")
concern = Concern(
    description="Application landscape overview",
    stakeholders=[cto],
    viewpoints=[my_viewpoint],
)
```

## Predefined Viewpoint Catalogue

etcion ships with 28 standard viewpoints from Appendix C of the ArchiMate 3.2 specification:

```python
from etcion import VIEWPOINT_CATALOGUE

org_vp = VIEWPOINT_CATALOGUE["Organization"]
print(org_vp.name)     # "Organization"
print(org_vp.purpose)  # PurposeCategory.DESIGNING

# List all available viewpoints
for name in VIEWPOINT_CATALOGUE:
    print(name)
```

Common predefined viewpoints include: Organization, Application Cooperation, Technology Usage, Motivation, Strategy, Layered, Implementation and Migration, and many more.

See also: [`examples/viewpoint_filter.py`](../examples/index.md)
