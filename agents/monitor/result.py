"""Monitor response explanation helpers.

Agent: monitor
Role: build close-decision and run-level explanations.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.common import Explanation

if TYPE_CHECKING:
    from contracts.monitor import CloseDecision


def decision_rationale(ticker: str, decision: str, trigger: str) -> Explanation:
    """Return rationale for one hold or close decision."""
    if decision == "close":
        return Explanation(
            summary=f"Close {ticker}: {trigger} exit rule triggered.",
            evidence_refs=("monitor.exit_rules",),
        )
    return Explanation(
        summary=f"Hold {ticker}: no exit rule triggered.",
        evidence_refs=("monitor.exit_rules",),
    )


def run_explanation(decisions: tuple[CloseDecision, ...]) -> Explanation:
    """Return a run-level monitor explanation."""
    closes = sum(item.decision == "close" for item in decisions)
    return Explanation(
        summary=(
            f"Monitor checked {len(decisions)} positions; {closes} close decisions."
        ),
        evidence_refs=("monitor.exit_rules", "provider.get_market_data"),
    )
