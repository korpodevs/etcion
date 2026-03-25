from __future__ import annotations

from pyarchi.enums import ContentCategory, PurposeCategory


class TestPurposeCategory:
    def test_member_count(self) -> None:
        assert len(PurposeCategory) == 3

    def test_members_exist(self) -> None:
        assert PurposeCategory.DESIGNING.value == "Designing"
        assert PurposeCategory.DECIDING.value == "Deciding"
        assert PurposeCategory.INFORMING.value == "Informing"

    def test_is_enum_not_str(self) -> None:
        assert not isinstance(PurposeCategory.DESIGNING, str)


class TestContentCategory:
    def test_member_count(self) -> None:
        assert len(ContentCategory) == 3

    def test_members_exist(self) -> None:
        assert ContentCategory.DETAILS.value == "Details"
        assert ContentCategory.COHERENCE.value == "Coherence"
        assert ContentCategory.OVERVIEW.value == "Overview"

    def test_is_enum_not_str(self) -> None:
        assert not isinstance(ContentCategory.DETAILS, str)
