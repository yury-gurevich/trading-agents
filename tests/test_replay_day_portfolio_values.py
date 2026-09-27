"""Tests for replay PM portfolio state inputs.

Agent: tooling
Role: prove replay passes held market values to PM evaluation.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from scripts.replay_day import ReplayDayInputs, run_replay_day
from scripts.replay_settings import build_effective_settings

from contracts.analyst import Recommendation
from contracts.common import Explanation, Money
from contracts.provider import OHLCVBar
from contracts.scanner import FilterTrace

if TYPE_CHECKING:
    import pytest

    from agents.portfolio_manager.portfolio import PortfolioState
    from contracts.portfolio_manager import OrderIntent


def test_replay_day_passes_holding_market_values_to_pm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PM-NEV-06 / PM-NEV-08: held market values reach concentration gates."""
    settings = build_effective_settings(())
    session = date(2020, 1, 2)
    bar = OHLCVBar(
        ticker="AAA",
        bar_date=session,
        open=10.0,
        high=11.0,
        low=9.0,
        close=10.5,
        volume=100,
    )
    recommendation = Recommendation(
        ticker="BBB",
        action="buy",
        confidence=0.9,
        technical_score=0.8,
        suggested_stop_pct=0.05,
        suggested_target_pct=0.1,
        rationale=Explanation(summary="buy", evidence_refs=("fixture",)),
    )

    monkeypatch.setattr("scripts.replay_day.classify_regime", lambda *_: "neutral")
    monkeypatch.setattr(
        "scripts.replay_day.apply_filters",
        lambda *_args, **_kwargs: ((), FilterTrace(universe_size=1, evaluated=1)),
    )
    monkeypatch.setattr("scripts.replay_day.rank_survivors", lambda *_args, **_: ())
    monkeypatch.setattr("scripts.replay_day.scoring_universe", lambda value, _: value)
    monkeypatch.setattr(
        "scripts.replay_day.score_candidates", lambda *_args, **_kwargs: (object(),)
    )
    monkeypatch.setattr(
        "scripts.replay_day.split_decisions", lambda _: ((recommendation,), ())
    )

    def evaluate(
        recommendations: tuple[Recommendation, ...],
        prices: dict[str, Money],
        portfolio: PortfolioState,
        **kwargs: object,
    ) -> tuple[tuple[OrderIntent, ...], tuple[object, ...]]:
        del recommendations, prices, kwargs
        assert portfolio.position_values == {"AAA": Money(amount=Decimal("123.45"))}
        return (), ()

    monkeypatch.setattr("scripts.replay_day.evaluate_recommendations", evaluate)

    run_replay_day(
        ReplayDayInputs(
            run_id="replay-20200102",
            session=session,
            tickers=("AAA",),
            bars=(bar,),
            benchmark_bars=(bar.model_copy(update={"ticker": "SPY"}),),
            vix=None,
            equity_cents=100_000,
            held=(),
            held_stops=(),
            active_broker_stop_refs=frozenset(),
            sectors={},
            position_values={"AAA": Money(amount=Decimal("123.45"))},
        ),
        settings,
    )
