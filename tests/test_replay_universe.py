"""Tests for the S231 replay-universe builder CLI surface.

Agent: tooling
Role: verify cache boundaries, snapshot rebuilds, and legacy replay cache safety.
External I/O: local tmp files only.
"""

from __future__ import annotations

import csv
import gzip
import io
from datetime import date
from pathlib import Path

import pytest
from tests.sp500_fixtures import universe_pages_fixture


def test_universe_build_leaves_existing_replay_cache_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S231-A11: build writes only sp500 files and legacy load() still works."""
    from scripts import replay_dataset
    from scripts.replay_universe import build_universe

    _write_gzip(tmp_path / "vix.csv.gz", ["date", "vix_close"], [["2020-01-01", 12]])
    _write_gzip(
        tmp_path / "bars.csv.gz",
        ["ticker", "date", "open", "high", "low", "close"],
        [["LEGACY", "2020-01-01", 1, 2, 3, 4]],
    )
    before = {
        name: (tmp_path / name).read_bytes() for name in ("vix.csv.gz", "bars.csv.gz")
    }
    monkeypatch.setattr(replay_dataset, "CACHE", tmp_path)

    build_universe(
        cache=tmp_path, page_fetcher=universe_pages_fixture, bar_fetcher=_bars
    )

    assert {path.name for path in tmp_path.iterdir()} == {
        "vix.csv.gz",
        "bars.csv.gz",
        "sp500_pages.json.gz",
        "sp500_sessions.csv.gz",
        "sp500_membership.csv.gz",
        "sp500_bars.csv.gz",
        "sp500_coverage.json",
    }
    assert (tmp_path / "vix.csv.gz").read_bytes() == before["vix.csv.gz"]
    assert (tmp_path / "bars.csv.gz").read_bytes() == before["bars.csv.gz"]
    assert replay_dataset.load()[1]["LEGACY"][0] == ("2020-01-01", 1.0, 2.0, 3.0, 4.0)


def test_universe_build_refuses_repo_cache_before_fetching() -> None:
    """S231-A12: an in-repo cache path is refused before any fetch."""
    from scripts.replay_universe import build_universe

    fetched = False

    def fetch_pages() -> dict[str, str]:
        nonlocal fetched
        fetched = True
        return universe_pages_fixture()

    with pytest.raises(RuntimeError, match="outside the repo"):
        build_universe(
            cache=Path.cwd() / "tmp-in-repo-sp500-cache",
            page_fetcher=fetch_pages,
            bar_fetcher=_bars,
        )

    assert fetched is False


def test_from_snapshot_rebuilds_without_wikipedia_fetch(tmp_path: Path) -> None:
    """S231-A13: --from-snapshot reuses saved pages and does not fetch them."""
    from scripts.replay_universe import build_universe

    first = build_universe(
        cache=tmp_path, page_fetcher=universe_pages_fixture, bar_fetcher=_bars
    )

    def forbidden_fetch() -> dict[str, str]:
        raise AssertionError("network fetch should not run")

    second = build_universe(
        cache=tmp_path,
        from_snapshot=True,
        page_fetcher=forbidden_fetch,
        bar_fetcher=_bars,
    )

    assert second.episodes == first.episodes


def test_daily_bars_start_default_is_backward_compatible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S231-A14: daily_bars defaults start to START and honors explicit start."""
    from scripts import replay_dataset_sources as sources

    starts: list[str] = []

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"bars": {}, "next_page_token": None}

    def fake_get(*args: object, **kwargs: object) -> Response:
        del args
        starts.append(kwargs["params"]["start"])  # type: ignore[index]
        return Response()

    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.setenv("ALPACA_API_SECRET", "secret")
    monkeypatch.setattr("scripts.replay_dataset_sources.requests.get", fake_get)

    sources.daily_bars(["AAA"], "2020-01-02")
    sources.daily_bars(["AAA"], "2020-01-02", start="2020-01-01")

    assert starts == [sources.START, "2020-01-01"]


def _bars(
    symbols: list[str], *, end: str, start: str
) -> dict[str, list[tuple[str, float, float, float, float]]]:
    del end, start
    sessions = (date(2020, 1, 1), date(2020, 1, 2))
    return {symbol: [_bar(day) for day in sessions] for symbol in symbols}


def _bar(day: date) -> tuple[str, float, float, float, float]:
    return (day.isoformat(), 1.0, 1.0, 1.0, 1.0)


def _write_gzip(path: Path, header: list[str], rows: list[list[object]]) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    path.write_bytes(gzip.compress(buffer.getvalue().encode("utf-8")))
