"""Alpaca OHLCV source tests.

Agent: provider
Role: verify Alpaca multi-symbol bar parsing, the Zulu-timestamp date parse,
window/malformed filtering, the empty-universe short-circuit, OHLCV-only
behaviour, and the settings builder routing OHLCV to Alpaca.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from types import MethodType

from agents.provider.alpaca_data import AlpacaDataSource
from agents.provider.composite import CompositeDataSource, market_source_from_settings
from agents.provider.settings import ProviderSettings
from contracts.common import Window

_WINDOW = Window(start=date(2026, 1, 1), end=date(2026, 1, 31))


def _source() -> AlpacaDataSource:
    return AlpacaDataSource(
        api_key="k",
        api_secret="s",  # noqa: S106 - test stub credential, not a real secret.
        base_url="https://alpaca.test",
        feed="iex",
        timeout=10,
    )


def _stub(payload: str) -> AlpacaDataSource:
    source = _source()

    def fake_download(
        _self: AlpacaDataSource, _tickers: tuple[str, ...], _window: Window
    ) -> str:
        return payload

    source._download = MethodType(fake_download, source)  # type: ignore[method-assign]
    return source


def test_alpaca_parses_multi_symbol_bars_and_zulu_date() -> None:
    payload = (
        '{"bars":{"AAPL":['
        '{"t":"2026-01-10T05:00:00Z","o":100.0,"h":105.0,"l":99.0,"c":104.0,"v":1000000},'
        '{"t":"2026-01-09T05:00:00Z","o":98.0,"h":101.0,"l":97.0,"c":100.0,"v":900000}'
        '],"MSFT":['
        '{"t":"2026-01-10T05:00:00Z","o":200.0,"h":205.0,"l":199.0,"c":204.0,"v":500000}'
        "]}}"
    )
    bars = _stub(payload).fetch_ohlcv(("AAPL", "MSFT"), _WINDOW)
    by_ticker = {(b.ticker, b.bar_date): b for b in bars}
    assert by_ticker[("AAPL", date(2026, 1, 10))].close == 104.0
    assert by_ticker[("AAPL", date(2026, 1, 10))].volume == 1000000
    assert by_ticker[("MSFT", date(2026, 1, 10))].open == 200.0
    assert len(bars) == 3


def test_alpaca_filters_out_of_window_and_malformed_rows() -> None:
    payload = (
        '{"bars":{"AAPL":['
        '{"t":"2026-01-10T05:00:00Z","o":100.0,"h":105.0,"l":99.0,"c":104.0,"v":1000000},'
        '{"t":"2025-12-31T05:00:00Z","o":1.0,"h":1.0,"l":1.0,"c":1.0,"v":1},'
        '{"t":"2026-01-11T05:00:00Z","o":0.0,"h":1.0,"l":1.0,"c":1.0,"v":1},'
        '{"t":"2026-01-12T05:00:00Z","o":1.0,"h":1.0,"l":1.0,"c":1.0},'
        '"not-a-dict"'
        "]}}"
    )
    bars = _stub(payload).fetch_ohlcv(("AAPL",), _WINDOW)
    assert [b.bar_date for b in bars] == [date(2026, 1, 10)]


def test_alpaca_empty_universe_short_circuits() -> None:
    assert _stub('{"bars":{}}').fetch_ohlcv((), _WINDOW) == ()


def test_alpaca_non_dict_payload_yields_empty() -> None:
    assert _stub("[]").fetch_ohlcv(("AAPL",), _WINDOW) == ()


def test_alpaca_missing_or_nonlist_bars_yield_empty() -> None:
    assert _stub('{"next_page_token":null}').fetch_ohlcv(("AAPL",), _WINDOW) == ()
    assert _stub('{"bars":{"AAPL":"oops"}}').fetch_ohlcv(("AAPL",), _WINDOW) == ()


def test_alpaca_serves_ohlcv_only() -> None:
    source = _source()
    assert source.fetch_fundamentals(("AAPL",), _WINDOW) == {}
    assert source.fetch_news(("AAPL",), _WINDOW) == {}
    assert source.fetch_sentiment(("AAPL",)) == {}
    assert source.fetch_sectors(("AAPL",)) == {}
    assert source.fetch_earnings(("AAPL",), _WINDOW) == {}
    assert source.fetch_regime_inputs(date(2026, 1, 2)).vix is None


def test_market_source_from_settings_routes_ohlcv_to_alpaca() -> None:
    composite = market_source_from_settings(ProviderSettings())
    assert isinstance(composite, CompositeDataSource)
    assert isinstance(composite._price_source, AlpacaDataSource)
