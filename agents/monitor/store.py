"""Monitor graph write and lookup path.

Agent: monitor
Role: open positions, write checks/close decisions, and read run fills.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from contracts.common import Provenance
from contracts.positions import is_active_position_node

if TYPE_CHECKING:
    from agents.monitor.domain.positions import PositionDraft
    from contracts.common import Explanation
    from kernel import GraphStore, Node


def fills_for_run(graph: GraphStore, run_id: str) -> tuple[Node, ...]:
    """Return filled buy fills for the PM run id."""
    run = graph.get_node("PMRun", run_id)
    if run is None:
        return ()
    fills: list[Node] = []
    for order in graph.ancestors(run, max_depth=1, edge_types={"EMITTED_BY"}):
        if order.props.get("action") != "buy":
            continue
        ticker = str(order.props["ticker"])
        fill = graph.get_node("Fill", f"{run_id}:{ticker}:buy")
        if fill is not None and fill.props.get("status") == "filled":
            fills.append(fill)
    return tuple(fills)


def open_position(graph: GraphStore, draft: PositionDraft, fill: Node) -> Node:
    """Idempotently open one Position node and connect it to its fill."""
    key = f"{draft.run_id}:{draft.ticker}"
    current = graph.get_node("Position", key)
    if current is not None:
        graph.add_edge(fill, current, "OPENS")
        return current
    node = graph.merge_node(
        "Position",
        key,
        {
            "run_id": draft.run_id,
            "ticker": draft.ticker,
            "opened_price_cents": draft.opened_price_cents,
            "quantity": draft.quantity,
            "stop_pct": draft.stop_pct,
            "target_pct": draft.target_pct,
            "horizon_days": draft.horizon_days,
            "opened_at": draft.opened_at,
            "status": "open",
            "degraded": draft.degraded,
        },
    )
    graph.add_edge(fill, node, "OPENS")
    return node


def write_check(
    graph: GraphStore,
    *,
    monitor_run_id: str,
    position: Node,
    decision: str,
    trigger: str,
    current_price_cents: int,
) -> Node:
    """Write one position check and connect it to the Position."""
    node = graph.merge_node(
        "PositionCheck",
        f"{monitor_run_id}:{position.key}:check",
        {
            "run_id": monitor_run_id,
            "ticker": position.props["ticker"],
            "checked_at": datetime.now(tz=UTC).isoformat(),
            "decision": decision,
            "trigger": trigger,
            "current_price_cents": current_price_cents,
        },
    )
    graph.add_edge(node, position, "CHECKS")
    return node


def write_close_decision(
    graph: GraphStore,
    *,
    monitor_run_id: str,
    position: Node,
    decision: str,
    trigger: str,
    rationale: Explanation,
    pnl_cents: int,
) -> Node:
    """Write one close decision (with realized PnL) and connect it to the Position."""
    node = graph.merge_node(
        "CloseDecision",
        # Run-scoped on purpose: the graph is append-only (graph_support.py
        # refuses to overwrite a property), so one position-keyed node cannot
        # carry a changing run_id. Under evidence-based closure the same exit
        # is re-decided each run, and each decision is its own fact.
        f"{monitor_run_id}:{position.key}:close",
        {
            "run_id": monitor_run_id,
            "ticker": position.props["ticker"],
            "position_id": position.key,
            "decision": decision,
            "trigger": trigger,
            "rationale": rationale.summary,
            "evidence_refs": list(rationale.evidence_refs),
            "pnl_cents": pnl_cents,
            "created_at": datetime.now(tz=UTC).isoformat(),
        },
    )
    graph.add_edge(node, position, "CLOSES")
    return node


def write_monitor_run(
    graph: GraphStore,
    *,
    monitor_run_id: str,
    source_run_id: str,
    positions_checked: int,
    closes: int,
    holds: int,
) -> Provenance:
    """Write the top-level monitor run node and return provenance."""
    node = graph.merge_node(
        "MonitorRun",
        monitor_run_id,
        {
            "source_run_id": source_run_id,
            "exec_run_id": f"execution-submit-{source_run_id}",
            "positions_checked": positions_checked,
            "closes": closes,
            "holds": holds,
            "created_at": datetime.now(tz=UTC).isoformat(),
        },
    )
    return Provenance(
        run_id=monitor_run_id,
        source_agent="monitor",
        graph_node_id=f"{node.label}:{node.key}",
    )


def is_open_position(graph: GraphStore, position: Node) -> bool:
    """Return whether broker reconciliation still shows this position active."""
    del graph
    return is_active_position_node(position)


def open_positions(graph: GraphStore, positions: tuple[Node, ...]) -> tuple[Node, ...]:
    """Return only positions that have not yet been closed."""
    return tuple(
        position for position in positions if is_open_position(graph, position)
    )
