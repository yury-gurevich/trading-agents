"""Deliberation trace verdict-count tests.

Agent: orchestration
Role: prove revise counts stay visible without becoming veto claims.
External I/O: none.
"""

from __future__ import annotations

from kernel import Node
from orchestration.trace_deliberation import format_deliberation_trace


def test_revise_trace_stays_visible_without_veto() -> None:
    """DLIB-OUT-02 / LAW-02: revise findings stay visible after veto narrows."""
    lines = format_deliberation_trace(
        None,
        Node(
            "DeliberationRun",
            "delib",
            {
                "verdicts": {"USB": "revise", "WFC": "revise", "AMZN": "uphold"},
                "vetoed_tickers": (),
            },
        ),
        Node("ExecutionRun", "exec", {"deliberation_status": "applied"}),
    )

    assert lines == ("reviewed=3  revised=2  vetoed=0  status=applied",)


def test_old_deliberation_row_renders_unknowns() -> None:
    """DLIB-OUT-02 / LAW-02: missing historical props render without raising."""
    lines = format_deliberation_trace(
        None,
        Node("DeliberationRun", "delib", {}),
        Node("ExecutionRun", "exec", {"deliberation_status": "applied"}),
    )

    assert lines == ("reviewed=?  revised=?  vetoed=?  status=applied",)
