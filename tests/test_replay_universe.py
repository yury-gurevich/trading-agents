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
from typing import Any, cast

import pytest
from tests.sp500_fixtures import universe_pages_fixture


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every source here is injected; a real HTTP call is a test defect."""

    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError(f"network call in a unit test: {kwargs.get('url')}")

    monkeypatch.setattr("requests.Session.request", refuse)


def test_universe_build_leaves_existing_replay_cache_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S235-A14: build adds sp500 context while legacy load() still works."""
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
        cache=tmp_path,
        page_fetcher=universe_pages_fixture,
        bar_fetcher=_bars,
        vix_fetcher=_vix,
    )

    assert {path.name for path in tmp_path.iterdir()} == {
        "vix.csv.gz",
        "bars.csv.gz",
        "sp500_pages.json.gz",
        "sp500_sessions.csv.gz",
        "sp500_membership.csv.gz",
        "sp500_bars.csv.gz",
        "sp500_benchmark.csv.gz",
        "sp500_coverage.json",
        "sp500_vix.csv.gz",
    }
    assert (tmp_path / "vix.csv.gz").read_bytes() == before["vix.csv.gz"]
    assert (tmp_path / "bars.csv.gz").read_bytes() == before["bars.csv.gz"]
    assert replay_dataset.load()[1]["LEGACY"][0] == ("2020-01-01", 1.0, 2.0, 3.0, 4.0)
    vix = gzip.decompress((tmp_path / "sp500_vix.csv.gz").read_bytes()).decode()
    assert "2020-01-02,17.5" in vix.splitlines()


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
        cache=tmp_path,
        page_fetcher=universe_pages_fixture,
        bar_fetcher=_bars,
        vix_fetcher=_vix,
    )

    def forbidden_fetch() -> dict[str, str]:
        raise AssertionError("network fetch should not run")

    second = build_universe(
        cache=tmp_path,
        from_snapshot=True,
        page_fetcher=forbidden_fetch,
        bar_fetcher=_bars,
        vix_fetcher=_vix,
    )

    assert second.episodes == first.episodes


def test_daily_bars_start_default_is_backward_compatible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S235-A12: defaults stay unchanged; with_volume adds only tuple volume."""
    from scripts import replay_dataset_sources as sources

    params: list[dict[str, object]] = []

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "bars": {
                    "AAA": [
                        {
                            "t": "2020-01-02T05:00:00Z",
                            "o": 1,
                            "h": 2,
                            "l": 0.5,
                            "c": 1.5,
                            "v": 1234,
                        }
                    ]
                },
                "next_page_token": None,
            }

    def fake_get(*args: object, **kwargs: Any) -> Response:
        del args
        params.append(dict(cast("dict[str, object]", kwargs["params"])))
        return Response()

    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.setenv("ALPACA_API_SECRET", "secret")
    monkeypatch.setattr("scripts.replay_dataset_sources.requests.get", fake_get)

    default = sources.daily_bars(["AAA"], "2020-01-02")
    with_volume = sources.daily_bars(
        ["AAA"],
        "2020-01-02",
        start="2020-01-01",
        asof="2020-01-02",
        adjustment="raw",
        with_volume=True,
    )

    assert params[0]["start"] == sources.START
    assert params[0]["adjustment"] == "all"
    assert "asof" not in params[0]
    assert params[1]["start"] == "2020-01-01"
    assert params[1]["adjustment"] == "raw"
    assert params[1]["asof"] == "2020-01-02"
    assert default["AAA"] == [("2020-01-02", 1, 2, 0.5, 1.5)]
    assert with_volume["AAA"] == [("2020-01-02", 1, 2, 0.5, 1.5, 1234)]


def _bars(
    symbols: list[str], *, end: str, start: str, **kwargs: object
) -> dict[str, list[tuple[str, float, float, float, float]]]:
    del end, start, kwargs
    sessions = (date(2020, 1, 1), date(2020, 1, 2))
    return {symbol: [_bar(day) for day in sessions] for symbol in symbols}


def _vix() -> dict[str, float]:
    return {"2020-01-02": 17.5}


def _bar(day: date) -> tuple[str, float, float, float, float]:
    return (day.isoformat(), 1.0, 1.0, 1.0, 1.0)


def _write_gzip(path: Path, header: list[str], rows: list[list[object]]) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    path.write_bytes(gzip.compress(buffer.getvalue().encode("utf-8")))
