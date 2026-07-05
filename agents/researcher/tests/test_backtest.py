"""Researcher walk-forward backtest tests.

Agent: researcher
Role: verify no-lookahead fills, slippage, IC, drawdown, and evidence conversion.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.researcher.domain import backtest


def test_next_close_fill_prevents_score_date_lookahead() -> None:
    closes = {
        "A": _series(10.0, 11.0, 22.0, 44.0),
        "B": _series(10.0, 10.0, 10.0, 10.0),
    }
    scores = {
        "2024-01-01": {"A": 1.0, "B": 0.0},
        "2024-01-02": {"A": 0.0, "B": 999.0},
        "2024-01-03": {"A": 0.0, "B": 999.0},
    }

    result = backtest.run_walkforward(
        scores, closes, top_k=1, slippage_bps=0.0, holdout_fraction=0.5
    )

    assert result.legs[0].holdings == ("A",)
    assert result.returns[0] == pytest.approx(1.0)
    assert result.legs[1].holdings == ("B",)


def test_turnover_and_slippage_are_charged_per_rebalance() -> None:
    closes = {ticker: _series(10.0, 10.0, 11.0, 12.1) for ticker in ("A", "B", "C")}
    scores = {
        "2024-01-01": {"A": 3.0, "B": 2.0, "C": 1.0},
        "2024-01-02": {"A": 3.0, "B": 1.0, "C": 2.0},
        "2024-01-03": {"A": 3.0, "B": 1.0, "C": 2.0},
    }

    result = backtest.run_walkforward(
        scores, closes, top_k=2, slippage_bps=100.0, holdout_fraction=0.5
    )

    assert [leg.turnover for leg in result.legs] == [1.0, 0.5]
    assert result.returns == pytest.approx((0.09, 0.095))


def test_max_drawdown_and_holdout_split_use_known_curve() -> None:
    closes = {"A": _dated((1, 10.0), (2, 100.0), (3, 110.0), (4, 88.0), (5, 92.4))}
    scores = {
        "2024-01-01": {"A": 1.0},
        "2024-01-02": {"A": 1.0},
        "2024-01-03": {"A": 1.0},
        "2024-01-04": {"A": 1.0},
    }

    result = backtest.run_walkforward(
        scores, closes, top_k=1, slippage_bps=0.0, holdout_fraction=0.34
    )

    assert result.returns == pytest.approx((0.1, -0.2, 0.05))
    assert result.max_drawdown == pytest.approx(-0.2)
    assert result.holdout_n_days == 2
    assert result.window_start == "2024-01-01"
    assert result.window_end == "2024-01-04"


def test_missing_prices_drop_tickers_without_fabricated_fills() -> None:
    closes = {
        "A": _dated((1, 10.0), (2, 10.0), (3, 12.0)),
        "B": _dated((1, 10.0), (2, 20.0)),
    }
    scores = {
        "2024-01-01": {"A": 2.0, "B": 1.0},
        "2024-01-02": {"A": 2.0, "B": 1.0},
    }

    result = backtest.run_walkforward(
        scores, closes, top_k=2, slippage_bps=0.0, holdout_fraction=0.5
    )

    assert result.legs[0].holdings == ("A",)
    assert result.legs[0].fill_count == 1
    assert result.returns == pytest.approx((0.2,))


def test_ic_mean_skips_undefined_dates() -> None:
    closes = {
        "A": _series(10.0, 10.0, 10.0, 12.0),
        "B": _series(10.0, 10.0, 10.0, 9.0),
    }
    scores = {
        "2024-01-01": {"A": 1.0, "B": 1.0},
        "2024-01-02": {"A": 2.0, "B": 1.0},
        "2024-01-03": {"A": 2.0, "B": 1.0},
    }

    result = backtest.run_walkforward(
        scores, closes, top_k=2, slippage_bps=0.0, holdout_fraction=0.5
    )

    assert result.legs[0].ic is None
    assert result.ic_mean == pytest.approx(1.0)


def test_empty_and_invalid_inputs_fail_honestly() -> None:
    empty = backtest.run_walkforward(
        {"2024-01-01": {"MISSING": 1.0}, "2024-01-02": {"MISSING": 1.0}},
        {},
        top_k=1,
        slippage_bps=0.0,
        holdout_fraction=0.5,
    )

    assert empty.n_days == 0
    assert empty.ic_mean is None
    with pytest.raises(ValueError, match="ic_mean is undefined"):
        backtest.to_evidence(empty, slippage_bps=0.0)
    with pytest.raises(ValueError, match="top_k"):
        backtest.run_walkforward(
            {}, {}, top_k=0, slippage_bps=0.0, holdout_fraction=0.5
        )
    with pytest.raises(ValueError, match="slippage"):
        backtest.run_walkforward(
            {}, {}, top_k=1, slippage_bps=-1.0, holdout_fraction=0.5
        )
    with pytest.raises(ValueError, match="holdout"):
        backtest.run_walkforward(
            {}, {}, top_k=1, slippage_bps=0.0, holdout_fraction=0.0
        )
    assert backtest._turnover((), ()) == 0.0
    assert backtest._pearson([1.0], [1.0, 2.0]) is None


def test_to_evidence_carries_complete_metrics() -> None:
    closes = {
        "A": _series(10.0, 10.0, 10.0, 12.0),
        "B": _series(10.0, 10.0, 10.0, 9.0),
    }
    scores = {
        "2024-01-01": {"A": 2.0, "B": 1.0},
        "2024-01-02": {"A": 2.0, "B": 1.0},
        "2024-01-03": {"A": 2.0, "B": 1.0},
    }

    result = backtest.run_walkforward(
        scores, closes, top_k=2, slippage_bps=10.0, holdout_fraction=0.5
    )
    evidence = backtest.to_evidence(result, slippage_bps=10.0)

    assert evidence.engine == "walkforward-v1"
    assert evidence.ic_mean == pytest.approx(1.0)
    assert evidence.slippage_bps == 10.0


def _series(*prices: float) -> list[tuple[str, float]]:
    return _dated(*enumerate(prices, start=1))


def _dated(*pairs: tuple[int, float]) -> list[tuple[str, float]]:
    return [(f"2024-01-{day:02d}", price) for day, price in pairs]
