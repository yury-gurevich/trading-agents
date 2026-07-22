"""Triangle-pattern edge assertions for mutation hardening.

Agent: analyst
Role: pin recent swing selection and strict triangle break thresholds.
External I/O: none.
"""

from __future__ import annotations

from agents.analyst.domain import indicators_pattern as ip


def test_triangle_uses_recent_swings_and_strict_rising_boundary() -> None:
    """Kills _triangle_pattern mutmut_10, 17, 21, 22, 23, 30, 31, and 32."""
    assert ip._triangle_pattern(
        [(0, 130.0), (3, 140.0), (10, 100.0), (16, 100.0)],
        [(4, 80.0), (12, 90.0)],
        0.02,
    ) == (
        "ascending_triangle",
        0.65,
    )
    assert ip._triangle_pattern(
        [(4, 100.0), (12, 100.0)],
        [(0, 60.0), (3, 70.0), (10, 80.0), (16, 90.0)],
        0.02,
    ) == (
        "ascending_triangle",
        0.65,
    )
    assert ip._triangle_pattern(
        [(4, 100.0), (12, 100.0)], [(4, 100.0), (12, 101.5)], 0.02
    ) == (
        "ascending_triangle",
        0.65,
    )
    assert (
        ip._triangle_pattern([(4, 100.0), (12, 100.0)], [(4, 100.0), (12, 101.0)], 0.02)
        is None
    )
    assert (
        ip._triangle_pattern([(4, 100.0), (12, 105.0)], [(4, 100.0), (12, 102.0)], 0.02)
        is None
    )
    assert (
        ip._triangle_pattern([(4, 100.0), (12, 100.0)], [(4, 100.0), (12, 100.5)], 0.02)
        is None
    )


def test_triangle_descending_side_uses_strict_falling_boundary() -> None:
    """Kills _triangle_pattern mutmut_36 and mutmut_43 through mutmut_46."""
    assert ip._triangle_pattern(
        [(4, 100.0), (12, 98.5)], [(4, 80.0), (12, 80.0)], 0.02
    ) == (
        "descending_triangle",
        0.65,
    )
    assert (
        ip._triangle_pattern([(4, 100.0), (12, 99.0)], [(4, 80.0), (12, 80.0)], 0.02)
        is None
    )
    assert (
        ip._triangle_pattern([(4, 100.0), (12, 100.5)], [(4, 80.0), (12, 80.0)], 0.02)
        is None
    )
    assert (
        ip._triangle_pattern([(4, 100.0), (12, 150.0)], [(4, 80.0), (12, 80.0)], 0.02)
        is None
    )
    assert (
        ip._triangle_pattern([(4, 100.0), (12, 98.0)], [(4, 80.0), (12, 90.0)], 0.02)
        is None
    )
