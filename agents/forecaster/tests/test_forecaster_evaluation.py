"""Return-model evaluation battery math tests.

Agent: forecaster
Role: verify rank IC, quantile group returns, IC-series summaries, and
      rank-autocorrelation stability helpers.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.forecaster.domain.evaluation import (
    ic_series_metrics,
    quantile_metrics,
    rank_autocorrelation,
    rank_ic,
)
from agents.forecaster.domain.return_scorecard import ReturnObservation


def _obs(ref: str, predicted: float, forward_return: float) -> ReturnObservation:
    return ReturnObservation(ref, predicted, forward_return)


def test_rank_ic_uses_spearman() -> None:
    observations = [_obs("A", 0.1, 0.2), _obs("B", 0.3, 0.5)]
    assert rank_ic(observations) == pytest.approx(1.0)


def test_quantile_metrics_uses_larger_tail_buckets() -> None:
    observations = [_obs(f"T{i:02d}", float(i), float(i)) for i in range(11)]
    metrics = quantile_metrics(observations, quantiles=5)

    assert metrics["q1_mean_ret"] == pytest.approx(0.5)
    assert metrics["q5_mean_ret"] == pytest.approx(9.0)
    assert metrics["top_bottom_spread"] == pytest.approx(8.5)
    assert metrics["monotonic_fraction"] == 1.0


def test_quantile_metrics_is_deterministic_under_ties() -> None:
    observations = [
        _obs("D", 1.0, 4.0),
        _obs("B", 1.0, 2.0),
        _obs("C", 1.0, 3.0),
        _obs("A", 1.0, 1.0),
    ]
    metrics = quantile_metrics(observations, quantiles=2)
    assert metrics["q1_mean_ret"] == pytest.approx(1.5)
    assert metrics["q2_mean_ret"] == pytest.approx(3.5)


def test_quantile_metrics_reports_non_monotonic_ordering() -> None:
    observations = [
        _obs("A", 1.0, 0.0),
        _obs("B", 2.0, 0.0),
        _obs("C", 3.0, 10.0),
        _obs("D", 4.0, 10.0),
        _obs("E", 5.0, 5.0),
        _obs("F", 6.0, 5.0),
    ]
    metrics = quantile_metrics(observations, quantiles=3)
    assert metrics["monotonic_fraction"] == 0.5
    assert metrics["top_bottom_spread"] == 5.0


def test_quantile_metrics_omits_too_small_or_invalid_samples() -> None:
    observations = [_obs(str(i), float(i), float(i)) for i in range(9)]
    assert quantile_metrics(observations, quantiles=5) == {}
    assert quantile_metrics(observations, quantiles=1) == {}


def test_quantile_metrics_spread_can_be_negative() -> None:
    observations = [_obs(str(i), float(i), float(10 - i)) for i in range(10)]
    metrics = quantile_metrics(observations, quantiles=5)
    assert metrics["top_bottom_spread"] < 0.0


def test_ic_series_metrics_summarizes_and_skips_undefined_periods() -> None:
    metrics = ic_series_metrics(
        {
            "2024-01-01": [_obs("A", 1.0, 1.0), _obs("B", 2.0, 2.0)],
            "2024-01-02": [_obs("A", 1.0, 2.0), _obs("B", 2.0, 1.0)],
            "2024-01-03": [_obs("A", 1.0, 5.0), _obs("B", 2.0, 5.0)],
        }
    )
    assert metrics["ic_mean"] == pytest.approx(0.0)
    assert metrics["ic_std"] == pytest.approx(1.0)
    assert metrics["ic_ir"] == pytest.approx(0.0)
    assert metrics["ic_periods"] == 2.0


def test_ic_series_metrics_omits_ir_when_std_is_zero() -> None:
    metrics = ic_series_metrics(
        {
            "2024-01-01": [_obs("A", 1.0, 1.0), _obs("B", 2.0, 2.0)],
            "2024-01-02": [_obs("A", 3.0, 3.0), _obs("B", 4.0, 4.0)],
        }
    )
    assert metrics["ic_std"] == 0.0
    assert "ic_ir" not in metrics


def test_ic_series_metrics_empty_when_no_period_yields_ic() -> None:
    assert ic_series_metrics({}) == {}
    assert ic_series_metrics({"2024-01-01": [_obs("A", 1.0, 1.0)]}) == {}


def test_rank_autocorrelation_joins_refs() -> None:
    prev = {"A": 1.0, "B": 2.0, "C": 3.0}
    curr = {"A": 3.0, "B": 2.0, "C": 1.0, "D": 0.0}
    assert rank_autocorrelation(prev, curr) == pytest.approx(-1.0)


def test_rank_autocorrelation_is_none_for_small_or_degenerate_joins() -> None:
    assert rank_autocorrelation({"A": 1.0}, {"B": 2.0}) is None
    assert rank_autocorrelation({"A": 1.0, "B": 1.0}, {"A": 2.0, "B": 3.0}) is None
