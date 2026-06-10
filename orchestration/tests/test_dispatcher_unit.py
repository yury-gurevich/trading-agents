"""Dispatcher unit tests.

Agent: orchestration
Role: verify graceful stops, step behavior, and dispatcher branch outcomes.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.broker import PaperBroker
from agents.provider.sources import FakeDataSource
from contracts.analyst import RecommendationSet
from contracts.common import Explanation, Provenance
from contracts.scanner import Candidate, CandidateSet, FilterTrace
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus
from orchestration import Dispatcher
from orchestration.dispatcher import _position_ids_for_run
from orchestration.steps import step_analyze
from orchestration.tests.helpers import fixture_universe, patch_success_until, trigger

if TYPE_CHECKING:
    import pytest


def test_execute_run_empty_universe_stops_without_crashing() -> None:
    graph = InMemoryGraphStore()
    result = Dispatcher(
        InProcessBus(),
        graph,
        source=FakeDataSource(),
        broker=PaperBroker(),
        universe_source=fixture_universe(),
    ).execute_run(trigger(universe="empty"))
    assert result.completed is False
    assert result.snapshot is None
    assert result.steps_completed == 0
    assert result.reason == "scan produced no candidates"


def test_execute_run_provider_fault_stops_and_records_fault() -> None:
    sink = CollectingFaultSink()
    result = Dispatcher(
        InProcessBus(sink=sink),
        InMemoryGraphStore(),
        source=FakeDataSource(fail_ohlcv=True),
        broker=PaperBroker(),
        universe_source=fixture_universe(),
        sink=sink,
    ).execute_run(trigger())
    assert result.completed is False
    assert result.reason == "scan produced no candidates"
    assert sink.faults


def test_step_analyze_empty_recommendations_returns_none() -> None:
    bus = InProcessBus()
    bus.register("analyst", "analyze", _empty_analysis)
    assert step_analyze(bus, _candidate_set()) is None
    assert step_analyze(bus, _candidate_set(empty=True)) is None


def test_dispatcher_default_bindings_construct_without_injected_ports() -> None:
    dispatcher = Dispatcher(InProcessBus(), InMemoryGraphStore())
    assert dispatcher.settings.universe == "sp500"


def test_dispatcher_stop_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = InMemoryGraphStore()
    dispatcher = Dispatcher(
        InProcessBus(),
        graph,
        source=FakeDataSource(),
        broker=PaperBroker(),
        universe_source=fixture_universe(),
    )
    patch_success_until(monkeypatch, "analysis")
    assert dispatcher.execute_run(trigger()).reason == (
        "analysis produced no recommendations"
    )
    patch_success_until(monkeypatch, "orders")
    assert (
        dispatcher.execute_run(trigger()).reason
        == "portfolio manager approved no orders"
    )
    patch_success_until(monkeypatch, "execution")
    assert (
        dispatcher.execute_run(trigger()).reason
        == "execution produced no submitted fills"
    )
    patch_success_until(monkeypatch, "monitor")
    assert (
        dispatcher.execute_run(trigger()).reason
        == "monitor produced no position decisions"
    )
    patch_success_until(monkeypatch, "report")
    assert dispatcher.execute_run(trigger()).reason == "reporter produced no snapshot"
    patch_success_until(monkeypatch, "narrative")
    assert (
        dispatcher.execute_run(trigger()).reason
        == "reporter produced no trade narratives"
    )
    assert _position_ids_for_run(graph, "missing") == ()


def test_dispatcher_uses_default_universe_for_blank_trigger() -> None:
    dispatcher = Dispatcher(
        InProcessBus(),
        InMemoryGraphStore(),
        source=FakeDataSource(),
        broker=PaperBroker(),
        universe_source=fixture_universe(),
    )
    result = dispatcher.execute_run(trigger(universe=""))
    assert result.reason == "scan produced no candidates"


def _empty_analysis(_payload: dict[str, object]) -> dict[str, object]:
    return RecommendationSet(
        run_id="analysis-empty",
        recommendations=(),
        rejections=(),
        explanation=Explanation(summary="empty"),
        provenance=Provenance(run_id="analysis-empty", source_agent="analyst"),
    ).model_dump(mode="json")


def _candidate_set(*, empty: bool = False) -> CandidateSet:
    return CandidateSet(
        run_id="scan",
        candidates=()
        if empty
        else (
            Candidate(
                ticker="AAPL",
                rank=1,
                score=0.1,
                survived_filters=("fixture",),
            ),
        ),
        filter_trace=FilterTrace(universe_size=1, evaluated=1),
        explanation=Explanation(summary="fixture"),
        provenance=Provenance(run_id="scan", source_agent="scanner"),
    )


def test_step_analyze_error_envelope_returns_none() -> None:
    bus = InProcessBus()
    response = step_analyze(bus, _candidate_set())
    assert response is None


def test_step_request_validation_fault_returns_none() -> None:
    bus = InProcessBus()
    bus.register(
        "analyst",
        "analyze",
        lambda _payload: AgentMessage(
            sender="x",
            recipient="x",
            message_type="response",
            capability="x",
            payload={},
        ).model_dump(mode="json"),
    )
    assert step_analyze(bus, _candidate_set()) is None
