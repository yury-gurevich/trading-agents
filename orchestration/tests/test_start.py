"""System-start pre-flight + RunRequest trigger tests.

Agent: orchestration
Role: verify pre-flight reports prerequisites honestly and place_run_request writes the
      single trigger node the provider polls.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING, cast

from agents.analyst.history_requirements import required_history_bars
from agents.analyst.settings import AnalystSettings
from agents.provider.domain.market_calendar import trading_sessions_between
from agents.provider.settings import ProviderSettings
from contracts.provider import (
    RUN_REQUEST_LABEL,
    RUN_REQUEST_LOOKBACK_DAYS_PROP,
    RUN_REQUEST_REQUIRED_HISTORY_BARS_PROP,
)
from kernel import InMemoryGraphStore
from orchestration.start import all_passed, place_run_request, preflight

if TYPE_CHECKING:
    from kernel import GraphStore, Node


class _BrokenGraph:
    """A graph whose reads raise — stands in for an unreachable store."""

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        raise RuntimeError(f"store unreachable for {label}")


def test_preflight_all_pass() -> None:
    checks = preflight(InMemoryGraphStore(), source=object(), tickers=("AAPL", "MSFT"))
    assert all_passed(checks)


def test_preflight_flags_unreachable_graph() -> None:
    checks = preflight(
        cast("GraphStore", _BrokenGraph()), source=object(), tickers=("AAPL",)
    )
    graph_check = next(c for c in checks if c.name == "graph reachable")
    assert graph_check.ok is False
    assert "unreachable" in graph_check.detail
    assert not all_passed(checks)


def test_preflight_flags_missing_source_and_empty_universe() -> None:
    checks = preflight(InMemoryGraphStore(), source=None, tickers=())
    by_name = {c.name: c for c in checks}
    assert by_name["data source configured"].ok is False
    assert by_name["data source configured"].detail == "missing"
    assert by_name["universe non-empty"].ok is False
    assert not all_passed(checks)


def test_place_run_request_writes_trigger_node() -> None:
    """ANLZ-IDN-01: the run trigger carries enough history for declared indicators."""
    graph = InMemoryGraphStore()
    as_of = date(2026, 8, 11)
    place_run_request(graph, run_id="r1", tickers=("AAPL", "MSFT"), as_of=as_of)
    node = graph.get_node(RUN_REQUEST_LABEL, "run-request:r1")
    assert node is not None
    assert list(node.props["tickers"]) == ["AAPL", "MSFT"]
    assert node.props["run_id"] == "r1"
    lookback = int(node.props[RUN_REQUEST_LOOKBACK_DAYS_PROP])
    required_bars = required_history_bars(AnalystSettings())
    buffer_sessions = ProviderSettings().max_staleness_days
    start = as_of - timedelta(days=lookback)
    assert node.props[RUN_REQUEST_REQUIRED_HISTORY_BARS_PROP] == required_bars
    assert lookback > AnalystSettings().lookback_days
    assert (
        trading_sessions_between(start - timedelta(days=1), as_of)
        >= required_bars + buffer_sessions
    )
