"""Proposal builder for bounded parameter-change recommendations.

Agent: researcher
Role: apply evidence-window and forbidden-combination rules to proposal payloads.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.common import Explanation, Provenance
from contracts.researcher import ParameterChangeProposal, ProposedChange

if TYPE_CHECKING:
    from agents.researcher.domain.evidence import RunEvidence
    from agents.researcher.settings import ResearcherSettings

PARAMETER = "analyst.confidence_floor"


def build_proposal(
    evidence: RunEvidence,
    settings: ResearcherSettings,
    proposal_id: str,
) -> ParameterChangeProposal:
    """Build a proposal from evidence, or a zero-change proposal when unwarranted."""
    window_days = settings.lookback_days
    if window_days < settings.min_evidence_window_days:
        return _zero(proposal_id, f"evidence window is too short: {window_days} days")
    current = settings.confidence_floor_reference
    if evidence.avg_confidence < settings.confidence_low_water:
        direction = "raise"
        proposed = min(current + settings.confidence_step, 1.0)
    elif evidence.avg_confidence > settings.confidence_high_water:
        direction = "lower"
        proposed = max(current - settings.confidence_step, 0.0)
    else:
        return _zero(proposal_id, "evidence does not yet warrant a change")
    if proposed == current:
        return _zero(proposal_id, "confidence floor is already at its safe bound")
    changes = (
        ProposedChange(
            parameter=PARAMETER,
            current_value=current,
            proposed_value=proposed,
            evidence_window_days=window_days,
            expected_effect=Explanation(summary=_effect(evidence, direction)),
        ),
    )
    if len(changes) > settings.max_changes_per_proposal:  # pragma: no cover
        return _zero(proposal_id, "proposal exceeds max changes per review")
    return ParameterChangeProposal(
        proposal_id=proposal_id,
        changes=changes,
        rationale=Explanation(summary=_rationale(evidence, direction)),
        provenance=Provenance(run_id=proposal_id, source_agent="researcher"),
    )


def _zero(proposal_id: str, reason: str) -> ParameterChangeProposal:
    return ParameterChangeProposal(
        proposal_id=proposal_id,
        changes=(),
        rationale=Explanation(summary=reason),
        provenance=Provenance(run_id=proposal_id, source_agent="researcher"),
    )


def _rationale(evidence: RunEvidence, direction: str) -> str:
    return (
        f"avg_confidence={evidence.avg_confidence:.2f} over "
        f"{evidence.snapshot_count} snapshots; propose to {direction} confidence floor"
    )


def _effect(evidence: RunEvidence, direction: str) -> str:
    if direction == "raise":
        return f"Fewer weak signals; avg confidence is {evidence.avg_confidence:.2f}."
    return f"Broader candidate flow; avg confidence is {evidence.avg_confidence:.2f}."
