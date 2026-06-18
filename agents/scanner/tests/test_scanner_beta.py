"""Scanner beta computation + beta-cap filter tests.

Agent: scanner
Role: verify the pure beta math and the beta-cap drop / keep / skip filter branches.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from agents.scanner.domain.beta import compute_beta
from agents.scanner.domain.filters import apply_filters
from agents.scanner.settings import ScannerSettings
from contracts.provider import OHLCVBar


def _bar(ticker: str, days_ago: int, close: float) -> OHLCVBar:
    day = datetime.now(tz=UTC).date() - timedelta(days=days_ago)
    open_ = close * 0.99
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=open_,
        high=max(open_, close) + 1.0,
        low=min(open_, close) - 1.0,
        close=close,
        volume=1_000_000,
    )


def _series(ticker: str, closes: list[float]) -> tuple[OHLCVBar, ...]:
    count = len(closes)
    return tuple(_bar(ticker, count - 1 - i, close) for i, close in enumerate(closes))


# Benchmark returns are [0.10, 0.20]; a 1x series tracks it (beta 1.0), a 2x series
# (returns [0.20, 0.40]) has beta 2.0.
_BENCH = _series("SPY", [100.0, 110.0, 132.0])
_ONE_X = _series("LOWB", [100.0, 110.0, 132.0])
_TWO_X = _series("HIGHB", [100.0, 120.0, 168.0])


def test_beta_of_a_one_to_one_series_is_one() -> None:
    beta = compute_beta(_ONE_X, _BENCH, min_observations=2)
    assert beta is not None
    assert round(beta, 6) == 1.0


def test_beta_of_a_double_amplitude_series_is_two() -> None:
    beta = compute_beta(_TWO_X, _BENCH, min_observations=2)
    assert beta is not None
    assert round(beta, 6) == 2.0


def test_beta_is_none_without_enough_aligned_observations() -> None:
    thin = _series("THIN", [100.0, 110.0])  # one aligned return only
    assert compute_beta(thin, _BENCH, min_observations=2) is None


def test_beta_is_none_when_the_benchmark_is_flat() -> None:
    flat = _series("FLAT", [100.0, 100.0, 100.0])
    assert compute_beta(_ONE_X, flat, min_observations=2) is None


def _beta_settings() -> ScannerSettings:
    return ScannerSettings(
        min_relative_strength=0.02,
        min_price=5.0,
        min_average_volume=500_000.0,
        candidate_cap=5,
        lookback_days=7,
        max_beta=1.5,
        beta_min_observations=2,
    )


def test_beta_cap_drops_high_beta_keeps_low_beta_skips_thin_history() -> None:
    bars = (*_ONE_X, *_TWO_X, *_series("THIN", [100.0, 110.0]))
    survivors, trace = apply_filters(
        ("LOWB", "HIGHB", "THIN"),
        bars,
        _BENCH,
        {},
        datetime.now(tz=UTC).date(),
        _beta_settings(),
    )

    by_ticker = {survivor.ticker: survivor for survivor in survivors}
    assert set(by_ticker) == {"LOWB", "THIN"}
    assert trace.dropped_by_filter == {"max_beta": 1}
    assert round(by_ticker["LOWB"].metrics["beta"], 6) == 1.0
    assert "max_beta" in by_ticker["LOWB"].survived_filters
    # Thin history: beta skipped, so no beta metric and no beta gate recorded.
    assert "beta" not in by_ticker["THIN"].metrics
    assert "max_beta" not in by_ticker["THIN"].survived_filters
