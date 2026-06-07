"""Provider graph write path.

Agent: provider
Role: write provider artifacts into the append-only GraphStore provenance graph.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from contracts.common import Provenance

if TYPE_CHECKING:
    from contracts.provider import DataQualityTrace, OHLCVBar
    from kernel import GraphStore, Node


def write_market_snapshot(
    graph: GraphStore,
    *,
    tickers: tuple[str, ...],
    bars: tuple[OHLCVBar, ...],
    quality: DataQualityTrace,
) -> Provenance:
    """Write one market-data artifact and ticker edges."""
    run_id = f"provider-market-{uuid.uuid4().hex}"
    snapshot = graph.merge_node(
        "MarketSnapshot",
        run_id,
        {
            "tickers": list(tickers),
            "bar_count": len(bars),
            "requested": quality.requested,
            "returned": quality.returned,
            "used_fallback": quality.used_fallback,
            "created_at": datetime.now(tz=UTC).isoformat(),
        },
    )
    for ticker in tickers:
        ticker_node = graph.merge_node("Ticker", ticker, {"symbol": ticker})
        graph.add_edge(snapshot, ticker_node, "CONTAINS_TICKER")
    return _provenance(run_id, snapshot, quality)


def write_regime(
    graph: GraphStore,
    *,
    label: str,
    vix: float | None,
    as_of: datetime,
    incident_refs: tuple[str, ...] = (),
) -> Provenance:
    """Write one regime artifact."""
    run_id = f"provider-regime-{uuid.uuid4().hex}"
    node = graph.merge_node(
        "Regime",
        run_id,
        {"label": label, "vix": vix, "as_of": as_of.isoformat()},
    )
    return Provenance(
        run_id=run_id,
        source_agent="provider",
        graph_node_id=_graph_id(node),
        incident_refs=incident_refs,
    )


def _provenance(run_id: str, node: Node, quality: DataQualityTrace) -> Provenance:
    incident_refs = ("market_data_degraded",) if quality.used_fallback else ()
    return Provenance(
        run_id=run_id,
        source_agent="provider",
        graph_node_id=_graph_id(node),
        incident_refs=incident_refs,
    )


def _graph_id(node: Node) -> str:
    return f"{node.label}:{node.key}"
