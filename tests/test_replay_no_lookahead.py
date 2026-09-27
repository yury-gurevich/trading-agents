"""Tests for S235 decision no-lookahead behavior.

Agent: tooling
Role: verify session decisions ignore bars after the decision date.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from scripts.replay_day import ReplayDayInputs, run_replay_day
from scripts.replay_settings import build_effective_settings

from agents.scanner.domain.filters import Survivor
from contracts.analyst import Recommendation
from contracts.common import Explanation, Money
from contracts.portfolio_manager import OrderIntent
from contracts.provider import OHLCVBar
from contracts.scanner import Candidate, FilterTrace

if TYPE_CHECKING:
    import pytest

    from agents.portfolio_manager.portfolio import PortfolioState


def test_replay_day_decision_ignores_bars_after_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S235-A1: decisions for d match with or without bars after d."""
    settings = build_effective_settings(())
    session = date(2020, 1, 2)
    bar = _bar("AAA", session, 10.0)
    future = _bar("AAA", date(2020, 1, 3), 99.0)
    benchmark = _bar("SPY", session, 20.0)
    recommendation = Recommendation(
        ticker="AAA",
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
        lambda *_args, **_kwargs: (
            (
                Survivor(
                    "AAA",
                    ("relative_strength",),
                    (),
                    {"relative_strength": 0.2, "average_volume": 100.0},
                ),
            ),
            FilterTrace(universe_size=1, evaluated=1),
        ),
    )
    monkeypatch.setattr(
        "scripts.replay_day.rank_survivors",
        lambda survivors, *, cap: (
            Candidate(
                ticker=survivors[0].ticker,
                rank=1,
                score=0.2,
                survived_filters=("relative_strength",),
            ),
        ),
    )
    monkeypatch.setattr("scripts.replay_day.scoring_universe", lambda value, _: value)
    monkeypatch.setattr(
        "scripts.replay_day.score_candidates", lambda *_args, **_kwargs: (object(),)
    )
    monkeypatch.setattr(
        "scripts.replay_day.split_decisions", lambda _: ((recommendation,), ())
    )
    monkeypatch.setattr("scripts.replay_day.evaluate_recommendations", _evaluate)

    base = _day_inputs(session, (bar,), (benchmark,))
    with_future = _day_inputs(session, (bar, future), (benchmark, future))

    assert (
        run_replay_day(base, settings).approved
        == run_replay_day(with_future, settings).approved
    )


def _evaluate(
    recommendations: tuple[Recommendation, ...],
    prices: dict[str, Money],
    portfolio: PortfolioState,
    **kwargs: object,
) -> tuple[tuple[OrderIntent, ...], tuple[object, ...]]:
    del recommendations, portfolio, kwargs
    return (
        (
            OrderIntent(
                ticker="AAA",
                action="buy",
                quantity=1,
                est_price=prices["AAA"],
                stop_pct=0.05,
                rationale=Explanation(summary="pm", evidence_refs=("fixture",)),
            ),
        ),
        (),
    )


def _day_inputs(
    session: date,
    bars: tuple[OHLCVBar, ...],
    benchmark: tuple[OHLCVBar, ...],
) -> ReplayDayInputs:
    return ReplayDayInputs(
        run_id="replay-20200102",
        session=session,
        tickers=("AAA",),
        bars=bars,
        benchmark_bars=benchmark,
        vix=None,
        equity_cents=100_000,
        held=(),
        held_stops=(),
        active_broker_stop_refs=frozenset(),
        sectors={},
    )


def _bar(ticker: str, day: date, close: float) -> OHLCVBar:
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=close,
        high=close,
        low=close,
        close=close,
        volume=100,
    )
