"""Trading vault seed probe tests.

Agent: orchestration
Role: verify pack probes route through existing clients and fail closed.
External I/O: none.
"""

from __future__ import annotations

import urllib.request
from typing import TYPE_CHECKING

import pytest

from orchestration.packs import trading_vault_probe_support as support
from orchestration.packs import trading_vault_probes as probes

if TYPE_CHECKING:
    from collections.abc import Mapping


class _BarsSource:
    def __init__(self, **_kwargs: object) -> None:
        pass

    def fetch_ohlcv(
        self, _tickers: tuple[str, ...], _window: object
    ) -> tuple[object, ...]:
        return (object(),)


class _EmptyBarsSource(_BarsSource):
    def fetch_ohlcv(
        self, _tickers: tuple[str, ...], _window: object
    ) -> tuple[object, ...]:
        return ()


class _FinnhubSource:
    def __init__(self, **_kwargs: object) -> None:
        pass

    def fetch_sectors(self, _tickers: tuple[str, ...]) -> dict[str, str]:
        return {"AAPL": "Technology"}


@pytest.mark.parametrize(
    ("name", "func", "patch_name", "env"),
    [
        (
            "tiingo",
            probes.probe_tiingo,
            "TiingoDataSource",
            {"PROVIDER_TIINGO_API_KEY": "x"},
        ),
        ("fmp", probes.probe_fmp, "FMPDataSource", {"PROVIDER_FMP_API_KEY": "x"}),
        (
            "alpaca-data",
            probes.probe_alpaca_data,
            "AlpacaDataSource",
            {"PROVIDER_ALPACA_API_KEY": "x", "PROVIDER_ALPACA_API_SECRET": "y"},
        ),
    ],
)
def test_market_data_probes_pass_with_rows(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    func: probes.Probe,
    patch_name: str,
    env: Mapping[str, str],
) -> None:
    monkeypatch.setattr(probes, patch_name, _BarsSource)
    out = func(env)
    assert out.ok is True
    assert out.message == f"{name} probe passed"


def test_market_data_probe_reports_no_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(probes, "TiingoDataSource", _EmptyBarsSource)
    out = probes.probe_tiingo({"PROVIDER_TIINGO_API_KEY": "x"})
    assert out.ok is False
    assert out.message == "tiingo probe returned no data"


def test_finnhub_probe_uses_sector_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(probes, "FinnhubDataSource", _FinnhubSource)
    out = probes.probe_finnhub({"PROVIDER_FINNHUB_API_KEY": "x"})
    assert out.ok is True
    assert out.message == "finnhub probe passed"


@pytest.mark.parametrize(
    ("func", "env"),
    [
        (probes.probe_openai, {"OPENAI_API_KEY": "x"}),
        (probes.probe_anthropic, {"ANTHROPIC_API_KEY": "x"}),
        (
            probes.probe_alpaca_broker,
            {"ALPACA_API_KEY": "x", "ALPACA_API_SECRET": "y"},
        ),
    ],
)
def test_http_probes_pass_when_endpoint_returns_json(
    monkeypatch: pytest.MonkeyPatch, func: probes.Probe, env: Mapping[str, str]
) -> None:
    monkeypatch.setattr(probes, "http_json", lambda _request: {"ok": True})
    out = func(env)
    assert out.ok is True
    assert out.message.endswith("probe passed")


def test_postgres_probe_uses_live_ready_check(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, str] = {}

    def ready(env: Mapping[str, str]) -> bool:
        called.update(env)
        return True

    monkeypatch.setattr(probes, "postgres_ready", ready)
    out = probes.probe_postgres({"POSTGRES_DSN": "postgresql://example.invalid/db"})
    assert out.ok is True
    assert out.message == "postgres probe passed"
    assert called["POSTGRES_DSN"].startswith("postgresql://")


def test_support_helpers_fail_closed_and_read_http(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert support.run_probe("x", lambda: False).message == "x probe returned no data"
    raising = support.run_probe("x", lambda: (_ for _ in ()).throw(RuntimeError()))
    assert raising.message == "x probe failed: RuntimeError"
    with pytest.raises(ValueError, match="missing"):
        support.required({}, "MISSING")

    class Response:
        def __enter__(self) -> Response:
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok": true}'

    monkeypatch.setattr(urllib.request, "urlopen", lambda _request, timeout: Response())
    request = urllib.request.Request("https://example.test")
    assert support.http_json(request) == {"ok": True}
    assert support.probe_window().start <= support.probe_window().end


def test_probe_registry_exports_expected_names() -> None:
    assert {
        "alpaca-broker",
        "alpaca-data",
        "anthropic",
        "finnhub",
        "fmp",
        "openai",
        "postgres",
        "tiingo",
    } <= set(probes.PROBES)
