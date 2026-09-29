"""barrier_scorecard: report whether one model's barrier claims come true.

Agent: forecaster
Role: answer the barrier_scorecard capability from the forecaster's own ledger, its
      BarrierForecast claims and their BarrierSettlements: counts settled, void and
      open, then EXP-018's scores over the settled ones (FORE-OUT-08). Read-only and
      repeatable (FORE-IDM-05); never promotion-eligible (FORE-OUT-04); it reports
      and decides nothing (FORE-NEV-01/02).
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.forecaster.domain.barrier_settlement import OUTCOMES, VOID
from agents.forecaster.domain.barrier_skill import ScoredCase, ledger_scores
from agents.forecaster.settlement_store import model_ledger
from contracts.forecaster import BarrierScorecardRequest, Scorecard

if TYPE_CHECKING:
    from pydantic import BaseModel

    from kernel import GraphStore, Node


def barrier_scorecard(graph: GraphStore, request: BaseModel) -> Scorecard:
    """Score one model's ledger; never promotion-eligible."""
    req = BarrierScorecardRequest.model_validate(request)
    claims, settlements = model_ledger(graph, req.model_id)
    settled = sorted(
        (
            (str(node.props["as_of"]), key)
            for key, node in settlements.items()
            if node.props["outcome"] != VOID
        )
    )
    cases = [_case(claims[key], settlements[key]) for _as_of, key in settled]
    metrics: dict[str, float] = {
        "settled": float(len(cases)),
        "void": float(len(settlements) - len(cases)),
        "open": float(len(claims) - len(settlements)),
    }
    metrics.update(ledger_scores(cases))
    return Scorecard(
        model_id=req.model_id,
        metrics=metrics,
        sample_size=len(cases),
        fresh_as_of=datetime.now(tz=UTC),
        promotion_eligible=False,
    )


def _case(claim: Node, settlement: Node) -> ScoredCase:
    """A settled claim: what it declared, what happened, and its recorded Brier."""
    return ScoredCase(
        as_of=str(settlement.props["as_of"]),
        outcome=OUTCOMES.index(str(settlement.props["outcome"])),
        declared=(
            float(claim.props["p_stop_first"]),
            float(claim.props["p_target_first"]),
            float(claim.props["p_neither"]),
        ),
        brier=float(settlement.props["brier"]),
    )
