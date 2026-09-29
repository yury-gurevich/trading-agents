"""The benchmark series a run's performance is scored against (S242, DL-246).

Agent: reporter
Role: read one MarketData - the run's own, by lineage - and its benchmark bars up to
      the run's as-of date, without listing any other run's payload.
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import GraphStore, Node

_ANALYST_RUN_LABEL = "AnalystRun"
_SOURCE_ANALYST_RUN_PROP = "source_analyst_run_id"
_ANALYZED_BY = "ANALYZED_BY"
_DERIVED_FROM = "DERIVED_FROM"


def run_benchmark(
    graph: GraphStore, pm_run: Node, *, as_of: date
) -> tuple[dict[date, float], str | None]:
    """The run's own benchmark closes up to ``as_of``, and the benchmark's ticker.

    A broken lineage, a MarketData dated after ``as_of`` or one with no benchmark
    bars is the no-benchmark path: ``({}, None)``. Another run's series is never
    read, so a re-report reproduces its figures (RPT-IDM-03).
    """
    market = _run_market_data(graph, pm_run)
    if market is None:
        return {}, None
    window_end = date_only(market.props.get("window_end"))
    snapshot = market.props.get("snapshot")
    if window_end is None or window_end > as_of or not isinstance(snapshot, Mapping):
        return {}, None
    benchmark = snapshot.get("benchmark")
    if not isinstance(benchmark, Sequence) or not benchmark:
        return {}, None
    closes: dict[date, float] = {}
    ticker: str | None = None
    for bar in benchmark:
        if not isinstance(bar, Mapping):
            continue
        bar_date = date_only(bar.get("bar_date"))
        close = bar.get("close")
        if bar_date is None or bar_date > as_of or not isinstance(close, int | float):
            continue
        closes[bar_date] = float(close)
        if ticker is None and isinstance(bar.get("ticker"), str):
            ticker = bar["ticker"]
    return closes, ticker


def _run_market_data(graph: GraphStore, pm_run: Node) -> Node | None:
    # PMRun.source_analyst_run_id keys the AnalystRun; write_analysis links
    # (scan)-[:ANALYZED_BY]->(analyst) and write_scan (scan)-[:DERIVED_FROM]->(market),
    # the walk the PM's own poll makes. One node per hop, never a label listing.
    analyst_key = pm_run.props.get(_SOURCE_ANALYST_RUN_PROP)
    if not isinstance(analyst_key, str):
        return None
    analyst_run = graph.get_node(_ANALYST_RUN_LABEL, analyst_key)
    if analyst_run is None:
        return None
    scan_run = next(
        iter(graph.ancestors(analyst_run, max_depth=1, edge_types={_ANALYZED_BY})),
        None,
    )
    if scan_run is None:
        return None
    return next(
        iter(graph.descendants(scan_run, max_depth=1, edge_types={_DERIVED_FROM})),
        None,
    )


def date_only(value: object) -> date | None:
    """The date an ISO-8601 string starts with, or None."""
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None
