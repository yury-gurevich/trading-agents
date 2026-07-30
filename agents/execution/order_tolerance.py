"""Order tolerance resolution for ADR-0018/S149 bounded submissions.

Agent: execution
Role: deterministically resolve flat or volatility-scaled order tolerances.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import ROUND_HALF_UP, Decimal
from math import isfinite
from typing import TYPE_CHECKING, Literal

from agents.execution.alpaca_orders import bounded_limit_price
from contracts.common import Money

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill
    from agents.execution.settings import ExecutionSettings
    from contracts.portfolio_manager import OrderIntent

OrderPriceToleranceMode = Literal["flat", "scaled"]

_BPS_PER_PERCENT = Decimal("100")
_ONE_BPS = Decimal("1")


@dataclass(frozen=True)
class OrderToleranceConfig:
    """Execution settings projected into pure tolerance-resolution inputs."""

    mode: OrderPriceToleranceMode
    flat_bps: int
    scaled_atr_multiplier: float
    scaled_floor_bps: int
    scaled_ceiling_bps: int

    @classmethod
    def from_settings(cls, settings: ExecutionSettings) -> OrderToleranceConfig:
        """Build the pure config from pydantic settings."""
        return cls(
            mode=settings.order_price_tolerance_mode,
            flat_bps=settings.order_price_tolerance_bps,
            scaled_atr_multiplier=settings.scaled_order_price_tolerance_atr_multiplier,
            scaled_floor_bps=settings.scaled_order_price_tolerance_floor_bps,
            scaled_ceiling_bps=settings.scaled_order_price_tolerance_ceiling_bps,
        )


@dataclass(frozen=True)
class OrderToleranceEvidence:
    """Applied and counterfactual tolerance facts for one broker order."""

    mode: OrderPriceToleranceMode
    counterfactual_mode: OrderPriceToleranceMode
    decided_price: Money
    applied_tolerance_bps: int
    applied_limit_price: Money
    counterfactual_tolerance_bps: int
    counterfactual_limit_price: Money
    flat_tolerance_bps: int
    flat_limit_price: Money
    scaled_tolerance_bps: int
    scaled_limit_price: Money
    decision_atr_pct: float | None
    volatility_present: bool
    volatility_fallback: bool


def resolve_order_tolerance(
    intent: OrderIntent,
    side: Literal["buy", "sell"],
    config: OrderToleranceConfig,
) -> OrderToleranceEvidence:
    """Resolve applied and counterfactual tolerance facts for one intent."""
    flat_bps = config.flat_bps
    scaled_bps, present, fallback = _scaled_tolerance_bps(
        intent.decision_atr_pct, config
    )
    flat_limit = _limit_price(intent.est_price, side, flat_bps)
    scaled_limit = _limit_price(intent.est_price, side, scaled_bps)
    if config.mode == "scaled":
        applied_bps = scaled_bps
        applied_limit = scaled_limit
        counter_bps = flat_bps
        counter_limit = flat_limit
        counter_mode: OrderPriceToleranceMode = "flat"
    else:
        applied_bps = flat_bps
        applied_limit = flat_limit
        counter_bps = scaled_bps
        counter_limit = scaled_limit
        counter_mode = "scaled"
    return OrderToleranceEvidence(
        mode=config.mode,
        counterfactual_mode=counter_mode,
        decided_price=intent.est_price,
        applied_tolerance_bps=applied_bps,
        applied_limit_price=applied_limit,
        counterfactual_tolerance_bps=counter_bps,
        counterfactual_limit_price=counter_limit,
        flat_tolerance_bps=flat_bps,
        flat_limit_price=flat_limit,
        scaled_tolerance_bps=scaled_bps,
        scaled_limit_price=scaled_limit,
        decision_atr_pct=_usable_atr_pct(intent.decision_atr_pct),
        volatility_present=present,
        volatility_fallback=fallback,
    )


def attach_order_tolerance(
    fill: BrokerFill, evidence: OrderToleranceEvidence
) -> BrokerFill:
    """Attach tolerance evidence to a broker outcome without changing outcome facts."""
    return replace(
        fill,
        order_tolerance_mode=evidence.mode,
        order_counterfactual_mode=evidence.counterfactual_mode,
        order_decided_price=evidence.decided_price,
        order_applied_tolerance_bps=evidence.applied_tolerance_bps,
        order_applied_limit_price=evidence.applied_limit_price,
        order_counterfactual_tolerance_bps=evidence.counterfactual_tolerance_bps,
        order_counterfactual_limit_price=evidence.counterfactual_limit_price,
        order_flat_tolerance_bps=evidence.flat_tolerance_bps,
        order_flat_limit_price=evidence.flat_limit_price,
        order_scaled_tolerance_bps=evidence.scaled_tolerance_bps,
        order_scaled_limit_price=evidence.scaled_limit_price,
        order_decision_atr_pct=evidence.decision_atr_pct,
        order_volatility_present=evidence.volatility_present,
        order_volatility_fallback=evidence.volatility_fallback,
    )


def _scaled_tolerance_bps(
    atr_pct: float | None, config: OrderToleranceConfig
) -> tuple[int, bool, bool]:
    value = _usable_atr_pct(atr_pct)
    if value is None:
        return config.flat_bps, False, True
    raw = (
        Decimal(str(value))
        * _BPS_PER_PERCENT
        * Decimal(str(config.scaled_atr_multiplier))
    )
    rounded = int(raw.quantize(_ONE_BPS, rounding=ROUND_HALF_UP))
    clamped = min(config.scaled_ceiling_bps, max(config.scaled_floor_bps, rounded))
    return clamped, True, False


def _limit_price(
    decision_price: Money, side: Literal["buy", "sell"], tolerance_bps: int
) -> Money:
    return Money(
        amount=bounded_limit_price(decision_price, side, tolerance_bps),
        currency=decision_price.currency,
    )


def _usable_atr_pct(value: float | None) -> float | None:
    if value is None or not isfinite(value) or value < 0.0:
        return None
    return value
