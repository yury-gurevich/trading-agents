"""Orchestration test helpers.

Agent: orchestration
Role: provide deterministic dispatcher fixtures and assertion helpers.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

from agents.provider.sources import RegimeInputs
from agents.scanner.universe import FakeUniverse
from contracts.common import Explanation, Provenance
from contracts.provider import OHLCVBar
from contracts.reporter import RunSnapshot
from orchestration.trigger import RunTrigger

if TYPE_CHECKING:
    import pytest

    from contracts.common import Window
    from kernel import InMemoryGraphStore

TICKER = "AAPL"
UNIVERSE = "fixture"


@dataclass
class ReboundingDataSource:
    """Return entry bars until monitor asks, then return lower rebound bars."""

    entry: tuple[OHLCVBar, ...]
    rebound: tuple[OHLCVBar, ...]
    rebound_after_calls: int = 3
    vix: float | None = 12.0
    calls: int = 0

    def fetch_ohlcv(
        self, tickers: tuple[str, ...], window: Window
    ) -> tuple[OHLCVBar, ...]:
        """Return phase bars; benchmark-only probes don't advance the phase."""
        ticker_set = set(tickers)
        served = {bar.ticker for bar in (*self.entry, *self.rebound)}
        if ticker_set & served:
            self.calls += 1
        rows = self.rebound if self.calls > self.rebound_after_calls else self.entry
        return tuple(
            bar
            for bar in rows
            if bar.ticker in ticker_set and window.start <= bar.bar_date <= window.end
        )

    def fetch_regime_inputs(self, as_of: date) -> RegimeInputs:
        """Return deterministic regime inputs."""
        return RegimeInputs(as_of=as_of, vix=self.vix)

    def fetch_fundamentals(
        self, tickers: tuple[str, ...], window: Window
    ) -> dict[str, dict[str, float]]:
        """Return no fundamentals; this fixture exercises the OHLCV path only."""
        return {}

    def fetch_news(
        self,
        tickers: tuple[str, ...],
        window: Window,
    ) -> dict[str, tuple[str, ...]]:
        """Return no news; this fixture exercises the OHLCV path only."""
        return {}

    def fetch_sentiment(self, tickers: tuple[str, ...]) -> dict[str, float]:
        """Return no sentiment; this fixture exercises the OHLCV path only."""
        return {}

    def fetch_sectors(self, tickers: tuple[str, ...]) -> dict[str, str]:
        """Return no sectors; this fixture exercises the OHLCV path only."""
        return {}

    def fetch_earnings(
        self, tickers: tuple[str, ...], window: Window
    ) -> dict[str, date]:
        """Return no earnings; this fixture exercises the OHLCV path only."""
        return {}


def bar(ticker: str, days_ago: int, close: float) -> OHLCVBar:
    """Build one deterministic OHLCV bar."""
    day = datetime.now(tz=UTC).date() - timedelta(days=days_ago)
    open_ = close * 0.99
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=open_,
        high=max(open_, close) + 1.0,
        low=min(open_, close) - 1.0,
        close=close,
        volume=1_000_000,
    )


def entry_bars() -> tuple[OHLCVBar, ...]:
    """Return scan/analyze/PM bars that approve one AAPL order.

    AAPL gets two in-window bars (older bar inside the scanner's 5-day lookback): below
    every indicator window (RSI-2 needs three closes), so the analyst degrades to
    neutral -> confidence 0.60, clearing the strict-``<`` regime floor. MSFT's older bar
    sits outside the scan window, so only AAPL survives as a candidate (one position).
    """
    return (
        bar("AAPL", 4, 100.0),
        bar("AAPL", 0, 116.0),
        bar("MSFT", 6, 100.0),
        bar("MSFT", 0, 110.0),
    )


def rebound_bars() -> tuple[OHLCVBar, ...]:
    """Return monitor bars that trip AAPL's stop."""
    return (bar("AAPL", 0, 100.0),)


def fixture_universe() -> FakeUniverse:
    """Return a two-name test universe."""
    return FakeUniverse({UNIVERSE: ("AAPL", "MSFT"), "empty": ()})


def trigger(run_id: str = "orchestration-test", universe: str = UNIVERSE) -> RunTrigger:
    """Build a dispatcher trigger for tests."""
    return RunTrigger(
        run_id=run_id,
        universe=universe,
        as_of=datetime.now(tz=UTC).date(),
    )


def source() -> ReboundingDataSource:
    """Build the successful-run source fixture."""
    return ReboundingDataSource(entry=entry_bars(), rebound=rebound_bars())


def node_count(graph: InMemoryGraphStore, label: str) -> int:
    """Return graph node count for one label."""
    return len(graph.list_nodes(label))


def patch_success_until(monkeypatch: pytest.MonkeyPatch, stop: str) -> None:
    """Patch dispatcher step functions to stop at one named stage."""
    monkeypatch.setattr("orchestration.dispatcher.step_scan", lambda *_args: object())
    monkeypatch.setattr(
        "orchestration.dispatcher.step_analyze",
        lambda *_args: None if stop == "analysis" else object(),
    )
    monkeypatch.setattr(
        "orchestration.dispatcher.step_evaluate",
        lambda *_args: None if stop == "orders" else _OrderFixture(),
    )
    monkeypatch.setattr(
        "orchestration.dispatcher.step_submit",
        lambda *_args: None if stop == "execution" else object(),
    )
    monkeypatch.setattr(
        "orchestration.dispatcher.step_check_positions",
        lambda *_args: None if stop == "monitor" else object(),
    )
    monkeypatch.setattr(
        "orchestration.dispatcher.step_report",
        lambda *_args: None if stop == "report" else _snapshot(),
    )
    monkeypatch.setattr(
        "orchestration.dispatcher.write_narratives",
        lambda *_args: stop != "narrative",
    )


class _OrderFixture:
    run_id = "pm-run"


def _snapshot() -> RunSnapshot:
    return RunSnapshot(
        run_id="pm-run",
        portfolio_metrics={},
        signal_metrics={},
        regime_attribution={},
        headline=Explanation(summary="ok"),
        provenance=Provenance(run_id="snapshot", source_agent="reporter"),
    )
