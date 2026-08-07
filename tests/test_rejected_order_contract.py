"""Rejected-order contract compatibility tests.

Agent: contracts (shared)
Role: verify additive rejected-order evidence keeps old payloads valid.
External I/O: none.
"""

from __future__ import annotations

from contracts.portfolio_manager import GateOutcome, OrderIntentSet


def test_rejected_order_gate_report_is_additive_for_historical_payloads() -> None:
    """PM-TYP-03 / PM-OBS-01: pre-S162 rejected orders without gate_report parse."""
    legacy_payload = {
        "run_id": "pm-run-legacy",
        "approved": [],
        "rejected": [{"ticker": "MSFT", "reason": "max_positions"}],
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
    outcome = GateOutcome(
        name="cash_available",
        value=100.0,
        threshold=0.0,
        passed=False,
        detail="fixture",
    )

    legacy = OrderIntentSet.model_validate(legacy_payload)
    current = legacy.model_copy(
        update={
            "rejected": (
                legacy.rejected[0].model_copy(update={"gate_report": (outcome,)}),
            )
        }
    )
    parsed = OrderIntentSet.model_validate(current.model_dump(mode="json"))

    assert legacy.rejected[0].gate_report == ()
    assert parsed.rejected[0].gate_report == (outcome,)
