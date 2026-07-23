"""Held-ticker expansion for analyst scoring.

Agent: analyst
Role: build the analyst-only union of scanner survivors and open positions.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.scanner import Candidate, CandidateSet

if TYPE_CHECKING:
    from contracts.positions import OpenPosition


def scoring_universe(
    candidate_set: CandidateSet, held: tuple[OpenPosition, ...]
) -> CandidateSet:
    """Return scanner survivors plus synthetic held candidates in stable order."""
    seen = {candidate.ticker for candidate in candidate_set.candidates}
    additions = tuple(
        _held_candidate(position, rank)
        for rank, position in enumerate(held, start=len(seen) + 1)
        if position.ticker not in seen
    )
    if not additions:
        return candidate_set
    return candidate_set.model_copy(
        update={"candidates": (*candidate_set.candidates, *additions)}
    )


def _held_candidate(position: OpenPosition, rank: int) -> Candidate:
    return Candidate(
        ticker=position.ticker,
        rank=rank,
        score=0.0,
        survived_filters=("held_position",),
        metrics={"held_quantity": float(position.quantity)},
    )
