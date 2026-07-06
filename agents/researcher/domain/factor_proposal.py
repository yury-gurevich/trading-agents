"""Proposal builder for governed factor recommendations.

Agent: researcher
Role: package bounded factor selections with deterministic backtest evidence.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.common import Explanation, Provenance
from contracts.researcher import BacktestEvidence, FactorProposal, ProposedFactor

if TYPE_CHECKING:
    from agents.researcher.domain.factors import FactorSelection


def build_factor_proposal(
    selection: FactorSelection,
    evidence: BacktestEvidence,
    provenance: Provenance,
    proposal_id: str,
) -> FactorProposal:
    """Build the human-review payload; the researcher never applies it."""
    return FactorProposal(
        proposal_id=proposal_id,
        factor=ProposedFactor(
            name=selection.name,
            params=selection.params,
            rationale=Explanation(summary=selection.rationale),
        ),
        provenance=provenance,
        backtest=evidence,
    )
