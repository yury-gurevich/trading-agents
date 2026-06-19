"""Dispatcher unit tests — P14 trigger-emitter.

Agent: orchestration
Role: verify the dispatcher publishes run.trigger, collects report.snapshot.ready,
      and returns a RunResult; existing dispatch recording and fault behavior preserved.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.broker import PaperBroker
from agents.provider.sources import FakeDataSource
from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus
from orchestration import Dispatcher
from orchestration.tests.helpers import fixture_universe, source, trigger


def test_execute_run_happy_path_returns_completed_true() -> None:
    result = Dispatcher(
        InProcessBus(),
        InMemoryGraphStore(),
        source=source(),
        broker=PaperBroker(),
        universe_source=fixture_universe(),
    ).execute_run(trigger())
    assert result.completed is True
    assert result.snapshot is not None


def test_execute_run_empty_universe_chain_still_completes() -> None:
    """Pub/sub chain always runs end-to-end; no early stops in the dispatcher."""
    result = Dispatcher(
        InProcessBus(),
        InMemoryGraphStore(),
        source=FakeDataSource(),
        broker=PaperBroker(),
        universe_source=fixture_universe(),
    ).execute_run(trigger(universe="empty"))
    assert result.completed is True
    assert result.run_id == "orchestration-test"


def test_execute_run_provider_fault_recorded_to_sink() -> None:
    sink = CollectingFaultSink()
    Dispatcher(
        InProcessBus(sink=sink),
        InMemoryGraphStore(),
        source=FakeDataSource(fail_ohlcv=True),
        broker=PaperBroker(),
        universe_source=fixture_universe(),
        sink=sink,
    ).execute_run(trigger())
    assert sink.faults


def test_execute_run_publishes_run_trigger_event() -> None:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    events: list[dict[str, object]] = []
    bus.subscribe("run.trigger", events.append)
    Dispatcher(
        bus, graph, source=FakeDataSource(), broker=PaperBroker(),
        universe_source=fixture_universe(),
    ).execute_run(trigger(universe="empty"))
    assert len(events) == 1
    assert events[0]["run_id"] == "orchestration-test"
    assert events[0]["universe"] == "empty"


def test_dispatcher_default_bindings_construct_without_injected_ports() -> None:
    dispatcher = Dispatcher(InProcessBus(), InMemoryGraphStore())
    assert dispatcher.settings.universe == "sp500"


def test_execute_run_uses_default_universe_for_blank_trigger() -> None:
    result = Dispatcher(
        InProcessBus(),
        InMemoryGraphStore(),
        source=FakeDataSource(),
        broker=PaperBroker(),
        universe_source=fixture_universe(),
    ).execute_run(trigger(universe=""))
    assert result.completed is True


def test_execute_run_fault_in_trigger_returns_not_completed() -> None:
    """Handler exception → completed=False and fault captured (fault-path test)."""
    from datetime import UTC, datetime

    from orchestration.trigger import RunTrigger

    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()

    def _exploding_handler(_event: dict[str, object]) -> None:
        raise RuntimeError("simulated chain failure")

    # Subscribe BEFORE Dispatcher so our handler fires first, raising before agents run.
    bus.subscribe("run.trigger", _exploding_handler)
    dispatcher = Dispatcher(
        bus, graph, source=FakeDataSource(), sink=sink,
        universe_source=fixture_universe(),
    )
    t = RunTrigger(
        run_id="fault-test", universe="empty", as_of=datetime.now(tz=UTC).date()
    )

    result = dispatcher.execute_run(t)

    assert result.completed is False
    assert sink.faults
