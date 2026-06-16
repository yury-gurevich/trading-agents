"""FMP OHLCV source tests.

Agent: provider
Role: verify FMP EOD parsing and window/malformed filtering (FMP is the
validation sub-universe / failover feed; routing is covered in test_tiingo).
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from types import MethodType

from agents.provider.fmp import FMPDataSource
from contracts.common import Window

_WINDOW = Window(start=date(2026, 1, 1), end=date(2026, 1, 31))


def _stub(payload: str) -> FMPDataSource:
    source = FMPDataSource(api_key="k", base_url="https://fmp.test", timeout=10)

    def fake_download(_self: FMPDataSource, _ticker: str, _window: Window) -> str:
        return payload

    source._download = MethodType(fake_download, source)  # type: ignore[method-assign]
    return source


def test_fmp_parses_eod_bars_without_network() -> None:
    payload = (
        '[{"symbol":"AAPL","date":"2026-01-10","open":100.0,"high":105.0,'
        '"low":99.0,"close":104.0,"volume":1000000},'
        '{"symbol":"AAPL","date":"2026-01-09","open":98.0,"high":101.0,'
        '"low":97.0,"close":100.0,"volume":900000}]'
    )
    bars = _stub(payload).fetch_ohlcv(("AAPL",), _WINDOW)
    assert [b.bar_date for b in bars] == [date(2026, 1, 10), date(2026, 1, 9)]
    assert bars[0].close == 104.0
    assert bars[0].volume == 1000000


def test_fmp_filters_out_of_window_and_malformed_rows() -> None:
    payload = (
        '[{"symbol":"AAPL","date":"2026-01-10","open":100.0,"high":105.0,'
        '"low":99.0,"close":104.0,"volume":1000000},'
        '{"symbol":"AAPL","date":"2025-12-31","open":1.0,"high":1.0,'
        '"low":1.0,"close":1.0,"volume":1},'
        '{"symbol":"AAPL","date":"2026-01-11","open":0.0,"high":1.0,'
        '"low":1.0,"close":1.0,"volume":1},'
        '{"symbol":"AAPL","date":"2026-01-12","open":1.0,"high":1.0,'
        '"low":1.0,"close":1.0},'
        '"not-a-dict"]'
    )
    bars = _stub(payload).fetch_ohlcv(("AAPL",), _WINDOW)
    assert [b.bar_date for b in bars] == [date(2026, 1, 10)]


def test_fmp_non_list_payload_yields_empty() -> None:
    assert _stub('{"Error Message":"premium"}').fetch_ohlcv(("AAPL",), _WINDOW) == ()


def test_fmp_serves_ohlcv_only() -> None:
    source = FMPDataSource(api_key="k", base_url="https://fmp.test", timeout=10)
    assert source.fetch_fundamentals(("AAPL",), _WINDOW) == {}
    assert source.fetch_news(("AAPL",), _WINDOW) == {}
    assert source.fetch_regime_inputs(date(2026, 1, 2)).vix is None
