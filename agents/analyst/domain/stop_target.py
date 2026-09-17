"""Volatility-aware stop and target proposal helpers.

Agent: analyst
Role: resolve flat or ATR-scaled stop/target suggestions plus challenger evidence.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import TYPE_CHECKING

from agents.analyst.domain.stop_target_outcome import (
    FAVORABLE_EXCURSION_HORIZON_DAYS,
    FAVORABLE_EXCURSION_LOOKBACK_WINDOWS,
    FAVORABLE_EXCURSION_PCT,
    FAVORABLE_EXCURSION_SAMPLE_COUNT,
)
from contracts.analyst import StopTargetEvidence, StopTargetMode

if TYPE_CHECKING:
    from collections.abc import Mapping

    from agents.analyst.settings import AnalystSettings
    from contracts.provider import RegimeContext

ATR_METRIC_NAME = "atr_pct"
_PERCENT = 100.0
_MAX_PCT = 1.0


@dataclass(frozen=True)
class StopTargetProposal:
    """Resolved applied proposal and durable counterfactual evidence."""

    stop_pct: float
    target_pct: float
    evidence: StopTargetEvidence


def resolve_stop_target(
    regime: RegimeContext,
    metrics: Mapping[str, float],
    settings: AnalystSettings,
) -> StopTargetProposal | None:
    """Resolve the buy-side stop/target proposal for the configured mode."""
    flat_stop = regime.base_stop_loss_pct
    base_target = regime.base_take_profit_pct
    atr_pct = _usable_atr_pct(metrics)
    scaled_stop = _scaled_stop(flat_stop, atr_pct, settings)
    if FAVORABLE_EXCURSION_SAMPLE_COUNT not in metrics:
        flat_target = base_target
        scaled_target = _scaled_target(flat_stop, base_target, scaled_stop)
    else:
        target = _measured_target(metrics)
        if target is None:
            return None
        flat_target = target
        scaled_target = target
    mode: StopTargetMode = settings.stop_target_mode
    applied_stop = flat_stop if mode == "flat" else scaled_stop
    applied_target = flat_target if mode == "flat" else scaled_target
    counter_mode: StopTargetMode = "scaled" if mode == "flat" else "flat"
    counter_stop = scaled_stop if mode == "flat" else flat_stop
    counter_target = scaled_target if mode == "flat" else flat_target
    return StopTargetProposal(
        stop_pct=applied_stop,
        target_pct=applied_target,
        evidence=StopTargetEvidence(
            mode=mode,
            counterfactual_mode=counter_mode,
            atr_pct=atr_pct,
            volatility_present=atr_pct is not None,
            volatility_fallback=atr_pct is None,
            applied_stop_pct=applied_stop,
            applied_target_pct=applied_target,
            counterfactual_stop_pct=counter_stop,
            counterfactual_target_pct=counter_target,
            flat_stop_pct=flat_stop,
            flat_target_pct=flat_target,
            scaled_stop_pct=scaled_stop,
            scaled_target_pct=scaled_target,
            favorable_excursion_pct=_optional_metric(metrics, FAVORABLE_EXCURSION_PCT),
            favorable_excursion_horizon_days=_optional_int_metric(
                metrics, FAVORABLE_EXCURSION_HORIZON_DAYS
            ),
            favorable_excursion_sample_count=_optional_int_metric(
                metrics, FAVORABLE_EXCURSION_SAMPLE_COUNT
            ),
            favorable_excursion_lookback_windows=_optional_int_metric(
                metrics, FAVORABLE_EXCURSION_LOOKBACK_WINDOWS
            ),
        ),
    )


def _scaled_stop(
    flat_stop: float, atr_pct: float | None, settings: AnalystSettings
) -> float:
    if atr_pct is None:
        return flat_stop
    raw = atr_pct / _PERCENT * settings.scaled_stop_atr_multiplier
    return min(
        max(raw, settings.scaled_stop_floor_pct),
        settings.scaled_stop_ceiling_pct,
    )


def _scaled_target(flat_stop: float, flat_target: float, scaled_stop: float) -> float:
    if flat_stop <= 0.0:
        return flat_target
    return min(flat_target * (scaled_stop / flat_stop), _MAX_PCT)


def _measured_target(metrics: Mapping[str, float]) -> float | None:
    sample_count = metrics.get(FAVORABLE_EXCURSION_SAMPLE_COUNT)
    if sample_count is None:
        return None
    if sample_count <= 0.0:
        return None
    value = metrics.get(FAVORABLE_EXCURSION_PCT)
    if value is None or not isfinite(value) or value < 0.0:
        return None
    return min(value, _MAX_PCT)


def _optional_metric(metrics: Mapping[str, float], name: str) -> float | None:
    value = metrics.get(name)
    if value is None or not isfinite(value):
        return None
    return value


def _optional_int_metric(metrics: Mapping[str, float], name: str) -> int | None:
    value = _optional_metric(metrics, name)
    if value is None:
        return None
    return int(value)


def _usable_atr_pct(metrics: Mapping[str, float]) -> float | None:
    value = metrics.get(ATR_METRIC_NAME)
    if value is None or not isfinite(value) or value <= 0.0:
        return None
    return value
