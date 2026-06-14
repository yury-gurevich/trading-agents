"""Fundamental scoring band tests.

Agent: analyst
Role: verify each metric's bands, fallback keys, require_positive, and averaging.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.analyst.domain.fundamental_rules import score_fundamental


def _only(metrics: dict[str, float], name: str) -> float:
    score, breakdown = score_fundamental(metrics)
    assert score is not None
    return breakdown[name]


@pytest.mark.parametrize(
    ("value", "expected"),
    [(9.99, 80.0), (10.0, 60.0), (25.0, 60.0), (25.01, 30.0)],
)
def test_pe_bands(value: float, expected: float) -> None:
    assert _only({"peTTM": value}, "pe") == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(15.01, 80.0), (15.0, 55.0), (5.01, 55.0), (5.0, 25.0)],
)
def test_roe_bands(value: float, expected: float) -> None:
    assert _only({"roeTTM": value}, "roe") == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(20.01, 80.0), (20.0, 55.0), (10.01, 55.0), (10.0, 30.0)],
)
def test_net_margin_bands(value: float, expected: float) -> None:
    assert _only({"netProfitMarginTTM": value}, "net_margin") == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(1.51, 70.0), (1.5, 50.0), (1.01, 50.0), (1.0, 25.0)],
)
def test_current_ratio_bands(value: float, expected: float) -> None:
    assert _only({"currentRatioQuarterly": value}, "current_ratio") == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(1.49, 80.0), (1.5, 60.0), (3.0, 60.0), (3.01, 40.0), (5.0, 40.0), (5.01, 20.0)],
)
def test_pb_bands(value: float, expected: float) -> None:
    assert _only({"pbQuarterly": value}, "pb") == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0.49, 80.0), (0.5, 65.0), (0.99, 65.0), (1.0, 45.0), (1.99, 45.0), (2.0, 20.0)],
)
def test_debt_equity_bands(value: float, expected: float) -> None:
    metrics = {"totalDebt/totalEquityQuarterly": value}
    assert _only(metrics, "debt_equity") == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(20.01, 85.0), (20.0, 65.0), (5.0, 45.0), (-5.0, 20.0), (-4.99, 45.0)],
)
def test_eps_growth_bands(value: float, expected: float) -> None:
    assert _only({"epsGrowthTTMYoy": value}, "eps_growth") == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(15.01, 80.0), (15.0, 60.0), (5.0, 45.0), (-5.0, 25.0), (-4.99, 45.0)],
)
def test_revenue_growth_bands(value: float, expected: float) -> None:
    assert _only({"revenueGrowthTTMYoy": value}, "revenue_growth") == expected


def test_fallback_key_precedence() -> None:
    # peBasicExclExtraTTM wins when present...
    assert _only({"peBasicExclExtraTTM": 8.0, "peTTM": 30.0}, "pe") == 80.0
    # ...peTTM is the fallback when the primary key is absent.
    assert _only({"peTTM": 8.0}, "pe") == 80.0


def test_require_positive_skips_non_positive() -> None:
    # P/E require_positive: a <= 0 value is skipped, not banded to the default.
    score, breakdown = score_fundamental({"peTTM": -5.0})
    assert score is None
    assert breakdown == {}


def test_missing_keys_are_skipped() -> None:
    score, breakdown = score_fundamental({"roeTTM": 20.0})
    assert score == 80.0
    assert breakdown["fundamentals_available"] == 1.0
    assert "pe" not in breakdown


def test_partial_average_over_present_subset() -> None:
    # pe 8 -> 80, roeTTM 5 -> 25; mean 52.5 over exactly two present metrics.
    score, breakdown = score_fundamental({"peTTM": 8.0, "roeTTM": 5.0})
    assert score == pytest.approx(52.5, abs=1e-9)
    assert breakdown["fundamentals_available"] == 2.0
    assert breakdown["pe"] == 80.0
    assert breakdown["roe"] == 25.0


def test_empty_and_all_unusable_return_none() -> None:
    assert score_fundamental({}) == (None, {})
    # require_positive P/B and current ratio both <= 0 -> all unusable.
    assert score_fundamental({"pbQuarterly": 0.0, "currentRatioQuarterly": -1.0}) == (
        None,
        {},
    )


def test_default_band_when_no_band_matches() -> None:
    # ROE 5.0 is not > 5 (strict) and not > 15 -> falls to the default 25.
    assert _only({"roeTTM": 5.0}, "roe") == 25.0
