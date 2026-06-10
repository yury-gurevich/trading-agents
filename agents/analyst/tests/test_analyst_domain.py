"""Analyst domain scoring and recommendation tests.

Agent: analyst
Role: verify deterministic scoring and decision edge cases.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime

from agents.analyst.domain.recommend import decide
from agents.analyst.domain.scoring import score_candidate
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import bar, candidate
from contracts.common import Provenance
from contracts.provider import RegimeContext


def _regime(floor: float = 0.6) -> RegimeContext:
    return RegimeContext(
        label="risk_on",
        vix=12.0,
        as_of=datetime.now(tz=UTC),
        base_min_confidence=floor,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="regime-fixture", source_agent="provider"),
    )


def test_score_candidate_reports_insufficient_history() -> None:
    score = score_candidate(candidate(), (bar("AAPL", 0, 100.0),), AnalystSettings())

    decision = decide(candidate(), score, _regime())

    assert score.rejection_reason == "insufficient_market_history"
    assert decision.recommendation is None
    assert decision.rejection is not None
    assert decision.rejection.reason == "insufficient_market_history"


def test_zero_weight_scoring_returns_zero_confidence() -> None:
    settings = AnalystSettings(
        candidate_score_weight=0.0,
        momentum_weight=0.0,
        trend_weight=0.0,
        confidence_floor=0.0,
    )

    score = score_candidate(
        candidate(),
        (bar("AAPL", 2, 100.0), bar("AAPL", 0, 120.0)),
        settings,
    )

    assert score.technical_score == 0.0
    assert score.confidence == 0.0


def test_long_ma_component_is_neutral_without_long_history() -> None:
    settings = AnalystSettings(long_ma_bars=5)

    score = score_candidate(
        candidate(),
        (bar("AAPL", 2, 100.0), bar("AAPL", 0, 120.0)),
        settings,
    )

    assert score.metrics["trend_component"] == 0.5


def test_long_ma_component_uses_long_history_when_available() -> None:
    settings = AnalystSettings(long_ma_bars=5, short_ma_bars=2)

    score = score_candidate(
        candidate(),
        (
            bar("AAPL", 4, 100.0),
            bar("AAPL", 3, 102.0),
            bar("AAPL", 2, 104.0),
            bar("AAPL", 1, 106.0),
            bar("AAPL", 0, 108.0),
        ),
        settings,
    )

    assert score.metrics["trend_component"] > 0.5
