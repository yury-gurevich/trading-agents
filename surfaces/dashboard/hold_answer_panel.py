"""Operator-facing dashboard actions for one active unanswered run hold.

Agent: surfaces
Role: expose only the two wired answers for a current dispatcher hold.
External I/O: reads the injected GraphStore.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from orchestration.fleet_readiness import is_active_run_hold

if TYPE_CHECKING:
    from kernel import GraphStore


def hold_answer_panel(graph: GraphStore) -> dict[str, object] | None:
    """Return buttons only while the latest hold is active and unanswered."""
    answered_run_ids = {
        node.props.get("run_id") for node in graph.list_nodes("RunHoldAnswer")
    }
    holds = [
        node
        for node in graph.list_nodes("RunHold")
        if is_active_run_hold(node)
        and "answered_with" not in node.props
        and node.props.get("run_id") not in answered_run_ids
    ]
    if not holds:
        return None
    hold = max(holds, key=lambda node: str(node.props.get("as_of", "")))
    run_id = hold.props.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        return None
    return {
        "run_id": run_id,
        "actions": [
            {"answer": "run_now", "label": "Run now"},
            {"answer": "skip_today", "label": "Skip today"},
        ],
    }
