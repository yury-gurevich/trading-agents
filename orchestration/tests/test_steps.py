"""Orchestration steps tests — P14 residual step helpers.

Agent: orchestration
Role: verify step_narrative and step_record_dispatch_run; including the error-envelope path.
External I/O: none.
"""

from __future__ import annotations

from contracts.common import Explanation, Provenance
from contracts.supervisor import DispatchRunRecord
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus
from orchestration.steps import step_narrative, step_record_dispatch_run


def _error_response(capability: str) -> dict[str, object]:
    return AgentMessage(
        sender="agent",
        recipient="dispatcher",
        message_type="error",
        capability=capability,
        payload={"message": "something went wrong"},
    ).model_dump(mode="json")


def test_step_narrative_error_response_returns_none() -> None:
    """Error envelope from reporter is captured → step returns None (covers steps.py:66)."""
    bus = InProcessBus()
    bus.register("reporter", "narrative", lambda _p: _error_response("narrative"))
    result = step_narrative(bus, "pos-id-1")
    assert result is None


def test_step_record_dispatch_run_succeeds() -> None:
    from agents.supervisor import SupervisorAgent

    bus = InProcessBus()
    graph = InMemoryGraphStore()
    SupervisorAgent(bus, graph=graph).bind()
    record = DispatchRunRecord(
        run_id="test-run-steps",
        steps_attempted=("run.trigger",),
        completed=True,
        faults=(),
    )
    result = step_record_dispatch_run(bus, record)
    assert result is not None


def test_step_narrative_no_handler_returns_none() -> None:
    bus = InProcessBus()
    result = step_narrative(bus, "pos-none", sink=CollectingFaultSink())
    assert result is None
