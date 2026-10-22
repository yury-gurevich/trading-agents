"""S289-A21 through A24: stage records, repeatability and refusal paths.

Agent: tooling
Role: exercise stage I/O with synthetic panels and an injected trainer.
External I/O: temporary directories outside the worktree only.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import pytest
from scripts import exp015
from scripts import exp015_stages as stages
from scripts.exp015_store import load_panel, panel_digest, save_panel
from scripts.replay_arms_record import RepoState
from scripts.sp500_guards import KnownMove
from tests.exp015_fixtures import replay_fixture, stage_panel, trainer


def clean_tree(monkeypatch):
    monkeypatch.setattr(
        stages, "read_repo_state", lambda: RepoState("synthetic-commit", False)
    )


def prepare_walk(out, monkeypatch):
    clean_tree(monkeypatch)
    save_panel(out, stage_panel())
    return stages.walk_forward_stage(out, trainer, (2018, 2019), resamples=200)


def test_a21_panel_stage_record(tmp_path, monkeypatch):
    """S289-A21: panel.json pins the commit, cache checksums and saved-array digest."""
    clean_tree(monkeypatch)
    context, _, _ = replay_fixture()
    monkeypatch.setattr(stages, "load_replay_cache", lambda _: context)
    checksums = {"sp500_bars.csv.gz": "synthetic-checksum"}
    monkeypatch.setattr(stages, "cache_checksums", lambda _: checksums)
    monkeypatch.setattr(
        stages,
        "load_known_moves",
        lambda: (
            KnownMove(
                "L03", context.universe.sessions[252], "adjustment-error", "synthetic"
            ),
            KnownMove("L04", context.universe.sessions[252], "event", "synthetic"),
        ),
    )
    record = stages.panel_stage(tmp_path / "synthetic-cache", tmp_path)
    panel = load_panel(tmp_path)
    assert record == json.loads((tmp_path / "panel.json").read_text(encoding="utf-8"))
    assert record["commit"] == "synthetic-commit"
    assert record["experiment"] == "EXP-015"
    assert record["cache"] == checksums
    assert record["panel_sha256"] == panel_digest(panel)
    assert record["rows"] == len(panel.lines) > 0
    assert record["primary_rows"] == int(panel.primary.sum())
    assert record["secondary_rows"] == int(panel.secondary.sum())
    assert record["first_session"] == panel.sessions[0]
    assert record["last_session"] == panel.sessions[-1]


def test_a22_walk_forward_is_byte_stable(tmp_path, monkeypatch):
    """S289-A22: two real stage runs have identical JSON/Markdown bytes and SHA-256."""
    first = prepare_walk(tmp_path, monkeypatch)
    path = tmp_path / stages.WALK_FORWARD
    data, page = path.read_bytes(), (tmp_path / "walk_forward.md").read_bytes()
    second = stages.walk_forward_stage(tmp_path, trainer, (2018, 2019), resamples=200)
    assert first == second == hashlib.sha256(data).hexdigest()
    assert path.read_bytes() == data
    assert (tmp_path / "walk_forward.md").read_bytes() == page
    record = json.loads(data)
    assert record["verdict"] == "PENDING HOLDOUT"
    assert record["reading"]["control"]["passed"]
    assert record["reading"]["bar1"]
    assert not record["reading"]["bar2"]
    assert record["reading"]["folds"] == 2
    assert (
        len(record["folds"]) == len(record["control"]) == len(record["secondary"]) == 2
    )
    assert b"PENDING HOLDOUT" in page
    assert b"Secondary universe" in page
    assert "2018" in record["folds"][0]["test_first"]
    assert all(d < "2020" for fold in record["folds"] for d in fold["ic"]["ensemble"])


def test_a23_holdout_guards_and_one_touch(tmp_path, monkeypatch):
    """S289-A23: refuse wrong digest, stopped walk and second touch before training."""
    digest = prepare_walk(tmp_path, monkeypatch)
    path = tmp_path / stages.WALK_FORWARD
    original = path.read_bytes()
    calls = []

    def observed_trainer(x, y):
        calls.append(len(x))
        return trainer(x, y)

    with pytest.raises(ValueError, match="recorded one"):
        stages.holdout_stage(tmp_path, "wrong", observed_trainer)
    assert calls == []
    assert not (tmp_path / stages.HOLDOUT).exists()
    stopped = json.loads(original)
    stopped["verdict"] = "STOPPED"
    path.write_text(json.dumps(stopped), encoding="utf-8")
    stopped_digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="experiment stopped"):
        stages.holdout_stage(tmp_path, stopped_digest, observed_trainer)
    assert calls == []
    assert not (tmp_path / stages.HOLDOUT).exists()
    path.write_bytes(original)
    result = stages.holdout_stage(tmp_path, digest, observed_trainer, date(2020, 1, 2))
    assert len(calls) == 2
    assert result["walk_forward_sha256"] == digest
    assert result == json.loads((tmp_path / stages.HOLDOUT).read_text(encoding="utf-8"))
    assert (tmp_path / "verdict.md").exists()
    before = (tmp_path / stages.HOLDOUT).read_bytes()
    with pytest.raises(ValueError, match="touched already"):
        stages.holdout_stage(tmp_path, digest, observed_trainer, date(2020, 1, 2))
    assert len(calls) == 2
    assert (tmp_path / stages.HOLDOUT).read_bytes() == before


def test_a24_dirty_tree_and_command_line(tmp_path, monkeypatch, capsys):
    """S289-A24: dirty stages, worktree output, required CLI arguments are refused."""
    monkeypatch.setattr(stages, "read_repo_state", lambda: RepoState("dirty", True))
    for run in (
        lambda: stages.panel_stage(tmp_path / "cache", tmp_path),
        lambda: stages.walk_forward_stage(tmp_path, trainer, (2018,)),
    ):
        with pytest.raises(ValueError, match="uncommitted"):
            run()
    root = Path(stages.__file__).resolve().parents[1]
    with pytest.raises(ValueError, match="inside the worktree"):
        exp015.main(["panel", "--out", str(root)])
    for args, message in (
        (["panel"], "panel needs --cache"),
        (["holdout"], "holdout needs --walk-forward-sha256"),
    ):
        with pytest.raises(SystemExit) as error:
            exp015.main([*args, "--out", str(tmp_path)])
        assert error.value.code == 2
        assert message in capsys.readouterr().err
