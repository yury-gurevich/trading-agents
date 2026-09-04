"""PM historical gate outcome graph-roundtrip regressions.

Agent: portfolio_manager
Role: prove historical gate reports validate after real GraphStore freezing.
External I/O: none.
"""

from __future__ import annotations

from types import MappingProxyType

import pytest
from pydantic import ValidationError

from contracts.portfolio_manager import GateOutcome, GateStatus, OrderIntentSet
from kernel import InMemoryGraphStore, Node
from orchestration.packs.trading_observatory_chain import pm


def test_legacy_passed_gate_round_tripped_through_graph_validates() -> None:
    """PM-NEV-09: graph-frozen legacy passed evidence keeps its passed state."""
    stored = _round_tripped_prop("gate", _legacy_gate(passed=True))

    assert isinstance(stored, MappingProxyType)
    assert GateOutcome.model_validate(stored).outcome is GateStatus.PASSED


def test_legacy_failed_gate_round_tripped_through_graph_validates() -> None:
    """PM-NEV-09: graph-frozen legacy failed evidence keeps its failed state."""
    stored = _round_tripped_prop("gate", _legacy_gate(passed=False))

    assert isinstance(stored, MappingProxyType)
    assert GateOutcome.model_validate(stored).outcome is GateStatus.FAILED


def test_shapeless_gate_round_tripped_through_graph_still_raises() -> None:
    """PM-NEV-09: unknown graph-frozen gate evidence cannot invent a state."""
    stored = _round_tripped_prop("gate", _legacy_gate(passed=None))

    with pytest.raises(ValidationError, match="outcome"):
        GateOutcome.model_validate(stored)


def test_current_outcome_round_tripped_through_graph_is_not_rewritten() -> None:
    """PM-NEV-09: graph-frozen current outcome remains authoritative."""
    stored = _round_tripped_prop(
        "gate",
        _legacy_gate(passed=True)
        | {"outcome": "not_evaluated", "detail": "missing_input=bars"},
    )

    outcome = GateOutcome.model_validate(stored)

    assert outcome.outcome is GateStatus.NOT_EVALUATED
    with pytest.raises(ValueError, match="was not evaluated"):
        _ = outcome.passed


def test_rejected_gate_report_round_tripped_through_graph_validates() -> None:
    """PM-NEV-09: nested graph-frozen historical gate_report state is read."""
    node = _pm_run(_legacy_order_set(_legacy_gate(passed=True)))[1]

    parsed = OrderIntentSet.model_validate(node.props["order_intent_set"])

    assert parsed.rejected[0].gate_report[0].outcome is GateStatus.PASSED


def test_pm_stage_view_renders_graph_frozen_historical_gate_report() -> None:
    """PM-NEV-09: the observatory PM reader renders historical gate_report."""
    graph, node = _pm_run(_legacy_order_set(_legacy_gate(passed=True)))

    stage = pm(graph, node)

    assert stage.name == "pm"
    assert stage.observed["evaluated"] == 1
    assert stage.outputs[0] == "approved=0  rejected=1"


def _round_tripped_prop(name: str, value: object) -> object:
    graph = InMemoryGraphStore()
    graph.merge_node("Fixture", "fixture", {name: value})
    node = graph.get_node("Fixture", "fixture")
    assert node is not None
    return node.props[name]


def _pm_run(payload: dict[str, object]) -> tuple[InMemoryGraphStore, Node]:
    graph = InMemoryGraphStore()
    graph.merge_node("PMRun", "pm-run-legacy", {"order_intent_set": payload})
    node = graph.get_node("PMRun", "pm-run-legacy")
    assert node is not None
    return graph, node


def _legacy_gate(*, passed: object) -> dict[str, object]:
    gate: dict[str, object] = {
        "name": "max_positions",
        "value": 10.0,
        "threshold": 10.0,
        "detail": "historical",
    }
    if passed is not None:
        gate["passed"] = passed
    return gate


def _legacy_order_set(gate: dict[str, object]) -> dict[str, object]:
    return {
        "run_id": "pm-run-legacy",
        "approved": [],
        "rejected": [
            {
                "ticker": "MSFT",
                "reason": "max_positions",
                "gate_report": [gate],
            }
        ],
        "explanation": {
            "summary": "No orders approved; 1 recommendations rejected.",
            "evidence_refs": ["portfolio_manager.risk"],
        },
        "provenance": {
            "run_id": "pm-run-legacy",
            "source_agent": "portfolio_manager",
            "graph_node_id": "PMRun:pm-run-legacy",
        },
    }
