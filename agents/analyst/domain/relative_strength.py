"""Relative-strength signal and its 0-100 band score.

Agent: analyst
Role: compare a candidate's trailing return to a benchmark and band-score the spread.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.provider import OHLCVBar

# Fixed reference bands (the rule, not tunable policy): a relative-strength spread
# (candidate return % minus benchmark return %) maps to a 0-100 sub-score. Strict ``>``,
# first match wins, else the default. Mirrors the band convention in technical_rules.py.
_RS_STRONG, _RS_POSITIVE, _RS_WEAK = 5.0, 0.0, -5.0
_RS_SCORES = (80.0, 60.0, 40.0, 20.0)


def _return_pct(bars: tuple[OHLCVBar, ...], window: int) -> float | None:
    """Trailing percentage return over ``window`` bars, or ``None`` if too short."""
    if len(bars) < window + 1:
        return None
    ordered = sorted(bars, key=lambda candle: candle.bar_date)
    # OHLCVBar enforces close > 0 (contract), so the base price is always positive.
    return (ordered[-1].close / ordered[-(window + 1)].close - 1.0) * 100.0


def compute_relative_strength(
    stock_bars: tuple[OHLCVBar, ...],
    benchmark_bars: tuple[OHLCVBar, ...],
    window: int,
) -> float | None:
    """Candidate minus benchmark trailing return; ``None`` if either is too short."""
    stock = _return_pct(stock_bars, window)
    benchmark = _return_pct(benchmark_bars, window)
    if stock is None or benchmark is None:
        return None
    return stock - benchmark


def score_relative_strength(relative_strength: float) -> float:
    """Band-score a relative-strength spread to 0-100 (higher = stronger)."""
    if relative_strength > _RS_STRONG:
        return _RS_SCORES[0]
    if relative_strength > _RS_POSITIVE:
        return _RS_SCORES[1]
    if relative_strength > _RS_WEAK:
        return _RS_SCORES[2]
    return _RS_SCORES[3]
