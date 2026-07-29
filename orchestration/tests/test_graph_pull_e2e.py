"""End-to-end graph-pull cascade test.

Agent: orchestration
Role: prove the dispatcher's single RunRequest drives the whole pipeline by graph-pull
      — position_sync→provider→scanner→analyst→PM→execution→monitor→reporter — with
      each agent waking itself off its prerequisite gate and no direct agent-to-agent
      calls.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.paper_broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider import poll as provider_poll
from agents.provider.settings import ProviderSettings
from contracts.position_sync import POSITION_SYNC_PHASE, SNAPSHOT_LABEL
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.batch_trace import walk_chain
from orchestration.local_pipeline import cascade_once
from orchestration.start import all_passed, place_run_request, preflight
from orchestration.tests.helpers import node_count, source

_CHAIN = (
    "MarketData",
    "ScanRun",
    "AnalystRun",
    "PMRun",
    "ExecutionRun",
    "MonitorRun",
    "Snapshot",
)


def _provider(graph: InMemoryGraphStore) -> ProviderAgent:
    return ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source(),
        settings=ProviderSettings(max_staleness_days=7),
    )


def test_preflight_passes_with_wired_prerequisites() -> None:
    graph = InMemoryGraphStore()
    checks = preflight(graph, source=source(), tickers=("AAPL", "MSFT"))
    assert all_passed(checks)
    assert [c.name for c in checks] == [
        "graph reachable",
        "data source configured",
        "universe non-empty",
    ]


def test_trigger_then_cascade_builds_full_chain() -> None:
    graph = InMemoryGraphStore()
    agent = _provider(graph)
    # Gate: nothing is pending until the dispatcher places the RunRequest.
    assert provider_poll.find_pending(graph) == []

    place_run_request(graph, run_id="e2e", tickers=("AAPL", "MSFT"))
    assert len(provider_poll.find_pending(graph)) == 1

    results = cascade_once(graph, provider_agent=agent, broker=PaperBroker())

    # Every stage woke off its prerequisite gate and processed exactly one item.
    # The forecaster is the advisory side branch off the AnalystRun (FORE-TRG-01).
    assert {r.name: r.processed for r in results} == {
        "position_sync": 1,
        "provider": 1,
        "scanner": 1,
        "analyst": 1,
        "forecaster": 1,
        "portfolio_manager": 1,
        "execution": 1,
        "monitor": 1,
        "reporter": 1,
    }
    # The full provenance chain now exists in the graph.
    for label in (*_CHAIN[:-2], "Snapshot"):
        assert node_count(graph, label) == 1, label
    assert (
        sum(
            1
            for node in graph.list_nodes(SNAPSHOT_LABEL)
            if node.props["run_id"] == "e2e"
        )
        == 1
    )
    sync_markers = [
        node
        for node in graph.list_nodes("MonitorRun")
        if node.props.get("phase") == POSITION_SYNC_PHASE
    ]
    monitor_runs = [
        node
        for node in graph.list_nodes("MonitorRun")
        if node.props.get("phase") != POSITION_SYNC_PHASE
    ]
    assert len(sync_markers) == 1
    assert len(monitor_runs) == 1


def test_second_cascade_is_idempotent() -> None:
    graph = InMemoryGraphStore()
    agent = _provider(graph)
    place_run_request(graph, run_id="e2e", tickers=("AAPL", "MSFT"))
    cascade_once(graph, provider_agent=agent, broker=PaperBroker())

    again = cascade_once(graph, provider_agent=agent, broker=PaperBroker())

    # Nothing is pending on a second pass: every gate is already satisfied.
    assert all(r.processed == 0 for r in again)


def test_tail_monitor_still_adopts_this_run_fill() -> None:
    """MON-IDN-02 / EXEC-OUT-02: tail monitor keeps this run's fill in the book."""
    graph = InMemoryGraphStore()
    agent = _provider(graph)
    place_run_request(graph, run_id="tail", tickers=("AAPL", "MSFT"))

    cascade_once(graph, provider_agent=agent, broker=PaperBroker())

    pm_run = walk_chain(graph, "tail")["PMRun"]
    assert any(
        position.props.get("run_id") == pm_run.key
        for position in graph.list_nodes("Position")
    )


def test_downstream_gates_block_until_provider_runs() -> None:
    from agents.scanner import poll as scanner_poll

    graph = InMemoryGraphStore()
    agent = _provider(graph)
    place_run_request(graph, run_id="e2e", tickers=("AAPL", "MSFT"))

    # Before the provider ingests, the scanner's prerequisite gate is empty even
    # though a RunRequest exists — work only flows once the upstream node appears.
    assert scanner_poll.find_pending(graph) == []

    cascade_once(graph, provider_agent=agent, broker=PaperBroker())

    # After one cascade the gate has opened and closed: the MarketData was produced
    # and already scanned, so nothing is pending again.
    assert scanner_poll.find_pending(graph) == []
    assert node_count(graph, "MarketData") == 1
