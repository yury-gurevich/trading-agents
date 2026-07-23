"""Monitor per-position decision.

Agent: monitor
Role: turn one open Position + its current price into a CloseDecision, persisting the
      position check and (on close) the realized-PnL close-decision node.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.monitor.domain.exit_rules import evaluate_position, realized_pnl_cents
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
    pnl_cents = (
        realized_pnl_cents(
            current_price_cents,
            int(position.props["opened_price_cents"]),
            int(position.props["quantity"]),
        )
        if decision == "close"
        else None
    )
    if decision == "close" and pnl_cents is not None:
        write_close_decision(
            graph,
            monitor_run_id=monitor_run_id,
            position=position,
            decision=decision,
            trigger=trigger,
            rationale=rationale,
            pnl_cents=pnl_cents,
        )
    return CloseDecision(
        ticker=ticker,
        position_id=position.key,
        decision=decision,
        trigger=trigger,
        rationale=rationale,
        quantity=int(position.props["quantity"]),
        reference_price_cents=current_price_cents,
        pnl_cents=pnl_cents,
    )
