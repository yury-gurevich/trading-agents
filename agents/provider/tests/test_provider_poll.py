"""Provider graph-poll find_pending + ingest_run_node tests.

Agent: provider
Role: verify the provider finds uningested RunRequest nodes, ingests their universe,
      and links the MarketData back so the request is not re-ingested.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.provider import ProviderAgent
from agents.provider.poll import find_pending, ingest_run_node
from agents.provider.sources import FakeDataSource
from contracts.provider import MARKET_DATA_LABEL, RUN_REQUEST_LABEL
from kernel import InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from kernel import Node


def _agent(graph: InMemoryGraphStore) -> ProviderAgent:
    return ProviderAgent(InProcessBus(), graph=graph, source=FakeDataSource())


def _run_request(graph: InMemoryGraphStore, tickers: tuple[str, ...]) -> Node:
    return graph.merge_node(
        RUN_REQUEST_LABEL, "run-request:r1", {"run_id": "r1", "tickers": list(tickers)}
    )


def test_find_pending_returns_uningested_run_request() -> None:
    graph = InMemoryGraphStore()
    _run_request(graph, ("AAPL",))
    assert len(find_pending(graph)) == 1


def test_find_pending_empty_when_no_run_request() -> None:
    assert find_pending(InMemoryGraphStore()) == []


def test_ingest_run_node_writes_market_data_and_marks_processed() -> None:
    graph = InMemoryGraphStore()
    agent = _agent(graph)
    node = _run_request(graph, ("AAPL",))
    ingest_run_node(node, agent=agent)
    assert len(graph.list_nodes(MARKET_DATA_LABEL)) == 1
    assert find_pending(graph) == []
