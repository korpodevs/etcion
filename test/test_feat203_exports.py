"""Tests for FEAT-20.3: Phase 3 public API exports."""

from __future__ import annotations

import pytest

import pyarchi

PHASE_3_EXPORTS = [
    "Viewpoint",
    "View",
    "Concern",
    "Profile",
    "PurposeCategory",
    "ContentCategory",
]


class TestPhase3Exports:
    @pytest.mark.parametrize("name", PHASE_3_EXPORTS)
    def test_symbol_importable_from_pyarchi(self, name: str) -> None:
        assert hasattr(pyarchi, name), f"{name} not found in pyarchi namespace"

    @pytest.mark.parametrize("name", PHASE_3_EXPORTS)
    def test_symbol_in_all(self, name: str) -> None:
        assert name in pyarchi.__all__, f"{name} not in pyarchi.__all__"

    def test_no_serialization_functions_in_all(self) -> None:
        forbidden = {
            "serialize_model",
            "deserialize_model",
            "write_model",
            "read_model",
            "model_to_dict",
            "model_from_dict",
        }
        leaked = forbidden & set(pyarchi.__all__)
        assert leaked == set(), f"Serialization functions leaked into __all__: {leaked}"
