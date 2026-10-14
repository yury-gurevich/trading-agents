"""Regression proof that a gate self-test run leaves no probe path, or fails.

Agent: tests
Role: prove a locked probe folder is removed and a leftover fails the run.
External I/O: temporary files, their permission bits and two symbolic links.
"""

from __future__ import annotations

import shutil
import stat
import sys
from typing import TYPE_CHECKING

import pytest
from scripts import gate_selftest as runner
from scripts import gate_selftest_cleanup as cleanup
from scripts.gate_selftest_types import PROBE_PREFIX

if TYPE_CHECKING:
    from pathlib import Path

LOCKED = stat.S_IREAD | stat.S_IEXEC


def _locked_probe(root: Path) -> Path:
    """Build a probe folder as one checkout held it: its owner may change none of it."""
    probe = root / "scripts" / f"{PROBE_PREFIX}_locked"
    cache = probe / "agents" / "probe" / "__pycache__"
    cache.mkdir(parents=True)
    compiled = cache / "settings.pyc"
    compiled.write_bytes(b"compiled")
    compiled.chmod(stat.S_IREAD)
    for folder in (cache, cache.parent, cache.parent.parent, probe):
        folder.chmod(LOCKED)
    return probe


def _empty_run(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setattr(runner, "_ROOT", root)
    monkeypatch.setattr(runner, "CASES", ())
    monkeypatch.setattr(runner, "ALL_INVARIANTS", ())


def test_sweep_removes_probe_folder_its_owner_may_not_change(tmp_path: Path) -> None:
    """L1: a read-only probe folder goes, where plain removal leaves it whole."""
    probe = _locked_probe(tmp_path)
    shutil.rmtree(probe, ignore_errors=True)
    if not probe.exists():
        pytest.skip("this account removes a folder it may not change: nothing to prove")
    assert (probe / "agents/probe/__pycache__/settings.pyc").is_file()
    assert runner.sweep_stale_probes(tmp_path) == []
    assert not probe.exists()
    assert (tmp_path / "scripts").is_dir()


@pytest.mark.skipif(sys.platform == "win32", reason="a link needs a privilege here")
def test_sweep_leaves_what_a_link_in_a_probe_folder_points_at(tmp_path: Path) -> None:
    """L2: a link inside a probe folder goes; its target keeps its bits and content."""
    kept = tmp_path / "kept"
    kept.mkdir()
    kept_file = kept / "file.txt"
    kept_file.write_text("kept\n", encoding="utf-8")
    kept_file.chmod(0o444)
    kept.chmod(0o555)
    probe = tmp_path / "scripts" / f"{PROBE_PREFIX}_linked"
    probe.mkdir(parents=True)
    (probe / "folder_link").symlink_to(kept, target_is_directory=True)
    (probe / "file_link").symlink_to(kept_file)
    runner.sweep_stale_probes(tmp_path)
    assert not probe.exists()
    assert stat.S_IMODE(kept.stat().st_mode) == 0o555
    assert stat.S_IMODE(kept_file.stat().st_mode) == 0o444
    assert kept_file.read_text(encoding="utf-8") == "kept\n"


def test_probes_left_names_each_probe_path_outside_git(tmp_path: Path) -> None:
    """L3: every probe path is named from the root; git's own folder is not read."""
    folder = tmp_path / "scripts" / f"{PROBE_PREFIX}_dir"
    page = tmp_path / "docs" / f"{PROBE_PREFIX}.md"
    hidden = tmp_path / ".git" / f"{PROBE_PREFIX}_keep"
    for path in (folder, page.parent, hidden):
        path.mkdir(parents=True)
    page.write_text("probe\n", encoding="utf-8")
    assert cleanup.probes_left(tmp_path) == [
        str(page.relative_to(tmp_path)),
        str(folder.relative_to(tmp_path)),
    ]


def test_run_fails_and_names_a_probe_path_it_could_not_remove(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """L4: a probe folder that outlives the run turns the run red and is named."""
    _empty_run(monkeypatch, tmp_path)
    monkeypatch.setattr(runner, "remove_probe_dirs", lambda _root: None)
    probe = tmp_path / "scripts" / f"{PROBE_PREFIX}_held"
    probe.mkdir(parents=True)
    assert runner.main() == 1
    printed = capsys.readouterr().out
    named = f"left behind: {probe.relative_to(tmp_path)}"
    assert f"FAIL  cleanup: no-probe-path-left — {named}" in printed
    assert "gate self-test: 0/1 passed" in printed


def test_run_passes_and_says_so_when_no_probe_path_is_left(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """L5: a run that removed its probes reads one more check passed."""
    _empty_run(monkeypatch, tmp_path)
    (tmp_path / "scripts" / f"{PROBE_PREFIX}_stale").mkdir(parents=True)
    assert runner.main() == 0
    printed = capsys.readouterr().out
    assert "PASS  cleanup: no-probe-path-left — the tree holds none" in printed
    assert "gate self-test: 1/1 passed" in printed
