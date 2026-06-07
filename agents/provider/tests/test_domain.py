"""Provider domain logic tests.

Agent: provider
Role: cover deterministic integrity and regime-classification branches.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

import pytest

from agents.provider.domain.integrity import validate_bars
from agents.provider.domain.regime import classify_regime
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource, RegimeInputs
from contracts.common import Window
from contracts.provider import OHLCVBar


def _bar(
    *,
    close: float = 101.0,
    high: float = 102.0,
    low: float = 99.0,
    volume: int = 1000,
) -> OHLCVBar:
    return OHLCVBar(
        ticker="AAPL",
        bar_date=date(2026, 1, 1),
        open=100.0,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


def test_integrity_rejects_invalid_bars_and_reports_stale_tickers() -> None:
    window = Window(start=date(2026, 1, 1), end=date(2026, 1, 10))
    settings = ProviderSettings(max_staleness_days=2)

    bars, quality = validate_bars(
        ("AAPL", "MSFT"),
        (
            _bar(close=float("nan")),
            _bar(close=101.0, volume=-1),
            _bar(close=101.0, high=100.5),
            _bar(close=101.0),
        ),
        window,
        settings,
    )

    assert len(bars) == 1
    assert quality.used_fallback is True
    assert quality.stale_tickers == ("AAPL", "MSFT")
    assert "non_finite_price_rejected" in quality.notes
    assert "invalid_ohlcv_rejected" in quality.notes
    assert "inconsistent_ohlcv_rejected" in quality.notes
    assert "stale_or_missing_tickers" in quality.notes


def test_integrity_clean_short_window_has_no_notes() -> None:
    window = Window(start=date(2026, 1, 1), end=date(2026, 1, 1))

    _bars, quality = validate_bars(
        ("AAPL",),
        (_bar(),),
        window,
        ProviderSettings(),
    )

    assert quality.used_fallback is False
    assert quality.notes == ()


def test_integrity_nonzero_sigma_without_anomaly_stays_clean() -> None:
    window = Window(start=date(2026, 1, 1), end=date(2026, 1, 1))

    _bars, quality = validate_bars(
        ("AAPL",),
        (
            _bar(close=101.0, high=104.0),
            _bar(close=102.0, high=104.0),
            _bar(close=103.0, high=104.0),
        ),
        window,
        ProviderSettings(max_daily_move_sigma=20.0),
    )

    assert quality.used_fallback is False
    assert quality.notes == ()


def test_regime_classifier_covers_vix_bands() -> None:
    settings = ProviderSettings()

    assert classify_regime(RegimeInputs(date(2026, 1, 1), None), settings) == "neutral"
    assert classify_regime(RegimeInputs(date(2026, 1, 1), 12.0), settings) == "risk_on"
    assert classify_regime(RegimeInputs(date(2026, 1, 1), 18.0), settings) == "neutral"
    assert classify_regime(RegimeInputs(date(2026, 1, 1), 21.0), settings) == "risk_off"
    assert (
        classify_regime(RegimeInputs(date(2026, 1, 1), 28.0), settings)
        == "high_volatility"
    )
    assert (
        classify_regime(RegimeInputs(date(2026, 1, 1), 36.0), settings)
        == "extreme_volatility"
    )


def test_fake_source_can_fail_regime_inputs() -> None:
    source = FakeDataSource(fail_regime=True)

    with pytest.raises(RuntimeError, match="regime source unavailable"):
        source.fetch_regime_inputs(date(2026, 1, 1))
