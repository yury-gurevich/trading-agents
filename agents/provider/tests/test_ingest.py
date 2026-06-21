"""Tests for agents.provider.ingest — universe parsing, window, and ingest_once.

Agent: provider
Role: verify universe parsing, window calculation, and ingest_once graph writes.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from agents.provider import ProviderAgent
from agents.provider.ingest import _today_window, ingest_once, universe_from_env
from agents.provider.sources import FakeDataSource
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
