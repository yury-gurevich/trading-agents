"""Supervisor stage-dispatch tests.

Agent: supervisor
Role: verify stage intents bridge to execution through the message bus.
External I/O: none.
"""

from __future__ import annotations

from typing import Any

from agents.supervisor.domain.gate import dispatch_intent
from contracts.common import Provenance
from contracts.execution import PromoteStageRequest, PromoteStageResult
from contracts.operator import TypedIntent
from kernel import InMemoryGraphStore, InProcessBus


def test_stage_dispatch_requires_bus_and_valid_target() -> None:
    graph = InMemoryGraphStore()

    no_bus = dispatch_intent(graph, _intent({"stage": "broker_shadow"}), bus=None)
    invalid = dispatch_intent(graph, _intent({"stage": "bad"}), bus=InProcessBus())

    assert no_bus.accepted is False
    assert "bus context" in str(no_bus.rejection)
    assert invalid.accepted is False
    assert "invalid stage target" in str(invalid.rejection)


def test_stage_dispatch_reports_missing_execution_handler() -> None:
    result = dispatch_intent(
        InMemoryGraphStore(),
        _intent({"stage": "broker_shadow", "confirmed": "true"}),
        bus=InProcessBus(),
    )

    assert result.accepted is False
    assert "No handler registered" in str(result.rejection)


def test_stage_dispatch_maps_execution_refusal_and_acceptance() -> None:
    refused_bus = InProcessBus()
    accepted_bus = InProcessBus()
    refused_bus.register("execution", "promote_stage", _execution_handler(False))
    accepted_bus.register("execution", "promote_stage", _execution_handler(True))

    refused = dispatch_intent(
        InMemoryGraphStore(),
        _intent({"stage": "broker_shadow", "confirmed": "true"}),
        bus=refused_bus,
    )
    accepted = dispatch_intent(
        InMemoryGraphStore(),
        _intent({"target": "broker_shadow", "confirmed": "true"}),
        bus=accepted_bus,
    )

    assert refused.accepted is False
    assert refused.rejection == "need better evidence"
    assert accepted.accepted is True
    assert accepted.routed_to == "execution.promote_stage"
    assert accepted.provenance.graph_node_id == "StageTransition:stage:broker_shadow"


def _intent(parameters: dict[str, str]) -> TypedIntent:
    return TypedIntent(
        family="stage",
        parameters=parameters,
        requires_confirmation=True,
        provenance=Provenance(run_id="stage:broker_shadow", source_agent="operator"),
    )


def _execution_handler(accepted: bool) -> Any:
    def handle(payload: dict[str, Any]) -> dict[str, Any]:
        request = PromoteStageRequest.model_validate(payload)
        return PromoteStageResult(
            accepted=accepted,
            previous_stage="paper",
            current_stage=request.target_stage if accepted else "paper",
            reason="applied" if accepted else "need better evidence",
            provenance=Provenance(
                run_id="stage-promotion",
                source_agent="execution",
                graph_node_id=(
                    f"StageTransition:stage:{request.target_stage}"
                    if accepted
                    else None
                ),
            ),
        ).model_dump(mode="json")

    return handle
