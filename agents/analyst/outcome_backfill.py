"""Backfill of realized drawdown onto settled Recommendation nodes.

Agent: analyst
Role: record what each past recommendation actually gave back, so the stop-mode
      counterfactual can be judged on this book instead of an external backtest.
External I/O: GraphStore reads and writes via the injected backend.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from agents.analyst.domain.stop_target_outcome import observed_drawdown

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from datetime import date

    from agents.analyst.domain.stop_target_outcome import DrawdownObservation
    from contracts.provider import OHLCVBar
    from kernel import GraphStore, Node

DRAWDOWN_PROP = "stop_target_observed_drawdown_pct"
HORIZON_PROP = "stop_target_drawdown_horizon_days"


def backfill_observed_drawdowns(
    graph: GraphStore, bars: Sequence[OHLCVBar], *, horizon_days: int
) -> int:
    """Write settled drawdowns onto the Recommendations this run's bars can measure.

    Returns the number of nodes written. A recommendation is skipped - never
    written as zero - when its window has not settled, when the run's bars do not
    reach its decision day, or when a drawdown is already recorded: the merge is
    append-only, so a recorded observation is immutable (`ANLZ-OBS-05`).
    """
    series = _bars_by_ticker(bars)
    if not series:
        return 0
    decision_days = _decision_days(graph)
    written = 0
    for node in graph.list_nodes("Recommendation"):
        observation = _observation_for(node, series, decision_days, horizon_days)
        if observation is None:
            continue
        graph.merge_node(
            "Recommendation",
            node.key,
            {
                DRAWDOWN_PROP: observation.drawdown_pct,
                HORIZON_PROP: observation.horizon_days,
            },
        )
        written += 1
    return written


def _observation_for(
    node: Node,
    series: Mapping[str, tuple[OHLCVBar, ...]],
    decision_days: Mapping[str, date],
    horizon_days: int,
) -> DrawdownObservation | None:
    if node.props.get(DRAWDOWN_PROP) is not None:
        return None
    ticker = node.props.get("ticker")
    if not isinstance(ticker, str):
        return None
    bars = series.get(ticker.upper())
    decision_day = decision_days.get(node.key.split(":", 1)[0])
    if bars is None or decision_day is None:
        return None
    return observed_drawdown(bars, decision_day, horizon_days)


def _bars_by_ticker(
    bars: Sequence[OHLCVBar],
) -> dict[str, tuple[OHLCVBar, ...]]:
    grouped: dict[str, list[OHLCVBar]] = {}
    for bar in bars:
        grouped.setdefault(bar.ticker.upper(), []).append(bar)
    return {ticker: tuple(rows) for ticker, rows in grouped.items()}


def _decision_days(graph: GraphStore) -> dict[str, date]:
    days: dict[str, date] = {}
    for run in graph.list_nodes("AnalystRun"):
        created = run.props.get("created_at")
        if not isinstance(created, str):
            continue
        parsed = _parse_day(created)
        if parsed is not None:
            days[run.key] = parsed
    return days


def _parse_day(value: str) -> date | None:
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None
