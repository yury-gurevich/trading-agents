"""S237 A11/A12: sessions.csv counts and stderr-only progress, over differing days.

Agent: tooling
Role: prove the rejection-reason header is the sorted union with 0 where absent, and
      progress lines land at the interval and at the end without touching outputs.
External I/O: local tmp files only.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
from datetime import date
from filecmp import cmp
from types import SimpleNamespace
from typing import TYPE_CHECKING

from scripts.replay_runner import run
from scripts.replay_universe_cache import write_universe_cache
from scripts.sp500_bars import BarRow
from scripts.sp500_membership import Episode, MembershipResult

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from scripts.replay_day import ReplayDayInputs

SESSIONS = tuple(date(2020, 1, day) for day in (2, 3, 6, 7, 8))
REASONS = {
    SESSIONS[0]: ("sector_concentration", "sector_concentration"),
    SESSIONS[1]: ("cash_buffer",),
    SESSIONS[2]: (),
    SESSIONS[3]: ("sector_name_count", "cash_buffer"),
    SESSIONS[4]: (),
}


def _fake_day(inputs: ReplayDayInputs, settings: object) -> object:
    del settings
    session = inputs.session
    return SimpleNamespace(
        absent_inputs={"fundamentals": 3},
        candidates=SimpleNamespace(candidates=(object(),)),
        recommendations=SimpleNamespace(recommendations=()),
        approved=(),
        rejected=tuple(SimpleNamespace(reason=reason) for reason in REASONS[session]),
    )


def _run(cache: Path, out: Path, progress_every: int) -> None:
    run(
        cache_dir=cache,
        out=out,
        start=SESSIONS[0],
        end=SESSIONS[-1],
        overrides=(),
        progress_every=progress_every,
    )


def test_a11_reason_columns_are_the_sorted_union_with_zero_where_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RPT-OUT-07 / PM-OUT-03: counts come from the day results, 0 where absent."""
    monkeypatch.setattr("scripts.replay_runner.run_replay_day", _fake_day)
    monkeypatch.setattr("scripts.replay_runner.performance_summary", lambda *_: {})

    _run(_cache(tmp_path / "cache"), tmp_path / "out", progress_every=0)

    with (tmp_path / "out" / "sessions.csv").open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or ())
        rows = list(reader)
    reason_columns = [name for name in header if name.startswith("rejected_")]
    assert reason_columns == [
        "rejected_cash_buffer",
        "rejected_sector_concentration",
        "rejected_sector_name_count",
    ]
    assert [[row[name] for name in reason_columns] for row in rows] == [
        ["0", "2", "0"],
        ["1", "0", "0"],
        ["0", "0", "0"],
        ["1", "0", "1"],
        ["0"] * 3,
    ]
    summary = json.loads((tmp_path / "out" / "summary.json").read_text("utf-8"))
    assert summary["absent_inputs"]["fundamentals"] == 3 * len(SESSIONS)


def test_a12_progress_lands_at_the_interval_and_the_end_on_stderr_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """RPT-OUT-07: progress is stderr only; outputs are byte-identical without it."""
    monkeypatch.setattr("scripts.replay_runner.run_replay_day", _fake_day)
    monkeypatch.setattr("scripts.replay_runner.performance_summary", lambda *_: {})
    cache = _cache(tmp_path / "cache")

    _run(cache, tmp_path / "quiet", progress_every=0)
    assert capsys.readouterr().err == ""
    _run(cache, tmp_path / "loud", progress_every=2)

    captured = capsys.readouterr()
    progress = [line.split()[3] for line in captured.err.splitlines()]
    assert progress == ["2/5", "4/5", "5/5"]
    assert captured.out == ""
    for name in ("equity.csv", "fills.csv", "sessions.csv", "summary.json"):
        assert cmp(tmp_path / "quiet" / name, tmp_path / "loud" / name, shallow=False)


def _cache(cache: Path) -> Path:
    cache.mkdir()
    membership = MembershipResult(
        episodes=(Episode("AAA", "AAA", SESSIONS[0], SESSIONS[-1]),),
        members_by_session=dict.fromkeys(SESSIONS, ("AAA",)),
        unreconciled=(),
        count_min=1,
        count_max=1,
    )
    write_universe_cache(
        cache,
        SESSIONS,
        membership,
        tuple(BarRow("AAA", "AAA", day, 10, 11, 9, 10, 100) for day in SESSIONS),
        {},
    )
    _write_csv(
        cache / "sp500_benchmark.csv.gz",
        ["symbol", "date", "open", "high", "low", "close", "volume"],
        [["SPY", day.isoformat(), 1, 1, 1, 1, 100] for day in SESSIONS],
    )
    _write_csv(cache / "sp500_vix.csv.gz", ["date", "vix_close"], [[SESSIONS[0], 19]])
    return cache


def _write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    path.write_bytes(gzip.compress(buffer.getvalue().encode("utf-8")))
