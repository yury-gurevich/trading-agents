"""Held-name claim barriers: the live stop and the declared target, from the close.

Agent: forecaster
Role: turn a held-name request's prices into the claim's barriers as fractions of
      its own last close (DL-310): the stop is ``1 - stop_price / close``; the
      target is ``target_price / close - 1`` while the close is below it (basis
      ``declared``), else the declared width again from the close (basis
      ``rebased``: the name already passed its target). A missing stop or target,
      or a close at or below the live stop, is a designed refusal (FORE-FAIL-04);
      a price that is not positive, or a barrier outside (0, 1], is malformed
      (FORE-IN-07). A barrier is never made up.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from agents.forecaster.barrier_refusal import DESIGNED, BarrierClaimRefusedError

TargetBasis = Literal["declared", "rebased"]


@dataclass(frozen=True)
class HeldPrices:
    """What the request says of a held name: its live stop and declared target."""

    stop_price: float
    target_price: float
    target_pct: float


@dataclass(frozen=True)
class HeldBarriers:
    """A held-name claim's barriers, measured from the claim's own close."""

    prices: HeldPrices
    stop_pct: float
    target_pct: float
    basis: TargetBasis


def held_prices(ticker: str, features: dict[str, float]) -> HeldPrices:
    """The request's prices, or a refusal before the history is read."""
    if "stop_price" not in features:
        raise BarrierClaimRefusedError(
            f"{ticker}: held with no live stop in the graph; no claim",
            severity=DESIGNED,
        )
    if "target_price" not in features or "target_pct" not in features:
        raise BarrierClaimRefusedError(
            f"{ticker}: held with no declared target in its lineage; no claim",
            severity=DESIGNED,
        )
    prices = HeldPrices(
        stop_price=features["stop_price"],
        target_price=features["target_price"],
        target_pct=features["target_pct"],
    )
    if min(prices.stop_price, prices.target_price) <= 0 or not (
        0 < prices.target_pct <= 1
    ):
        raise BarrierClaimRefusedError(
            f"{ticker}: held prices must be positive and the declared width in "
            f"(0, 1]: {prices}; no claim"
        )
    return prices


def held_barriers(ticker: str, prices: HeldPrices, close: float) -> HeldBarriers:
    """The claim's stop and target as fractions of ``close``."""
    if close <= prices.stop_price:
        raise BarrierClaimRefusedError(
            f"{ticker}: close {close} at or below the live stop "
            f"{prices.stop_price}; no claim",
            severity=DESIGNED,
        )
    stop_pct = 1 - prices.stop_price / close
    basis: TargetBasis = "declared" if close < prices.target_price else "rebased"
    target_pct = (
        prices.target_price / close - 1 if basis == "declared" else prices.target_pct
    )
    if not (0 < stop_pct <= 1 and 0 < target_pct <= 1):
        raise BarrierClaimRefusedError(
            f"{ticker}: barriers from close {close} outside (0, 1]: "
            f"stop_pct={stop_pct} target_pct={target_pct}; no claim"
        )
    return HeldBarriers(prices, stop_pct, target_pct, basis)
