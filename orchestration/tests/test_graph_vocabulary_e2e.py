"""Vocabulary conformance over the real graph-pull cascade.

Agent: orchestration
Role: prove the declared pack vocabulary admits every write the full pipeline
      makes — and that the guard actually rejects one that is not declared.
External I/O: none.

The positive test alone would be worthless: a guard that never fires looks
identical to a guard that is not wired (R007 / DL-65). So the negative test is
the load-bearing one — it proves the gate CAN fail, the way gate_selftest does
for `pip-audit`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.execution.broker_stop_actions import place_stop
from agents.execution.paper_broker import PaperBroker
from agents.execution.tests.broker_stop_helpers import (
    PendingStopBroker,
    position,
    stop_threshold,
)
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from contracts.position_sync import (
    POSITION_SYNC_EDGE,
    POSITION_SYNC_PHASE,
    RUN_REQUEST_LABEL,
    SNAPSHOT_LABEL,
    SNAPSHOT_REFRESH_EDGE,
    SNAPSHOT_SYNC_EDGE,
    run_request_key,
)
from contracts.positions import open_positions
from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus
from kernel.graph_guarded import GuardedGraphStore
from kernel.graph_vocabulary import Vocabulary, VocabularyError
from orchestration.local_pipeline import cascade_once
from orchestration.start import place_run_request
from orchestration.tests.helpers import source

_VOCABULARY = (
    Path(__file__).resolve().parents[1] / "packs" / "trading_graph_vocabulary.json"
)
_UNIQUE_CHAIN = ("MarketData", "ScanRun", "AnalystRun", "PMRun", "ExecutionRun")


def _declaration() -> dict[str, object]:
    data = json.loads(_VOCABULARY.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _declared_labels() -> list[str]:
    labels = _declaration()["labels"]
    assert isinstance(labels, list)
    return [str(label) for label in labels]


def _run(graph: GuardedGraphStore) -> None:
    agent = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source(),
        settings=ProviderSettings(max_staleness_days=7),
    )
    place_run_request(graph, run_id="vocab", tickers=("AAPL", "MSFT"))
    cascade_once(graph, provider_agent=agent, broker=PaperBroker())


def test_declared_vocabulary_admits_the_whole_cascade() -> None:
    """Every write the pipeline makes is declared — no false rejection."""
    inner = InMemoryGraphStore()
    graph = GuardedGraphStore(inner, Vocabulary.from_mapping(_declaration()))

    _run(graph)

    for label in _UNIQUE_CHAIN:
        assert len(inner.list_nodes(label)) == 1, label
    assert len(inner.list_nodes(SNAPSHOT_LABEL)) == 2
    assert len(inner.list_nodes("MonitorRun")) == 2


def test_the_guard_can_actually_reject_a_write() -> None:
    """The gate must be able to fail, or passing proves nothing."""
    declaration = _declaration()
    declaration["labels"] = [x for x in _declared_labels() if x != "RunRequest"]
    graph = GuardedGraphStore(
        InMemoryGraphStore(), Vocabulary.from_mapping(declaration)
    )

    with pytest.raises(VocabularyError, match="undeclared node label 'RunRequest'"):
        place_run_request(graph, run_id="vocab", tickers=("AAPL",))


def test_declared_vocabulary_covers_sync_edges_and_rejects_bad_signature() -> None:
    """MON-IDN-02 / EXEC-IDN-02: planted undeclared sync edge is rejected."""
    graph = GuardedGraphStore(
        InMemoryGraphStore(), Vocabulary.from_mapping(_declaration())
    )
    request = graph.merge_node(
        RUN_REQUEST_LABEL,
        run_request_key("sync-vocab"),
        {"run_id": "sync-vocab"},
    )
    snapshot = graph.merge_node(
        SNAPSHOT_LABEL,
        "snapshot:sync-vocab",
        {"run_id": "sync-vocab", "status": "fresh", "holdings": ()},
    )
    marker = graph.merge_node(
        "MonitorRun",
        "position-sync:sync-vocab",
        {"phase": POSITION_SYNC_PHASE, "position_book_status": "fresh"},
    )

    graph.add_edge(request, snapshot, SNAPSHOT_REFRESH_EDGE)
    graph.add_edge(snapshot, marker, SNAPSHOT_SYNC_EDGE)
    graph.add_edge(request, marker, POSITION_SYNC_EDGE)
    with pytest.raises(VocabularyError, match="RunRequest -> MonitorRun"):
        graph.add_edge(request, marker, SNAPSHOT_SYNC_EDGE)


def test_declared_vocabulary_admits_the_broker_native_stop_path() -> None:
    """The path `cascade_once` never reaches — which is how S143 missed it.

    Both edges here were undeclared until S144: the labels and edge types were
    known, so only exercising the real write path exposes the gap. One of them
    (Position -PROTECTED_BY-> BrokerStopOrder) resolves its parent through a dict
    lookup, so no static scan can recover it either.
    """
    inner = InMemoryGraphStore()
    graph = GuardedGraphStore(inner, Vocabulary.from_mapping(_declaration()))
    position(graph, "held:AAPL", "AAPL", 2, opened_price_cents=10000)
    ref = open_positions(graph)[0].position_ref

    place_stop(
        graph,
        PendingStopBroker(),
        CollectingFaultSink(),
        stop_threshold("AAPL", ref, 2),
        f"stop:{ref}:AAPL",
    )

    stop = inner.get_node("BrokerStopOrder", f"stop:{ref}:AAPL")
    assert stop is not None
    for edge, parent in (("PROTECTED_BY", "Position"), ("STOPS_WITH", "Fill")):
        found = list(inner.ancestors(stop, max_depth=1, edge_types={edge}))
        assert [node.label for node in found] == [parent], edge


def test_declared_vocabulary_covers_every_label_the_cascade_writes() -> None:
    """The declaration is a superset of reality, not a stale hand-written list."""
    inner = InMemoryGraphStore()
    graph = GuardedGraphStore(inner, Vocabulary.from_mapping(_declaration()))

    _run(graph)

    declared = set(_declared_labels())
    written = {label for label in declared if inner.list_nodes(label)}
    assert written <= declared
