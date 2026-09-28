"""Provider BarrierHistory work kind: failures and drops are written, not hidden.

Agent: provider
Role: prove a failed fetch or an error in the fetch path still writes a failed
      BarrierHistory (so no reader waits forever), and a dropped ticker carries its
      named reason while a stale one keeps its bars (S239 / DL-241 D10).
External I/O: none (a fake source; the graph is in memory).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.provider import ProviderAgent
from agents.provider.barrier_history import (
    find_pending_barrier_history,
    write_barrier_history,
)
from agents.provider.tests.barrier_history_helpers import (
    analyst_run,
    bars,
    counting_source,
    provider_agent,
    read_history,
    rec,
)
from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    import pytest


def test_a_failed_fetch_still_writes_a_failed_node() -> None:
    """PROV-OUT-08 / PROV-FAIL-01: the source failing writes the node with status
    failed and the reason, every ticker listed, so no reader waits forever."""
    graph = InMemoryGraphStore()
    run = analyst_run(graph, rec("AAPL", "buy"))

    write_barrier_history(
        run, agent=provider_agent(graph, counting_source((), fail=True))
    )

    history = read_history(graph)
    assert (history.status, history.reason) == ("failed", "source_unavailable")
    assert history.histories == {}
    assert history.dropped == {"AAPL": "fetch failed: source_unavailable"}
    assert find_pending_barrier_history(graph) == []


def test_an_exception_in_the_fetch_path_still_writes_a_failed_node(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PROV-OUT-08 / PROV-FAIL-01: an error past the source boundary is captured as a
    fault and recorded as the failed node's reason."""
    graph = InMemoryGraphStore()
    run = analyst_run(graph, rec("AAPL", "buy"))
    sink = CollectingFaultSink()
    agent = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=counting_source(bars("AAPL", 800)),
        sink=sink,
    )

    def _boom(request: object) -> object:
        raise RuntimeError("validation exploded")

    monkeypatch.setattr(agent, "_get_market_data", _boom)
    write_barrier_history(run, agent=agent)

    history = read_history(graph)
    assert (history.status, history.reason) == (
        "failed",
        "RuntimeError: validation exploded",
    )
    assert [fault.capability for fault in sink.faults] == ["barrier_history"]


def test_a_dropped_ticker_carries_its_named_reason() -> None:
    """PROV-OUT-08 / PROV-FAIL-02: the unchanged 8-sigma guard's exclusion and a
    ticker the source served nothing for are each listed with a reason; a served
    but stale ticker keeps its bars and is marked stale."""
    graph = InMemoryGraphStore()
    run = analyst_run(
        graph,
        rec("AAPL", "buy"),
        rec("TSLA", "buy"),
        rec("GME", "buy"),
        rec("IBM", "buy"),
    )
    spike = bars("TSLA", 800)
    jump = spike[400].model_copy(
        update={"close": spike[400].open * 1.6, "high": spike[400].open * 1.6}
    )
    served = (
        *bars("AAPL", 800),
        *spike[:400],
        jump,
        *spike[401:],
        *bars("IBM", 800, end_days_ago=20),
    )

    write_barrier_history(run, agent=provider_agent(graph, counting_source(served)))

    history = read_history(graph)
    assert history.status == "ok"
    assert set(history.histories) == {"AAPL", "IBM"}
    assert history.dropped["TSLA"].startswith("extreme_move_guard")
    assert history.dropped["GME"] == "no_bars_returned: stale_or_missing"
    assert history.stale == ("IBM",)
