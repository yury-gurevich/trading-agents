"""barrier_scorecard: report whether one model's barrier claims come true.

Agent: forecaster
Role: answer the barrier_scorecard capability from the forecaster's own ledger, its
      BarrierForecast claims and their BarrierSettlements: counts settled, void and
      open, then EXP-018's scores over the settled ones (FORE-OUT-08): buys' claims
      under the names S241 gave them, held names' claims apart under ``held_``
      once the ledger holds one (DL-310), each against the same climatology; and,
      once a settled claim stated its return, the return scores (DL-312).
      Read-only and
      repeatable (FORE-IDM-05); never promotion-eligible (FORE-OUT-04); it reports
      and decides nothing (FORE-NEV-01/02).
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.forecaster.domain.barrier_return_scores import ReturnCase, return_scores
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
    held = {key for key, node in claims.items() if _held(node)}
    buys = {key: node for key, node in claims.items() if key not in held}
    metrics, sample_size = _scores(buys, settlements, "")
    if held:
        held_claims = {key: claims[key] for key in held}
        metrics.update(_scores(held_claims, settlements, "held_")[0])
    return Scorecard(
        model_id=req.model_id,
        metrics=metrics,
        sample_size=sample_size,
        fresh_as_of=datetime.now(tz=UTC),
        promotion_eligible=False,
    )


def _held(claim: Node) -> bool:
    return claim.props.get("subject_kind") == "position"


def _scores(
    claims: dict[str, Node], settlements: dict[str, Node], prefix: str
) -> tuple[dict[str, float], int]:
    """Counts and scores over ``claims``, names prefixed; and the settled count."""
    mine = {key: node for key, node in settlements.items() if key in claims}
    settled = sorted(
        (str(node.props["as_of"]), key)
        for key, node in mine.items()
        if node.props["outcome"] != VOID
    )
    cases = [_case(claims[key], mine[key]) for _as_of, key in settled]
    metrics: dict[str, float] = {
        "settled": float(len(cases)),
        "void": float(len(mine) - len(cases)),
        "open": float(len(claims) - len(mine)),
    }
    metrics.update(ledger_scores(cases))
    returns = [_return_case(claims[key], mine[key]) for _as_of, key in settled]
    metrics.update(return_scores([case for case in returns if case is not None]))
    return {f"{prefix}{name}": value for name, value in metrics.items()}, len(cases)


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


def _return_case(claim: Node, settlement: Node) -> ReturnCase | None:
    """A settled claim's return figures, or None when it stated none.

    A claim stated before its figures existed, or settled before the settlement
    recorded a realised return, has nothing to score.
    """
    declared = claim.props.get("expected_return")
    realised = settlement.props.get("realised_return")
    if declared is None or realised is None:
        return None
    return ReturnCase(
        as_of=str(settlement.props["as_of"]),
        declared=float(declared),
        realised=float(realised),
        close_p05=float(claim.props["close_return_p05"]),
        close_return=float(settlement.props["close_return"]),
    )
