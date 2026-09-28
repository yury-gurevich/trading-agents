"""Provider barrier-history work kind: the long daily history a barrier claim needs.

Agent: provider
Role: find AnalystRun nodes holding a buy with both a suggested stop and target and no
      BarrierHistory yet; fetch those tickers' daily bars in ONE request through the
      provider's own fetch path (the source's feed and end rule, then validation and
      the unchanged extreme-move guard), and write ONE BarrierHistory node linked from
      the AnalystRun. A dropped ticker is listed with its reason; a failed fetch still
      writes the node, status failed, so no reader waits forever (DL-241 D10).
External I/O: none directly (delegates to ProviderAgent, which calls the DataSource).
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Literal

from contracts.analyst import RecommendationSet
from contracts.barrier_history import (
    BARRIER_HISTORY_EDGE,
    BARRIER_HISTORY_LABEL,
    BarrierHistory,
    TickerHistory,
    barrier_buys,
    barrier_history_key,
)
from contracts.common import Window
from contracts.provider import DataRequest
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from agents.provider.agent import ProviderAgent
    from contracts.provider import DataQualityTrace, MarketData, OHLCVBar
    from kernel import GraphStore, Node
    from kernel.errors import AgentFault

ANALYST_RUN_LABEL = "AnalystRun"
#: Calendar days asked per session: 250 a year is below the exchange's 251-253, so
#: the window always over-asks (EXP-018: 752 sessions in 1,097 days; DL-241 D3).
_DAYS_PER_SESSION = 365.25 / 250
#: Slack for a holiday cluster, a non-session end day, a session not yet served.
_WINDOW_MARGIN_DAYS = 14
#: The quality note the provider's fetch path writes when the source itself failed.
_SOURCE_FAILED_NOTE = "source_unavailable"


def find_pending_barrier_history(graph: GraphStore) -> list[Node]:
    """AnalystRun nodes with a qualifying buy and no BarrierHistory yet."""
    pending: list[Node] = []
    for node in graph.list_nodes(ANALYST_RUN_LABEL):
        done = graph.descendants(node, max_depth=1, edge_types={BARRIER_HISTORY_EDGE})
        if not list(done) and _qualifying_tickers(node):
            pending.append(node)
    return pending


def write_barrier_history(node: Node, *, agent: ProviderAgent) -> None:
    """Fetch the run's qualifying tickers once and write one linked BarrierHistory."""
    tickers = _qualifying_tickers(node)
    sessions = agent._settings.barrier_history_sessions
    window = barrier_window(sessions)
    market: MarketData | None = None
    with fault_boundary(
        agent.sink,
        agent="provider",
        module="agents.provider.barrier_history",
        capability="barrier_history",
        reraise=False,
    ) as capture:
        market = agent._get_market_data(
            DataRequest(tickers=tickers, window=window, fields=("ohlcv",))
        )
    history = _history(node.key, tickers, window, sessions, market, capture.fault)
    written = _write(agent._graph, history)
    agent._graph.add_edge(node, written, BARRIER_HISTORY_EDGE)


def barrier_window(sessions: int) -> Window:
    """A calendar window ending today that holds at least ``sessions`` sessions."""
    end = datetime.now(tz=UTC).date()
    days = math.ceil(sessions * _DAYS_PER_SESSION) + _WINDOW_MARGIN_DAYS
    return Window(start=end - timedelta(days=days), end=end)


def _qualifying_tickers(node: Node) -> tuple[str, ...]:
    raw = node.props.get("recommendation_set")
    if raw is None:
        return ()
    recommendation_set = RecommendationSet.model_validate(raw)
    return tuple(dict.fromkeys(rec.ticker for rec in barrier_buys(recommendation_set)))


def _history(
    run_key: str,
    tickers: tuple[str, ...],
    window: Window,
    sessions: int,
    market: MarketData | None,
    fault: AgentFault | None,
) -> BarrierHistory:
    failure = _failure(market, fault)
    status: Literal["ok", "failed"] = "failed"
    histories: dict[str, TickerHistory] = {}
    dropped = dict.fromkeys(tickers, f"fetch failed: {failure}")
    stale: tuple[str, ...] = ()
    if market is not None and failure is None:
        status, dropped = "ok", {}
        for ticker in tickers:
            bars = [bar for bar in market.bars if bar.ticker == ticker]
            if bars:
                histories[ticker] = _ticker_history(bars, sessions)
            else:
                dropped[ticker] = _drop_reason(ticker, market.quality)
        stale = tuple(t for t in market.quality.stale_tickers if t in histories)
    return BarrierHistory(
        analyst_run_key=run_key,
        status=status,
        reason=failure,
        window_start=window.start,
        window_end=window.end,
        sessions_requested=sessions,
        requested=tickers,
        histories=histories,
        dropped=dropped,
        stale=stale,
        created_at=datetime.now(tz=UTC),
    )


def _failure(market: MarketData | None, fault: AgentFault | None) -> str | None:
    if fault is not None:
        return f"{fault.error_type}: {fault.message}"
    if market is not None and _SOURCE_FAILED_NOTE in market.quality.notes:
        return _SOURCE_FAILED_NOTE
    return None


def _drop_reason(ticker: str, quality: DataQualityTrace) -> str:
    """Why a requested ticker came back with no bars: the guard, or nothing served.

    A ticker with no valid bars is always in ``stale_tickers`` (the staleness
    check counts a missing ticker), so those are the only two reasons.
    """
    if ticker in quality.anomalous_tickers:
        return "extreme_move_guard: an open-to-close move beyond max_daily_move_sigma"
    return "no_bars_returned: stale_or_missing"


def _ticker_history(bars: list[OHLCVBar], sessions: int) -> TickerHistory:
    kept = sorted(bars, key=lambda bar: bar.bar_date)[-sessions:]
    rows = tuple(
        (bar.bar_date.isoformat(), bar.open, bar.high, bar.low, bar.close)
        for bar in kept
    )
    return TickerHistory(bars=rows, bar_count=len(rows))


def _write(graph: GraphStore, history: BarrierHistory) -> Node:
    """Merge the node; the literal keys keep its properties checkable (the pack)."""
    data = history.model_dump(mode="json")
    return graph.merge_node(
        BARRIER_HISTORY_LABEL,
        barrier_history_key(history.analyst_run_key),
        {
            "analyst_run_key": data["analyst_run_key"],
            "status": data["status"],
            "reason": data["reason"],
            "window_start": data["window_start"],
            "window_end": data["window_end"],
            "sessions_requested": data["sessions_requested"],
            "requested": data["requested"],
            "histories": data["histories"],
            "dropped": data["dropped"],
            "stale": data["stale"],
            "created_at": data["created_at"],
        },
    )
