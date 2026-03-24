"""Notation metadata for ArchiMate 3.2 element rendering.

NotationMetadata carries the rendering hints (shape, colour, badge letter)
that correspond to each element type's standard graphical notation as
defined in the ArchiMate 3.2 specification iconography chapter.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__: list[str] = ["NotationMetadata"]


@dataclass(frozen=True)
class NotationMetadata:
    """Static rendering hints for an ArchiMate element type.

    Each concrete element class carries a class-level ``NotationMetadata``
    instance describing the standard graphical notation defined by the
    ArchiMate 3.2 specification (Appendix A).

    Attributes:
        corner_shape: Corner rendering style (e.g., ``"square"``, ``"round"``,
            ``"cut"``).  String rather than enum because the spec defines
            corner styles in prose, not a formal vocabulary.
        layer_color: Recommended layer colour as a hex string (e.g.,
            ``"#FFFFB5"``) or CSS colour name.
        badge_letter: Letter badge displayed on the element icon (e.g.,
            ``"S"`` for Service).  ``None`` for element types that use an
            icon rather than a letter badge.
    """

    corner_shape: str
    layer_color: str
    badge_letter: str | None
