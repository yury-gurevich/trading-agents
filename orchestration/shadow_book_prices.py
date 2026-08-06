"""Market-snapshot pricing helpers for the read-only shadow book.

Agent: orchestration
Role: resolve run-local reference prices and graph-derived forward trading dates.
External I/O: GraphStore reads via the injected backend; never writes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.provider import MarketData

if TYPE_CHECKING:
    from datetime import date

    from kernel import GraphStore, Node

_SCAN_RUN_LABEL = "ScanRun"
_DERIVED_FROM = "DERIVED_FROM"


def market_history(
    nodes: tuple[Node, ...],
) -> tuple[dict[str, dict[date, float]], tuple[date, ...]]:
    """Build an append-stable price history and observed trading calendar."""
    history: dict[str, dict[date, float]] = {}
    trading_dates: set[date] = set()
    ordered = sorted(nodes, key=lambda item: (str(item.props["window_end"]), item.key))
    for node in ordered:
        market = MarketData.model_validate(node.props["snapshot"])
        for bar in market.bars:
            trading_dates.add(bar.bar_date)
            history.setdefault(bar.ticker, {}).setdefault(bar.bar_date, bar.close)
    return history, tuple(sorted(trading_dates))


def source_market(graph: GraphStore, analyst_run: Node) -> MarketData | None:
    """Return the MarketData snapshot consumed by one AnalystRun."""
    scan_id = str(analyst_run.props["source_scan_run_id"])
    scan_run = graph.get_node(_SCAN_RUN_LABEL, scan_id)
    if scan_run is None:
        return None
    market_node = next(
        iter(graph.descendants(scan_run, max_depth=1, edge_types={_DERIVED_FROM})),
        None,
    )
    return (
        MarketData.model_validate(market_node.props["snapshot"])
        if market_node is not None
        else None
    )


def reference_price(
    market: MarketData | None, ticker: str, as_of: date
) -> float | None:
    """Return the last run-local close at or before the analyst as-of date."""
    bars = (
        [bar for bar in market.bars if bar.ticker == ticker and bar.bar_date <= as_of]
        if market is not None
        else []
    )
    return max(bars, key=lambda bar: bar.bar_date).close if bars else None


def target_date(
    trading_dates: tuple[date, ...], as_of: date, horizon: int
) -> date | None:
    """Return the horizon-th observed trading date after the recommendation."""
    future = [bar_date for bar_date in trading_dates if bar_date > as_of]
    return future[horizon - 1] if len(future) >= horizon else None
