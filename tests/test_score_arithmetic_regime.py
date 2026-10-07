"""S255 provider threshold and VIX independence pins.

Agent: testing
Role: compare classification boundaries with recorded thresholds and scoring.
External I/O: local fixture reads only; all provider requests use a fake source.
"""

from __future__ import annotations

import pytest
from tests.score_arithmetic_analyst_support import FUNDAMENTALS, NEWS, bars, settings
from tests.score_arithmetic_regime_support import provider_settings, regime_for
from tests.veto_context_provider_fixtures import market_data

from agents.analyst.domain.analyze import score_candidates
from agents.analyst.tests.helpers import candidate, candidate_set
from contracts.provider import MarketData
from kernel import CollectingFaultSink


@pytest.mark.parametrize("moved", [False, True])
def test_provider_records_the_thresholds_at_every_classification_boundary(
    moved: bool,
) -> None:
    """PROV-OUT-02: below, at and above each threshold use the recorded settings."""
    config = provider_settings(moved)
    on, off, high, extreme = (
        config.vix_risk_on_threshold,
        config.vix_risk_off_threshold,
        config.vix_high_threshold,
        config.vix_extreme_threshold,
    )
    points = [
        (None, "neutral"),
        (on - 0.01, "risk_on"),
        (on, "risk_on"),
        (on + 0.01, "neutral"),
        (off - 0.01, "neutral"),
        (off, "risk_off"),
        (off + 0.01, "risk_off"),
        (high - 0.01, "risk_off"),
        (high, "high_volatility"),
        (high + 0.01, "high_volatility"),
        (extreme - 0.01, "high_volatility"),
        (extreme, "extreme_volatility"),
        (extreme + 0.01, "extreme_volatility"),
    ]
    for vix, label in points:
        regime = regime_for(vix, config)
        assert regime.label == label, (moved, vix)
        assert regime.vix_thresholds is not None
        assert regime.vix_thresholds.model_dump() == {
            "risk_on_at_or_below": on,
            "risk_off_from": off,
            "high_volatility_from": high,
            "extreme_volatility_from": extreme,
        }


@pytest.mark.parametrize("moved", [False, True])
def test_all_regime_labels_keep_the_same_four_policy_constants(moved: bool) -> None:
    """DLIB-NEV-09 / PROV-NEV-07: labels change none of the four base values."""
    config = provider_settings(moved)
    points = [
        config.vix_risk_on_threshold,
        (config.vix_risk_on_threshold + config.vix_risk_off_threshold) / 2,
        config.vix_risk_off_threshold,
        config.vix_high_threshold,
        config.vix_extreme_threshold,
        None,
    ]
    regimes = [regime_for(vix, config) for vix in points]
    assert {r.label for r in regimes} == {
        "risk_on",
        "neutral",
        "risk_off",
        "high_volatility",
        "extreme_volatility",
    }
    for name in (
        "base_min_confidence",
        "base_stop_loss_pct",
        "base_take_profit_pct",
        "base_max_holding_days",
    ):
        assert {getattr(r, name) for r in regimes} == {getattr(config, name)}


def test_vix_and_regime_labels_do_not_change_real_analyst_scores() -> None:
    """DLIB-NEV-09: the full batch scorer gives the same candidate the same scores."""
    config = provider_settings()
    market = MarketData.model_validate(market_data(True)).model_copy(
        update={
            "bars": bars(),
            "fundamentals": {"AAPL": FUNDAMENTALS},
            "news": {"AAPL": NEWS},
        }
    )
    output = []
    for vix in (config.vix_risk_on_threshold, config.vix_extreme_threshold):
        sink = CollectingFaultSink()
        decisions = score_candidates(
            candidate_set(candidate()),
            market,
            regime_for(vix, config),
            bars("SPY"),
            settings(),
            sink,
            held_tickers=("AAPL",),
        )
        assert decisions is not None
        assert not sink.faults
        rec = decisions[0].recommendation
        assert rec is not None
        output.append(rec)
    assert output[0] == output[1]
