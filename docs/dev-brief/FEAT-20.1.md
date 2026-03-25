# Technical Brief: FEAT-20.1 -- Resolve Conformance xfails

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-032-epic020-conformance-cleanup.md` (Decisions 1, 4)
**Depends on:** FEAT-20.3 (exports must exist before xfails are removed)

## Scope

Remove the last two `xfail` markers from `test/test_conformance.py` and update the structural meta-tests in `test/test_feat012_structure.py`.

## Changes

### 1. `test/test_conformance.py` -- Remove xfail decorators

| Line range | Current | Action |
|---|---|---|
| 208-211 | `@pytest.mark.xfail(strict=False, reason="Phase 2: Viewpoint mechanism...")` on `test_viewpoint_mechanism` | Delete the 4-line decorator |
| 215-218 | `@pytest.mark.xfail(strict=False, reason="Phase 2: Language customization...")` on `test_language_customization` | Delete the 4-line decorator |

After removal, the two methods remain as plain test methods (no decorator).

### 2. `test/test_feat012_structure.py` -- Update `TestShouldFeaturesMarkers`

Current class (lines 243-258) asserts ALL methods have xfail. After this change, ZERO methods have xfail. Replace the class with a `_PROMOTED` set pattern matching `TestShallFeaturesMarkers`.

Replace `TestShouldFeaturesMarkers` (lines 243-258) with:

```python
class TestShouldFeaturesMarkers:
    """Methods in TestShouldFeatures that are still pending must carry
    @pytest.mark.xfail(strict=False).  Methods whose implementing epic is
    complete may have their xfail decorator removed; they are tracked in
    the exclusion list below."""

    _PROMOTED: set[str] = {
        "test_viewpoint_mechanism",
        "test_language_customization",
    }

    def test_pending_methods_have_xfail_decorator(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestShouldFeatures"])
        pending = [m for m in methods if m.name not in self._PROMOTED]
        missing = [m.name for m in pending if not _has_decorator(m, "xfail")]
        assert missing == [], f"Methods in TestShouldFeatures missing @pytest.mark.xfail: {missing}"

    def test_pending_xfail_decorators_have_strict_false(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestShouldFeatures"])
        pending = [m for m in methods if m.name not in self._PROMOTED]
        wrong = [m.name for m in pending if _get_xfail_strict_value(m) is not False]
        assert wrong == [], f"Methods in TestShouldFeatures where strict != False: {wrong}"

    def test_promoted_methods_have_no_xfail_decorator(self) -> None:
        tree = _parse_tree()
        classes = _get_classes(tree)
        methods = _get_methods(classes["TestShouldFeatures"])
        promoted = [m for m in methods if m.name in self._PROMOTED]
        wrong = [m.name for m in promoted if _has_decorator(m, "xfail")]
        assert wrong == [], f"Promoted methods in TestShouldFeatures still have xfail: {wrong}"
```

### 3. `test/test_feat012_structure.py` -- Update `test_functional_outcome`

| Line | Current assertion | New assertion |
|---|---|---|
| 346 | `assert "22 passed" in output` | `assert "24 passed" in output` |
| 349-351 | `assert "2 xfailed" in output` | **Delete** these 3 lines |
| 352-354 | `assert "1 skipped" in output` | Keep unchanged |

Also update the docstring on line 320 from `"15 passed, 9 xfailed, 1 skipped..."` to `"24 passed, 1 skipped -- no xfails remain."`.

The `"failed" not in output` guard (line 355-357) stays unchanged.

### Expected conformance test summary after FEAT-20.1

```
24 passed, 1 skipped
```

- 7 TestConformanceProfile + 12 TestShallFeatures + 2 TestShouldFeatures + 3 TestUndefinedTypeGuard = 24 passed
- 1 TestMayFeatures skipped

## Verification

```bash
pytest test/test_conformance.py -v           # Expect: 24 passed, 1 skipped
pytest test/test_feat012_structure.py -v      # All structural meta-tests green
```
