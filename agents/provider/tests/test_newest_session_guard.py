"""The extreme-move guard judges each name's newest session only (S243 / DL-247).

Agent: provider
Role: prove a real extreme day in a name's history never drops it, from the scan
      universe or from the barrier history, while an extreme newest bar is still
      excluded by name; a lagging name is judged on its own newest session; a
      session of one move abstains; and the pooled z-score's sqrt(n-1) ceiling.
External I/O: none (a fake source; the graph is in memory).
"""

from __future__ import annotations

from datetime import timedelta

from agents.provider import ProviderAgent
from agents.provider.barrier_history import write_barrier_history
from agents.provider.domain.integrity import validate_bars
from agents.provider.ingest import ingest_once
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from agents.provider.tests.barrier_history_helpers import (
    analyst_run,
    counting_source,
    provider_agent,
    read_history,
    rec,
)
from agents.provider.tests.guard_fixture import NEWEST, TODAY, batch, names
from contracts.common import Window
from contracts.provider import MARKET_DATA_LABEL, MarketData, OHLCVBar
from kernel import InMemoryGraphStore, InProcessBus

_BARRIER_SESSIONS = 760
_INGEST_SESSIONS = 203
_UNIVERSE = 98  # + the named ticker = an S&P-100-sized batch


def _window(sessions: int) -> Window:
    return Window(start=TODAY - timedelta(days=sessions), end=TODAY)


def _delivered(
    tickers: tuple[str, ...], bars: tuple[OHLCVBar, ...], sessions: int
) -> set[str]:
    delivered, _quality = validate_bars(
        tickers, bars, _window(sessions), ProviderSettings()
    )
    return {bar.ticker for bar in delivered}


def test_a_real_old_extreme_day_keeps_the_name() -> None:
    """PROV-OUT-09 (B1): +17 % on session 100 of 760, ordinary since: the guard
    never re-judges a history day, so the name is delivered and not anomalous."""
    tickers = names(_UNIVERSE, "TXN")
    bars = batch(tickers, _BARRIER_SESSIONS, shocks={("TXN", 100): 0.17})

    delivered, quality = validate_bars(
        tickers, bars, _window(_BARRIER_SESSIONS), ProviderSettings()
    )

    assert "TXN" in {bar.ticker for bar in delivered}
    assert quality.anomalous_tickers == ()
    assert quality.returned == len(tickers)


def test_a_bad_newest_bar_is_still_dropped_by_name() -> None:
    """PROV-OUT-09 / PROV-FAIL-02 (B2): the same +17 % on the newest session is
    judged against that session's 99 moves, beyond 8 sigma: excluded, named."""
    tickers = names(_UNIVERSE, "TXN")
    bars = batch(tickers, _BARRIER_SESSIONS, shocks={("TXN", NEWEST): 0.17})

    delivered, quality = validate_bars(
        tickers, bars, _window(_BARRIER_SESSIONS), ProviderSettings()
    )

    assert quality.anomalous_tickers == ("TXN",)
    assert "TXN" not in {bar.ticker for bar in delivered}
    assert quality.returned == _UNIVERSE
    assert quality.used_fallback is False  # a per-name exclusion, never a taint


def test_the_daily_ingest_keeps_a_name_with_a_real_crash_mid_window() -> None:
    """PROV-OUT-09 / PROV-OUT-01 (B3): CHTR's -22.7 % (2026-04-24) mid-way through
    the ingest's 203 sessions: the MarketData the scanner reads carries CHTR."""
    tickers = names(_UNIVERSE, "CHTR")
    bars = batch(tickers, _INGEST_SESSIONS, shocks={("CHTR", 101): -0.227})
    agent = ProviderAgent(
        InProcessBus(),
        graph=InMemoryGraphStore(),
        source=FakeDataSource(bars=bars),
        settings=ProviderSettings(ingest_ohlcv_only=True),
    )

    ingest_once(agent, tickers, "s243", lookback_days=_INGEST_SESSIONS + 7)

    [node] = agent._graph.list_nodes(MARKET_DATA_LABEL)
    market = MarketData.model_validate(node.props["snapshot"])
    assert market.quality.anomalous_tickers == ()
    assert {bar.ticker for bar in market.bars} == set(tickers)
    assert sum(bar.ticker == "CHTR" for bar in market.bars) == _INGEST_SESSIONS


def test_a_real_history_day_never_drops_a_buy_from_its_barrier_history() -> None:
    """PROV-OUT-08 / PROV-OUT-09: TXN and COP's 2025-04-09 (+16.76 % / +12.82 %)
    inside 760 sessions of 14 buys: both keep their full history, none dropped."""
    tickers = names(12, "TXN", "COP")
    shocks = {("TXN", 100): 0.1676, ("COP", 100): 0.1282}
    graph = InMemoryGraphStore()
    run = analyst_run(graph, *(rec(ticker, "buy") for ticker in tickers))

    write_barrier_history(
        run,
        agent=provider_agent(
            graph, counting_source(batch(tickers, _BARRIER_SESSIONS, shocks=shocks))
        ),
    )

    history = read_history(graph)
    assert history.dropped == {}
    assert history.histories["TXN"].bar_count == _BARRIER_SESSIONS
    assert history.histories["COP"].bar_count == _BARRIER_SESSIONS


def test_a_lagging_ticker_is_judged_on_its_own_newest_session() -> None:
    """PROV-OUT-09 (B6, DL-247 D1): a name whose last bar is two sessions behind the
    batch's is judged on that bar against that session's cross-section: extreme,
    it is dropped by name; the same move on a current name's older bar is kept."""
    tickers = names(_UNIVERSE, "LAG", "CUR")
    shocks = {("LAG", 27): 0.17, ("CUR", 20): 0.17}
    bars = batch(tickers, 30, shocks=shocks, lag={"LAG": 2})

    delivered, quality = validate_bars(tickers, bars, _window(30), ProviderSettings())

    assert quality.anomalous_tickers == ("LAG",)
    assert quality.stale_tickers == ()  # two sessions behind is not stale (<= 3)
    assert "CUR" in {bar.ticker for bar in delivered}


def test_a_session_of_one_move_abstains() -> None:
    """PROV-OUT-09: a lone name has no cross-section to be extreme against, so even
    a +200 % newest bar is not judged (fewer than two moves abstains)."""
    tickers = ("AAPL",)
    bars = batch(tickers, 30, shocks={("AAPL", NEWEST): 2.0})

    assert _delivered(tickers, bars, 30) == {"AAPL"}


def test_a_session_of_65_names_or_fewer_cannot_pass_8_sigma() -> None:
    """PROV-OUT-09 (DRIFT-090): a population z over n moves never exceeds
    sqrt(n - 1), and the guard needs more than 8, so an absurd +500 % newest bar
    passes among 65 names and is dropped among 66. The barrier fetch's ~14 buys
    sit far below the ceiling."""
    for count, dropped in ((65, False), (66, True)):
        tickers = names(count - 1, "BAD")
        bars = batch(tickers, 5, shocks={("BAD", NEWEST): 5.0})

        assert ("BAD" not in _delivered(tickers, bars, 5)) is dropped
