"""PM and regime gate renderers for deliberation veto evidence.

Agent: orchestration
Role: render explicit pass/fail gate outcomes for the challenger-veto context.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.analyst import Recommendation
    from contracts.common import Explanation
    from contracts.portfolio_manager import GateOutcome, OrderIntent
    from contracts.provider import OHLCVBar, RegimeContext


def order_lines(intent: OrderIntent) -> list[str]:
    """Render the PM order shell plus the additive PM gate report."""
    return [_order_line(intent), *_pm_gate_lines(intent)]


def recommendation_line(rec: Recommendation) -> str:
    """Render the analyst recommendation values for one ticker."""
    return (
        f"Analyst recommendation for {rec.ticker}: action={rec.action}; "
        f"confidence={rec.confidence:.3f}; technical_score={rec.technical_score:.3f}; "
        f"sentiment_score={_num(rec.sentiment_score)}; "
        f"fundamental_score={_num(rec.fundamental_score)}; "
        f"suggested_stop_pct={_pct(rec.suggested_stop_pct)}; "
        f"suggested_target_pct={_pct(rec.suggested_target_pct)}; "
        f"quant_metrics={_quant_metrics(rec)}; "
        f"rationale={_explain(rec.rationale)}"
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
            f"label={regime.label}; vix={regime.vix}; "
            f"base_min_confidence={regime.base_min_confidence:.3f}; "
            f"base_stop_loss_pct={_pct(regime.base_stop_loss_pct)}; "
            f"base_take_profit_pct={_pct(regime.base_take_profit_pct)}; "
            f"base_max_holding_days={regime.base_max_holding_days}"
        ),
        _confidence_floor_line(regime, rec),
        _stop_regime_line(regime, intent, bars),
    ]


def _order_line(intent: OrderIntent) -> str:
    return (
        f"PM order: action={intent.action}; ticker={intent.ticker}; "
        f"quantity={intent.quantity}; est_price={intent.est_price.amount} "
        f"{intent.est_price.currency}; stop_pct={_pct(intent.stop_pct)}; "
        f"target_pct={_pct(intent.target_pct)}; rationale={_explain(intent.rationale)}"
    )


def _pm_gate_lines(intent: OrderIntent) -> list[str]:
    if not intent.gate_report:
        return [
            f"PM gate report unavailable: no gate outcomes emitted for {intent.ticker}."
        ]
    return [f"PM gate outcome: {_gate_line(gate)}" for gate in intent.gate_report]


def _gate_line(gate: GateOutcome) -> str:
    detail = f" ({gate.detail})" if gate.detail else ""
    return (
        f"name={gate.name} value={gate.value:.4g} "
        f"threshold={gate.threshold:.4g} -> {_outcome(gate.passed)}{detail}"
    )


def _confidence_floor_line(
    regime: RegimeContext | None, rec: Recommendation | None
) -> str:
    if rec is None:
        return "confidence_floor gate unavailable: no analyst recommendation."
    if regime is None:
        return (
            "confidence_floor gate unavailable: no regime threshold; "
            f"confidence={rec.confidence:.3f}."
        )
    passed = rec.confidence >= regime.base_min_confidence
    return (
        "confidence_floor gate: "
        f"confidence={rec.confidence:.3f} vs "
        f"base_min_confidence={regime.base_min_confidence:.3f} "
        f"-> {_outcome(passed)}"
    )


def _stop_regime_line(
    regime: RegimeContext | None, intent: OrderIntent, bars: tuple[OHLCVBar, ...]
) -> str:
    atr = _atr_pct(bars, intent.ticker)
    atr_note = (
        f"ATR%={_pct(atr)}"
        if atr is not None
        else "ATR%=unavailable (need at least 2 OHLCV bars)"
    )
    if regime is None or intent.stop_pct is None or intent.target_pct is None:
        return (
            "stop_vs_regime_volatility gate unavailable: "
            f"stop_pct={_pct(intent.stop_pct)}; target_pct={_pct(intent.target_pct)}; "
            f"{atr_note}."
        )
    stop_base_passed = intent.stop_pct <= regime.base_stop_loss_pct
    target_base_passed = intent.target_pct >= regime.base_take_profit_pct
    atr_fragment = _atr_fragment(intent.stop_pct, atr)
    return (
        "stop_vs_regime_volatility gate: "
        f"stop_pct={_pct(intent.stop_pct)} vs "
        f"base_stop_loss_pct={_pct(regime.base_stop_loss_pct)} "
        f"-> {_outcome(stop_base_passed)}; "
        f"target_pct={_pct(intent.target_pct)} vs "
        f"base_take_profit_pct={_pct(regime.base_take_profit_pct)} "
        f"-> {_outcome(target_base_passed)}; {atr_fragment}"
    )


def _atr_fragment(stop_pct: float, atr: float | None) -> str:
    if atr is None:
        return "ATR%=unavailable (need at least 2 OHLCV bars)"
    return (
        f"stop_pct={_pct(stop_pct)} vs ATR%={_pct(atr)} -> {_outcome(stop_pct >= atr)}"
    )


def _atr_pct(bars: tuple[OHLCVBar, ...], ticker: str) -> float | None:
    ticker_bars = sorted(
        (bar for bar in bars if bar.ticker == ticker), key=lambda bar: bar.bar_date
    )
    if len(ticker_bars) < 2:
        return None
    ranges: list[float] = []
    previous_close = ticker_bars[0].close
    for bar in ticker_bars[1:]:
        true_range = max(
            bar.high - bar.low,
            abs(bar.high - previous_close),
            abs(bar.low - previous_close),
        )
        ranges.append(true_range)
        previous_close = bar.close
    latest_close = ticker_bars[-1].close
    return (sum(ranges) / len(ranges)) / latest_close


def _outcome(passed: bool) -> str:
    return "PASSED" if passed else "FAILED"


def _explain(value: Explanation) -> str:
    refs = f" refs={list(value.evidence_refs)}" if value.evidence_refs else ""
    return f"{value.summary}{refs}"


def _num(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2%}"


def _quant_metrics(rec: Recommendation) -> str:
    if not rec.quant_metrics:
        return "{}"
    return (
        "{"
        + ", ".join(f"{metric.name}={metric.value:.4g}" for metric in rec.quant_metrics)
        + "}"
    )
