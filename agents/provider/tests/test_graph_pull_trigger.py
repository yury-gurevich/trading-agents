"""A RunRequest on the graph is a request; an idle graph is none (S251 D4, DL-260).

Agent: provider
Role: drive the deployed work list and its dispatcher with no bus event at all, and
      show that a recorded RunRequest is ingested while an idle graph fetches nothing.
External I/O: none (in-memory graph, recording fixture source).
"""

from __future__ import annotations

from agents.provider.poll import INGESTED_EDGE, find_current_work, process_work_item
from agents.provider.tests.as_of_helpers import RecordingSource, agent_over, run_request
from contracts.provider import MARKET_DATA_LABEL, RUN_REQUEST_LABEL
from kernel import InMemoryGraphStore


def test_a_recorded_run_request_is_ingested_with_no_bus_event() -> None:
    """PROV-TRG-01 / PROV-TRG-02 (DRIFT-082): a RunRequest another stage wrote is a
    recorded data need, so the provider's own poll finds it and ingests it with no
    request event on any topic; once linked by INGESTED_BY it is never work again."""
    graph = InMemoryGraphStore()
    source = RecordingSource()
    agent = agent_over(graph, source)
    request = run_request(graph, "2026-09-30")

    work = find_current_work(graph)

    assert [(item.kind, item.node.key) for item in work] == [("ingest", request.key)]
    for item in work:
        process_work_item(item, agent=agent)
    market = graph.get_node(MARKET_DATA_LABEL, "market-data:r1")
    assert market is not None
    assert len(source.ohlcv_windows) == 1
    linked = graph.descendants(request, max_depth=1, edge_types={INGESTED_EDGE})
    assert [node.key for node in linked] == [market.key]
    assert find_current_work(graph) == []


def test_an_idle_graph_asks_the_feed_for_nothing() -> None:
    """PROV-TRG-02 / PROV-TRG-01: with no recorded need of any kind, polling finds
    no work however often it runs: zero external calls and zero records."""
    graph = InMemoryGraphStore()
    source = RecordingSource()
    agent_over(graph, source)

    polls = [find_current_work(graph) for _ in range(3)]

    assert polls == [[], [], []]
    assert source.calls == 0
    assert graph.list_nodes(MARKET_DATA_LABEL) == ()
    assert graph.list_nodes(RUN_REQUEST_LABEL) == ()
