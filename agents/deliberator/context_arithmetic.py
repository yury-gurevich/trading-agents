"""The frozen EXP-019 score arithmetic, rendered from recorded values.

Agent: deliberator
Role: append arithmetic only when it reproduces the recommendation's record.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.analyst import Recommendation, ScoreArithmetic
    from contracts.provider import RegimeContext, VixThresholds

# D5: compare unrounded recorded numbers; four-decimal text can hide real drift.
TOLERANCE = 1e-9
_MISMATCH = "the stated rule does not reproduce the recorded confidence_score"


@dataclass(frozen=True)
class ComputedArithmetic:
    """Unrounded values used by the record check and the frozen order line."""

    q: dict[str, float]
    tech: tuple[float, ...]
    fund: tuple[float, ...]
    present: dict[str, float]
    total: float
    composite: float
    confidence: float


def recompute(rec: Recommendation, sa: ScoreArithmetic) -> ComputedArithmetic:
    """Apply the Appendix's rule to its recorded sub-scores and present pillars."""
    q = {m.name: m.value for m in rec.quant_metrics}
    tech = tuple(q[name] for name in sa.technical_sub_scores)
    fund = tuple(q[name] for name in sa.fundamental_sub_scores)
    w = sa.relative_strength_weight
    technical = (1 - w) * (sum(tech) / len(tech) / 100) + w * q["rs_score"] / 100
    pillars = {
        "technical": technical,
        "fundamental": sum(fund) / len(fund) / 100 if fund else None,
        "sentiment": rec.sentiment_score,
    }
    present = {name: value for name, value in pillars.items() if value is not None}
    total = sum(getattr(sa, f"{name}_weight") for name in present)
    weighted = sum(
        getattr(sa, f"{name}_weight") * value for name, value in present.items()
    )
    composite = weighted / total if total else float("nan")
    return ComputedArithmetic(
        q,
        tech,
        fund,
        present,
        total,
        composite,
        sa.confidence_floor + sa.confidence_span * composite,
    )


def arithmetic_lines(
    rec: Recommendation | None, regime: RegimeContext | None, ticker: str
) -> list[str]:
    """D4: the first failed condition withholds; old records add nothing."""
    if rec is None or rec.score_arithmetic is None:
        return []
    sa = rec.score_arithmetic
    q = {m.name: m.value for m in rec.quant_metrics}
    if regime is None:
        return _withheld("no regime record")
    if regime.vix_thresholds is None:
        return _withheld("the regime record carries no label thresholds")
    if "alpha158_score" in q:
        return _withheld("the alpha158 pillar is active")
    names = (*sa.technical_sub_scores, *sa.fundamental_sub_scores)
    if not sa.technical_sub_scores or not set(names).issubset(q):
        return _withheld("the recorded sub-scores are incomplete")
    if "rs_score" not in q:
        return _withheld("this order has no rs_score")
    r = recompute(rec, sa)
    if not (
        abs(r.confidence - rec.confidence) <= TOLERANCE
        and abs(r.present["technical"] - rec.technical_score) <= TOLERANCE
    ):
        return _withheld(_MISMATCH)
    return [
        _rule(sa),
        _order_line(r, sa, regime.base_min_confidence, ticker),
        _regime_rule(regime.vix_thresholds),
    ]


def _withheld(reason: str) -> list[str]:
    return [f"Score arithmetic: withheld; {reason}."]


def _rule(sa: ScoreArithmetic) -> str:
    rsw = sa.relative_strength_weight
    return (
        "Score arithmetic, the rule for every order (definitions from the analyst's "
        "code, the same for every reviewer): inside quant_metrics each key ending in "
        "_score, and each fundamental sub-score, is a 0-100 band score in which 50 is "
        "neutral, except technical_score, fundamental_score, sentiment_score and "
        "composite_score, which are on a 0-1 scale; "
        f"technical_score = {1 - rsw:.2f} x (mean of the technical sub-scores / 100) + "
        f"{rsw:.2f} x (rs_score / 100); fundamental_score = "
        "(mean of the fundamental sub-scores) / 100; "
        f"composite_score = {sa.technical_weight:.2f} x technical_score + "
        f"{sa.fundamental_weight:.2f} x fundamental_score + "
        f"{sa.sentiment_weight:.2f} x sentiment_score, divided by the sum of the "
        "weights of the pillars that are present; "
        f"confidence = {sa.confidence_floor:.2f} + {sa.confidence_span:.2f} x "
        "composite_score; a pillar score of 0.50 is neutral; "
        "an order is recommended only if confidence >= "
        "base_min_confidence_score."
    )


def _order_line(
    r: ComputedArithmetic, sa: ScoreArithmetic, floor: float, ticker: str
) -> str:
    parts = [
        f"technical sub-scores ({len(r.tech)}): mean {sum(r.tech) / len(r.tech):.2f}",
        f"rs_score={r.q['rs_score']:g}",
        f"technical_score={r.present['technical']:.4f}",
    ]
    if r.fund:
        subs = ", ".join(f"{name}={r.q[name]:g}" for name in sa.fundamental_sub_scores)
        parts += [
            f"fundamental sub-scores ({len(r.fund)}): {subs}",
            f"fundamental_score={r.present['fundamental']:.4f}",
        ]
    if "sentiment" in r.present:
        parts.append(f"sentiment_score={r.present['sentiment']:.4f}")
    shares = ", ".join(
        f"{name} {getattr(sa, f'{name}_weight') * value / r.total:.4f}"
        for name, value in r.present.items()
    )
    parts += [
        f"contributions to composite_score: {shares}",
        f"composite_score={r.composite:.4f}",
        f"confidence={r.confidence:.4f}",
        f"base_min_confidence_score={floor:.3f}",
        f"margin over the floor={r.confidence - floor:+.4f}",
    ]
    return f"Score arithmetic for {ticker}: " + "; ".join(parts) + "."


def _regime_rule(vix: VixThresholds) -> str:
    return (
        "Regime, the rule for every order: vix_index only selects the regime label "
        f"(risk_on at or below {vix.risk_on_at_or_below:g}, "
        f"risk_off from {vix.risk_off_from:g}, "
        f"high_volatility from {vix.high_volatility_from:g}, "
        f"extreme_volatility from {vix.extreme_volatility_from:g}, neutral otherwise). "
        "The label is printed and changes no number: base_min_confidence_score, "
        "base_stop_loss_pct, base_take_profit_pct and base_max_holding_days are the "
        "same constants under every label, and the VIX is "
        "not an input to any score."
    )
