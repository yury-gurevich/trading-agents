"""PM and regime gate renderers for deliberation evidence.

Agent: deliberator
Role: render explicit pass/fail gate outcomes for the debate context.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.deliberator.context_stop import stop_target_basis
from agents.deliberator.context_values import (
    explain,
    gate_value_labels,
    number,
    percent,
    quant_metrics,
)

if TYPE_CHECKING:
    from contracts.analyst import Recommendation
    from contracts.portfolio_manager import GateOutcome, OrderIntent
    from contracts.provider import OHLCVBar, RegimeContext


def order_lines(intent: OrderIntent) -> list[str]:
    """Render the PM order shell plus the additive PM gate report."""
    return [_order_line(intent), *_pm_gate_lines(intent)]


def recommendation_line(rec: Recommendation) -> str:
    """Render the analyst recommendation values for one ticker."""
    return (
        f"Analyst recommendation for {rec.ticker}: action={rec.action}; "
        f"confidence_score={rec.confidence:.3f}; "
        f"technical_score={rec.technical_score:.3f}; "
        f"analyst_sentiment_score={number(rec.sentiment_score)}; "
        f"fundamental_score={number(rec.fundamental_score)}; "
        f"suggested_stop_pct={percent(rec.suggested_stop_pct)}; "
        f"suggested_target_pct={percent(rec.suggested_target_pct)}; "
        f"quant_metrics={quant_metrics(rec)}; "
        f"{stop_target_basis(rec)}; "
        f"rationale={explain(rec.rationale)}"
    )


def regime_gate_lines(
    regime: RegimeContext | None,
    rec: Recommendation | None,
    intent: OrderIntent,
    bars: tuple[OHLCVBar, ...],
) -> list[str]:
    """Render regime values plus explicit analyst and stop/volatility outcomes."""
    if regime is None:
        return [
            "Regime: unavailable (no RegimeContext linked to MarketData).",
            _confidence_floor_line(None, rec),
            _stop_regime_line(None, intent, bars),
        ]
    return [
        (
            "Regime: "
            f"label={regime.label}; vix_index={regime.vix}; "
            f"base_min_confidence_score={regime.base_min_confidence:.3f}; "
            f"base_stop_loss_pct={percent(regime.base_stop_loss_pct)}; "
            f"base_take_profit_pct={percent(regime.base_take_profit_pct)}; "
            f"base_max_holding_days={regime.base_max_holding_days}"
        ),
        _confidence_floor_line(regime, rec),
        _stop_regime_line(regime, intent, bars),
    ]


def _order_line(intent: OrderIntent) -> str:
    return (
        f"PM order: action={intent.action}; ticker={intent.ticker}; "
        f"quantity_shares={intent.quantity}; "
        f"est_price_{intent.est_price.currency.lower()}={intent.est_price.amount}; "
        f"stop_pct={percent(intent.stop_pct)}; "
        f"target_pct={percent(intent.target_pct)}; "
        f"rationale={explain(intent.rationale)}"
    )


def _pm_gate_lines(intent: OrderIntent) -> list[str]:
    if not intent.gate_report:
        return [
            f"PM gate report unavailable: no gate outcomes emitted for {intent.ticker}."
        ]
    return [f"PM gate outcome: {_gate_line(gate)}" for gate in intent.gate_report]


def _gate_line(gate: GateOutcome) -> str:
    detail = f" ({gate.detail})" if gate.detail else ""
    value_label, threshold_label = gate_value_labels(gate.name)
    return (
        f"name={gate.name} {value_label}={gate.value:.4g} "
        f"{threshold_label}={gate.threshold:.4g} -> {_outcome(gate.passed)}{detail}"
    )


def _confidence_floor_line(
    regime: RegimeContext | None, rec: Recommendation | None
) -> str:
    if rec is None:
        return "confidence_floor gate unavailable: no analyst recommendation."
    if regime is None:
        return (
            "confidence_floor gate unavailable: no regime threshold; "
            f"confidence_score={rec.confidence:.3f}."
        )
    passed = rec.confidence >= regime.base_min_confidence
    return (
        "confidence_floor gate: "
        f"confidence_score={rec.confidence:.3f} vs "
        f"base_min_confidence_score={regime.base_min_confidence:.3f} "
        f"-> {_outcome(passed)}"
    )


def _stop_regime_line(
    regime: RegimeContext | None, intent: OrderIntent, _bars: tuple[OHLCVBar, ...]
) -> str:
    if regime is None or intent.stop_pct is None or intent.target_pct is None:
        return (
            "stop_vs_regime_volatility gate unavailable: "
            f"stop_pct={percent(intent.stop_pct)}; "
            f"target_pct={percent(intent.target_pct)}."
        )
    stop_base_passed = intent.stop_pct <= regime.base_stop_loss_pct
    target_base_passed = intent.target_pct >= regime.base_take_profit_pct
    return (
        "stop_vs_regime_volatility gate: "
        f"stop_pct={percent(intent.stop_pct)} vs "
        f"base_stop_loss_pct={percent(regime.base_stop_loss_pct)} "
        f"-> {_outcome(stop_base_passed)}; "
        f"target_pct={percent(intent.target_pct)} vs "
        f"base_take_profit_pct={percent(regime.base_take_profit_pct)} "
        f"-> {_outcome(target_base_passed)}"
    )


def _outcome(passed: bool) -> str:
    return "PASSED" if passed else "FAILED"
