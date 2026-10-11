"""The window a barrier history covers: how long it is, and the day it ends on.

Agent: provider
Role: read the as-of of the run an AnalystRun belongs to through the run's lineage
      (AnalystRun <-ANALYZED_BY- ScanRun -DERIVED_FROM-> MarketData: one node, never
      a listing of them), the `window_end` the provider itself stored for that run
      (PROV-TRG-05), and build the calendar window ending on it that holds the
      sessions a barrier claim is fitted on (PROV-OUT-08, DL-241 D3).
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

from contracts.common import Window

if TYPE_CHECKING:
    from kernel import GraphStore, Node

#: Calendar days asked per session: 250 a year is below the exchange's 251-253, so
#: the window always over-asks (EXP-018: 752 sessions in 1,097 days; DL-241 D3).
_DAYS_PER_SESSION = 365.25 / 250
#: Slack for a holiday cluster, a non-session end day, a session not yet served.
_WINDOW_MARGIN_DAYS = 14
_ANALYZED_EDGE = "ANALYZED_BY"
_DERIVED_FROM = "DERIVED_FROM"


def run_as_of(graph: GraphStore, analyst_run: Node) -> date | None:
    """The as-of of the run ``analyst_run`` was scanned for, or None when it has none.

    The `window_end` of the MarketData the run's ScanRun was derived from. Only a
    run built by hand has no such lineage: the graph-pull analyst recommends
    nothing without a MarketData.
    """
    scan = next(
        iter(graph.ancestors(analyst_run, max_depth=1, edge_types={_ANALYZED_EDGE})),
        None,
    )
    if scan is None:
        return None
    market = next(
        iter(graph.descendants(scan, max_depth=1, edge_types={_DERIVED_FROM})), None
    )
    if market is None:
        return None
    return date.fromisoformat(str(market.props["window_end"]))


def barrier_window(sessions: int, as_of: date | None = None) -> Window:
    """A calendar window holding at least ``sessions`` sessions, ending on ``as_of``.

    ``as_of`` is the run's as-of; a run with none is served as an ingest no run
    triggered is, ending on today's UTC date (PROV-TRG-05).
    """
    end = as_of or datetime.now(tz=UTC).date()
    days = math.ceil(sessions * _DAYS_PER_SESSION) + _WINDOW_MARGIN_DAYS
    return Window(start=end - timedelta(days=days), end=end)
