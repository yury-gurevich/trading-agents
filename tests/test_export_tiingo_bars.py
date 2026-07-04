"""Tiingo exporter helper tests.

Agent: tooling
Role: verify resumable export helpers without live Tiingo calls.
External I/O: temporary CSV fixtures only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from urllib.error import HTTPError

import pytest
from scripts import export_tiingo_bars, tiingo_export_retry

from contracts.common import Window

_WINDOW = Window(start=date(2024, 1, 1), end=date(2024, 1, 3))


@dataclass(frozen=True)
class _Bar:
    bar_date: date
    close: float
    volume: int


class _Source:
    def __init__(
        self,
        bars: dict[str, tuple[_Bar, ...]],
        *,
        errors: tuple[BaseException, ...] = (),
    ) -> None:
        self.bars = bars
        self.errors = list(errors)
        self.calls: list[str] = []

    def fetch_ohlcv(self, tickers, window):
        self.calls.append(tickers[0])
        if self.errors:
            raise self.errors.pop(0)
        return self.bars.get(tickers[0], ())


def test_load_tickers_skips_blanks_and_indented_comments(tmp_path) -> None:
    path = tmp_path / "tickers.txt"
    path.write_text("\nAAPL\n  # comment\nMSFT\n", encoding="utf-8")

    assert export_tiingo_bars.load_tickers(str(path)) == ("AAPL", "MSFT")


def test_completed_tickers_reads_existing_csv(tmp_path) -> None:
    path = tmp_path / "bars.csv"
    path.write_text(
        "date,ticker,close,volume\n2024-01-01,AAPL,10,100\n",
        encoding="utf-8",
    )

    assert export_tiingo_bars.completed_tickers(str(path)) == {"AAPL"}


def test_start_for_years_uses_leap_safe_calendar_window() -> None:
    start = export_tiingo_bars.start_for_years(today=date(2026, 7, 4), years=4)

    assert start == date(2022, 7, 1)


def test_export_bars_resumes_and_paces_successes(tmp_path, monkeypatch) -> None:
    path = tmp_path / "bars.csv"
    path.write_text(
        "date,ticker,close,volume\n2024-01-01,AAPL,10,100\n",
        encoding="utf-8",
    )
    sleeps: list[float] = []
    monkeypatch.setattr(export_tiingo_bars.time, "sleep", sleeps.append)
    source = _Source(
        {"MSFT": (_Bar(date(2024, 1, 2), 20.0, 200),)},
    )

    count = export_tiingo_bars.export_bars(
        source,
        ("AAPL", "MSFT", "NVDA"),
        out=str(path),
        window=_WINDOW,
        pace_seconds=3.5,
        max_requests=1,
    )

    assert count == 1
    assert source.calls == ["MSFT"]
    assert sleeps == [3.5]
    assert export_tiingo_bars.completed_tickers(str(path)) == {"AAPL", "MSFT"}


def test_export_bars_stops_on_hourly_limit_without_success(tmp_path) -> None:
    path = tmp_path / "bars.csv"
    error = HTTPError("https://tiingo.test", 429, "limited", {}, None)
    source = _Source({}, errors=(error,))

    count = export_tiingo_bars.export_bars(
        source,
        ("AAPL", "MSFT"),
        out=str(path),
        window=_WINDOW,
        pace_seconds=0.0,
    )

    assert count == 0
    assert source.calls == ["AAPL"]
    assert export_tiingo_bars.completed_tickers(str(path)) == set()


def test_export_bars_retries_timeout_then_exports(tmp_path, monkeypatch) -> None:
    path = tmp_path / "bars.csv"
    sleeps: list[float] = []
    monkeypatch.setattr(tiingo_export_retry.time, "sleep", sleeps.append)
    monkeypatch.setattr(export_tiingo_bars.time, "sleep", sleeps.append)
    source = _Source(
        {"AAPL": (_Bar(date(2024, 1, 1), 10.0, 100),)},
        errors=(TimeoutError("slow"),),
    )

    count = export_tiingo_bars.export_bars(
        source,
        ("AAPL",),
        out=str(path),
        window=_WINDOW,
        pace_seconds=3.0,
        max_retries=1,
        backoff_seconds=0.5,
    )

    assert count == 1
    assert source.calls == ["AAPL", "AAPL"]
    assert sleeps == [0.5, 3.0]


def test_export_bars_skips_after_exhausted_timeout_retries(tmp_path) -> None:
    path = tmp_path / "bars.csv"
    source = _Source({}, errors=(TimeoutError("slow"),))

    count = export_tiingo_bars.export_bars(
        source,
        ("AAPL",),
        out=str(path),
        window=_WINDOW,
        pace_seconds=0.0,
        max_retries=0,
    )

    assert count == 0
    assert source.calls == ["AAPL"]


def test_default_pace_honors_tiingo_free_hourly_budget() -> None:
    assert export_tiingo_bars.DEFAULT_PACE_SECONDS >= 72.0


def test_source_from_env_requires_tiingo_credential(monkeypatch) -> None:
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)

    with pytest.raises(ValueError, match="TIINGO_API_KEY missing"):
        export_tiingo_bars.source_from_env({})
