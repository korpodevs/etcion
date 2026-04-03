# Profiles

::: etcion.metamodel.profiles

---

## Declarative Constraints Reference

### `AttributeConstraint`

`AttributeConstraint` is the normalized internal representation of a single attribute constraint. It is created automatically by `Profile` during construction — you never instantiate it directly. Use `resolve_constraint()` to convert a raw value, or call `Profile.get_constraints()` to retrieve the resolved constraints for an element type.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `attr_type` | `type` | — | Python type the attribute value must be an instance of. |
| `allowed` | `list[Any] \| None` | `None` | Permitted values. `None` means no restriction. |
| `min` | `int \| float \| None` | `None` | Inclusive lower bound (numeric attributes only). |
| `max` | `int \| float \| None` | `None` | Inclusive upper bound (numeric attributes only). |
| `required` | `bool` | `False` | When `True`, the attribute must be present and non-`None` on every element of the declared type. |

### `resolve_constraint(raw)`

```python
def resolve_constraint(raw: type | dict[str, Any]) -> AttributeConstraint: ...
```

Converts a bare Python type or a constraint dict into an `AttributeConstraint`.

**Parameters**

- `raw` — Either a plain Python type (e.g. `str`) or a `dict` with a required `"type"` key and any subset of the optional keys `"allowed"`, `"min"`, `"max"`, `"required"`.

**Returns** — An `AttributeConstraint` instance.

**Raises** `ValueError` in these cases:

| Condition | Message pattern |
|-----------|----------------|
| `raw` is neither a type nor a dict | `"attribute_extensions value must be a type or a dict, got ..."` |
| Dict is missing `"type"` | `"constraint dict is missing the required 'type' key"` |
| `"type"` value is not a Python type | `"'type' must be a Python type, got ..."` |
| Unknown keys present in the dict | `"unrecognized constraint key(s): [...]"` |
| `"allowed"` is not a `list` | `"'allowed' must be a list, got ..."` |
| `"min"` or `"max"` is not numeric | `"'min'/'max' must be a numeric value (int or float), got ..."` |
| `"required"` is not a `bool` | `"'required' must be a bool, got ..."` |
| `min > max` | `"'min' (...) must not be greater than 'max' (...)"` |

### `Profile.get_constraints(elem_type)`

```python
def get_constraints(self, elem_type: type[Element]) -> dict[str, AttributeConstraint]: ...
```

Returns the resolved `AttributeConstraint` map for `elem_type`, including constraints declared on parent types (subclass matching via `issubclass`).

**Parameters**

- `elem_type` — A concrete `Element` subclass.

**Returns** — A `dict` mapping attribute name (`str`) to `AttributeConstraint`. Returns an empty dict when no constraints are declared for `elem_type`.

### Constraint Dict Syntax Summary

```python
{
    "type":     <Python type>,         # required
    "allowed":  [value, ...],          # optional — restrict to enumerated values
    "min":      <int | float>,         # optional — inclusive lower bound
    "max":      <int | float>,         # optional — inclusive upper bound
    "required": <bool>,                # optional — default False
}
```

All keys except `"type"` are optional and independent. They may be combined freely on a single attribute:

```python
"risk_score": {"type": str, "required": True, "allowed": ["low", "medium", "high", "critical"]}
"tco":        {"type": float, "min": 0.0}
"sla_hours":  {"type": int, "min": 1, "max": 720}
```

### Validation Error Messages

`Model.validate()` (and `Model.validate(strict=True)`) produces `ValidationError` instances with the following message patterns for constraint violations:

| Constraint | Error message pattern |
|------------|----------------------|
| Attribute not declared in any profile | `"Element '{id}': extended attribute '{name}' is not declared in any profile"` |
| Type mismatch | `"Element '{id}': extended attribute '{name}' expected type {T}, got {actual}"` |
| `allowed` violation | `"Element '{id}': extended attribute '{name}' value {v!r} is not in the allowed list {list!r}"` |
| `min` violation | `"Element '{id}': extended attribute '{name}' value {v!r} is below min {min!r}"` |
| `max` violation | `"Element '{id}': extended attribute '{name}' value {v!r} is above max {max!r}"` |
| `required` violation | `"Element '{id}': extended attribute '{name}' is required but missing"` |
