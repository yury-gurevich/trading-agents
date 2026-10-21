"""BarrierForecast write path: one append-only claim per model, ticker and last bar.

Agent: forecaster
Role: persist a barrier claim with every field its later settlement reads, keyed
      so a rerun on the same last bar merges into the same node (DL-241 D2/D5); a
      held name's claim is keyed apart from a buy's and says which stop and target
      it stood on (DL-310).
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.forecaster.domain.barrier_garch import (
    BARRIER_MODEL_ID,
    BARRIER_MODEL_VERSION,
    HORIZON_SESSIONS,
)

if TYPE_CHECKING:
    from datetime import date

    from agents.forecaster.domain.barrier_garch import GarchParams
    from agents.forecaster.held_claim import HeldBarriers
    from kernel import GraphStore, Node

BARRIER_LABEL = "BarrierForecast"
#: The key segment and ``subject_kind`` of a held name's claim.
HELD_KEY_SEGMENT = "held"


@dataclass(frozen=True)
class BarrierClaim:
    """One stated claim: the barriers, what the model said, and what it stood on."""

    ticker: str
    as_of: date
    entry_close: float
    stop_pct: float
    target_pct: float
    probabilities: tuple[float, float, float]
    params: GarchParams
    history_bars: int
    n_paths: int
    seed: int
    history_ref: str
    """The provider's BarrierHistory key the bars were read from (DL-241 D10)."""
    sessions_requested: int
    held: HeldBarriers | None = None
    """A held name's stop and target, and where they came from; None for a buy."""

    @property
    def key(self) -> str:
        """``{model_id}:{ticker}:{as_of}``, or ``{model_id}:held:{ticker}:{as_of}``."""
        subject = "" if self.held is None else f"{HELD_KEY_SEGMENT}:"
        return f"{BARRIER_MODEL_ID}:{subject}{self.ticker}:{self.as_of.isoformat()}"


def write_claim(graph: GraphStore, claim: BarrierClaim) -> Node:
    """Merge the claim; a rerun keeps the first ``created_at`` and ``history_ref``.

    The graph refuses to overwrite a property, so a rerun stating the same claim
    merges into the same node, and one stating a different claim raises: the
    first claim stands (FORE-IDM-04).
    """
    p_stop, p_target, p_neither = claim.probabilities
    props: dict[str, object] = {
        "ticker": claim.ticker,
        "as_of": claim.as_of.isoformat(),
        "entry_close": claim.entry_close,
        "horizon_sessions": HORIZON_SESSIONS,
        "stop_pct": claim.stop_pct,
        "target_pct": claim.target_pct,
        "p_stop_first": p_stop,
        "p_target_first": p_target,
        "p_neither": p_neither,
        "model_id": BARRIER_MODEL_ID,
        "model_version": BARRIER_MODEL_VERSION,
        "history_bars": claim.history_bars,
        "n_paths": claim.n_paths,
        "seed": claim.seed,
        "history_ref": claim.history_ref,
        "fit_status": claim.params.status,
        "garch_mu": claim.params.mu,
        "garch_omega": claim.params.omega,
        "garch_alpha": claim.params.alpha,
        "garch_beta": claim.params.beta,
        "created_at": datetime.now(tz=UTC).isoformat(),
        "shadow": True,
    }
    if claim.held is not None:
        props.update(
            {
                "subject_kind": "position",
                "target_basis": claim.held.basis,
                "stop_price": claim.held.prices.stop_price,
                "target_price": claim.held.prices.target_price,
                "declared_target_pct": claim.held.prices.target_pct,
            }
        )
    existing = graph.get_node(BARRIER_LABEL, claim.key)
    if existing is not None:
        # A rerun on the same last bar (a resumed run) keeps where and when the claim
        # was first stated; every other field must agree, or the merge refuses it.
        props["created_at"] = existing.props.get("created_at")
        props["history_ref"] = existing.props.get("history_ref")
    return graph.merge_node(BARRIER_LABEL, claim.key, props)
