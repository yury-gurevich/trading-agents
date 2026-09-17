"""Measured stop/target evidence tests for S211.

Agent: analyst
Role: prove measured target evidence changes targets without moving stops.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal, cast

import pytest

from agents.analyst.domain.recommend import decide
from agents.analyst.domain.scoring import ScoreBreakdown
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import candidate
from contracts.common import Provenance
from contracts.provider import RegimeContext

if TYPE_CHECKING:
    from contracts.analyst import Recommendation


def test_measured_target_evidence_keeps_stop_values_unchanged() -> None:
    """ANLZ-OBS-06 / ANLZ-TYP-01: measured targets keep stops auditable."""
    flat = _recommendation(_score(_target_metrics(0.12, atr_pct=3.2)), mode="flat")
    scaled = _recommendation(_score(_target_metrics(0.12, atr_pct=3.2)), mode="scaled")

    assert flat.suggested_stop_pct == 0.05
    assert scaled.suggested_stop_pct == pytest.approx(0.064)
    assert flat.suggested_target_pct == pytest.approx(0.12)
    assert scaled.suggested_target_pct == pytest.approx(0.12)
    assert scaled.stop_target_evidence is not None
    assert scaled.stop_target_evidence.favorable_excursion_pct == pytest.approx(0.12)
    assert scaled.stop_target_evidence.favorable_excursion_horizon_days == 10
    assert scaled.stop_target_evidence.favorable_excursion_sample_count == 5


def test_unavailable_measured_target_is_rejected_not_flattened() -> None:
    """ANLZ-OBS-06 / ANLZ-OUT-03: unavailable target estimate is visible."""
    decision = decide(
        candidate("AAPL"),
        _score(
            {
                "favorable_excursion_horizon_days": 10.0,
                "favorable_excursion_lookback_windows": 120.0,
                "favorable_excursion_sample_count": 0.0,
            }
        ),
        _regime(),
        settings=AnalystSettings(stop_target_mode="scaled"),
    )

    assert decision.recommendation is None
    assert decision.rejection is not None
    assert decision.rejection.reason == "target_estimate_unavailable"


def test_legacy_scaled_target_handles_zero_flat_stop() -> None:
    """ANLZ-OBS-06 / ANLZ-TYP-01: legacy target math avoids division by zero."""
    decision = decide(
        candidate("AAPL"),
        _score({"atr_pct": 3.2}),
        _regime(stop_pct=0.0),
        settings=AnalystSettings(stop_target_mode="scaled"),
    )

    assert decision.recommendation is not None
    assert decision.recommendation.suggested_target_pct == pytest.approx(0.10)


@pytest.mark.parametrize(
    "metrics",
    [
        cast(
            "dict[str, float]",
            {
                "favorable_excursion_pct": 0.12,
                "favorable_excursion_horizon_days": 10.0,
                "favorable_excursion_lookback_windows": 120.0,
                "favorable_excursion_sample_count": None,
            },
        ),
        {
            "favorable_excursion_pct": 0.12,
            "favorable_excursion_horizon_days": 10.0,
            "favorable_excursion_lookback_windows": 120.0,
            "favorable_excursion_sample_count": -1.0,
        },
        {
            "favorable_excursion_horizon_days": 10.0,
            "favorable_excursion_lookback_windows": 120.0,
            "favorable_excursion_sample_count": 5.0,
        },
    ],
)
def test_incomplete_measured_target_evidence_is_unavailable(
    metrics: dict[str, float],
) -> None:
    """ANLZ-OBS-06 / ANLZ-TYP-02: target evidence must be complete."""
    decision = decide(
        candidate("AAPL"),
        _score(metrics),
        _regime(),
        settings=AnalystSettings(stop_target_mode="flat"),
    )

    assert decision.recommendation is None
    assert decision.rejection is not None
    assert decision.rejection.reason == "target_estimate_unavailable"


def _recommendation(
    score: ScoreBreakdown, *, mode: Literal["flat", "scaled"]
) -> Recommendation:
    decision = decide(
        candidate("AAPL"),
        score,
        _regime(),
        settings=AnalystSettings(stop_target_mode=mode),
    )
    assert decision.recommendation is not None
    return decision.recommendation


def _score(metrics: dict[str, float], *, confidence: float = 0.81) -> ScoreBreakdown:
    return ScoreBreakdown(
        technical_score=0.72,
        confidence=confidence,
        metrics=metrics,
    )


def _target_metrics(target_pct: float, *, atr_pct: float) -> dict[str, float]:
    return {
        "atr_pct": atr_pct,
        "favorable_excursion_pct": target_pct,
        "favorable_excursion_horizon_days": 10.0,
        "favorable_excursion_lookback_windows": 120.0,
        "favorable_excursion_sample_count": 5.0,
    }


def _regime(*, stop_pct: float = 0.05) -> RegimeContext:
    return RegimeContext(
        label="risk_on",
        vix=12.0,
        as_of=datetime.now(tz=UTC),
        base_min_confidence=0.30,
        base_stop_loss_pct=stop_pct,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="regime-fixture", source_agent="provider"),
    )
