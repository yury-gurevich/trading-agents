"""Supervisor intent gate.

Agent: supervisor
Role: enforce hard-NO, confirmation, and capability-matrix routing in order.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.supervisor.domain.hard_no import is_hard_no
from agents.supervisor.domain.matrix import CAPABILITY_MATRIX, not_available_reason
from agents.supervisor.result import provenance, rejected
from agents.supervisor.store import resolve_flag, write_flag, write_message
from contracts.supervisor import DispatchResult

if TYPE_CHECKING:
    from contracts.operator import TypedIntent
    from kernel import GraphStore


def dispatch_intent(graph: GraphStore, intent: TypedIntent) -> DispatchResult:
    """Gate one intent and return a routing hint without executing it."""
    blocked, reason = is_hard_no(intent)
    if blocked:
        return rejected(intent.provenance.run_id, reason)
    if _needs_confirmation(intent):
        write_flag(
            graph,
            subject_ref=intent.provenance.run_id,
            severity="warn",
            reason="awaiting confirmation",
        )
        return rejected(
            intent.provenance.run_id,
            "confirmation required - resubmit with confirmed=true",
        )
    if intent.parameters.get("confirmed") == "true":
        resolve_flag(graph, intent.provenance.run_id, "warn")
    spec = CAPABILITY_MATRIX[intent.family]
    if not spec.available:
        return rejected(intent.provenance.run_id, not_available_reason(intent.family))
    node = write_message(
        graph,
        run_id=intent.provenance.run_id,
        step_name=intent.family,
        status="dispatched",
    )
    return DispatchResult(
        accepted=True,
        routed_to=spec.routed_to,
        provenance=provenance(intent.provenance.run_id, "Message", node.key),
    )


def _needs_confirmation(intent: TypedIntent) -> bool:
    return intent.requires_confirmation and intent.parameters.get("confirmed") != "true"
