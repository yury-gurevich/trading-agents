"""Tests for S235 one-session replay choreography.

Agent: tooling
Role: verify replay calls fleet domain functions instead of copied stage logic.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from scripts.replay_day import ReplayDayInputs, run_replay_day
from scripts.replay_settings import build_effective_settings

from agents.scanner.domain.filters import Survivor
from contracts.analyst import Recommendation
from contracts.common import Explanation, Money
from contracts.portfolio_manager import OrderIntent
from contracts.provider import OHLCVBar, RegimeContext
from contracts.scanner import Candidate, CandidateSet, FilterTrace

if TYPE_CHECKING:
    import pytest

    from agents.portfolio_manager.portfolio import PortfolioState
    from agents.provider.sources import RegimeInputs
    from contracts.provider import MarketData


def test_replay_day_calls_fleet_stages_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S235-A6: replay day delegates every decision stage to the fleet functions."""
    observed: list[str] = []
    settings = build_effective_settings(("SCANNER_CANDIDATE_CAP=1",))
    bar = OHLCVBar(
        ticker="AAA",
        bar_date=date(2020, 1, 2),
        open=10.0,
        high=11.0,
        low=9.0,
        close=10.5,
        volume=100,
    )
    benchmark = bar.model_copy(update={"ticker": "SPY"})
    recommendation = Recommendation(
        ticker="AAA",
        action="buy",
        confidence=0.9,
        technical_score=0.8,
        suggested_stop_pct=0.05,
        suggested_target_pct=0.1,
        rationale=Explanation(summary="buy", evidence_refs=("fixture",)),
    )

    def classify(inputs: RegimeInputs, provider_settings: object) -> str:
        observed.append("classify")
        assert inputs.vix == 19.0
        assert provider_settings is settings.provider
        return "neutral"

    def filters(
        *args: object, **kwargs: object
    ) -> tuple[tuple[Survivor, ...], FilterTrace]:
        observed.append("filters")
        assert args[0] == ("AAA",)
        assert args[1] == (bar,)
        assert args[2] == (benchmark,)
        assert args[3] == {}
        assert kwargs["earnings_horizon_days"] is None
        return (
            (
                Survivor(
                    "AAA",
                    ("relative_strength",),
                    (),
                    {"relative_strength": 0.2, "average_volume": 100.0},
                ),
            ),
            FilterTrace(universe_size=1, evaluated=1),
        )

    def rank(survivors: tuple[Survivor, ...], *, cap: int) -> tuple[Candidate, ...]:
        observed.append("rank")
        assert len(survivors) == 1
        assert cap == 1
        return (
            Candidate(
                ticker="AAA",
                rank=1,
                score=0.2,
                survived_filters=("relative_strength",),
            ),
        )

    def score_universe(
        candidate_set: CandidateSet, held: tuple[object, ...]
    ) -> CandidateSet:
        observed.append("scoring_universe")
        assert held == ()
        return candidate_set

    def score_candidates(
        _candidate_set: CandidateSet,
        market: MarketData,
        regime: RegimeContext,
        *_args: object,
        **kwargs: object,
    ) -> tuple[object, ...]:
        observed.append("score")
        assert market.fundamentals == {}
        assert market.news == {}
        assert market.sentiment == {}
        assert market.earnings == {}
        assert regime.base_stop_loss_pct == settings.provider.base_stop_loss_pct
        assert kwargs["held_stops"] == ()
        assert kwargs["active_broker_stop_refs"] == frozenset()
        return (object(),)

    def split(
        decisions: tuple[object, ...],
    ) -> tuple[tuple[Recommendation, ...], tuple[object, ...]]:
        observed.append("split")
        assert len(decisions) == 1
        return (recommendation,), ()

    def evaluate(
        recommendations: tuple[Recommendation, ...],
        prices: dict[str, Money],
        portfolio: PortfolioState,
        **kwargs: object,
    ) -> tuple[tuple[OrderIntent, ...], tuple[object, ...]]:
        observed.append("evaluate")
        assert recommendations == (recommendation,)
        assert prices["AAA"] == Money(amount=Decimal("10.5"))
        assert portfolio.cash == Money(amount=Decimal("1000"))
        assert kwargs["default_stop_pct"] == settings.provider.base_stop_loss_pct
        return (
            (
                OrderIntent(
                    ticker="AAA",
                    action="buy",
                    quantity=1,
                    est_price=Money(amount=Decimal("10.5")),
                    stop_pct=0.05,
                    target_pct=0.1,
                    rationale=Explanation(summary="pm", evidence_refs=("fixture",)),
                ),
            ),
            (),
        )

    monkeypatch.setattr("scripts.replay_day.classify_regime", classify)
    monkeypatch.setattr("scripts.replay_day.apply_filters", filters)
    monkeypatch.setattr("scripts.replay_day.rank_survivors", rank)
    monkeypatch.setattr("scripts.replay_day.scoring_universe", score_universe)
    monkeypatch.setattr("scripts.replay_day.score_candidates", score_candidates)
    monkeypatch.setattr("scripts.replay_day.split_decisions", split)
    monkeypatch.setattr("scripts.replay_day.evaluate_recommendations", evaluate)

    result = run_replay_day(
        ReplayDayInputs(
            run_id="replay-20200102",
            session=date(2020, 1, 2),
            tickers=("AAA",),
            bars=(bar,),
            benchmark_bars=(benchmark,),
            vix=19.0,
            equity_cents=100_000,
            held=(),
            held_stops=(),
            active_broker_stop_refs=frozenset(),
            sectors={},
        ),
        settings,
    )

    assert observed == [
        "classify",
        "filters",
        "rank",
        "scoring_universe",
        "score",
        "split",
        "evaluate",
    ]
    assert result.absent_inputs == {
        "fundamentals": 1,
        "news": 1,
        "sentiment": 1,
        "earnings": 1,
        "deliberator": 1,
    }
    assert result.approved[0].ticker == "AAA"
