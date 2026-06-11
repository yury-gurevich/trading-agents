"""Execution stage-gate test helpers.

Agent: execution
Role: provide stage-promotion fixtures without cross-agent imports.
External I/O: none.
"""

from __future__ import annotations

from typing import Any

from contracts.common import Provenance
from contracts.execution import PromoteStageRequest
from contracts.supervisor import DispatchResult, FlagRequest
from kernel import AgentMessage, InMemoryGraphStore


def promote_message(target_stage: str, *, confirmed: bool = False) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="execution",
        message_type="request",
        capability="promote_stage",
        payload=PromoteStageRequest(
            target_stage=target_stage,  # type: ignore[arg-type]
            reason="test promotion",
            confirmed=confirmed,
        ).model_dump(mode="json"),
    )


def seed_stage_snapshots(graph: InMemoryGraphStore, *, approval_rate: float) -> None:
    for index in range(10):
        graph.merge_node(
            "Snapshot",
            f"snapshot:stage-{index}",
            {"metrics": {"portfolio": {"approval_rate": approval_rate}}},
        )


def resolve_stage_flag(graph: InMemoryGraphStore, target_stage: str) -> None:
    graph.merge_node(
        "FlagResolution",
        f"resolution:flag:stage_promote:{target_stage}:info",
        {"subject_ref": f"stage_promote:{target_stage}", "severity": "info"},
    )


def flag_handler(graph: InMemoryGraphStore) -> Any:
    def handle(payload: dict[str, Any]) -> dict[str, Any]:
        request = FlagRequest.model_validate(payload)
        node = graph.merge_node(
            "Flag",
            f"flag:{request.subject_ref}:{request.severity}",
            {
                "subject_ref": request.subject_ref,
                "severity": request.severity,
                "reason": request.reason,
            },
        )
        return DispatchResult(
            accepted=True,
            provenance=Provenance(
                run_id=request.subject_ref,
                source_agent="supervisor",
                graph_node_id=f"Flag:{node.key}",
            ),
        ).model_dump(mode="json")

    return handle
