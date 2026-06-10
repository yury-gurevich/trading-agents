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
        """Return matching bars from the current fixture phase."""
        self.calls += 1
        rows = self.rebound if self.calls > self.rebound_after_calls else self.entry
        ticker_set = set(tickers)
        return tuple(
            bar
            for bar in rows
            if bar.ticker in ticker_set and window.start <= bar.bar_date <= window.end
        )

    def fetch_regime_inputs(self, as_of: date) -> RegimeInputs:
        """Return deterministic regime inputs."""
        return RegimeInputs(as_of=as_of, vix=self.vix)


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
    """Return scan/analyze/PM bars that approve one AAPL order."""
    return (
        bar("AAPL", 6, 100.0),
        bar("AAPL", 4, 104.0),
        bar("AAPL", 2, 108.0),
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
    return sum(1 for node_label, _key in graph._nodes if node_label == label)


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
        "orchestration.dispatcher.step_narrative",
        lambda *_args: None if stop == "narrative" else object(),
    )
    if stop == "narrative":
        monkeypatch.setattr(
            "orchestration.dispatcher._position_ids_for_run",
            lambda *_args: ("pm-run:AAPL",),
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
