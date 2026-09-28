"""Barrier-claim test helpers.

Agent: forecaster
Role: wire a provider + forecaster pair for forecast_barrier with a fake GARCH
      fitter, build multi-year bar fixtures and request messages, and record every
      bus request so a test can see exactly what was asked of whom.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from agents.forecaster import ForecasterAgent
from agents.forecaster.barrier_fit import FakeGarchFitter
from agents.forecaster.domain.barrier_garch import RawGarchFit
from agents.forecaster.tests.barrier_fixture import ohlc_series
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.forecaster import ForecastRequest
from contracts.provider import OHLCVBar
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from datetime import date

    from agents.forecaster.barrier_fit import GarchFitter
    from agents.forecaster.settings import ForecasterSettings
    from kernel import GraphStore

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


def wire_barrier(
    *,
    bars: tuple[OHLCVBar, ...] = (),
    fitter: GarchFitter | None = None,
    settings: ForecasterSettings | None = None,
    graph: GraphStore | None = None,
    fail_ohlcv: bool = False,
    register_provider: bool = True,
) -> tuple[RecordingBus, GraphStore, CollectingFaultSink]:
    """Bind a fake-source provider and a forecaster onto one recording bus."""
    bus = RecordingBus()
    store: GraphStore = graph if graph is not None else InMemoryGraphStore()
    sink = CollectingFaultSink()
    if register_provider:
        ProviderAgent(
            bus,
            graph=store,
            source=FakeDataSource(bars=bars, fail_ohlcv=fail_ohlcv),
            settings=ProviderSettings(max_staleness_days=7),
        ).bind()
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
) -> AgentMessage:
    """A forecast_barrier request carrying a buy's stop and target."""
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
        ).model_dump(mode="json"),
    )
