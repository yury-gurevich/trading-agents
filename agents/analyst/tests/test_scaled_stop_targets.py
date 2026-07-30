"""Volatility-scaled stop/target proposal tests for S150.

Agent: analyst
Role: prove stop/target scaling is opt-in, bounded, and degradable.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

import pytest
from pydantic import ValidationError

from agents.analyst.domain.recommend import decide
from agents.analyst.domain.scoring import ScoreBreakdown
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import candidate
from contracts.common import Provenance
from contracts.provider import RegimeContext
from kernel.config import AgentSettings, describe

if TYPE_CHECKING:
    from contracts.analyst import Recommendation


def test_flat_mode_applied_stop_and_target_ignore_atr() -> None:
    """ANLZ-OUT-02 / ANLZ-IDM-01: flat applied proposal is byte-stable."""
    low_atr = _recommendation(_score({"atr_pct": 2.1}), mode="flat")
    high_atr = _recommendation(_score({"atr_pct": 8.5}), mode="flat")

    assert low_atr.suggested_stop_pct == 0.05
    assert high_atr.suggested_stop_pct == 0.05
    assert low_atr.suggested_target_pct == 0.10
    assert high_atr.suggested_target_pct == 0.10


def test_scaled_mode_resolves_quiet_and_volatile_exact_values() -> None:
    """ANLZ-OUT-02 / ANLZ-IDM-01: scaled proposal follows ATR before caps."""
    quiet = _recommendation(_score({"atr_pct": 2.1}), mode="scaled")
    volatile = _recommendation(_score({"atr_pct": 3.2}), mode="scaled")

    assert quiet.suggested_stop_pct == pytest.approx(0.042)
    assert quiet.suggested_target_pct == pytest.approx(0.084)
    assert volatile.suggested_stop_pct == pytest.approx(0.064)
    assert volatile.suggested_target_pct == pytest.approx(0.128)


def test_scaled_mode_floor_and_risk_ceiling_clamp() -> None:
    """ANLZ-TYP-02 / ANLZ-FAIL-03: scaled rails bound tiny and huge ATR."""
    tiny = _recommendation(_score({"atr_pct": 0.1}), mode="scaled")
    huge = _recommendation(_score({"atr_pct": 99.0}), mode="scaled")

    assert tiny.suggested_stop_pct == 0.025
    assert huge.suggested_stop_pct == 0.08
    assert huge.suggested_stop_pct <= 0.08
    with pytest.raises(AssertionError):
        assert huge.suggested_stop_pct == pytest.approx(1.98)


def test_scaled_stop_knobs_are_tunables_and_mode_is_bounded() -> None:
    """ANLZ-PARAM / ADR-0013: scaled knobs are bounded tunables."""
    docs = {item.name: item for item in describe(AnalystSettings)}
    for name in _SCALED_TUNABLES:
        assert docs[name].justification
        assert docs[name].minimum is not None
        assert docs[name].maximum is not None
        assert docs[name].unit
    with pytest.raises(AssertionError):
        _assert_scaled_tunables(BareStopSettings)
    with pytest.raises(ValidationError):
        AnalystSettings.model_validate({"stop_target_mode": "wide"})
    with pytest.raises(ValidationError, match="floor"):
        AnalystSettings(scaled_stop_floor_pct=0.08, scaled_stop_ceiling_pct=0.025)


def test_resolution_is_deterministic_for_same_inputs() -> None:
    """ANLZ-IDM-01: same score, regime, and settings produce identical proposal."""
    score = _score({"atr_pct": 3.2})
    first = _recommendation(score, mode="scaled")
    second = _recommendation(score, mode="scaled")

    assert first.suggested_stop_pct == second.suggested_stop_pct
    assert first.suggested_target_pct == second.suggested_target_pct
    assert first.stop_target_evidence == second.stop_target_evidence


def test_missing_atr_falls_back_to_flat_without_suppressing_recommendation() -> None:
    """ANLZ-FAIL-03 / ANLZ-OUT-01 / DL-57: missing ATR degrades, never vetoes."""
    recommendation = _recommendation(_score({}), mode="scaled")

    assert recommendation.suggested_stop_pct == 0.05
    assert recommendation.suggested_target_pct == 0.10
    assert recommendation.stop_target_evidence is not None
    assert recommendation.stop_target_evidence.volatility_fallback is True
    with pytest.raises(AssertionError):
        assert recommendation is None


def test_nonsensical_atr_is_missing_or_clamped_not_trusted() -> None:
    """ANLZ-FAIL-03 / ANLZ-TYP-02: bad ATR never yields nonsense stops."""
    zero = _recommendation(_score({"atr_pct": 0.0}), mode="scaled")
    negative = _recommendation(_score({"atr_pct": -1.0}), mode="scaled")
    huge = _recommendation(_score({"atr_pct": 99.0}), mode="scaled")

    assert zero.suggested_stop_pct == 0.05
    assert negative.suggested_stop_pct == 0.05
    assert huge.suggested_stop_pct == 0.08


def test_zero_flat_stop_keeps_target_defined_when_scaled() -> None:
    """ANLZ-FAIL-03 / ANLZ-TYP-02: zero flat risk never divides target math."""
    decision = decide(
        candidate("AAPL"),
        _score({"atr_pct": 2.1}),
        _regime().model_copy(update={"base_stop_loss_pct": 0.0}),
        settings=AnalystSettings(stop_target_mode="scaled"),
    )

    assert decision.recommendation is not None
    assert decision.recommendation.suggested_stop_pct == pytest.approx(0.042)
    assert decision.recommendation.suggested_target_pct == 0.10


def test_sells_are_unchanged_under_scaled_mode() -> None:
    """ANLZ-NEV-01 / ANLZ-OUT-02: sell recommendations carry no entry stop."""
    decision = decide(
        candidate("AAPL"),
        _score({}, confidence=0.30),
        _regime(),
        held=True,
        exit_confidence_floor=0.70,
        settings=AnalystSettings(stop_target_mode="scaled"),
    )

    assert decision.recommendation is not None
    assert decision.recommendation.action == "sell"
    assert decision.recommendation.suggested_stop_pct is None
    assert decision.recommendation.suggested_target_pct is None
    assert decision.recommendation.stop_target_evidence is None


_SCALED_TUNABLES = (
    "scaled_stop_atr_multiplier",
    "scaled_stop_floor_pct",
    "scaled_stop_ceiling_pct",
)


class BareStopSettings(AgentSettings):
    scaled_stop_atr_multiplier: float = 2.0
    scaled_stop_floor_pct: float = 0.025
    scaled_stop_ceiling_pct: float = 0.08


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


def _regime() -> RegimeContext:
    return RegimeContext(
        label="risk_on",
        vix=12.0,
        as_of=datetime.now(tz=UTC),
        base_min_confidence=0.30,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="regime-fixture", source_agent="provider"),
    )


def _assert_scaled_tunables(settings_cls: type[AgentSettings]) -> None:
    docs = {item.name: item for item in describe(settings_cls)}
    for name in _SCALED_TUNABLES:
        field = docs[name]
        assert field.justification
        assert field.minimum is not None
        assert field.maximum is not None
        assert field.unit
