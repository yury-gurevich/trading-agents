"""Forecaster/researcher factor-copy parity tests.

Agent: forecaster
Role: pin duplicated factor semantics without creating cross-agent imports.
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.domain import factor_signal as forecaster
from agents.researcher.domain import factors as researcher


def test_forecaster_factor_copy_matches_researcher_catalogue_values() -> None:
    bars = {
        "A": _bars(10.0, 11.0, 12.0, 13.0, 14.0, 15.0),
        "B": _bars(10.0, 10.0, 10.0, 10.0, 20.0, 18.0),
    }
    cases = (
        ("momentum", {"lookback": 5}),
        ("mean_reversion", {"window": 5}),
        ("volatility_rank", {"window": 5}),
    )

    for name, params in cases:
        f_selection = forecaster.validate_selection(name, params)
        r_selection = researcher.validate_selection(name, params)
        assert f_selection is not None
        assert r_selection is not None
        assert forecaster.score(f_selection, bars) == researcher.score(
            r_selection, bars
        )


def _bars(*closes: float) -> list[tuple[str, float, float]]:
    return [
        (f"2024-01-{index:02d}", close, 100.0)
        for index, close in enumerate(closes, start=1)
    ]
