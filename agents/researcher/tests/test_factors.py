"""Researcher governed factor catalogue tests.

Agent: researcher
Role: verify catalogue bounds, pure factor scores, and proposal packaging.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.researcher.domain.factor_proposal import build_factor_proposal
from agents.researcher.domain.factors import CATALOGUE, score, validate_selection
from contracts.common import Provenance
from contracts.researcher import BacktestEvidence, FactorProposal


def test_catalogue_exposes_exactly_three_bounded_factors() -> None:
    assert tuple(CATALOGUE) == ("momentum", "mean_reversion", "volatility_rank")
    momentum = CATALOGUE["momentum"].parameters["lookback"]
    assert momentum.default == 20.0
    assert momentum.minimum == 5.0
    assert momentum.maximum == 120.0
    assert momentum.unit == "bars"
    assert "Momentum" in momentum.why


def test_validate_selection_returns_sorted_hashable_params() -> None:
    selection = validate_selection("momentum", {"lookback": 5}, rationale="test")

    assert selection is not None
    assert selection.name == "momentum"
    assert selection.params == (("lookback", 5.0),)
    assert hash(selection.params)


def test_validate_selection_fails_open_on_bad_catalogue_inputs() -> None:
    assert validate_selection("unknown", {"lookback": 5}) is None
    assert validate_selection("momentum", {}) is None
    assert validate_selection("momentum", {"lookback": "5"}) is None
    assert validate_selection("momentum", {"lookback": float("nan")}) is None
    assert validate_selection("momentum", {"lookback": 5.5}) is None
    assert validate_selection("momentum", {"lookback": 4}) is None
    assert validate_selection("momentum", {"lookback": 121}) is None


def test_momentum_scores_trailing_returns_without_lookahead() -> None:
    selection = validate_selection("momentum", {"lookback": 5})
    assert selection is not None
    bars = {
        "A": _bars(10.0, 11.0, 12.0, 13.0, 14.0, 15.0),
        "Z": _bars(0.0, 10.0, 10.0, 10.0, 10.0, 20.0),
    }

    scores = score(selection, bars)
    changed_future = {
        "A": _bars(10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 999.0),
        "Z": bars["Z"],
    }

    assert scores["2024-01-06"]["A"] == pytest.approx(0.5)
    assert "Z" not in scores["2024-01-06"]
    assert (
        score(selection, changed_future)["2024-01-06"]["A"] == scores["2024-01-06"]["A"]
    )


def test_mean_reversion_scores_negative_zscore_and_flat_neutral() -> None:
    selection = validate_selection("mean_reversion", {"window": 5})
    assert selection is not None

    scores = score(
        selection,
        {"A": _bars(10.0, 10.0, 10.0, 10.0, 20.0), "B": _bars(7.0, 7.0, 7.0, 7.0, 7.0)},
    )

    assert scores["2024-01-05"]["A"] == pytest.approx(-2.0)
    assert scores["2024-01-05"]["B"] == pytest.approx(0.0)


def test_volatility_rank_prefers_lower_realized_volatility() -> None:
    selection = validate_selection("volatility_rank", {"window": 5})
    assert selection is not None

    scores = score(
        selection,
        {
            "LOW": _bars(10.0, 10.1, 10.2, 10.3, 10.4),
            "HIGH": _bars(10.0, 15.0, 9.0, 18.0, 8.0),
        },
    )

    assert scores["2024-01-05"]["LOW"] > scores["2024-01-05"]["HIGH"]


def test_build_factor_proposal_round_trips_contract() -> None:
    selection = validate_selection("momentum", {"lookback": 5}, rationale="bounded")
    assert selection is not None
    evidence = _evidence()

    proposal = build_factor_proposal(
        selection,
        evidence,
        Provenance(run_id="factor-test", source_agent="researcher"),
        "factor-test",
    )
    parsed = FactorProposal.model_validate(proposal.model_dump(mode="json"))

    assert parsed.factor.name == "momentum"
    assert parsed.factor.params == (("lookback", 5.0),)
    assert parsed.factor.rationale.summary == "bounded"
    assert parsed.backtest == evidence


def _bars(*closes: float) -> list[tuple[str, float, float]]:
    return [
        (f"2024-01-{index:02d}", close, 100.0)
        for index, close in enumerate(closes, start=1)
    ]


def _evidence() -> BacktestEvidence:
    return BacktestEvidence(
        sharpe=1.0,
        ic_mean=0.1,
        max_drawdown=-0.05,
        turnover=0.2,
        n_days=10,
        window_start="2024-01-01",
        window_end="2024-01-10",
        holdout_sharpe=0.8,
        holdout_ic_mean=0.05,
        slippage_bps=10.0,
    )
