"""Neutral, admission and corrected metric-scale statements are source pinned.

Agent: testing
Role: compare the packet's statements with source constants and actual outputs.
External I/O: local fixture reads only.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from tests.score_arithmetic_analyst_support import scored_order, settings
from tests.score_arithmetic_support import fixture, recorded_order

from agents.analyst.domain import (
    signal_selection,
    technical_rules,
    technical_rules_event,
    technical_rules_pattern,
    technical_rules_range,
)
from agents.analyst.domain.recommend import decide
from agents.analyst.domain.scoring import ScoreBreakdown, _composite
from agents.analyst.tests.helpers import candidate
from agents.deliberator.context_arithmetic import arithmetic_lines, recompute
from contracts.analyst import QuantMetric, Recommendation

NORMALIZED = {
    "technical_score",
    "fundamental_score",
    "sentiment_score",
    "composite_score",
}


def test_band_neutral_constants_and_zero_signal_contribution_are_fifty() -> None:
    """DLIB-NEV-09: neutral is 50 in the source, with zero signal influence."""
    for module in (
        technical_rules,
        technical_rules_event,
        technical_rules_range,
        technical_rules_pattern,
        signal_selection,
    ):
        assert module._NEUTRAL == 50.0
    for pillar in ("technical", "fundamental", "sentiment"):
        assert (
            signal_selection._contribution(
                signal_selection.Signal("neutral", pillar, 50.0),
                {pillar: 0.7},
            )
            == 0.0
        )


@pytest.mark.parametrize("moved", [False, True])
def test_neutral_bands_and_rs_fifty_normalize_to_a_neutral_pillar(moved: bool) -> None:
    """DLIB-NEV-09: 50/100 is neutral 0.50, including the RS part of the blend."""
    _, rec = scored_order(settings(moved))
    sa = rec.score_arithmetic
    assert sa is not None
    neutral = rec.model_copy(
        update={
            "technical_score": 0.5,
            "fundamental_score": 0.5,
            "sentiment_score": 0.5,
            "confidence": sa.confidence_floor + sa.confidence_span * 0.5,
            "quant_metrics": tuple(
                QuantMetric(name=m.name, value=0.5 if m.name in NORMALIZED else 50.0)
                for m in rec.quant_metrics
            ),
        }
    )
    r = recompute(neutral, sa)
    assert r.present == {"technical": 0.5, "fundamental": 0.5, "sentiment": 0.5}
    assert _composite(0.5, 0.5, 0.5, None, settings(moved)) == r.composite == 0.5
    _, regime = recorded_order()
    assert len(arithmetic_lines(neutral, regime, neutral.ticker)) == 3


@pytest.mark.parametrize(
    ("offset", "admitted"), [(-2e-9, False), (0.0, True), (2e-9, True)]
)
def test_buy_admission_is_inclusive_at_the_regime_confidence_floor(
    offset: float, admitted: bool
) -> None:
    """DLIB-NEV-09 / ANLZ-OUT-02: below, equal and above pins the buy-only floor."""
    _, regime = recorded_order()
    # Empty legacy metrics isolate the admission gate from target-availability gates.
    score = ScoreBreakdown(
        technical_score=0.5, confidence=regime.base_min_confidence, metrics={}
    )
    decision = decide(
        candidate(), replace(score, confidence=score.confidence + offset), regime
    )
    assert (decision.recommendation is not None) == admitted
    if admitted:
        assert decision.recommendation.action == "buy"
    else:
        assert "below regime floor" in decision.rejection.reason


def test_recorded_score_keys_obey_the_corrected_four_exceptions() -> None:
    """DLIB-NEV-09: fixture and actual A6 output pin the four unit scores."""
    records = [
        Recommendation.model_validate(order["recommendation"])
        for order in fixture()["orders"]
    ]
    records += [
        scored_order(settings(moved), absent)[1]
        for moved in (False, True)
        for absent in ("none", "fundamental", "sentiment", "both")
    ]
    observed = set()
    for rec in records:
        q = {m.name: m.value for m in rec.quant_metrics}
        for name, value in q.items():
            if name.endswith("_score"):
                observed.add(name)
                assert 0.0 <= value <= (1.0 if name in NORMALIZED else 100.0), (
                    name,
                    value,
                )
        for name in NORMALIZED - {"composite_score"}:
            if name in q:
                assert q[name] == getattr(rec, name)
        if rec.score_arithmetic is not None:
            assert all(
                0.0 <= q[name] <= 100.0
                for name in rec.score_arithmetic.fundamental_sub_scores
            )
    assert observed >= NORMALIZED
    rec, regime = recorded_order()
    clause = (
        ", except technical_score, fundamental_score, sentiment_score and "
        "composite_score, "
        "which are on a 0-1 scale"
    )
    assert clause in arithmetic_lines(rec, regime, rec.ticker)[0]
