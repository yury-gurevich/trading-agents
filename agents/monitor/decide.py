"""Monitor per-position decision.

Agent: monitor
Role: turn one open Position + its current price into a CloseDecision, persisting the
      position check and close intent.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.monitor.domain.exit_rules import evaluate_position
from agents.monitor.domain.positions import exit_position
from agents.monitor.result import decision_rationale
from agents.monitor.store import write_check, write_close_decision
from contracts.monitor import CloseDecision

if TYPE_CHECKING:
    from datetime import date

    from kernel import GraphStore, Node


def evaluate_one(
    graph: GraphStore,
    monitor_run_id: str,
    position: Node,
    current_price_cents: int,
    today: date,
) -> CloseDecision:
    """Evaluate one open position; persist its check/close, return the decision."""
    ticker = str(position.props["ticker"])
    decision, trigger = evaluate_position(
        exit_position(position), current_price_cents, today
    )
    rationale = decision_rationale(ticker, decision, trigger)
    write_check(
        graph,
        monitor_run_id=monitor_run_id,
        position=position,
        decision=decision,
        trigger=trigger,
        current_price_cents=current_price_cents,
    )
    if decision == "close":
        write_close_decision(
            graph,
            monitor_run_id=monitor_run_id,
            position=position,
            decision=decision,
            trigger=trigger,
            rationale=rationale,
        )
    return CloseDecision(
        ticker=ticker,
        position_id=position.key,
        decision=decision,
        trigger=trigger,
        rationale=rationale,
        quantity=int(position.props["quantity"]),
        reference_price_cents=current_price_cents,
    )
