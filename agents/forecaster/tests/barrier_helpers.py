"""Barrier-claim test helpers.

Agent: forecaster
Role: wire the forecaster alone (as deployed) with a fake GARCH fitter, seed the
      provider-written BarrierHistory it reads (DL-241 D10), build multi-year bar
      fixtures and request messages, and record every bus request.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Literal

from agents.forecaster import ForecasterAgent
from agents.forecaster.barrier_fit import FakeGarchFitter
from agents.forecaster.domain.barrier_garch import RawGarchFit
from agents.forecaster.tests.barrier_fixture import ohlc_series
from contracts.analyst import Recommendation, RecommendationSet
from contracts.barrier_history import (
    BARRIER_HISTORY_LABEL,
    BarrierHistory,
    TickerHistory,
    barrier_history_key,
)
from contracts.common import Explanation, Provenance
from contracts.forecaster import ForecastRequest
from contracts.provider import OHLCVBar
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from datetime import date

    from agents.forecaster.barrier_fit import GarchFitter
    from agents.forecaster.settings import ForecasterSettings
    from kernel import GraphStore, Node

#: The AnalystRun every seeded history belongs to, and that history's key.
RUN_KEY = "analyst-run-s239"
HISTORY_KEY = barrier_history_key(RUN_KEY)
#: A fit EXP-018's rule accepts as it stands (alpha + beta = 0.95).
ACCEPTED = RawGarchFit(mu=0.02, omega=0.05, alpha=0.05, beta=0.90, converged=True)


class RecordingBus(InProcessBus):
    """An in-process bus that keeps every request it carried, in order."""

    def __init__(self) -> None:
        """Start with no recorded requests."""
        super().__init__()
        self.requests: list[AgentMessage] = []

    def request(self, message: AgentMessage) -> AgentMessage:
        """Record the request, then dispatch it as the in-process bus does."""
        self.requests.append(message)
        return super().request(message)


def barrier_bars(
    ticker: str, count: int, *, drift: float = 0.0, end: date | None = None
) -> tuple[OHLCVBar, ...]:
    """Build ``count`` consecutive daily bars ending on ``end`` (default today)."""
    last = end or datetime.now(tz=UTC).date()
    opens, highs, lows, closes = ohlc_series(count, drift=drift)
    return tuple(
        OHLCVBar(
            ticker=ticker,
            bar_date=last - timedelta(days=count - 1 - index),
            open=opens[index],
            high=highs[index],
            low=lows[index],
            close=closes[index],
            volume=1_000_000,
        )
        for index in range(count)
    )


def seed_history(
    graph: GraphStore,
    bars: tuple[OHLCVBar, ...],
    *,
    run_key: str = RUN_KEY,
    sessions: int = 760,
    dropped: dict[str, str] | None = None,
    status: Literal["ok", "failed"] = "ok",
    reason: str | None = None,
) -> str:
    """Write a BarrierHistory as the provider's contract shapes it; return its key."""
    histories: dict[str, TickerHistory] = {}
    for ticker in dict.fromkeys(bar.ticker for bar in bars):
        kept = [bar for bar in bars if bar.ticker == ticker][-sessions:]
        rows = tuple(
            (b.bar_date.isoformat(), b.open, b.high, b.low, b.close) for b in kept
        )
        histories[ticker] = TickerHistory(bars=rows, bar_count=len(rows))
    today = datetime.now(tz=UTC).date()
    history = BarrierHistory(
        analyst_run_key=run_key,
        status=status,
        reason=reason,
        window_start=today - timedelta(days=1125),
        window_end=today,
        sessions_requested=sessions,
        requested=(*histories, *(dropped or {})),
        histories=histories,
        dropped=dropped or {},
        created_at=datetime.now(tz=UTC),
    )
    key = barrier_history_key(run_key)
    graph.merge_node(BARRIER_HISTORY_LABEL, key, history.model_dump(mode="json"))
    return key


def wire_barrier(
    *,
    bars: tuple[OHLCVBar, ...] = (),
    fitter: GarchFitter | None = None,
    settings: ForecasterSettings | None = None,
    graph: GraphStore | None = None,
    dropped: dict[str, str] | None = None,
    status: Literal["ok", "failed"] = "ok",
    reason: str | None = None,
) -> tuple[RecordingBus, GraphStore, CollectingFaultSink]:
    """Bind the forecaster alone (as deployed) and seed the run's BarrierHistory."""
    bus = RecordingBus()
    store: GraphStore = graph if graph is not None else InMemoryGraphStore()
    sink = CollectingFaultSink()
    seed_history(store, bars, dropped=dropped, status=status, reason=reason)
    ForecasterAgent(
        bus,
        graph=store,
        settings=settings,
        sink=sink,
        barrier_fitter=fitter if fitter is not None else FakeGarchFitter(ACCEPTED),
    ).bind()
    return bus, store, sink


def barrier_message(
    ticker: str,
    *,
    stop_pct: float = 0.05,
    target_pct: float = 0.06,
    features: dict[str, float] | None = None,
    history_ref: str | None = HISTORY_KEY,
) -> AgentMessage:
    """A forecast_barrier request carrying a buy's stop, target and history ref."""
    return AgentMessage(
        sender="tester",
        recipient="forecaster",
        message_type="request",
        capability="forecast_barrier",
        payload=ForecastRequest(
            subject_kind="recommendation",
            subject_ref=ticker,
            features=(
                features
                if features is not None
                else {"stop_pct": stop_pct, "target_pct": target_pct}
            ),
            history_ref=history_ref,
        ).model_dump(mode="json"),
    )


def deployed_analyst_run(graph: GraphStore) -> Node:
    """An AnalystRun with two buys carrying both barriers (AAPL, GOOG) and a sell."""
    recs = tuple(
        Recommendation.model_validate(
            {
                "ticker": ticker,
                "action": action,
                "confidence": 0.8,
                "technical_score": 0.7,
                "suggested_stop_pct": 0.05,
                "suggested_target_pct": 0.07,
                "rationale": Explanation(summary=f"{ticker} fixture"),
            }
        )
        for ticker, action in (("AAPL", "buy"), ("GOOG", "buy"), ("NVDA", "sell"))
    )
    recommendation_set = RecommendationSet(
        run_id="analyst-run-deployed",
        recommendations=recs,
        rejections=(),
        explanation=Explanation(summary="fixture run"),
        provenance=Provenance(run_id="analyst-run-deployed", source_agent="analyst"),
    )
    return graph.merge_node(
        "AnalystRun",
        "analyst-run-deployed",
        {"recommendation_set": recommendation_set.model_dump(mode="json")},
    )
