"""The settling bars: one AnalystRun's MarketData, read through the run's lineage.

Agent: forecaster
Role: find the MarketData the provider wrote for a run (AnalystRun <-ANALYZED_BY-
      ScanRun -DERIVED_FROM-> MarketData, as the PM reads it: one node by lineage,
      never a listing of them) and turn its bars into each ticker's settling series
      (S241, DL-243). Market data read only from a node the provider wrote
      (FORE-NEV-04); a snapshot that cannot be read is a fault and no bars.
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.forecaster.domain.barrier_settlement import SettlingBar
from contracts.provider import MarketData
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from kernel import FaultSink, GraphStore, Node

_ANALYZED_EDGE = "ANALYZED_BY"
_DERIVED_FROM = "DERIVED_FROM"


def settling_market(graph: GraphStore, run: Node) -> Node | None:
    """The MarketData ``run`` was scanned from, or None when it has no lineage.

    The run's ANALYZED_BY ancestor's DERIVED_FROM descendant.
    """
    scan = next(
        iter(graph.ancestors(run, max_depth=1, edge_types={_ANALYZED_EDGE})), None
    )
    if scan is None:
        return None
    return next(
        iter(graph.descendants(scan, max_depth=1, edge_types={_DERIVED_FROM})), None
    )


def bars_by_ticker(market: Node, sink: FaultSink) -> dict[str, list[SettlingBar]]:
    """The run's daily bars per ticker, oldest first; none if they cannot be read.

    Bars are matched by their date, never a timestamp.
    """
    by_ticker: dict[str, list[SettlingBar]] = {}
    with fault_boundary(
        sink,
        agent="forecaster",
        module="agents.forecaster.settling_bars",
        reraise=False,
    ) as capture:
        snapshot = MarketData.model_validate(market.props["snapshot"])
        for bar in sorted(snapshot.bars, key=lambda row: row.bar_date):
            by_ticker.setdefault(bar.ticker, []).append(
                SettlingBar(bar.bar_date, bar.high, bar.low, bar.close)
            )
    return {} if capture.fault is not None else by_ticker
