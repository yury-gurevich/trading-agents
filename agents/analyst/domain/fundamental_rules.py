"""Fundamental metric scoring rules and their pillar score.

Agent: analyst
Role: map Finnhub valuation/quality/growth metrics to 0-100 sub-scores and average them.
External I/O: none.
"""

from __future__ import annotations

# Fixed reference rule table (the rule itself, not tunable policy): each spec is
# ``(name, keys, require_positive, bands, default)`` where ``keys`` is tried in order
# (first present wins), ``require_positive`` skips a value ``<= 0``, and ``bands`` is a
# top-to-bottom ``(op, threshold, score)`` list (first match wins, else ``default``).
# Operators: ``lt``/``gt`` are strict ``<``/``>``; ``le`` is inclusive ``<=``. These
# are named module constants mirroring the band convention in ``technical_rules.py``.
_FUNDAMENTAL_RULES: tuple[
    tuple[str, tuple[str, ...], bool, tuple[tuple[str, float, float], ...], float], ...
] = (
    (
        "pe",
        ("peBasicExclExtraTTM", "peTTM"),
        True,
        (("lt", 10.0, 80.0), ("le", 25.0, 60.0)),
        30.0,
    ),
    (
        "roe",
        ("roeTTM",),
        False,
        (("gt", 15.0, 80.0), ("gt", 5.0, 55.0)),
        25.0,
    ),
    (
        "net_margin",
        ("netProfitMarginTTM",),
        False,
        (("gt", 20.0, 80.0), ("gt", 10.0, 55.0)),
        30.0,
    ),
    (
        "current_ratio",
        ("currentRatioQuarterly",),
        True,
        (("gt", 1.5, 70.0), ("gt", 1.0, 50.0)),
        25.0,
    ),
    (
        "pb",
        ("pbQuarterly", "pbAnnual"),
        True,
        (("lt", 1.5, 80.0), ("le", 3.0, 60.0), ("le", 5.0, 40.0)),
        20.0,
    ),
    (
        "debt_equity",
        ("totalDebt/totalEquityQuarterly", "totalDebt/totalEquityAnnual"),
        False,
        (("lt", 0.5, 80.0), ("lt", 1.0, 65.0), ("lt", 2.0, 45.0)),
        20.0,
    ),
    (
        "eps_growth",
        ("epsGrowthTTMYoy",),
        False,
        (("gt", 20.0, 85.0), ("gt", 5.0, 65.0), ("gt", -5.0, 45.0)),
        20.0,
    ),
    (
        "revenue_growth",
        ("revenueGrowthTTMYoy",),
        False,
        (("gt", 15.0, 80.0), ("gt", 5.0, 60.0), ("gt", -5.0, 45.0)),
        25.0,
    ),
)


def _match(value: float, op: str, threshold: float) -> bool:
    """Return whether ``value`` satisfies ``op`` against ``threshold``."""
    if op == "lt":
        return value < threshold
    if op == "le":
        return value <= threshold
    return value > threshold


def _lookup(metrics: dict[str, float], keys: tuple[str, ...]) -> float | None:
    """Return the first present metric across ``keys`` (fallback precedence)."""
    for key in keys:
        if key in metrics:
            return metrics[key]
    return None


def _score_metric(
    value: float,
    bands: tuple[tuple[str, float, float], ...],
    default: float,
) -> float:
    """Apply bands top-to-bottom (first match wins) else the default sub-score."""
    for op, threshold, score in bands:
        if _match(value, op, threshold):
            return score
    return default


def score_fundamental(
    metrics: dict[str, float],
) -> tuple[float | None, dict[str, float]]:
    """Average the present metrics' 0-100 sub-scores; ``(None, {})`` when none usable.

    First present of the fallback keys wins; ``require_positive`` metrics are skipped
    when the value is ``<= 0``; missing keys are skipped. Never raises.
    """
    sub_scores: dict[str, float] = {}
    for name, keys, require_positive, bands, default in _FUNDAMENTAL_RULES:
        value = _lookup(metrics, keys)
        if value is None:
            continue
        if require_positive and value <= 0.0:
            continue
        sub_scores[name] = _score_metric(value, bands, default)
    if not sub_scores:
        return None, {}
    mean = sum(sub_scores.values()) / len(sub_scores)
    sub_scores["fundamentals_available"] = float(len(sub_scores))
    return mean, sub_scores
