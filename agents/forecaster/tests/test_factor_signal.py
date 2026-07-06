"""Forecaster factor-signal domain tests.

Agent: forecaster
Role: verify governed factor bounds, scoring semantics, and no-lookahead fences.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.forecaster.domain import factor_signal


def test_catalogue_matches_s113_names_and_bounds() -> None:
    assert tuple(factor_signal.CATALOGUE) == (
        "momentum",
        "mean_reversion",
        "volatility_rank",
    )
    assert factor_signal.CATALOGUE["momentum"].parameter == "lookback"
    assert factor_signal.CATALOGUE["momentum"].minimum == 5.0
    assert factor_signal.CATALOGUE["momentum"].maximum == 120.0


def test_parse_selection_validates_operator_settings() -> None:
    selection = factor_signal.parse_selection("momentum", "lookback=5")

    assert selection is not None
    assert selection.params == (("lookback", 5.0),)
    assert factor_signal.model_id(selection) == "factor-momentum-5"
    assert factor_signal.model_ref(selection) == "factor:momentum:lookback=5"


def test_invalid_selection_fails_closed_to_disabled() -> None:
    assert factor_signal.parse_selection("", "lookback=5") is None
    assert factor_signal.parse_selection("missing", "lookback=5") is None
    assert factor_signal.parse_selection("momentum", "") is None
    assert factor_signal.parse_selection("momentum", "lookback") is None
    assert factor_signal.parse_selection("momentum", "=5") is None
    assert factor_signal.parse_selection("momentum", "lookback=") is None
    assert factor_signal.parse_selection("momentum", "lookback=bad") is None
    assert factor_signal.parse_selection("momentum", "lookback=5,lookback=6") is None
    assert factor_signal.parse_selection("momentum", "window=5") is None
    assert factor_signal.validate_selection("momentum", {"lookback": "5"}) is None
    assert factor_signal.validate_selection("momentum", {"lookback": 5.5}) is None
    assert (
        factor_signal.validate_selection("momentum", {"lookback": float("nan")}) is None
    )
    assert factor_signal.validate_selection("momentum", {"lookback": 4}) is None
    assert factor_signal.validate_selection("momentum", {"lookback": 121}) is None


def test_momentum_scores_do_not_look_ahead() -> None:
    selection = factor_signal.parse_selection("momentum", "lookback=5")
    assert selection is not None
    base = {"A": _bars(10.0, 11.0, 12.0, 13.0, 14.0, 15.0)}
    future = {"A": [*base["A"], ("2024-01-07", 999.0, 100.0)]}

    scores = factor_signal.score(selection, base)

    assert scores["2024-01-06"]["A"] == pytest.approx(0.5)
    assert (
        factor_signal.score(selection, future)["2024-01-06"]["A"]
        == scores["2024-01-06"]["A"]
    )
    assert factor_signal.latest_score(selection, {}) is None


def test_momentum_scores_skip_non_positive_base_price() -> None:
    selection = factor_signal.parse_selection("momentum", "lookback=5")
    assert selection is not None

    assert (
        factor_signal.score(selection, {"A": _bars(0.0, 1.0, 2.0, 3.0, 4.0, 5.0)}) == {}
    )


def test_mean_reversion_and_volatility_values_are_deterministic() -> None:
    reversion = factor_signal.parse_selection("mean_reversion", "window=5")
    volatility = factor_signal.parse_selection("volatility_rank", "window=5")
    assert reversion is not None
    assert volatility is not None

    reversion_scores = factor_signal.score(
        reversion,
        {
            "A": _bars(10.0, 10.0, 10.0, 10.0, 20.0),
            "B": _bars(7.0, 7.0, 7.0, 7.0, 7.0),
        },
    )
    volatility_scores = factor_signal.score(
        volatility,
        {
            "LOW": _bars(10.0, 10.1, 10.2, 10.3, 10.4),
            "HIGH": _bars(10.0, 15.0, 9.0, 18.0, 8.0),
        },
    )

    assert reversion_scores["2024-01-05"]["A"] == pytest.approx(-2.0)
    assert reversion_scores["2024-01-05"]["B"] == pytest.approx(0.0)
    assert (
        volatility_scores["2024-01-05"]["LOW"] > volatility_scores["2024-01-05"]["HIGH"]
    )


def _bars(*closes: float) -> list[tuple[str, float, float]]:
    return [
        (f"2024-01-{index:02d}", close, 100.0)
        for index, close in enumerate(closes, start=1)
    ]
