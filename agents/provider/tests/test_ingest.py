"""Tests for agents.provider.ingest — universe parsing, window, and ingest_once.

Agent: provider
Role: verify universe parsing, window calculation, and ingest_once graph writes.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from agents.provider import ProviderAgent
from agents.provider.ingest import (
    MARKET_FIELDS,
    _ingest_fields,
    _today_window,
    ingest_once,
    universe_from_env,
)
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.provider import (
    MARKET_DATA_LABEL,
    REGIME_CONTEXT_LABEL,
    MarketData,
    OHLCVBar,
)
from kernel import InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    import pytest


def _make_agent() -> ProviderAgent:
    return ProviderAgent(
        InProcessBus(),
        graph=InMemoryGraphStore(),
        source=FakeDataSource(),
    )


def test_universe_from_env_empty_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PROVIDER_UNIVERSE", raising=False)
    assert universe_from_env() == ()


def test_universe_from_env_parses_tickers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROVIDER_UNIVERSE", "aapl,msft,tsla")
    assert universe_from_env() == ("AAPL", "MSFT", "TSLA")


def test_universe_from_env_strips_whitespace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROVIDER_UNIVERSE", " AAPL , MSFT ")
    assert universe_from_env() == ("AAPL", "MSFT")


def test_universe_from_env_ignores_blank_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROVIDER_UNIVERSE", "AAPL,,MSFT,")
    assert universe_from_env() == ("AAPL", "MSFT")


def test_today_window_span_is_lookback_days() -> None:
    today = datetime.now(tz=UTC).date()
    window = _today_window(lookback_days=30)
    assert window.end == today
    assert window.start == today - timedelta(days=30)


def test_today_window_default_span() -> None:
    today = datetime.now(tz=UTC).date()
    window = _today_window()
    assert window.end == today
    assert window.start == today - timedelta(days=60)


def test_ingest_once_noop_on_empty_universe() -> None:
    agent = _make_agent()
    ingest_once(agent, ())
    assert agent._graph.list_nodes("MarketSnapshot") == ()


def test_ingest_once_writes_market_snapshot_to_graph() -> None:
    agent = _make_agent()
    ingest_once(agent, ("AAPL",))
    assert len(agent._graph.list_nodes("MarketSnapshot")) == 1


def test_ingest_once_writes_regime_to_graph() -> None:
    agent = _make_agent()
    ingest_once(agent, ("AAPL",))
    assert len(agent._graph.list_nodes("Regime")) == 1


def test_ingest_once_writes_full_market_data_node() -> None:
    agent = _make_agent()
    ingest_once(agent, ("AAPL",))
    nodes = agent._graph.list_nodes(MARKET_DATA_LABEL)
    assert len(nodes) == 1
    assert list(nodes[0].props["tickers"]) == ["AAPL"]
    assert "snapshot" in nodes[0].props
    assert "window_end" in nodes[0].props


def test_ingest_once_writes_full_regime_context_node() -> None:
    agent = _make_agent()
    ingest_once(agent, ("AAPL",))
    nodes = agent._graph.list_nodes(REGIME_CONTEXT_LABEL)
    assert len(nodes) == 1
    assert "snapshot" in nodes[0].props
    assert "window_end" in nodes[0].props


def test_ingest_fields_full_by_default_ohlcv_only_when_flagged() -> None:
    """DL-29: the fast-mode flag narrows the requested fields to OHLCV only."""
    assert _ingest_fields(ProviderSettings()) == MARKET_FIELDS
    assert _ingest_fields(ProviderSettings(ingest_ohlcv_only=True)) == ("ohlcv",)


def _recent_bars() -> tuple[OHLCVBar, ...]:
    today = datetime.now(tz=UTC).date()
    return tuple(
        OHLCVBar(
            ticker="AAPL",
            bar_date=today - timedelta(days=d),
            open=100.0,
            high=103.0,
            low=99.0,
            close=101.0 + d,
            volume=1000,
        )
        for d in (2, 0)
    )


def _enriching_source() -> FakeDataSource:
    return FakeDataSource(
        bars=_recent_bars(),
        sectors={"AAPL": "Tech"},
        fundamentals={"AAPL": {"pe": 1.0}},
    )


def _agent_with(source: FakeDataSource, settings: ProviderSettings) -> ProviderAgent:
    return ProviderAgent(
        InProcessBus(), graph=InMemoryGraphStore(), source=source, settings=settings
    )


def _snapshot(agent: ProviderAgent) -> MarketData:
    node = agent._graph.list_nodes(MARKET_DATA_LABEL)[0]
    return MarketData.model_validate(node.props["snapshot"])


def test_ingest_full_mode_populates_enrichment() -> None:
    """Baseline: the default ingest requests + persists the optional pillars."""
    agent = _agent_with(_enriching_source(), ProviderSettings())
    ingest_once(agent, ("AAPL",))
    market = _snapshot(agent)
    assert market.bars  # OHLCV delivered
    assert market.sectors == {"AAPL": "Tech"}
    assert market.fundamentals == {"AAPL": {"pe": 1.0}}


def test_ingest_ohlcv_only_skips_enrichment_keeps_bars() -> None:
    """DL-29: OHLCV-only ingest delivers bars but no enrichment, even when the
    source could provide it — the cost the acceptance gate doesn't need is not paid."""
    agent = _agent_with(_enriching_source(), ProviderSettings(ingest_ohlcv_only=True))
    ingest_once(agent, ("AAPL",))
    market = _snapshot(agent)
    assert market.bars  # OHLCV still delivered
    assert market.sectors == {}  # enrichment skipped
    assert market.fundamentals == {}
