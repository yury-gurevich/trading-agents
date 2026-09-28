"""Provider BarrierHistory work kind: which runs, one fetch, one node (S239 D10).

Agent: provider
Role: prove the provider writes one BarrierHistory per AnalystRun holding a buy with
      both barriers (never for sells, holds or a buy missing a target), from ONE
      batched fetch over a 1,125-day window, keeping <= 760 bars per ticker; that the
      node passes the pack's vocabulary guard; and that the loop carries both kinds.
External I/O: none (a fake source; the graph is in memory).
"""

from __future__ import annotations

import json

from agents.provider.barrier_history import (
    find_pending_barrier_history,
    write_barrier_history,
)
from agents.provider.poll import ProviderWorkItem, find_pending_work, process_work_item
from agents.provider.tests.barrier_history_helpers import (
    MIXED,
    PACK,
    TODAY,
    analyst_run,
    bars,
    counting_source,
    provider_agent,
    read_history,
    rec,
)
from contracts.barrier_history import BARRIER_HISTORY_EDGE
from kernel import InMemoryGraphStore
from kernel.graph_guarded import GuardedGraphStore
from kernel.graph_vocabulary import Vocabulary


def test_only_buys_with_both_barriers_get_a_history_from_one_fetch() -> None:
    """PROV-TRG-04 / PROV-OUT-08: one batched OHLCV request for exactly the buys
    with a stop and a target (not the sell, the hold, or the buy missing a target),
    over 1,125 calendar days ending today; one node, linked from the AnalystRun,
    holding the last 760 bars per ticker."""
    graph = InMemoryGraphStore()
    run = analyst_run(graph, *MIXED)
    everyone = tuple(
        b for t in ("AAPL", "MSFT", "NVDA", "AMZN", "GOOG") for b in bars(t, 800)
    )
    source = counting_source(everyone)

    assert find_pending_barrier_history(graph) == [run]
    write_barrier_history(run, agent=provider_agent(graph, source))

    [(tickers, window)] = source.asks
    assert tickers == ("AAPL", "GOOG")
    assert (window.end, (window.end - window.start).days) == (TODAY, 1125)
    history = read_history(graph)
    assert (history.status, history.reason, history.dropped) == ("ok", None, {})
    assert history.requested == ("AAPL", "GOOG")
    assert set(history.histories) == {"AAPL", "GOOG"}
    aapl = history.histories["AAPL"]
    assert aapl.bar_count == len(aapl.bars) == 760
    last = bars("AAPL", 800)[-1]
    assert aapl.bars[-1] == (
        last.bar_date.isoformat(),
        last.open,
        last.high,
        last.low,
        last.close,
    )
    assert history.sessions_requested == 760
    linked = list(
        graph.descendants(run, max_depth=1, edge_types={BARRIER_HISTORY_EDGE})
    )
    assert [node.label for node in linked] == ["BarrierHistory"]
    assert find_pending_barrier_history(graph) == []


def test_a_run_without_a_qualifying_buy_gets_no_history() -> None:
    """PROV-TRG-04: sells, holds, a buy missing its target, or no recommendation set
    at all ask the provider for nothing."""
    graph = InMemoryGraphStore()
    analyst_run(graph, *MIXED[1:4])
    graph.merge_node("AnalystRun", "ar-bare", {})

    assert find_pending_barrier_history(graph) == []


def test_the_history_passes_the_packs_vocabulary_guard() -> None:
    """PROV-IDN-03 / PROV-OUT-08: the label, its properties and the AnalystRun edge
    are declared in the trading pack, so the fail-closed guard admits the write."""
    pack = json.loads((PACK / "trading_graph_vocabulary.json").read_text("utf-8"))
    graph = GuardedGraphStore(InMemoryGraphStore(), Vocabulary.from_mapping(pack))
    run = analyst_run(graph, rec("AAPL", "buy"))

    write_barrier_history(
        run, agent=provider_agent(graph, counting_source(bars("AAPL", 800)))
    )

    assert read_history(graph).status == "ok"


def test_the_provider_loop_carries_both_work_kinds() -> None:
    """PROV-TRG-04: run ingests come before barrier histories in one work list, and
    each item is dispatched to its own handler."""
    graph = InMemoryGraphStore()
    run = analyst_run(graph, rec("AAPL", "buy"))
    graph.merge_node(
        "RunRequest",
        "run-1",
        {
            "run_id": "run-1",
            "tickers": ["AAPL"],
            "lookback_days": 400,
            "required_history_bars": 200,
        },
    )
    agent = provider_agent(graph, counting_source(bars("AAPL", 800)))

    items = find_pending_work(graph)
    assert [(item.kind, item.node.key) for item in items] == [
        ("ingest", "run-1"),
        ("barrier_history", run.key),
    ]
    for item in items:
        process_work_item(item, agent=agent)

    assert find_pending_work(graph) == []
    assert graph.list_nodes("MarketData")
    assert read_history(graph).status == "ok"
    assert isinstance(items[0], ProviderWorkItem)
