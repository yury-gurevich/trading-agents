"""Tiingo OHLCV source tests.

Agent: provider
Role: verify Tiingo EOD parsing, the Z-suffixed date parse, window/malformed
filtering, and the settings builder routing OHLCV to Tiingo.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from types import MethodType

from agents.provider.composite import CompositeDataSource, market_source_from_settings
from agents.provider.settings import ProviderSettings
from agents.provider.tiingo import TiingoDataSource
from contracts.common import Window

_WINDOW = Window(start=date(2026, 1, 1), end=date(2026, 1, 31))


def _stub(payload: str) -> TiingoDataSource:
    source = TiingoDataSource(api_key="k", base_url="https://tiingo.test", timeout=10)

    def fake_download(_self: TiingoDataSource, _ticker: str, _window: Window) -> str:
        return payload

    source._download = MethodType(fake_download, source)  # type: ignore[method-assign]
    return source


def test_tiingo_parses_eod_bars_and_zulu_date_without_network() -> None:
    payload = (
        '[{"date":"2026-01-10T00:00:00.000Z","open":100.0,"high":105.0,'
        '"low":99.0,"close":104.0,"volume":1000000},'
        '{"date":"2026-01-09T00:00:00.000Z","open":98.0,"high":101.0,'
        '"low":97.0,"close":100.0,"volume":900000}]'
    )
    bars = _stub(payload).fetch_ohlcv(("AAPL",), _WINDOW)
    assert [b.bar_date for b in bars] == [date(2026, 1, 10), date(2026, 1, 9)]
    assert bars[0].close == 104.0
    assert bars[0].volume == 1000000


def test_tiingo_filters_out_of_window_and_malformed_rows() -> None:
    payload = (
        '[{"date":"2026-01-10T00:00:00.000Z","open":100.0,"high":105.0,'
        '"low":99.0,"close":104.0,"volume":1000000},'
        '{"date":"2025-12-31T00:00:00.000Z","open":1.0,"high":1.0,'
        '"low":1.0,"close":1.0,"volume":1},'
        '{"date":"2026-01-11T00:00:00.000Z","open":0.0,"high":1.0,'
        '"low":1.0,"close":1.0,"volume":1},'
        '{"date":"2026-01-12T00:00:00.000Z","open":1.0,"high":1.0,'
        '"low":1.0,"close":1.0},'
        '"not-a-dict"]'
    )
    bars = _stub(payload).fetch_ohlcv(("AAPL",), _WINDOW)
    assert [b.bar_date for b in bars] == [date(2026, 1, 10)]


def test_tiingo_non_list_payload_yields_empty() -> None:
    assert _stub('{"detail":"Error: Not found"}').fetch_ohlcv(("AAPL",), _WINDOW) == ()


def test_tiingo_serves_ohlcv_only() -> None:
    source = TiingoDataSource(api_key="k", base_url="https://tiingo.test", timeout=10)
    assert source.fetch_fundamentals(("AAPL",), _WINDOW) == {}
    assert source.fetch_news(("AAPL",), _WINDOW) == {}
    assert source.fetch_sentiment(("AAPL",)) == {}
    assert source.fetch_regime_inputs(date(2026, 1, 2)).vix is None


def test_market_source_from_settings_routes_ohlcv_to_tiingo() -> None:
    composite = market_source_from_settings(ProviderSettings())
    assert isinstance(composite, CompositeDataSource)
    assert isinstance(composite._price_source, TiingoDataSource)
