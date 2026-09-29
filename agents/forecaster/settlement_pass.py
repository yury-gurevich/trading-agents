"""Barrier settlement pass: one per AnalystRun, over the run's own MarketData.

Agent: forecaster
Role: find AnalystRuns not yet passed over and, for each, read the MarketData the
      provider wrote for it through the run's lineage (AnalystRun <-ANALYZED_BY-
      ScanRun -DERIVED_FROM-> MarketData: one node, never a listing), settle or void
      every open BarrierForecast claim its bars decide (FORE-OUT-08, FORE-FAIL-05),
      then record one BarrierSettlementPass so the run is passed once (FORE-IDM-05).
      Loop work fired by the run (FORE-TRG-01/02), never a timer; it sends nothing
      on the bus and touches nothing on the decision path (FORE-NEV-01/02).
External I/O: GraphStore reads and writes via the injected backend.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from agents.forecaster.barrier_store import BARRIER_LABEL
from agents.forecaster.domain.barrier_settlement import VOID, settle
from agents.forecaster.settlement_store import settled_claim_keys, write_settlement
from agents.forecaster.settling_bars import bars_by_ticker, settling_market
from contracts.barrier_history import is_current_run
from kernel import CollectingFaultSink
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from agents.forecaster.domain.barrier_settlement import SettlingBar
    from kernel import FaultSink, GraphStore, Node

ANALYST_RUN_LABEL = "AnalystRun"
#: The node that marks one AnalystRun's pass done, written last (DL-243 D1).
SETTLEMENT_MARKER_LABEL = "BarrierSettlementPass"
#: AnalystRun -BARRIER_SETTLEMENT_BY-> BarrierSettlementPass.
SETTLEMENT_MARKER_EDGE = "BARRIER_SETTLEMENT_BY"


def settlement_marker_key(analyst_run_key: str) -> str:
    """One pass per AnalystRun: ``settlement-pass:{run key}``."""
    return f"settlement-pass:{analyst_run_key}"


def find_pending_settlement(
    graph: GraphStore, *, now: datetime | None = None
) -> list[Node]:
    """AnalystRuns with no pass yet; with ``now``, current runs only (D11)."""
    pending: list[Node] = []
    for node in graph.list_nodes(ANALYST_RUN_LABEL):
        if now is not None and not is_current_run(node.props, now):
            continue
        marked = graph.descendants(
            node, max_depth=1, edge_types={SETTLEMENT_MARKER_EDGE}
        )
        if not list(marked):
            pending.append(node)
    return pending


def settle_analyst_node(
    node: Node, *, graph: GraphStore, sink: FaultSink | None = None
) -> None:
    """Settle every open claim this run's bars decide, then mark the run passed.

    A run already passed is left alone. The marker is written last, so a pass
    that stops half way leaves the run pending, and the retry skips the claims it
    already settled.
    """
    key = settlement_marker_key(node.key)
    if graph.get_node(SETTLEMENT_MARKER_LABEL, key) is not None:
        return
    sink = sink if sink is not None else CollectingFaultSink()
    pass_date = _pass_date(node)
    market = settling_market(graph, node)
    settling_ref = market.key if market is not None else None
    bars = bars_by_ticker(market, sink) if market is not None else {}
    settled = settled_claim_keys(graph)
    counts: Counter[str] = Counter()
    for claim in graph.list_nodes(BARRIER_LABEL):
        if claim.key not in settled:
            status = _settle_claim(graph, sink, claim, bars, pass_date, settling_ref)
            counts[status] += 1
    marker = graph.merge_node(
        SETTLEMENT_MARKER_LABEL,
        key,
        {
            "analyst_run_key": node.key,
            "pass_date": pass_date.isoformat(),
            "settling_ref": settling_ref,
            "settled": counts["settled"],
            "voided": counts["voided"],
            "open": counts["open"],
            "created_at": datetime.now(tz=UTC).isoformat(),
        },
    )
    graph.add_edge(node, marker, SETTLEMENT_MARKER_EDGE)


def _settle_claim(
    graph: GraphStore,
    sink: FaultSink,
    claim: Node,
    bars: dict[str, list[SettlingBar]],
    pass_date: date,
    settling_ref: str | None,
) -> str:
    """Settle one claim; a claim the pass cannot read faults and stays open."""
    status = "open"
    with fault_boundary(
        sink,
        agent="forecaster",
        module="agents.forecaster.settlement_pass",
        reraise=False,
    ) as capture:
        props = claim.props
        settlement = settle(
            bars.get(str(props["ticker"]), []),
            as_of=date.fromisoformat(str(props["as_of"])),
            entry_close=float(props["entry_close"]),
            stop_pct=float(props["stop_pct"]),
            target_pct=float(props["target_pct"]),
            pass_date=pass_date,
        )
        if settlement is not None:
            write_settlement(graph, claim, settlement, settling_ref=settling_ref)
            status = "voided" if settlement.outcome == VOID else "settled"
    return "open" if capture.fault is not None else status


def _pass_date(node: Node) -> date:
    """The run's creation date: the pass's date, a fact of the run (DL-243 D3).

    The analyst stamps ``created_at`` in UTC; a run without a readable stamp (a
    hand-built one) falls back to today's UTC date, recorded on the marker.
    """
    try:
        return datetime.fromisoformat(str(node.props.get("created_at"))).date()
    except ValueError:
        return datetime.now(tz=UTC).date()
