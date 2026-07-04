"""Return scorecard math tests — IC, hit rate, directional breakdown.

Agent: forecaster
Role: verify return_scorecard_metrics over known observations +
      build_return_observations alignment from a fake graph.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.forecaster.domain.return_scorecard import (
    ReturnObservation,
    build_return_observations,
    return_scorecard_metrics,
)
from kernel import InMemoryGraphStore


def _obs(
    predicted: float,
    forward_return: float,
    subject_ref: str = "AAPL",
) -> ReturnObservation:
    return ReturnObservation(subject_ref, predicted, forward_return)


def test_return_scorecard_metrics_empty() -> None:
    assert return_scorecard_metrics([]) == {}


def test_return_scorecard_metrics_single_case_no_ic() -> None:
    metrics = return_scorecard_metrics([_obs(0.7, 0.03)])
    assert metrics["complete_cases"] == 1.0
    assert "ic" not in metrics  # Pearson undefined for n < 2
    assert "rank_ic" not in metrics
    assert "q1_mean_ret" not in metrics
    assert metrics["hit_rate"] == 1.0  # 0.7 > 0.5 and 0.03 > 0 → hit
    assert metrics["mean_up_pred"] == pytest.approx(0.7)
    assert "mean_down_pred" not in metrics


def test_return_scorecard_metrics_two_correct_calls_ic_defined() -> None:
    # Both predict up (>0.5) and both actually up → IC = 1.0, hit_rate = 1.0
    obs = [_obs(0.6, 0.02), _obs(0.8, 0.05)]
    metrics = return_scorecard_metrics(obs)
    assert metrics["complete_cases"] == 2.0
    assert "ic" in metrics
    assert metrics["hit_rate"] == 1.0


def test_return_scorecard_metrics_all_wrong_direction() -> None:
    # Predict up (>0.5) but actual down → hit_rate = 0
    obs = [_obs(0.7, -0.02), _obs(0.9, -0.05)]
    metrics = return_scorecard_metrics(obs)
    assert metrics["hit_rate"] == 0.0
    assert "mean_up_pred" not in metrics
    assert "mean_down_pred" in metrics


def test_return_scorecard_metrics_constant_predictions_no_ic() -> None:
    obs = [_obs(0.6, 0.01), _obs(0.6, -0.01)]
    metrics = return_scorecard_metrics(obs)
    assert "ic" not in metrics  # constant predicted → zero variance


def test_return_scorecard_metrics_up_down_breakdown() -> None:
    obs = [_obs(0.8, 0.05), _obs(0.3, -0.02)]
    metrics = return_scorecard_metrics(obs)
    assert metrics["mean_up_pred"] == pytest.approx(0.8)
    assert metrics["mean_down_pred"] == pytest.approx(0.3)


def test_return_scorecard_metrics_adds_rank_and_quantile_keys() -> None:
    obs = [
        _obs(0.10, -0.05, "T0"),
        _obs(0.20, -0.04, "T1"),
        _obs(0.30, -0.03, "T2"),
        _obs(0.40, -0.02, "T3"),
        _obs(0.45, -0.01, "T4"),
        _obs(0.55, 0.01, "T5"),
        _obs(0.60, 0.02, "T6"),
        _obs(0.70, 0.03, "T7"),
        _obs(0.80, 0.04, "T8"),
        _obs(0.90, 0.05, "T9"),
    ]
    metrics = return_scorecard_metrics(obs)
    assert metrics["complete_cases"] == 10.0
    assert metrics["hit_rate"] == 1.0
    assert metrics["mean_up_pred"] == pytest.approx(0.71)
    assert metrics["mean_down_pred"] == pytest.approx(0.29)
    assert metrics["rank_ic"] == pytest.approx(1.0)
    assert metrics["q1_mean_ret"] == pytest.approx(-0.045)
    assert metrics["q5_mean_ret"] == pytest.approx(0.045)
    assert metrics["top_bottom_spread"] == pytest.approx(0.09)


def test_return_scorecard_metrics_supports_raw_return_threshold() -> None:
    obs = [_obs(-0.02, -0.01), _obs(0.03, 0.01)]
    metrics = return_scorecard_metrics(obs, neutral_prediction=0.0)
    assert metrics["hit_rate"] == 1.0


def test_build_return_observations_aligns_by_subject_ref() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "ShadowPrediction",
        "lgbm-return-v1:AAPL:run1",
        {"subject_ref": "AAPL", "model_id": "lgbm-return-v1", "value": 0.7},
    )
    obs = build_return_observations(graph, "lgbm-return-v1", {"AAPL": 0.03})
    assert len(obs) == 1
    assert obs[0].subject_ref == "AAPL"
    assert obs[0].predicted == pytest.approx(0.7)
    assert obs[0].forward_return == pytest.approx(0.03)


def test_build_return_observations_skips_missing_forward_return() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "ShadowPrediction",
        "lgbm-return-v1:MSFT:run1",
        {"subject_ref": "MSFT", "model_id": "lgbm-return-v1", "value": 0.6},
    )
    obs = build_return_observations(graph, "lgbm-return-v1", {"AAPL": 0.03})
    assert obs == []


def test_build_return_observations_filters_by_model_id() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "ShadowPrediction",
        "other-model:AAPL:run1",
        {"subject_ref": "AAPL", "model_id": "other-model", "value": 0.9},
    )
    obs = build_return_observations(graph, "lgbm-return-v1", {"AAPL": 0.03})
    assert obs == []
