"""Tests for S235 replay context cache files.

Agent: tooling
Role: verify benchmark, VIX, sectors, and cache-volume compatibility.
External I/O: local tmp files only.
"""

from __future__ import annotations

import csv
import gzip
import io
from datetime import date
from typing import TYPE_CHECKING

import pytest
from scripts.replay_cache import load_replay_cache
from scripts.replay_universe_cache import load_universe_cache, write_universe_cache
from scripts.sp500_bars import BarRow
from scripts.sp500_context import build_context_files, fetch_sectors
from scripts.sp500_membership import Episode, MembershipResult

if TYPE_CHECKING:
    from pathlib import Path


def test_loader_reports_old_cache_without_volume(tmp_path: Path) -> None:
    """S235-A11: old sp500_bars caches load but report volume absent."""
    _write_csv(tmp_path / "sp500_sessions.csv.gz", ["date"], [["2020-01-02"]])
    _write_csv(
        tmp_path / "sp500_membership.csv.gz",
        ["line", "ticker", "first", "last"],
        [["AAA", "AAA", "2020-01-02", "2020-01-02"]],
    )
    _write_csv(
        tmp_path / "sp500_bars.csv.gz",
        ["line", "symbol", "date", "open", "high", "low", "close"],
        [["AAA", "AAA", "2020-01-02", 1, 2, 1, 2]],
    )
    (tmp_path / "sp500_coverage.json").write_text("{}", encoding="utf-8")

    loaded = load_universe_cache(tmp_path)

    assert loaded.has_volume is False
    assert loaded.bars[0].volume == 0


def test_pipeline_refuses_cache_without_volume(tmp_path: Path) -> None:
    """S235-A11: replay harness names the missing volume column."""
    _write_csv(tmp_path / "sp500_sessions.csv.gz", ["date"], [["2020-01-02"]])
    _write_csv(
        tmp_path / "sp500_membership.csv.gz",
        ["line", "ticker", "first", "last"],
        [["AAA", "AAA", "2020-01-02", "2020-01-02"]],
    )
    _write_csv(
        tmp_path / "sp500_bars.csv.gz",
        ["line", "symbol", "date", "open", "high", "low", "close"],
        [["AAA", "AAA", "2020-01-02", 1, 2, 1, 2]],
    )
    (tmp_path / "sp500_coverage.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="volume"):
        load_replay_cache(tmp_path)


def test_universe_cache_writes_volume_column(tmp_path: Path) -> None:
    """S235-A1: new sp500_bars cache carries SIP volume."""
    membership = MembershipResult(
        episodes=(Episode("AAA", "AAA", date(2020, 1, 2), date(2020, 1, 2)),),
        members_by_session={date(2020, 1, 2): ("AAA",)},
        unreconciled=(),
        count_min=1,
        count_max=1,
    )
    write_universe_cache(
        tmp_path,
        (date(2020, 1, 2),),
        membership,
        (BarRow("AAA", "AAA", date(2020, 1, 2), 1, 2, 1, 2, 123),),
        {},
    )

    text = gzip.decompress((tmp_path / "sp500_bars.csv.gz").read_bytes()).decode()
    assert text.splitlines()[0].split(",")[-1] == "volume"


def test_context_files_write_benchmark_and_vix(tmp_path: Path) -> None:
    """S235-A14: context build writes SPY OHLCV and VIX beside the universe."""
    sessions = (date(2020, 1, 2), date(2020, 1, 3))

    def bars(
        symbols: list[str], *, end: str, start: str, **kwargs: object
    ) -> dict[str, list[tuple[str, int, int, int, int, int]]]:
        assert symbols == ["SPY"]
        assert end == "2020-01-03"
        assert kwargs["asof"] == "2020-01-03"
        assert kwargs["adjustment"] == "all"
        assert kwargs["with_volume"] is True
        return {
            "SPY": [(day.isoformat(), 1, 2, 1, 2, 99) for day in sessions],
        }

    build_context_files(
        tmp_path,
        sessions,
        bars,
        lambda: {day.isoformat(): 10.0 + index for index, day in enumerate(sessions)},
    )

    assert _rows(tmp_path / "sp500_benchmark.csv.gz")[0]["volume"] == "99"
    assert [row["vix_close"] for row in _rows(tmp_path / "sp500_vix.csv.gz")] == [
        "10.0",
        "11.0",
    ]


def test_sectors_are_paced_and_parsed(tmp_path: Path) -> None:
    """S235-A15: sectors uses provider parser and one paced call per symbol."""
    sleeps: list[float] = []
    urls: list[str] = []

    def get(url: str, *, params: dict[str, str], timeout: int) -> str:
        del timeout
        urls.append(f"{url}?symbol={params['symbol']}")
        return '{"finnhubIndustry":"Technology"}' if params["symbol"] == "AAA" else "{}"

    rows = fetch_sectors(
        tmp_path,
        ("AAA", "BBB", "AAA"),
        api_key="key",  # pragma: allowlist secret - synthetic fixture token
        get=get,
        sleep=sleeps.append,
    )

    assert rows == (("AAA", "AAA", "Technology"), ("BBB", "BBB", ""))
    assert len(urls) == 2
    assert sleeps == [1.0]
    assert _rows(tmp_path / "sp500_sectors.csv.gz")[1]["sector"] == ""


def _write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    path.write_bytes(gzip.compress(buffer.getvalue().encode("utf-8")))


def _rows(path: Path) -> list[dict[str, str]]:
    return list(
        csv.DictReader(io.StringIO(gzip.decompress(path.read_bytes()).decode()))
    )
