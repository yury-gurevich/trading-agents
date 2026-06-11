"""Researcher graph write path.

Agent: researcher
Role: write Experiment and ParamChange graph artifacts.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.researcher import ParameterChangeProposal
    from kernel import GraphStore


def write_proposal(graph: GraphStore, proposal: ParameterChangeProposal) -> None:
    """Write Experiment + ParamChange nodes; idempotent on proposal_id."""
    exp_node = graph.merge_node(
        "Experiment",
        f"experiment:{proposal.proposal_id}",
        {
            "proposal_id": proposal.proposal_id,
            "change_count": len(proposal.changes),
            "rationale_summary": proposal.rationale.summary,
            "created_at": datetime.now(tz=UTC).isoformat(),
        },
    )
    for change in proposal.changes:
        change_node = graph.merge_node(
            "ParamChange",
            f"param-change:{proposal.proposal_id}:{change.parameter}",
            {
                "proposal_id": proposal.proposal_id,
                "parameter": change.parameter,
                "current_value": change.current_value,
                "proposed_value": change.proposed_value,
                "evidence_window_days": change.evidence_window_days,
                "effect_summary": change.expected_effect.summary,
            },
        )
        graph.add_edge(exp_node, change_node, "PROPOSES")
