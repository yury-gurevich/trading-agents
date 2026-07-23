"""Unified-decision conservation tests.

Agent: orchestration
Role: prove analyst scoring is bounded by scanner survivors plus held positions.
External I/O: none.
"""

from __future__ import annotations

from orchestration.observatory import StageView, accept
from orchestration.packs.trading_boundaries import _CONSERVATION


def test_conservation_allows_scanner_survivors_plus_held_names() -> None:
    """ADR-0016: analyst.scored may equal scanner.survived + analyst.held."""
    stages = (
        StageView("provider", "x", {"returned": 3}, reached=True),
        StageView("scanner", "x", {"survived": 1}, reached=True),
        StageView("analyst", "x", {"scored": 3, "held": 2}, reached=True),
        StageView("pm", "x", {"approved": 2}, reached=True),
        StageView("execution", "x", {"submitted": 2}, reached=True),
    )

    result = accept(stages, _CONSERVATION)

    assert result.passed


def test_conservation_rejects_fabrication_beyond_held_allowance() -> None:
    """ADR-0016: analyst.scored above scanner.survived + analyst.held fails."""
    stages = (
        StageView("provider", "x", {"returned": 4}, reached=True),
        StageView("scanner", "x", {"survived": 1}, reached=True),
        StageView("analyst", "x", {"scored": 4, "held": 2}, reached=True),
    )

    result = accept(stages, _CONSERVATION)

    assert not result.passed
    assert result.breaches[0].stage == "analyst"
    assert "fabricated" in result.breaches[0].detail
