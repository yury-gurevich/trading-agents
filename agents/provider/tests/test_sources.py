"""Provider source adapter tests.

Agent: provider
Role: verify deterministic source adapters and optional Stooq integration.
External I/O: optional HTTPS call to Stooq when STOOQ_TEST_NETWORK=1.
"""

from __future__ import annotations

import os
from datetime import date
from types import MethodType

import pytest

from agents.provider.sources import StooqDataSource
from contracts.common import Window


def test_stooq_source_parses_csv_without_network() -> None:
    source = StooqDataSource()

    def fake_download(_self: StooqDataSource, _ticker: str, _window: Window) -> str:
        return (
            "Date,Open,High,Low,Close,Volume\n,,,,,\n2024-01-02,100,105,99,104,12345\n"
        )

    source._download = MethodType(fake_download, source)  # type: ignore[method-assign]

    bars = source.fetch_ohlcv(
        ("AAPL",), Window(start=date(2024, 1, 2), end=date(2024, 1, 3))
    )

    assert len(bars) == 1
    assert bars[0].ticker == "AAPL"
    assert bars[0].close == 104.0


def test_stooq_source_skips_rows_missing_volume() -> None:
    source = StooqDataSource()

    def fake_download(_self: StooqDataSource, _ticker: str, _window: Window) -> str:
        return "Date,Open,High,Low,Close,Volume\n2024-01-02,100,105,99,104,\n"

    source._download = MethodType(fake_download, source)  # type: ignore[method-assign]

    assert (
        source.fetch_ohlcv(
            ("AAPL",), Window(start=date(2024, 1, 2), end=date(2024, 1, 3))
        )
        == ()
    )


def test_stooq_source_returns_empty_regime_inputs() -> None:
    inputs = StooqDataSource().fetch_regime_inputs(date(2024, 1, 2))

    assert inputs.as_of == date(2024, 1, 2)
    assert inputs.vix is None


@pytest.mark.integration
def test_stooq_source_fetches_real_ohlcv_when_network_enabled() -> None:
    if os.getenv("STOOQ_TEST_NETWORK") != "1":
        pytest.skip("STOOQ_TEST_NETWORK=1 is not set")

    bars = StooqDataSource().fetch_ohlcv(
        ("AAPL",), Window(start=date(2024, 1, 2), end=date(2024, 1, 5))
    )

    assert bars
    assert bars[0].ticker == "AAPL"
