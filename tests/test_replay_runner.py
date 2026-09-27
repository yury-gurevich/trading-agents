"""Tests for S235 replay runner cache slicing and summary counters.

Agent: tooling
Role: verify fixed-list mode and absent-input accounting through the runner.
External I/O: local tmp files only.
"""

from __future__ import annotations

import csv
import gzip
import io
from datetime import date
from types import SimpleNamespace
from typing import TYPE_CHECKING

from scripts.replay_runner import run
from scripts.replay_universe_cache import write_universe_cache
from scripts.sp500_bars import BarRow
from scripts.sp500_membership import Episode, MembershipResult

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_universe_file_limits_decision_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S235-A10: fixed-list mode considers only listed lines with bars."""
    cache = _cache(tmp_path / "cache")
    universe_file = tmp_path / "live99.txt"
    universe_file.write_text("AAA\n", encoding="utf-8")
    observed: list[tuple[str, ...]] = []

    def fake_day(inputs: object, settings: object) -> object:
        del settings
        observed.append(inputs.tickers)  # type: ignore[attr-defined]
        return SimpleNamespace(absent_inputs={}, approved=())

    monkeypatch.setattr("scripts.replay_runner.run_replay_day", fake_day)
    monkeypatch.setattr("scripts.replay_runner.performance_summary", lambda *_: {})

    run(
        cache_dir=cache,
        out=tmp_path / "out",
        start=date(2020, 1, 2),
        end=date(2020, 1, 2),
        overrides=(),
        universe_file=universe_file,
    )

    assert observed == [("AAA",)]


def test_summary_counts_missing_context_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S235-A18: summary names price pillars and context absence counters."""
    cache = _cache(tmp_path / "cache")

    monkeypatch.setattr(
        "scripts.replay_runner.run_replay_day",
        lambda *_: SimpleNamespace(absent_inputs={}, approved=()),
    )
    monkeypatch.setattr("scripts.replay_runner.performance_summary", lambda *_: {})

    summary = run(
        cache_dir=cache,
        out=tmp_path / "out",
        start=date(2020, 1, 2),
        end=date(2020, 1, 3),
        overrides=(),
    )

    assert summary["absent_inputs"]["pillars_present"] == [
        "technical",
        "relative_strength",
    ]
    assert summary["absent_inputs"]["member_sessions_without_sector"] == 4
    assert summary["absent_inputs"]["sessions_without_vix"] == 1
    assert summary["absent_inputs"]["gap_marks"] == 0
    assert summary["absent_inputs"]["adjustment_error_rebases"] == 0
    assert summary["absent_inputs"]["expired_no_bar"] == 0
    assert summary["absent_inputs"]["buy_without_stop"] == 0


def _cache(cache: Path) -> Path:
    cache.mkdir()
    sessions = (date(2020, 1, 2), date(2020, 1, 3))
    membership = MembershipResult(
        episodes=(
            Episode("AAA", "AAA", sessions[0], sessions[1]),
            Episode("BBB", "BBB", sessions[0], sessions[1]),
        ),
        members_by_session=dict.fromkeys(sessions, ("AAA", "BBB")),
        unreconciled=(),
        count_min=2,
        count_max=2,
    )
    write_universe_cache(
        cache,
        sessions,
        membership,
        (
            BarRow("AAA", "AAA", sessions[0], 10, 11, 9, 10, 100),
            BarRow("AAA", "AAA", sessions[1], 10, 11, 9, 10, 100),
            BarRow("BBB", "BBB", sessions[0], 20, 21, 19, 20, 100),
            BarRow("BBB", "BBB", sessions[1], 20, 21, 19, 20, 100),
        ),
        {},
    )
    _write_csv(
        cache / "sp500_benchmark.csv.gz",
        ["symbol", "date", "open", "high", "low", "close", "volume"],
        [["SPY", day.isoformat(), 1, 1, 1, 1, 100] for day in sessions],
    )
    _write_csv(cache / "sp500_vix.csv.gz", ["date", "vix_close"], [[sessions[0], 19]])
    return cache


def _write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    path.write_bytes(gzip.compress(buffer.getvalue().encode("utf-8")))
