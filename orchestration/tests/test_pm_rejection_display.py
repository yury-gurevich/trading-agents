"""One rejection map: the display cannot disagree with the gate that rejected.

Agent: orchestration
Role: prove a rejection names its own failing gate once, never as its own echo.
External I/O: none.
"""

from __future__ import annotations

from agents.portfolio_manager.domain.position_gates import position_rejection
from agents.portfolio_manager.domain.rejection_reasons import (
    POSITION_GATE_REASONS,
    REASON_TO_GATE,
)
from contracts.portfolio_manager import GateOutcome, GateStatus, RejectedOrder
from orchestration.pm_rejections import format_pm_rejection


def _outcome(name: str, status: GateStatus) -> GateOutcome:
    return GateOutcome(name=name, value=1.0, threshold=0.0, outcome=status, detail="")


def test_a_sizing_rejection_does_not_echo_sizing_as_a_secondary_failure() -> None:
    """The live defect on sched-2026-09-21: `GOOGL SKIP sizing (also failed: sizing)`.

    `_REASON_GATE` omitted `sizing`, so `primary_gate` was None and the very gate
    that produced the rejection was not filtered out of the secondary list.
    """

    rejection = RejectedOrder(
        ticker="GOOGL",
        reason="sizing",
        gate_report=(_outcome("sizing", GateStatus.FAILED),),
    )

    rendered = format_pm_rejection(rejection)

    assert "also failed" not in rendered
    assert rendered.strip() == "GOOGL  SKIP  sizing"


def test_a_genuine_secondary_failure_is_still_reported() -> None:
    """The negative control. A filter that hides real secondary failures is worse."""

    rejection = RejectedOrder(
        ticker="MSFT",
        reason="sizing",
        gate_report=(
            _outcome("sizing", GateStatus.FAILED),
            _outcome("max_positions", GateStatus.FAILED),
        ),
    )

    rendered = format_pm_rejection(rejection)

    assert "(also failed: max_positions)" in rendered
    assert rendered.count("sizing") == 1


def test_every_position_rejection_reason_resolves_to_its_own_gate() -> None:
    """The anti-drift guarantee, not the missing key.

    Adding `"sizing"` by hand would silence one instance and leave two copies of
    one map free to diverge again. This asserts the structural property instead:
    every reason `position_rejection` can emit resolves back to the gate that
    emitted it, so a new gate cannot be added on one side alone.
    """

    for gate_name, reason in POSITION_GATE_REASONS.items():
        rejection = position_rejection(
            "AAPL", (_outcome(gate_name, GateStatus.FAILED),)
        )
        assert rejection is not None, gate_name
        assert rejection.reason == reason
        assert REASON_TO_GATE[rejection.reason] == gate_name
        assert "also failed" not in format_pm_rejection(rejection)


def test_the_display_map_is_derived_from_the_gate_map_not_retyped() -> None:
    """Every position gate reaches the display map by derivation, not by hand."""

    for gate_name, reason in POSITION_GATE_REASONS.items():
        assert REASON_TO_GATE[reason] == gate_name
