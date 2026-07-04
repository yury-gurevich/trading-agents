"""Retrain-policy tests for rolling return-model evidence.

Agent: forecaster
Role: verify IC-decay and champion-comparison verdict branches.
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.domain.retrain_policy import compare_models, should_retrain
from agents.forecaster.settings import ForecasterSettings


def test_should_retrain_refuses_thin_recent_evidence() -> None:
    decision = should_retrain(
        {"complete_cases": 49.0, "ic_ir": 0.1},
        {"ic_ir": 0.2},
        trigger_fraction=0.5,
        min_cases=50.0,
    )
    assert decision.retrain is False
    assert decision.reason == "insufficient recent cases"
    assert decision.recent is None
    assert decision.reference is None


def test_should_retrain_refuses_undefined_metric() -> None:
    decision = should_retrain(
        {"complete_cases": 500.0},
        {"ic_ir": 0.2},
        trigger_fraction=0.5,
        min_cases=50.0,
    )
    assert decision.retrain is False
    assert decision.reason == "metric undefined"
    assert decision.recent is None
    assert decision.reference == 0.2


def test_should_retrain_on_non_positive_reference() -> None:
    decision = should_retrain(
        {"complete_cases": 500.0, "ic_ir": 0.01},
        {"ic_ir": 0.0},
        trigger_fraction=0.5,
        min_cases=50.0,
    )
    assert decision.retrain is True
    assert decision.reason == "reference non-positive"


def test_should_retrain_when_recent_decays_below_trigger() -> None:
    decision = should_retrain(
        {"complete_cases": 500.0, "ic_ir": 0.09},
        {"ic_ir": 0.2},
        trigger_fraction=0.5,
        min_cases=50.0,
    )
    assert decision.retrain is True
    assert decision.reason == "recent 0.0900 < trigger 0.1000"


def test_should_retrain_keeps_healthy_recent_signal() -> None:
    decision = should_retrain(
        {"complete_cases": 500.0, "ic_ir": 0.11},
        {"ic_ir": 0.2},
        trigger_fraction=0.5,
        min_cases=50.0,
    )
    assert decision.retrain is False
    assert decision.reason == "recent 0.1100 >= trigger 0.1000"


def test_compare_models_swaps_when_challenger_wins_both() -> None:
    verdict = compare_models(
        {"rank_ic": 0.01, "ic_ir": 0.1},
        {"rank_ic": 0.02, "ic_ir": 0.1},
    )
    assert verdict.swap is True
    assert verdict.reason == "challenger wins both metrics"
    assert verdict.primary_delta == 0.01
    assert verdict.secondary_delta == 0.0


def test_compare_models_rejects_primary_only_win() -> None:
    verdict = compare_models(
        {"rank_ic": 0.01, "ic_ir": 0.1},
        {"rank_ic": 0.02, "ic_ir": 0.09},
    )
    assert verdict.swap is False
    assert verdict.reason == "challenger did not win both"


def test_compare_models_rejects_secondary_only_win() -> None:
    verdict = compare_models(
        {"rank_ic": 0.02, "ic_ir": 0.1},
        {"rank_ic": 0.01, "ic_ir": 0.11},
    )
    assert verdict.swap is False
    assert verdict.primary_delta == -0.01
    assert verdict.secondary_delta is not None
    assert round(verdict.secondary_delta, 2) == 0.01


def test_compare_models_rejects_missing_challenger_metric() -> None:
    verdict = compare_models({"rank_ic": 0.01, "ic_ir": 0.1}, {"rank_ic": 0.02})
    assert verdict.swap is False
    assert verdict.reason == "challenger metric undefined"
    assert verdict.primary_delta is None


def test_compare_models_allows_defined_challenger_over_undefined_incumbent() -> None:
    verdict = compare_models({}, {"rank_ic": 0.02, "ic_ir": 0.1})
    assert verdict.swap is True
    assert verdict.reason == "incumbent metric undefined"


def test_forecaster_retrain_settings_defaults_and_bounds() -> None:
    settings = ForecasterSettings()
    assert settings.retrain_window_days == 60
    assert settings.retrain_trigger_fraction == 0.5
    assert settings.retrain_horizon_days == 20
    assert settings.retrain_min_cases == 500
