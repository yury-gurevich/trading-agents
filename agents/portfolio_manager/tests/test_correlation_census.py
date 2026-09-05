"""Correlated-cluster census tests.

Agent: portfolio_manager
Role: prove the cluster gate reports the size of the comparison behind its verdict.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.correlation import CorrelationBook
from agents.portfolio_manager.domain.correlation_census import (
    CorrelationCensus,
    build_census,
)
from agents.portfolio_manager.tests.s184_helpers import buy
from contracts.provider import OHLCVBar

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

_HELD = {
    "BAC": ("BAC",),
    "C": ("C",),
    "SCHW": ("SCHW",),
}
_MEASURED: Mapping[str, tuple[float | None, int]] = {
    "BAC": (0.7639, 120),
    "C": (0.5650, 120),
    "SCHW": (0.3180, 120),
}


def _pair_from(
    table: Mapping[str, tuple[float | None, int]],
) -> Callable[[str, str], tuple[float | None, int]]:
    def pair(_candidate: str, held: str) -> tuple[float | None, int]:
        return table[held]

    return pair


def _census(
    table: Mapping[str, tuple[float | None, int]],
    tickers: Mapping[str, tuple[str, ...]],
    *,
    min_bars: int = 60,
) -> CorrelationCensus:
    return build_census(
        candidate_ticker="USB",
        candidate_issuer="USB",
        issuer_keys=(*tickers, "USB"),
        issuer_tickers=tickers,
        pair=_pair_from(table),
        threshold=0.70,
        min_bars=min_bars,
    )


def test_census_names_the_issuers_it_examined_and_the_ones_it_ruled_out() -> None:
    """PM-OBS-03: a cluster of one reports the comparisons that produced it."""
    census = _census(_MEASURED, _HELD)

    assert census.clustered() == ("BAC",)
    assert census.detail() == (
        "examined_issuers=3; "
        "correlated_issuers=BAC:0.7639; "
        "below_threshold_top=C:0.5650,SCHW:0.3180; "
        "correlation_threshold=0.7000; "
        "min_pair_overlap_bars=120"
    )


def test_a_census_of_nothing_says_so_rather_than_rendering_as_a_clean_pass() -> None:
    """PM-OBS-03: examined nothing and found nothing are not the same string."""
    census = _census({}, {})

    assert census.clustered() == ()
    assert census.detail() == (
        "examined_issuers=0; "
        "correlated_issuers=none; "
        "below_threshold_top=none; "
        "correlation_threshold=0.7000; "
        "min_pair_overlap_bars=none"
    )


def test_below_threshold_list_is_ranked_and_capped_at_three() -> None:
    """PM-OBS-03: the near misses are the strongest three, in order."""
    table: Mapping[str, tuple[float | None, int]] = {
        "AAA": (0.10, 120),
        "BBB": (0.60, 120),
        "CCC": (0.55, 120),
        "DDD": (0.40, 90),
        "EEE": (0.65, 120),
    }
    census = _census(table, {name: (name,) for name in table})

    assert "below_threshold_top=EEE:0.6500,BBB:0.6000,CCC:0.5500" in census.detail()
    assert "min_pair_overlap_bars=90" in census.detail()


def test_an_unmeasurable_pair_is_labelled_and_ranked_last() -> None:
    """PM-OBS-03: a pair with no defined correlation is reported, never omitted."""
    table: Mapping[str, tuple[float | None, int]] = {
        "AAA": (None, 120),
        "BBB": (0.20, 120),
    }
    census = _census(table, {name: (name,) for name in table})

    assert "examined_issuers=2" in census.detail()
    assert "below_threshold_top=BBB:0.2000,AAA:unmeasured" in census.detail()


def test_a_thin_pair_is_excluded_from_correlation_but_counted_in_overlap() -> None:
    """PM-OBS-03: min_correlation_bars is visible as the overlap it enforced."""
    table: Mapping[str, tuple[float | None, int]] = {"AAA": (0.99, 30)}
    census = _census(table, {"AAA": ("AAA",)}, min_bars=60)

    assert census.clustered() == ()
    assert "below_threshold_top=AAA:unmeasured" in census.detail()
    assert "min_pair_overlap_bars=30" in census.detail()


def test_a_multi_ticker_issuer_is_judged_on_its_strongest_pair() -> None:
    """PM-NEV-07 / PM-OBS-03: share classes collapse to one issuer comparison."""
    table: Mapping[str, tuple[float | None, int]] = {
        "GOOG": (0.20, 120),
        "GOOGL": (0.85, 120),
    }
    census = _census(table, {"GOOG": ("GOOG", "GOOGL")})

    assert census.clustered() == ("GOOG",)
    assert "correlated_issuers=GOOG:0.8500" in census.detail()


def test_gate_detail_carries_the_census_beside_the_cluster() -> None:
    """PM-OBS-03: the census reaches the gate_report the deliberator reads."""
    book = CorrelationBook(
        (*_bars("AAPL", days=66), *_bars("MSFT", days=66, drift=1.01)),
        {},
        120,
        0.70,
        0.25,
        60,
    )

    outcomes = book.outcomes(
        buy("AAPL"),
        Decimal("500.00"),
        Decimal("10000.00"),
        issuer_values={"MSFT": Decimal("1000.00")},
        issuer_tickers={"MSFT": ("MSFT",)},
    )

    assert len(outcomes) == 1
    assert "examined_issuers=1" in outcomes[0].detail
    assert "min_pair_overlap_bars=65" in outcomes[0].detail


def _bars(ticker: str, *, days: int, drift: float = 1.0) -> tuple[OHLCVBar, ...]:
    rows: list[OHLCVBar] = []
    close = 100.0
    for offset in range(days):
        if offset:
            close *= (1.01 if offset % 2 else 0.995) * drift
        day = date(2026, 1, 1) + timedelta(days=offset)
        rows.append(
            OHLCVBar(
                ticker=ticker,
                bar_date=day,
                open=close,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=1_000_000,
            )
        )
    return tuple(rows)
