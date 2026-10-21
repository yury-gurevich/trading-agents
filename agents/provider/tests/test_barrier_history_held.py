"""Sprint 286 A16-A17: one ordered history for buys and held names.

Agent: provider
Role: prove held names extend the batched fetch and trigger a no-buy history.
External I/O: none; fake feed and in-memory graph.
"""

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
from kernel import InMemoryGraphStore


def _hold(graph: InMemoryGraphStore, ticker: str, *, absent: bool = False) -> None:
    graph.merge_node(
        "Position",
        f"held-{ticker}",
        {"ticker": ticker, "quantity": 8, "status": "open", "broker_absent": absent},
    )


def test_the_history_holds_the_buys_then_each_held_name_once() -> None:
    """PROV-TRG-04 / PROV-OUT-08: buys first, then held, one fetch and no repeats."""
    graph = InMemoryGraphStore()
    run = analyst_run(graph, rec("AAPL", "buy"), rec("KO", "buy"), rec("XOM", "hold"))
    _hold(graph, "KO")
    _hold(graph, "COP")
    _hold(graph, "META", absent=True)
    source = counting_source(
        tuple(bar for ticker in ("AAPL", "KO", "COP") for bar in bars(ticker, 760))
    )

    write_barrier_history(run, agent=provider_agent(graph, source))

    [(requested, _window)] = source.asks
    assert requested == ("AAPL", "KO", "COP")
    history = read_history(graph)
    assert history.requested == ("AAPL", "KO", "COP")
    assert set(history.histories) == {"AAPL", "KO", "COP"}
    assert find_pending_barrier_history(graph) == []


def test_a_run_with_no_buy_gets_a_history_while_the_book_holds_a_name() -> None:
    """PROV-TRG-04: held COP triggers hold/sell history, never a bare run."""
    graph = InMemoryGraphStore()
    run = analyst_run(graph, rec("XOM", "hold"), rec("NVDA", "sell"))
    graph.merge_node("AnalystRun", "bare-run", {})
    assert find_pending_barrier_history(graph) == []

    _hold(graph, "COP")

    assert find_pending_barrier_history(graph) == [run]
