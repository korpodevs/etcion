# Querying

::: etcion.metamodel.model

---

## elements_where()

```python
Model.elements_where(predicate: Callable[[Element], bool]) -> list[Element]
```

Return every `Element` for which *predicate* returns `True`, in insertion
order.  This is the open-ended complement to the type-, layer-, aspect-, and
name-based query methods.

**Parameters**

| Name | Type | Description |
|---|---|---|
| `predicate` | `Callable[[Element], bool]` | Called once per element. Return `True` to include the element in the result. |

**Returns** `list[Element]` — may be empty.

**Example**

```python
# Elements whose fitness_score extended attribute is below the threshold
low_quality = model.elements_where(
    lambda e: e.extended_attributes.get("fitness_score", 5) < 3.0
)

# Elements that carry a specific tag
tagged = model.elements_where(
    lambda e: e.extended_attributes.get("tag") == "review-required"
)
```

See the [querying user guide](../user-guide/querying.md#filter-by-predicate)
for a full walkthrough of common predicates and performance guidance.
