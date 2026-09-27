"""Tests for S237 replay runner progress and session counters.

Agent: tooling
Role: verify session count columns and stderr-only replay progress.
External I/O: local tmp files only.
"""

from __future__ import annotations

import csv
import gzip
import io
from datetime import date
from filecmp import cmp
from types import SimpleNamespace
from typing import TYPE_CHECKING

from scripts.replay_runner import run
from scripts.replay_universe_cache import write_universe_cache
from scripts.sp500_bars import BarRow
from scripts.sp500_membership import Episode, MembershipResult

from contracts.common import Explanation, Money
from contracts.portfolio_manager import OrderIntent

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_sessions_csv_counts_pipeline_outputs_and_progress_is_stderr_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """RPT-OUT-07 / SCAN-OBS-01 / PM-OUT-03: sessions.csv counts results."""
    cache = _cache(tmp_path / "cache")

    def fake_day(inputs: object, settings: object) -> object:
        del inputs, settings
        return SimpleNamespace(
            absent_inputs={},
            candidates=SimpleNamespace(candidates=(object(), object())),
            recommendations=SimpleNamespace(
                recommendations=(
                    SimpleNamespace(action="buy"),
                    SimpleNamespace(action="hold"),
                    SimpleNamespace(action="sell"),
                )
            ),
            approved=(
                OrderIntent(
                    ticker="AAA",
                    action="buy",
                    quantity=1,
                    est_price=Money(amount=10),
                    stop_pct=0.05,
                    target_pct=0.1,
                    rationale=Explanation(summary="buy", evidence_refs=("fixture",)),
                ),
                OrderIntent(
                    ticker="BBB",
                    action="sell",
                    quantity=1,
                    est_price=Money(amount=20),
                    stop_pct=0.05,
                    target_pct=0.1,
                    rationale=Explanation(summary="sell", evidence_refs=("fixture",)),
                ),
            ),
            rejected=(
                SimpleNamespace(reason="sector_concentration"),
                SimpleNamespace(reason="sector_concentration"),
                SimpleNamespace(reason="cash_buffer"),
            ),
        )

    monkeypatch.setattr("scripts.replay_runner.run_replay_day", fake_day)
    monkeypatch.setattr("scripts.replay_runner.performance_summary", lambda *_: {})

    out_quiet = tmp_path / "out-quiet"
    out_progress = tmp_path / "out-progress"
    run(
        cache_dir=cache,
        out=out_quiet,
        start=date(2020, 1, 2),
        end=date(2020, 1, 3),
        overrides=(),
        progress_every=0,
    )
    run(
        cache_dir=cache,
        out=out_progress,
        start=date(2020, 1, 2),
        end=date(2020, 1, 3),
        overrides=(),
        progress_every=1,
    )

    captured = capsys.readouterr()
    assert "replay progress 2020-01-02 1/2" in captured.err
    assert "replay progress 2020-01-03 2/2" in captured.err
    for filename in ("equity.csv", "fills.csv", "sessions.csv", "summary.json"):
        assert cmp(out_quiet / filename, out_progress / filename, shallow=False)
    rows = list(csv.DictReader((out_progress / "sessions.csv").open()))
    assert rows[0]["members"] == "2"
    assert rows[0]["candidates"] == "2"
    assert rows[0]["recommendations_buy"] == "1"
    assert rows[0]["recommendations_hold"] == "1"
    assert rows[0]["recommendations_sell"] == "1"
    assert rows[0]["approved_buy"] == "1"
    assert rows[0]["approved_sell"] == "1"
    assert rows[0]["rejected_cash_buffer"] == "1"
    assert rows[0]["rejected_sector_concentration"] == "2"


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
