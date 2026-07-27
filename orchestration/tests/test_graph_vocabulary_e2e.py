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

from agents.execution.paper_broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from kernel import InMemoryGraphStore, InProcessBus
from kernel.graph_guarded import GuardedGraphStore
from kernel.graph_vocabulary import Vocabulary, VocabularyError
from orchestration.local_pipeline import cascade_once
from orchestration.start import place_run_request
from orchestration.tests.helpers import source

_VOCABULARY = (
    Path(__file__).resolve().parents[1] / "packs" / "trading_graph_vocabulary.json"
)
_CHAIN = ("MarketData", "ScanRun", "AnalystRun", "PMRun", "ExecutionRun", "MonitorRun")


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

    for label in _CHAIN:
        assert len(inner.list_nodes(label)) == 1, label


def test_the_guard_can_actually_reject_a_write() -> None:
    """The gate must be able to fail, or passing proves nothing."""
    declaration = _declaration()
    declaration["labels"] = [x for x in _declared_labels() if x != "RunRequest"]
    graph = GuardedGraphStore(
        InMemoryGraphStore(), Vocabulary.from_mapping(declaration)
    )

    with pytest.raises(VocabularyError, match="undeclared node label 'RunRequest'"):
        place_run_request(graph, run_id="vocab", tickers=("AAPL",))


def test_declared_vocabulary_covers_every_label_the_cascade_writes() -> None:
    """The declaration is a superset of reality, not a stale hand-written list."""
    inner = InMemoryGraphStore()
    graph = GuardedGraphStore(inner, Vocabulary.from_mapping(_declaration()))

    _run(graph)

    declared = set(_declared_labels())
    written = {node.label for label in _CHAIN for node in inner.list_nodes(label)}
    assert written <= declared
