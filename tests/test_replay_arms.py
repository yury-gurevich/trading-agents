"""S250: the arms manifest is Appendix P, and the arms command records what it ran.

Agent: tooling
Role: prove exp014_arms.json and the scorer's defaults; run arms with a fake runner.
External I/O: local tmp files only.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
from datetime import date
from typing import TYPE_CHECKING, Any

import pytest
from scripts.replay_arms import load_manifest, main, run_arm, select
from scripts.replay_arms_record import RepoState
from scripts.replay_settings import build_effective_settings
from scripts.replay_verdict_rule import ABLATION_ARMS, BASE_ARM
from scripts.replay_verdict_score import MEAN_BLOCK, RESAMPLES, SEED

from agents.analyst.settings import AnalystSettings

if TYPE_CHECKING:
    from pathlib import Path

SESSIONS = (date(2017, 1, 3), date(2017, 1, 4), date(2017, 1, 5))
CLEAN = RepoState("a" * 40, dirty=False)


def test_c14_the_manifest_is_appendix_p() -> None:
    """S250-C14: Appendix P's five arms (names, slippage, overrides) and bootstrap."""
    manifest = load_manifest()

    assert [(arm.name, arm.slippage_bps, arm.overrides) for arm in manifest.arms] == [
        ("base-05", 5, ()),
        ("base-10", 10, ()),
        ("base-25", 25, ()),
        ("technical-only-25", 25, ("ANALYST_RELATIVE_STRENGTH_WEIGHT=0.0",)),
        ("relative-strength-only-25", 25, ("ANALYST_RELATIVE_STRENGTH_WEIGHT=1.0",)),
    ]
    assert (manifest.experiment, manifest.start, manifest.require_history) == (
        "EXP-014",
        date(2017, 1, 3),
        True,
    )
    weights = [
        build_effective_settings(arm.overrides).analyst.relative_strength_weight
        for arm in manifest.arms
    ]
    live = AnalystSettings().relative_strength_weight
    assert weights == [live, live, live, 0.0, 1.0]
    assert (BASE_ARM, ABLATION_ARMS) == (
        "base-25",
        ("technical-only-25", "relative-strength-only-25"),
    )
    assert (MEAN_BLOCK, RESAMPLES, SEED) == (20, 10_000, 0)


def _cache(cache: Path) -> Path:
    cache.mkdir()
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["symbol", "date", "open", "high", "low", "close", "volume"])
    writer.writerows(
        ["SPY", day.isoformat(), 1, 1, 1, 300 + index, 100]
        for index, day in enumerate(SESSIONS)
    )
    (cache / "sp500_benchmark.csv.gz").write_bytes(
        gzip.compress(buffer.getvalue().encode("utf-8"))
    )
    for name in ("sp500_bars.csv.gz", "sp500_sessions.csv.gz", "sp500_vix.csv.gz"):
        (cache / name).write_bytes(name.encode("utf-8"))
    return cache


class FakeRunner:
    """Stands in for `replay_runner.run`: records its arguments, writes equity.csv."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        out = kwargs["out"]
        out.mkdir(parents=True)
        rows = "".join(f"{day.isoformat()},1000,800\n" for day in SESSIONS)
        (out / "equity.csv").write_text(
            "date,equity_cents,long_cents\n" + rows, encoding="utf-8"
        )
        return {}


def test_c16_the_arms_command_records_what_it_ran(tmp_path: Path) -> None:
    """S250-C16: one named arm runs with its slippage, overrides, start, rule on."""
    cache, runner = _cache(tmp_path / "cache"), FakeRunner()
    manifest = load_manifest()
    (spec,) = select(manifest, "technical-only-25")

    out = run_arm(
        spec,
        manifest,
        cache_dir=cache,
        out_root=tmp_path / "arms",
        runner=runner,
        repo=lambda: CLEAN,
        progress_every=0,
    )

    assert out == tmp_path / "arms" / "technical-only-25"
    assert runner.calls == [
        {
            "cache_dir": cache,
            "out": out,
            "start": date(2017, 1, 3),
            "end": None,
            "overrides": ("ANALYST_RELATIVE_STRENGTH_WEIGHT=0.0",),
            "slippage_bps": 25,
            "progress_every": 0,
            "require_history": True,
        }
    ]
    bars = hashlib.sha256(b"sp500_bars.csv.gz").hexdigest()[:12]
    record = json.loads((out / "arm.json").read_text(encoding="utf-8"))
    assert record == {
        "arm": "technical-only-25",
        "cache": {
            "sp500_bars.csv.gz": bars,
            "sp500_benchmark.csv.gz": record["cache"]["sp500_benchmark.csv.gz"],
            "sp500_coverage.json": "absent",
            "sp500_membership.csv.gz": "absent",
            "sp500_sectors.csv.gz": "absent",
            "sp500_sessions.csv.gz": hashlib.sha256(
                b"sp500_sessions.csv.gz"
            ).hexdigest()[:12],
            "sp500_vix.csv.gz": hashlib.sha256(b"sp500_vix.csv.gz").hexdigest()[:12],
        },
        "commit": "a" * 40,
        "dirty": False,
        "experiment": "EXP-014",
        "first_session": "2017-01-03",
        "last_session": "2017-01-05",
        "overrides": ["ANALYST_RELATIVE_STRENGTH_WEIGHT=0.0"],
        "require_history": True,
        "sessions": 3,
        "slippage_bps": 25,
        "start": "2017-01-03",
    }
    assert (out / "benchmark.csv").read_text(encoding="utf-8") == (
        "date,close\n2017-01-03,300.0\n2017-01-04,301.0\n2017-01-05,302.0\n"
    )


def test_c16_an_unknown_arm_and_a_dirty_worktree_are_refused(tmp_path: Path) -> None:
    """S250-C16: an unknown name is refused; a dirty worktree never starts an arm."""
    manifest = load_manifest()
    with pytest.raises(ValueError, match="unknown arm 'base-50'"):
        select(manifest, "base-50")
    runner = FakeRunner()
    with pytest.raises(ValueError, match="uncommitted changes"):
        run_arm(
            manifest.arms[0],
            manifest,
            cache_dir=_cache(tmp_path / "cache"),
            out_root=tmp_path / "arms",
            runner=runner,
            repo=lambda: RepoState("b" * 40, dirty=True),
        )
    assert runner.calls == []


def test_c16_all_runs_every_arm_from_the_command_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S250-C16: `run --arm all` runs the five arms in manifest order."""
    runner = FakeRunner()
    monkeypatch.setattr("scripts.replay_arms.run", runner)
    monkeypatch.setattr("scripts.replay_arms.read_repo_state", lambda: CLEAN)
    cache = _cache(tmp_path / "cache")

    argv = ["run", "--arm", "all", "--out-root", str(tmp_path / "arms")]
    assert main([*argv, "--cache", str(cache), "--progress-every", "0"]) == 0

    assert [call["slippage_bps"] for call in runner.calls] == [5, 10, 25, 25, 25]
    names = sorted(path.name for path in (tmp_path / "arms").iterdir())
    assert names == sorted(arm.name for arm in load_manifest().arms)
