"""Run lineage determines the barrier history's window end (S266 / DL-287).

Agent: provider
Role: prove the as-of read, calendar length, no-lineage fallback, and loud
      refusal of a broken stored date before any fetch or history write.
External I/O: none (in-memory graph and counting fake source).
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from typing import TYPE_CHECKING
from unittest.mock import call, patch

import pytest

from agents.provider import barrier_window
from agents.provider.barrier_history import write_barrier_history
from agents.provider.barrier_window import run_as_of
from agents.provider.tests.barrier_history_helpers import (
    TODAY,
    analyst_run,
    bars,
    counting_source,
    provider_agent,
    read_history,
    rec,
)
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from datetime import tzinfo

    from kernel import Node

AS_OF = TODAY - timedelta(days=3)
FETCH_DAY = TODAY + timedelta(days=1)


class _NoClock(datetime):
    @classmethod
    def now(cls, tz: tzinfo | None = None) -> datetime:  # type: ignore[override]
        raise AssertionError("a run with an as-of must not read the window clock")


class _FetchClock(datetime):
    @classmethod
    def now(cls, tz: tzinfo | None = None) -> datetime:  # type: ignore[override]
        assert tz is UTC
        return datetime.combine(FETCH_DAY, time(0, 0, 30), tzinfo=UTC)


def _lineage(
    graph: InMemoryGraphStore,
    run: Node,
    props: dict[str, object],
    *,
    prefix: str = "source",
) -> Node:
    scan = graph.merge_node("ScanRun", f"{prefix}:scan", {})
    market = graph.merge_node("MarketData", f"{prefix}:market", props)
    graph.add_edge(scan, run, "ANALYZED_BY")
    graph.add_edge(scan, market, "DERIVED_FROM")
    return scan


def test_a_runs_barrier_history_ends_on_its_as_of_without_reading_the_clock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PROV-OUT-08 / PROV-TRG-05: B1, the run's end and 1,125 calendar days."""
    monkeypatch.setattr(barrier_window, "datetime", _NoClock)
    graph = InMemoryGraphStore()
    run = analyst_run(graph, rec("AAPL", "buy"))
    _lineage(graph, run, {"window_end": AS_OF.isoformat()})
    later_bars = bars("AAPL", 800)
    source = counting_source(later_bars)

    write_barrier_history(run, agent=provider_agent(graph, source))

    [(tickers, window)] = source.asks
    assert tickers == ("AAPL",)
    assert (window.end, (window.end - window.start).days) == (AS_OF, 1125)
    history = read_history(graph)
    assert history.window_end == AS_OF
    assert history.histories["AAPL"].bars[-1][0] == AS_OF.isoformat()
    assert history.histories["AAPL"].bar_count == 760
    assert later_bars[-1].bar_date == TODAY > AS_OF


def test_the_as_of_is_read_by_edge_never_by_key() -> None:
    """PROV-OUT-08: B2, each run reads its own end, including a resume clone."""
    graph = InMemoryGraphStore()
    first = analyst_run(graph, rec("AAPL", "buy"))
    second = analyst_run(graph, rec("AAPL", "buy"), key="new-analysis")
    scan = _lineage(
        graph, first, {"window_start": "2000-01-01", "window_end": AS_OF.isoformat()}
    )
    clone = _lineage(
        graph, second, {"window_end": TODAY.isoformat()}, prefix="resume-link:child"
    )
    decoy = graph.merge_node(
        "MarketData", "not-the-source", {"window_end": "1999-01-01"}
    )
    graph.add_edge(scan, decoy, "LINKED_FROM")
    with (
        patch.object(graph, "get_node", side_effect=AssertionError("no key lookup")),
        patch.object(graph, "list_nodes", side_effect=AssertionError("no listing")),
        patch.object(graph, "ancestors", wraps=graph.ancestors) as ancestors,
        patch.object(graph, "descendants", wraps=graph.descendants) as descendants,
    ):
        assert run_as_of(graph, first) == AS_OF
        assert run_as_of(graph, second) == TODAY
    assert ancestors.call_args_list == [
        call(first, max_depth=1, edge_types={"ANALYZED_BY"}),
        call(second, max_depth=1, edge_types={"ANALYZED_BY"}),
    ]
    assert descendants.call_args_list == [
        call(scan, max_depth=1, edge_types={"DERIVED_FROM"}),
        call(clone, max_depth=1, edge_types={"DERIVED_FROM"}),
    ]


@pytest.mark.parametrize("has_scan", [False, True], ids=["no-scan", "no-market"])
def test_a_run_with_no_market_data_is_served_today(
    monkeypatch: pytest.MonkeyPatch, has_scan: bool
) -> None:
    """PROV-OUT-08 / PROV-TRG-05: B3, either missing hop means no as-of."""
    monkeypatch.setattr(barrier_window, "datetime", _FetchClock)
    graph = InMemoryGraphStore()
    run = analyst_run(graph, rec("AAPL", "buy"))
    if has_scan:
        scan = graph.merge_node("ScanRun", "without-market", {})
        graph.add_edge(scan, run, "ANALYZED_BY")
    source = counting_source(bars("AAPL", 800))

    assert run_as_of(graph, run) is None
    write_barrier_history(run, agent=provider_agent(graph, source))

    [(_, window)] = source.asks
    assert window.end == FETCH_DAY
    assert read_history(graph).window_end == FETCH_DAY


@pytest.mark.parametrize(
    ("props", "error"),
    [({}, KeyError), ({"window_end": "not-a-date"}, ValueError)],
    ids=["absent", "not-a-date"],
)
def test_an_unreadable_window_end_fails_before_any_fetch(
    props: dict[str, object], error: type[Exception]
) -> None:
    """PROV-OUT-08: B4, a broken stored date raises before fetching or writing."""
    graph = InMemoryGraphStore()
    run = analyst_run(graph, rec("AAPL", "buy"))
    _lineage(graph, run, props)
    source = counting_source(bars("AAPL", 800))

    with pytest.raises(error):
        write_barrier_history(run, agent=provider_agent(graph, source))

    assert source.asks == []
    assert graph.list_nodes("BarrierHistory") == ()
