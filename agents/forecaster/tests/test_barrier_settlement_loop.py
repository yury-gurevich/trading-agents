"""S241 C8 / C9: the deployed loop settles on a current run, and nothing leaves.

Agent: forecaster
Role: prove the deployed work list (the forecast and the settlement pass per run)
      settles an older claim on a current AnalystRun and skips an old one (DL-241
      D11), that a full deployed pass writes nothing on the decision path and sends
      nothing to its agents, and that no module outside the forecaster reads the
      settlements or the scorecard.
External I/O: reads repo sources (the structural reader scan).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from agents.forecaster import ForecasterAgent
from agents.forecaster.barrier_fit import FakeGarchFitter
from agents.forecaster.poll import DEPLOYED_CAPABILITIES
from agents.forecaster.tests.barrier_helpers import (
    ACCEPTED,
    RecordingBus,
    barrier_bars,
    deployed_analyst_run,
    seed_history,
)
from agents.forecaster.tests.settlement_helpers import link_market, seed_claim, seed_run
from agents.forecaster.tests.settlement_paths import ohlcv, path
from agents.forecaster.work import find_pending_work, process_work_item
from contracts import execution, monitor, portfolio_manager
from kernel import CollectingFaultSink, InMemoryGraphStore

_ROOT = Path(__file__).resolve().parents[3]
_TARGET_PATH = path(events={2: (108.0, 99.0)})
#: The only shipped readers of the ledger: the forecaster and its read-only script.
_READERS = (
    "agents/forecaster/",
    "contracts/forecaster.py",
    "scripts/barrier_ledger.py",
)
_LEDGER_NAMES = ("BarrierSettlement", "barrier_scorecard", "SETTLED_BY")


def _wire(graph: InMemoryGraphStore) -> tuple[RecordingBus, CollectingFaultSink]:
    bus = RecordingBus()
    sink = CollectingFaultSink()
    ForecasterAgent(
        bus, graph=graph, sink=sink, barrier_fitter=FakeGarchFitter(ACCEPTED)
    ).bind()
    return bus, sink


def test_the_deployed_loop_settles_on_a_current_run_only() -> None:
    """FORE-TRG-01 (DL-241 D11): a current run's work is its forecast and its
    settlement pass, which settles an older claim from that run's bars; an old run
    whose bars also cover the claim gets no work at all."""
    graph = InMemoryGraphStore()
    seed_claim(graph)
    now = datetime.now(tz=UTC)
    bars = ohlcv("AAPL", _TARGET_PATH)
    seed_run(graph, "run-current", bars=bars, created=now)
    seed_run(graph, "run-old", bars=bars, created=now - timedelta(days=2))
    bus, sink = _wire(graph)

    items = find_pending_work(graph, now=now)
    for item in items:
        process_work_item(
            item, graph=graph, bus=bus, capabilities=DEPLOYED_CAPABILITIES, sink=sink
        )

    assert [(item.kind, item.node.key) for item in items] == [
        ("forecast", "run-current"),
        ("settle", "run-current"),
    ]
    [settlement] = graph.list_nodes("BarrierSettlement")
    assert settlement.props["settling_ref"] == "market-data:run-current"
    assert settlement.props["outcome"] == "target"
    assert [node.key for node in graph.list_nodes("BarrierSettlementPass")] == [
        "settlement-pass:run-current"
    ]
    assert find_pending_work(graph, now=now) == []
    assert sink.faults == []


def test_a_full_deployed_pass_never_reaches_the_decision_path() -> None:
    """FORE-NEV-01 / FORE-NEV-02: the deployed work for a current run with two buys
    (two claims) whose bars settle an older claim writes claims, one settlement and
    the run's markers only: no PM, execution or monitor label, and no message to
    any agent but the forecaster."""
    graph = InMemoryGraphStore()
    run = deployed_analyst_run(graph)
    seed_history(
        graph, barrier_bars("AAPL", 760) + barrier_bars("GOOG", 760), run_key=run.key
    )
    seed_claim(graph, ticker="MSFT")
    link_market(graph, run, ohlcv("MSFT", _TARGET_PATH))
    bus, sink = _wire(graph)

    for item in find_pending_work(graph, now=datetime.now(tz=UTC)):
        process_work_item(
            item, graph=graph, bus=bus, capabilities=DEPLOYED_CAPABILITIES, sink=sink
        )

    assert len(graph.list_nodes("BarrierForecast")) == 3
    assert len(graph.list_nodes("BarrierSettlement")) == 1
    decision_labels = {
        *portfolio_manager.CONTRACT.owns_graph,
        *execution.CONTRACT.owns_graph,
        *monitor.CONTRACT.owns_graph,
    }
    assert decision_labels
    assert {
        label: graph.list_nodes(label) for label in decision_labels
    } == dict.fromkeys(decision_labels, ())
    assert {message.recipient for message in bus.requests} == {"forecaster"}
    assert sink.faults == []


def test_nothing_outside_the_forecaster_reads_the_ledger() -> None:
    """FORE-NEV-01 / FORE-NEV-02: no shipped module outside the forecaster (and its
    read-only ledger script) names the settlement label, its edge or the scorecard,
    so nothing on the decision path can read them."""
    offenders = [
        relative
        for package in (
            "agents",
            "contracts",
            "kernel",
            "orchestration",
            "surfaces",
            "scripts",
        )
        for source in sorted((_ROOT / package).rglob("*.py"))
        if "tests" not in source.parts
        and not (relative := source.relative_to(_ROOT).as_posix()).startswith(_READERS)
        and any(name in source.read_text(encoding="utf-8") for name in _LEDGER_NAMES)
    ]

    assert offenders == []
