"""Pure-statistics tests for the scorecard harness.

Agent: forecaster
Role: verify Pearson correlation, population std, and 2-regressor OLS, incl. the
      undefined (None) edges.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.forecaster.domain.statistics import ols2, pearson, std


def test_pearson_perfect_positive() -> None:
    assert pearson([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == pytest.approx(1.0)


def test_pearson_perfect_negative() -> None:
    assert pearson([1.0, 2.0, 3.0], [6.0, 4.0, 2.0]) == pytest.approx(-1.0)


def test_pearson_too_few_points_is_none() -> None:
    assert pearson([1.0], [2.0]) is None


def test_pearson_constant_series_is_none() -> None:
    assert pearson([5.0, 5.0, 5.0], [1.0, 2.0, 3.0]) is None


def test_std_is_zero_for_a_constant_series() -> None:
    assert std([3.0, 3.0, 3.0]) == 0.0


def test_std_known_value() -> None:
    assert std([1.0, 2.0, 3.0]) == pytest.approx((2.0 / 3.0) ** 0.5)


def test_ols2_recovers_an_exact_plane() -> None:
    a = [1.0, 2.0, 3.0, 4.0]
    b = [1.0, 0.0, 2.0, 1.0]
    f = [5.0 + 2.0 * ai + 3.0 * bi for ai, bi in zip(a, b, strict=True)]
    fit = ols2(f, a, b)
    assert fit is not None
    alpha, beta, gamma, residuals = fit
    assert alpha == pytest.approx(5.0)
    assert beta == pytest.approx(2.0)
    assert gamma == pytest.approx(3.0)
    assert all(abs(r) < 1e-9 for r in residuals)


def test_ols2_too_few_points_is_none() -> None:
    assert ols2([1.0, 2.0], [1.0, 2.0], [3.0, 4.0]) is None


def test_ols2_collinear_regressors_is_none() -> None:
    a = [1.0, 2.0, 3.0]
    b = [2.0, 4.0, 6.0]  # b == 2*a -> singular design
    assert ols2([1.0, 5.0, 2.0], a, b) is None
